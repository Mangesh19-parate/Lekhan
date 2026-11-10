"""Background worker process executing asynchronous jobs (docs/ARCHITECTURE.md Section 1).

Claims queued jobs using transactional locking (FOR UPDATE SKIP LOCKED)
and executes the generation pipeline FSM.
"""

from __future__ import annotations

import time

from app.generation.jobs import job_queue
from app.generation.pipeline import generation_pipeline
from app.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("worker")


def run_worker_once() -> bool:
    """Claims and executes a single pending job. Returns True if a job was processed."""
    job = job_queue.claim_next_job()
    if not job:
        return False

    logger.info("Claimed job %s (type: %s, tenant: %s)", job.id, job.type, job.tenant_id)
    try:
        if job.type == "generate_docx":
            doc = generation_pipeline.process_job(job)
            logger.info("Job %s completed successfully. Document reference: %s", job.id, doc.file_ref)
        else:
            logger.warning("Unknown job type: %s", job.type)
            job.status = "dead"
            job.error = {"error": f"Unknown job type: {job.type}"}
    except Exception as e:
        logger.error("Job %s failed with error: %s", job.id, e)

    return True


def run_worker_loop() -> None:
    """Continuous polling loop for worker daemon."""
    logger.info("Lekhan background worker daemon started.")
    while True:
        processed = run_worker_once()
        if not processed:
            time.sleep(1.0)


if __name__ == "__main__":
    run_worker_loop()

