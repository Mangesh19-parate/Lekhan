"""Background worker process executing asynchronous jobs (docs/ARCHITECTURE.md Section 1).

Claims queued jobs using transactional locking (FOR UPDATE SKIP LOCKED)
with visibility timeouts for crashed workers, exponential backoff, and dead-letter state.
Executes the generation pipeline FSM idempotently with atomic file writes.
Uses PostgresDocumentRepository to ensure consistent storage between Worker and API.
"""

from __future__ import annotations

import signal
import subprocess
import time
from typing import Any

from app.adapters.db import current_tenant_id_ctx
from app.adapters.pdf import LibreOfficeNotFoundError, PdfConversionTimeoutError
from app.adapters.repositories.documents import PostgresDocumentRepository
from app.adapters.repositories.jobs import PostgresJobRepository
from app.generation.jobs import JobRepository
from app.generation.pipeline import GenerationPipelineFSM, GenerationTimeoutError
from app.generation.repository import DocumentRepository
from app.shared.logging import get_correlation_id, get_logger, setup_logging

setup_logging()
logger = get_logger("worker")

_shutdown_requested = False


def _sig_handler(signum: int, frame: Any) -> None:
    global _shutdown_requested
    logger.info("Shutdown signal received (%d). Finishing current job and exiting gracefully...", signum)
    _shutdown_requested = True


def get_default_worker_pipeline() -> GenerationPipelineFSM:
    """Instantiates pipeline with production persistent PostgresDocumentRepository."""
    return GenerationPipelineFSM(repository=PostgresDocumentRepository())


def classify_job_exception(exc: Exception) -> tuple[str, str, bool]:
    """Classifies an exception into a safe error code, customer-safe message, and transient flag.

    Never leaks raw exception strings, file paths, or internal variables to clients.
    """
    if isinstance(exc, ValueError):
        return "VALIDATION_FAILED", "Document input validation failed.", False
    if isinstance(exc, KeyError):
        return "PAYLOAD_ERROR", "Required generation parameter missing.", False
    if isinstance(exc, LibreOfficeNotFoundError):
        return "CONVERTER_MISSING", "Document conversion utility not available.", False
    if isinstance(exc, (PdfConversionTimeoutError, GenerationTimeoutError, subprocess.TimeoutExpired, TimeoutError)):
        return "CONVERTER_TIMEOUT", "Document generation or conversion timed out.", True
    err_type_name = type(exc).__name__
    if "OperationalError" in err_type_name or "DBAPIError" in err_type_name:
        return "DATABASE_TIMEOUT", "Database service temporarily unavailable.", True

    return "GENERATION_ERROR", "Document generation encountered a temporary failure.", True


def run_worker_once(
    repo: JobRepository | None = None,
    pipeline: GenerationPipelineFSM | None = None,
    visibility_timeout_seconds: int = 300,
    max_attempts: int = 3,
) -> bool:
    """Claims and executes a single pending job. Returns True if a job was processed."""
    active_repo = repo if repo is not None else PostgresJobRepository()
    active_pipeline = pipeline if pipeline is not None else get_default_worker_pipeline()

    job = active_repo.claim_next(
        tenant_id=None,
        visibility_timeout_seconds=visibility_timeout_seconds,
    )
    if not job:
        return False

    # Establish tenant context for RLS and logging
    current_tenant_id_ctx.set(job.tenant_id)
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
            doc = active_pipeline.process_job(job)
            active_repo.update_state(
                tenant_id=job.tenant_id,
                job_id=job.id,
                status="succeeded",
                state=job.state or "COMPLETED",
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
                error={
                    "code": "UNKNOWN_JOB_TYPE",
                    "message": f"Unsupported job type: {job.type}",
                    "correlation_id": cid,
                    "dead_letter": True,
                },
            )
    except Exception as exc:
        code, safe_msg, is_transient = classify_job_exception(exc)
        logger.exception(
            "Job %s failed with %s (code=%s, transient=%s) [cid=%s]: %s",
            job.id,
            type(exc).__name__,
            code,
            is_transient,
            cid,
            exc,
        )

        error_payload = {
            "code": code,
            "message": safe_msg,
            "correlation_id": cid,
        }

        if is_transient:
            active_repo.record_failure(
                tenant_id=job.tenant_id,
                job_id=job.id,
                error=error_payload,
                max_attempts=max_attempts,
            )
        else:
            active_repo.update_state(
                tenant_id=job.tenant_id,
                job_id=job.id,
                status="failed",
                error={
                    **error_payload,
                    "retryable": False,
                    "dead_letter": True,
                    "attempts": job.attempts,
                },
            )
    finally:
        current_tenant_id_ctx.set(None)

    return True


def run_worker_loop(visibility_timeout_seconds: int = 300, max_attempts: int = 3) -> None:
    """Continuous polling loop for worker daemon with graceful shutdown and heartbeat."""
    global _shutdown_requested
    try:
        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)
    except (ValueError, AttributeError):
        pass  # On platforms or threads where signal handling is restricted

    logger.info("Lekhan background worker daemon started (Postgres persistence wired).")
    last_heartbeat = time.time()

    while not _shutdown_requested:
        processed = run_worker_once(
            visibility_timeout_seconds=visibility_timeout_seconds,
            max_attempts=max_attempts,
        )
        now = time.time()
        if now - last_heartbeat > 60.0:
            logger.info("Worker heartbeat: active and listening for queued jobs.")
            last_heartbeat = now

        if not processed:
            time.sleep(1.0)

    logger.info("Worker daemon stopped cleanly.")


if __name__ == "__main__":
    run_worker_loop()
