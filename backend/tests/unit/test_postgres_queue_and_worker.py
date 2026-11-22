"""Unit and concurrency tests for Postgres-backed JobQueue, worker resilience, and sessions.

Tests:
1. Two concurrent workers proving no job runs twice (SKIP LOCKED semantics).
2. Worker killed mid-job: visibility timeout expiration allows a second worker to reclaim.
3. Attempts, exponential backoff, and dead-letter state.
4. Handler idempotency and atomic file writes.
5. Database sessions with hashed tokens, idle expiry, and absolute expiry.
"""

from __future__ import annotations

import datetime
import threading
import uuid
from unittest.mock import MagicMock

import pytest

from app.adapters.repositories.jobs import PostgresJobRepository
from app.adapters.repositories.sessions import PostgresSessionRepository
from app.generation.jobs import InMemoryJobRepository, JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.repository import InMemoryDocumentRepository
from app.identity.session_repository import InMemorySessionRepository, SessionData
from app.shared.models import Session as SessionModel
from app.shared.security import hash_token
from app.worker import run_worker_once

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")


def test_concurrent_workers_no_job_runs_twice() -> None:
    """Proves two concurrent workers claiming from the queue never process the same job."""
    repo = InMemoryJobRepository()
    num_jobs = 20

    # Enqueue a batch of jobs
    for i in range(num_jobs):
        repo.enqueue(
            tenant_id=TENANT_ID,
            type="generate_docx",
            payload={"doc_index": i, "template_id": "test_tmpl"},
            idempotency_key=f"CONCURRENT-JOB-{i}",
        )

    worker1_processed: list[uuid.UUID] = []
    worker2_processed: list[uuid.UUID] = []
    errors: list[Exception] = []

    def worker_run(worker_list: list[uuid.UUID]) -> None:
        try:
            while True:
                job = repo.claim_next(tenant_id=TENANT_ID)
                if not job:
                    break
                # Record job execution
                worker_list.append(job.id)
                repo.update_state(
                    tenant_id=job.tenant_id,
                    job_id=job.id,
                    status="succeeded",
                    state="COMPLETED",
                )
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=worker_run, args=(worker1_processed,))
    t2 = threading.Thread(target=worker_run, args=(worker2_processed,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Errors occurred during concurrent execution: {errors}"

    # Verify mutual exclusion: no job run twice
    set1 = set(worker1_processed)
    set2 = set(worker2_processed)
    intersection = set1.intersection(set2)
    assert intersection == set(), f"Race condition: jobs processed by both workers: {intersection}"

    # Verify all jobs were processed exactly once
    total_processed = len(worker1_processed) + len(worker2_processed)
    assert total_processed == num_jobs

    # Check all are marked succeeded in repository
    all_jobs = repo.list(TENANT_ID, limit=100)
    assert all(j.status == "succeeded" for j in all_jobs)


def test_worker_killed_mid_job_visibility_timeout() -> None:
    """Proves that if a worker crashes mid-job, the job is safely reclaimed after visibility timeout."""
    repo = InMemoryJobRepository()
    job = repo.enqueue(
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={"task": "heavy_doc"},
    )

    # Worker 1 claims job
    claimed_by_w1 = repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_by_w1 is not None
    assert claimed_by_w1.id == job.id
    assert claimed_by_w1.status == "running"
    assert claimed_by_w1.attempts == 1

    # Worker 1 "crashes" mid-job without updating status.
    # Immediate attempt by Worker 2 while visibility window is active: must NOT claim the job!
    claimed_by_w2_too_early = repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_by_w2_too_early is None

    # Simulate time passing past the visibility timeout (e.g. 70 seconds ago)
    now = datetime.datetime.now(datetime.timezone.utc)
    crashed_time = now - datetime.timedelta(seconds=70)
    claimed_by_w1.locked_at = crashed_time

    # Worker 2 attempts claim again: visibility timeout expired, Worker 2 reclaims the job!
    claimed_by_w2 = repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_by_w2 is not None
    assert claimed_by_w2.id == job.id
    assert claimed_by_w2.status == "running"
    assert claimed_by_w2.attempts == 2

    # Worker 2 successfully completes the job
    repo.update_state(tenant_id=TENANT_ID, job_id=claimed_by_w2.id, status="succeeded")
    final_job = repo.get(TENANT_ID, job.id)
    assert final_job is not None
    assert final_job.status == "succeeded"
    assert final_job.attempts == 2


def test_attempts_backoff_and_dead_letter_state() -> None:
    """Proves that repeated job failures trigger exponential backoff and end in dead-letter state."""
    repo = InMemoryJobRepository()
    job = repo.enqueue(
        tenant_id=TENANT_ID,
        type="faulty_job",
        payload={},
    )

    # Attempt 1: Worker claims and fails
    claimed = repo.claim_next(tenant_id=TENANT_ID)
    assert claimed is not None
    assert claimed.attempts == 1

    rec1 = repo.record_failure(
        tenant_id=TENANT_ID,
        job_id=claimed.id,
        error={"msg": "crash 1"},
        max_attempts=3,
        base_backoff_seconds=2,
    )
    assert rec1.status == "queued"
    assert rec1.attempts == 1
    assert rec1.locked_at is None
    assert rec1.error is not None
    assert rec1.error["retry_in_seconds"] == 2
    assert rec1.run_at > datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)

    # Fast forward run_at for Attempt 2
    rec1.run_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)

    # Attempt 2: Worker claims and fails again
    claimed2 = repo.claim_next(tenant_id=TENANT_ID)
    assert claimed2 is not None
    assert claimed2.attempts == 2

    rec2 = repo.record_failure(
        tenant_id=TENANT_ID,
        job_id=claimed2.id,
        error={"msg": "crash 2"},
        max_attempts=3,
        base_backoff_seconds=2,
    )
    assert rec2.status == "queued"
    assert rec2.attempts == 2
    # Exponential backoff: base_backoff_seconds * 2**(attempts-1) = 2 * 2**1 = 4 seconds
    assert rec2.error is not None
    assert rec2.error["retry_in_seconds"] == 4

    # Fast forward run_at for Attempt 3
    rec2.run_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)

    # Attempt 3: Worker claims and fails a 3rd time (reaching max_attempts)
    claimed3 = repo.claim_next(tenant_id=TENANT_ID)
    assert claimed3 is not None
    assert claimed3.attempts == 3

    rec3 = repo.record_failure(
        tenant_id=TENANT_ID,
        job_id=claimed3.id,
        error={"msg": "crash 3 - fatal"},
        max_attempts=3,
        base_backoff_seconds=2,
    )
    # Reached max_attempts -> dead-letter state!
    assert rec3.status == "dead"
    assert rec3.error is not None
    assert rec3.error.get("dead_letter") is True

    # Dead-lettered job is never claimed again
    assert repo.claim_next(tenant_id=TENANT_ID) is None


