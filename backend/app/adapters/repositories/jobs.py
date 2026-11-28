"""PostgreSQL implementation of the JobRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with the `jobs` table.
Implements transactional job claiming using FOR UPDATE SKIP LOCKED.
Enforces strict tenant scoping on every method.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.generation.jobs import JobRecord
from app.shared.crypto import decrypt_json_payload, encrypt_json_payload
from app.shared.ids import uuid7
from app.shared.models import Job as JobModel


def _to_record(model: JobModel) -> JobRecord:
    """Converts a SQLAlchemy JobModel to domain JobRecord."""
    return JobRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        type=model.type,
        payload=decrypt_json_payload(model.payload),
        status=model.status,
        state=model.state or "REQUESTED",
        run_at=model.run_at,
        attempts=model.attempts,
        locked_at=model.locked_at,
        idempotency_key=model.idempotency_key,
        error=model.error,
        created_at=model.created_at,
    )


class PostgresJobRepository:
    """Production PostgreSQL job repository implementing JobRepository."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session is not None else SessionLocal()

    def enqueue(
        self,
        tenant_id: uuid.UUID,
        type: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> JobRecord:
        session = self._get_session()
        should_close = self._session is None
        try:
            if idempotency_key:
                existing = (
                    session.query(JobModel)
                    .filter(
                        JobModel.tenant_id == tenant_id,
                        JobModel.idempotency_key == idempotency_key,
                    )
                    .first()
                )
                if existing:
                    return _to_record(existing)

            job_id = uuid7()
            now = datetime.datetime.now(datetime.timezone.utc)
            db_job = JobModel(
                id=job_id,
                tenant_id=tenant_id,
                type=type,
                payload=encrypt_json_payload(payload),
                status="queued",
                state="REQUESTED",
                run_at=now,
                attempts=0,
                locked_at=None,
                idempotency_key=idempotency_key,
                error=None,
                created_at=now,
            )
            session.add(db_job)
            session.commit()
            session.refresh(db_job)
            return _to_record(db_job)
        finally:
            if should_close:
                session.close()

    def get(self, tenant_id: uuid.UUID, job_id: uuid.UUID) -> JobRecord | None:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_job = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.tenant_id == tenant_id,
                )
                .first()
            )
            return _to_record(db_job) if db_job else None
        finally:
            if should_close:
                session.close()

    def update_state(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        status: str,
        state: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_job = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.tenant_id == tenant_id,
                )
                .first()
            )
            if not db_job:
                raise KeyError(f"Job {job_id} not found in tenant {tenant_id}")

            db_job.status = status
            if state is not None:
                db_job.state = state
            if error is not None:
                db_job.error = error

            session.commit()
        finally:
            if should_close:
                session.close()

    def claim_next(
        self,
        tenant_id: uuid.UUID | None = None,
        visibility_timeout_seconds: int = 300,
        max_attempts: int = 3,
    ) -> JobRecord | None:
        """Claims the next pending job atomically via FOR UPDATE SKIP LOCKED.

        Includes queued runnable jobs and crashed running jobs whose locked_at
        exceeds the visibility timeout, strictly enforcing max_attempts.
        For cross-tenant worker claiming under least-privilege PostgreSQL RLS,
        invokes the SECURITY DEFINER function `claim_next_job`.
        """
        session = self._get_session()
        should_close = self._session is None
        try:
            bind = session.get_bind()
            if bind is not None and bind.dialect.name == "postgresql" and tenant_id is None:
                stmt = text(
                    """
                    SELECT id, tenant_id, type, payload, status, state, run_at, attempts, locked_at, idempotency_key, error, created_at
                    FROM claim_next_job(:timeout, :max_attempts)
                    """
                )
                row = (
                    session.execute(
                        stmt,
                        {"timeout": visibility_timeout_seconds, "max_attempts": max_attempts},
                    )
                    .mappings()
                    .first()
                )
                if not row:
                    return None
                session.commit()
                return JobRecord(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    type=row["type"],
                    payload=decrypt_json_payload(row["payload"]),
                    status=row["status"],
                    state=row["state"],
                    run_at=row["run_at"],
                    attempts=row["attempts"],
                    locked_at=row["locked_at"],
                    idempotency_key=row["idempotency_key"],
                    error=row["error"],
                    created_at=row["created_at"],
                )

            now = datetime.datetime.now(datetime.timezone.utc)
            visibility_cutoff = now - datetime.timedelta(seconds=visibility_timeout_seconds)

            # Dead-letter crashed jobs that exceeded max_attempts past visibility timeout
            stale_dead_cond = and_(
                JobModel.status == "running",
                JobModel.locked_at <= visibility_cutoff,
                JobModel.attempts >= max_attempts,
            )
            stale_query = session.query(JobModel).filter(stale_dead_cond)
            if tenant_id is not None:
                stale_query = stale_query.filter(JobModel.tenant_id == tenant_id)
            for stale_job in stale_query.all():
                stale_job.status = "dead"
                stale_job.error = {
                    "code": "MAX_ATTEMPTS_EXCEEDED",
                    "message": "Job exceeded maximum retry attempts during background execution",
                }

            claimable_cond = or_(
                and_(
                    JobModel.status == "queued",
                    JobModel.run_at <= now,
                    JobModel.attempts < max_attempts,
                ),
                and_(
                    JobModel.status == "running",
                    JobModel.locked_at <= visibility_cutoff,
                    JobModel.attempts < max_attempts,
                ),
            )

            query = (
                session.query(JobModel)
                .filter(claimable_cond)
                .order_by(JobModel.run_at.asc())
                .with_for_update(skip_locked=True)
            )
            if tenant_id is not None:
                query = query.filter(JobModel.tenant_id == tenant_id)

            db_job = query.first()
            if not db_job:
                session.commit()
                return None

            db_job.status = "running"
            db_job.locked_at = now
            db_job.attempts += 1
            session.commit()
            session.refresh(db_job)
            return _to_record(db_job)
        finally:
            if should_close:
                session.close()

    def record_failure(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        error: dict[str, Any],
        max_attempts: int = 3,
        base_backoff_seconds: int = 2,
    ) -> JobRecord:
        """Handles job failure: calculates exponential backoff or dead-letters the job."""
        session = self._get_session()
        should_close = self._session is None
        try:
            db_job = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.tenant_id == tenant_id,
                )
                .first()
            )
            if not db_job:
                raise KeyError(f"Job {job_id} not found in tenant {tenant_id}")

            now = datetime.datetime.now(datetime.timezone.utc)
            db_job.locked_at = None

            if db_job.attempts >= max_attempts:
                db_job.status = "dead"
                db_job.error = {**error, "dead_letter": True, "attempts": db_job.attempts}
            else:
                db_job.status = "queued"
                delay = base_backoff_seconds * (2 ** max(0, db_job.attempts - 1))
                db_job.run_at = now + datetime.timedelta(seconds=delay)
                db_job.error = {**error, "retry_in_seconds": delay, "attempts": db_job.attempts}

            session.commit()
            session.refresh(db_job)
            return _to_record(db_job)
        finally:
            if should_close:
                session.close()

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        session = self._get_session()
        should_close = self._session is None
        try:
            query = session.query(JobModel).filter(JobModel.tenant_id == tenant_id)
            if status:
                query = query.filter(JobModel.status == status)

            db_jobs = query.order_by(JobModel.created_at.desc()).offset(offset).limit(limit).all()
            return [_to_record(j) for j in db_jobs]
        finally:
            if should_close:
                session.close()
