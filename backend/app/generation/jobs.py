"""Job queue management and worker claiming."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from threading import Lock
from typing import Any

from app.shared.ids import uuid7


@dataclass
class JobRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str
    payload: dict[str, Any]
    status: str  # queued, running, succeeded, failed, dead
    state: str  # REQUESTED, VALIDATED, RENDERED, VERIFIED, STORED, COMPLETED
    run_at: datetime.datetime
    attempts: int
    locked_at: datetime.datetime | None
    idempotency_key: str | None
    error: dict[str, Any] | None
    created_at: datetime.datetime
    result_ref: str | None = None


class JobQueue:
    """Thread-safe transactional job queue supporting deduplication and locking."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[uuid.UUID, JobRecord] = {}

    def enqueue(
        self,
        tenant_id: uuid.UUID,
        job_type: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> JobRecord:
        """Enqueues a job with idempotency deduplication."""
        with self._lock:
            # Check idempotency deduplication per tenant
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
                type=job_type,
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

    def claim_next_job(self) -> JobRecord | None:
        """Atomically claims the next runnable queued job (simulating FOR UPDATE SKIP LOCKED)."""
        with self._lock:
            now = datetime.datetime.now(datetime.timezone.utc)
            for job in self._jobs.values():
                if job.status == "queued" and job.run_at <= now:
                    job.status = "running"
                    job.locked_at = now
                    job.attempts += 1
                    return job
            return None

    def get_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> JobRecord | None:
        """Retrieves a job strictly scoped to tenant."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.tenant_id != tenant_id:
                return None
            return job

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()


job_queue = JobQueue()