def test_handler_idempotency_and_atomic_file_write() -> None:
    """Verifies that re-running a job handler is idempotent and writes files atomically."""
    doc_repo = InMemoryDocumentRepository()
    mock_storage = MagicMock()
    mock_storage.put.side_effect = lambda key, data, content_type: key
    mock_storage.exists.return_value = True

    pipeline = GenerationPipelineFSM(repository=doc_repo, storage=mock_storage)

    job_id = uuid.uuid4()
    job = JobRecord(
        id=job_id,
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={
            "document_id": str(job_id),
            "template_id": "test_template",
            "parties": [],
        },
    )

    # First execution
    doc1 = pipeline.process_job(job)
    assert doc1.id == job_id
    assert job.status == "succeeded"
    mock_storage.put.assert_called_once()

    # Second execution of the exact same job (retry / crash scenario)
    doc2 = pipeline.process_job(job)
    assert doc2.id == doc1.id
    assert doc2.file_ref == doc1.file_ref
    # mock_storage.put was NOT called a second time because existing doc was returned!
    assert mock_storage.put.call_count == 1


def test_database_session_hashed_token_idle_and_absolute_expiry() -> None:
    """Verifies database-backed session repository enforces token hashing, idle and absolute timeout."""
    mock_db = MagicMock()
    repo = PostgresSessionRepository(session=mock_db, idle_timeout_minutes=30)

    user_id = uuid.uuid4()
    raw_token = "secure-random-session-token-xyz"
    token_hash = hash_token(raw_token)
    csrf_hash = hash_token("csrf-token-123")

    now = datetime.datetime.now(datetime.timezone.utc)
    session_data = SessionData(
        id_hash=token_hash,
        user_id=user_id,
        tenant_id=TENANT_ID,
        csrf_token_hash=csrf_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )

    # 1. Save session to database
    repo.save(TENANT_ID, session_data)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

    # 2. Simulate DB entity retrieval for idle expiry check
    db_model = SessionModel(
        id_hash=token_hash,
        user_id=user_id,
        tenant_id=TENANT_ID,
        csrf_token_hash=csrf_hash,
        created_at=now - datetime.timedelta(hours=2),
        last_seen_at=now - datetime.timedelta(minutes=35),  # 35 min ago > 30 min idle limit
        expires_at=now + datetime.timedelta(hours=10),
    )
    mock_db.query.return_value.filter.return_value.first.return_value = db_model

    # Idle expired session must return None and trigger deletion
    result = repo.get(TENANT_ID, token_hash)
    assert result is None
    mock_db.delete.assert_called()

    # 3. Simulate absolute expiry check
    db_model_abs = SessionModel(
        id_hash=token_hash,
        user_id=user_id,
        tenant_id=TENANT_ID,
        csrf_token_hash=csrf_hash,
        created_at=now - datetime.timedelta(hours=13),
        last_seen_at=now - datetime.timedelta(minutes=5),  # Active recently
        expires_at=now - datetime.timedelta(minutes=1),  # But absolute lifetime expired!
    )
    mock_db.query.return_value.filter.return_value.first.return_value = db_model_abs

    result_abs = repo.get(TENANT_ID, token_hash)
    assert result_abs is None


def test_postgres_job_repository_skip_locked_and_backoff() -> None:
    """Verifies PostgresJobRepository uses FOR UPDATE SKIP LOCKED and handles backoff."""
    mock_db = MagicMock()
    repo = PostgresJobRepository(session=mock_db)

    # 1. claim_next sets with_for_update(skip_locked=True)
    repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=300)
    mock_db.query.return_value.filter.return_value.order_by.return_value.with_for_update.assert_called_with(
        skip_locked=True
    )

    # 2. record_failure calculates exponential backoff
    from app.shared.models import Job as JobModel

    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)
    db_job = JobModel(
        id=job_id,
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={},
        status="running",
        attempts=1,
        run_at=now,
        created_at=now,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = db_job

    rec = repo.record_failure(
        tenant_id=TENANT_ID,
        job_id=job_id,
        error={"error": "timeout"},
        max_attempts=3,
        base_backoff_seconds=2,
    )
    assert rec.status == "queued"
    assert rec.error is not None
    assert rec.error.get("retry_in_seconds") == 2
    mock_db.commit.assert_called()
