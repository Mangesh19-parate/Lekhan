"""Background worker process executing asynchronous jobs (docs/ARCHITECTURE.md Section 1).

Claims queued jobs using transactional locking (FOR UPDATE SKIP LOCKED)
with visibility timeouts for crashed workers, exponential backoff, and dead-letter state.
Executes the generation pipeline FSM idempotently with atomic file writes.
"""

from __future__ import annotations

import time

from app.adapters.repositories.jobs import PostgresJobRepository
from app.generation.jobs import JobRepository
from app.generation.pipeline import generation_pipeline
from app.shared.logging import get_correlation_id, get_logger, setup_logging

setup_logging()
logger = get_logger("worker")


def run_worker_once(
    repo: JobRepository | None = None,
    visibility_timeout_seconds: int = 300,
    max_attempts: int = 3,
) -> bool:
    """Claims and executes a single pending job. Returns True if a job was processed."""
    active_repo = repo if repo is not None else PostgresJobRepository()
    job = active_repo.claim_next(
        tenant_id=None,
        visibility_timeout_seconds=visibility_timeout_seconds,
    )
    if not job:
        return False

    cid = get_correlation_id()
    logger.info(
        "Claimed job %s (type: %s, tenant: %s, attempt: %d) [cid=%s]",
        job.id,
        job.type,
        job.tenant_id,
        job.attempts,
        cid,
    )
    try:
        if job.type == "generate_docx":
            doc = generation_pipeline.process_job(job)
            active_repo.update_state(
                tenant_id=job.tenant_id,
                job_id=job.id,
                status="succeeded",
                state=job.state,
            )
            logger.info(
                "Job %s completed successfully. Document reference: %s [cid=%s]",
                job.id,
                doc.file_ref,
                cid,
            )
        else:
            logger.warning("Unknown job type: %s [cid=%s]", job.type, cid)
            active_repo.update_state(
                tenant_id=job.tenant_id,
                job_id=job.id,
                status="dead",
                error={"error": f"Unknown job type: {job.type}"},
            )
    except Exception as exc:
        logger.exception("Job %s failed with error [cid=%s]: %s", job.id, cid, exc)
        active_repo.record_failure(
            tenant_id=job.tenant_id,
            job_id=job.id,
            error={"error": str(exc)},
            max_attempts=max_attempts,
        )

    return True


def run_worker_loop(visibility_timeout_seconds: int = 300, max_attempts: int = 3) -> None:
    """Continuous polling loop for worker daemon."""
    logger.info("Lekhan background worker daemon started.")
    while True:
        processed = run_worker_once(
            visibility_timeout_seconds=visibility_timeout_seconds,
            max_attempts=max_attempts,
        )
        if not processed:
            time.sleep(1.0)


if __name__ == "__main__":
    run_worker_loop()
