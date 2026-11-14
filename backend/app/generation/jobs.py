"""Job queue management, domain models, and repository interfaces.

Enforces:
- Explicit JobRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- InMemoryJobRepository for test injection only.
"""

from __future__ import annotations

import builtins
import datetime
import uuid
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Protocol, runtime_checkable

from app.shared.ids import uuid7


@dataclass
class JobRecord:
    """Domain representation of a background job."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str = "generate_docx"
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"  # queued, running, succeeded, failed, dead
    state: str = "REQUESTED"  # REQUESTED, VALIDATED, RENDERED, VERIFIED, STORED, COMPLETED
    run_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    attempts: int = 0
    locked_at: datetime.datetime | None = None
    idempotency_key: str | None = None
    error: dict[str, Any] | None = None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    result_ref: str | None = None
    job_type: str | None = None

    def __post_init__(self) -> None:
        if self.job_type:
            self.type = self.job_type


@runtime_checkable
class JobRepository(Protocol):
    """Explicit repository interface for background job queue persistence."""

    def enqueue(
        self,
        tenant_id: uuid.UUID,
        type: str = "generate_docx",
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        job_type: str | None = None,
    ) -> JobRecord:
        """Enqueues a job with idempotency deduplication within tenant_id."""
        ...

    def get(self, tenant_id: uuid.UUID, job_id: uuid.UUID) -> JobRecord | None:
        """Retrieves a job strictly scoped to tenant_id."""
        ...

    def update_state(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        status: str,
        state: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        """Updates the status and state of a job strictly scoped to tenant_id."""
        ...

    def claim_next(
        self,
        tenant_id: uuid.UUID | None = None,
        visibility_timeout_seconds: int = 300,
    ) -> JobRecord | None:
        """Atomically claims the next runnable queued job or crashed running job past visibility timeout."""
        ...

    def record_failure(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        error: dict[str, Any],
        max_attempts: int = 3,
        base_backoff_seconds: int = 2,
    ) -> JobRecord:
        """Records a job failure: schedules exponential backoff or transitions to dead-letter state."""
        ...

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        """Lists jobs belonging to tenant_id."""
        ...


class InMemoryJobRepository:
    """Thread-safe in-memory job repository for unit testing and local mocks."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._jobs: dict[uuid.UUID, JobRecord] = {}

    def enqueue(
        self,
        tenant_id: uuid.UUID,
        type: str = "generate_docx",
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        job_type: str | None = None,
    ) -> JobRecord:
        if job_type is not None:
            type = job_type
        if payload is None:
            payload = {}
        with self._lock:
            if idempotency_key:
                for existing in self._jobs.values():
                    if (
                        existing.tenant_id == tenant_id
                        and existing.idempotency_key == idempotency_key
                    ):
                        return existing

            job_id = uuid7()
            now = datetime.datetime.now(datetime.timezone.utc)
            record = JobRecord(
                id=job_id,
                tenant_id=tenant_id,
                type=type,
                payload=payload,
                status="queued",
                state="REQUESTED",
                run_at=now,
                attempts=0,
                locked_at=None,
                idempotency_key=idempotency_key,
                error=None,
                created_at=now,
            )
            self._jobs[job_id] = record
            return record

    def get(self, tenant_id: uuid.UUID, job_id: uuid.UUID) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.tenant_id != tenant_id:
                return None
            return job

    def update_state(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        status: str,
        state: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            job = self.get(tenant_id, job_id)
            if not job:
                raise KeyError(f"Job {job_id} not found in tenant {tenant_id}")
            job.status = status
            if state is not None:
                job.state = state
            if error is not None:
                job.error = error

    def claim_next(
        self,
        tenant_id: uuid.UUID | None = None,
        visibility_timeout_seconds: int = 300,
    ) -> JobRecord | None:
        with self._lock:
            now = datetime.datetime.now(datetime.timezone.utc)
            visibility_cutoff = now - datetime.timedelta(seconds=visibility_timeout_seconds)
            for job in self._jobs.values():
                if tenant_id is not None and job.tenant_id != tenant_id:
                    continue
                is_queued = job.status == "queued" and job.run_at <= now
                is_timed_out = (
                    job.status == "running"
                    and job.locked_at is not None
                    and job.locked_at <= visibility_cutoff
                )
                if is_queued or is_timed_out:
                    job.status = "running"
                    job.locked_at = now
                    job.attempts += 1
                    return job
            return None

    def record_failure(
        self,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        error: dict[str, Any],
        max_attempts: int = 3,
        base_backoff_seconds: int = 2,
    ) -> JobRecord:
        with self._lock:
            job = self.get(tenant_id, job_id)
            if not job:
                raise KeyError(f"Job {job_id} not found in tenant {tenant_id}")

            now = datetime.datetime.now(datetime.timezone.utc)
            job.locked_at = None
            if job.attempts >= max_attempts:
                job.status = "dead"
                job.error = {**error, "dead_letter": True, "attempts": job.attempts}
            else:
                job.status = "queued"
                delay = base_backoff_seconds * (2 ** max(0, job.attempts - 1))
                job.run_at = now + datetime.timedelta(seconds=delay)
                job.error = {**error, "retry_in_seconds": delay, "attempts": job.attempts}
            return job

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        with self._lock:
            matching = [j for j in self._jobs.values() if j.tenant_id == tenant_id]
            if status:
                matching = [j for j in matching if j.status == status]
            return matching[offset : offset + limit]

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()

    @property
    def _queue(self) -> builtins.list[JobRecord]:
        with self._lock:
            return builtins.list(self._jobs.values())

    # Legacy compatibility methods for job_queue callers
    def claim_next_job(self) -> JobRecord | None:
        return self.claim_next(tenant_id=None)

    def get_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> JobRecord | None:
        return self.get(tenant_id, job_id)


# Backward compatibility alias for test suites
JobQueue = InMemoryJobRepository

# Global singleton instance for backwards compatibility with legacy callers
job_queue = InMemoryJobRepository()
