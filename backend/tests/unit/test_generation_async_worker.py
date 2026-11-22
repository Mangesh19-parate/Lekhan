"""Unit tests for asynchronous document generation, worker resilience, and job polling.

Verifies:
1. POST /documents returns 202 Accepted + job id (generation moved off request path).
2. GET /jobs/{id} reports state, outputs, and safe errors.
3. Worker crash mid-job (visibility timeout recovery).
4. Duplicate Idempotency-Key deduplication.
5. Missing LibreOffice handling (safe error code, correlation ID).
6. Transient error retries with backoff -> dead-letter after N attempts.
"""

from __future__ import annotations

import datetime
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.adapters.pdf import LibreOfficeNotFoundError, LibreOfficePdfConverter, PdfConversionTimeoutError
from app.api.auth import get_current_actor
from app.api.documents import get_job_repo
from app.generation.jobs import InMemoryJobRepository, JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.identity.policy import Actor
from app.main import app
from app.worker import classify_job_exception, run_worker_once

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
ACTOR_USER = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")

TEST_ACTOR = Actor(
    user_id=ACTOR_USER,
    tenant_id=TENANT_ID,
    role="drafter",
)


@pytest.fixture
def mock_job_repo() -> InMemoryJobRepository:
    """Provides a fresh InMemoryJobRepository for tests."""
    repo = InMemoryJobRepository()
    repo.clear()
    return repo


@pytest.fixture
def client(mock_job_repo: InMemoryJobRepository) -> TestClient:
    """FastAPI TestClient with overridden actor and in-memory job repository."""
    app.dependency_overrides[get_current_actor] = lambda: TEST_ACTOR
    app.dependency_overrides[get_job_repo] = lambda: mock_job_repo
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_post_documents_returns_202_and_job_id(
    client: TestClient, mock_job_repo: InMemoryJobRepository
) -> None:
    """POST /api/v1/documents returns 202 Accepted and job id immediately without synchronous generation."""
    payload = {
        "template_id": "sale_deed_plot_mr",
        "data": {"consideration": "500000"},
    }

    res = client.post("/api/v1/documents", json=payload)
    assert res.status_code == 202, f"Expected 202 Accepted, got {res.status_code}: {res.text}"

    data = res.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["state"] == "REQUESTED"
    assert "document_id" in data
    assert "download_url" in data

    # Verify job is enqueued in the repository and NOT executed yet
    job_uuid = uuid.UUID(data["job_id"])
    job = mock_job_repo.get(TENANT_ID, job_uuid)
    assert job is not None
    assert job.status == "queued"


def test_get_jobs_reports_state_and_polling_flow(
    client: TestClient, mock_job_repo: InMemoryJobRepository
) -> None:
    """GET /jobs/{id} and GET /api/v1/jobs/{id} report pipeline state and outputs."""
    # 1. Enqueue job
    enqueue_res = client.post(
        "/api/v1/documents",
        json={"template_id": "sale_deed_plot_mr", "data": {}},
    )
    assert enqueue_res.status_code == 202
    job_id = enqueue_res.json()["job_id"]

    # 2. Poll GET /jobs/{id} while queued
    poll_res1 = client.get(f"/jobs/{job_id}")
    assert poll_res1.status_code == 200
    poll_data1 = poll_res1.json()
    assert poll_data1["status"] == "queued"
    assert poll_data1["state"] == "REQUESTED"
    assert poll_data1["outputs"]["docx"] is False

    # Also test /api/v1/jobs/{id} alias
    alias_res = client.get(f"/api/v1/jobs/{job_id}")
    assert alias_res.status_code == 200
    assert alias_res.json()["status"] == "queued"

    # 3. Worker executes the job
    with patch("app.worker.generation_pipeline.process_job") as mock_process:
        mock_doc = MagicMock()
        mock_doc.file_ref = "documents/test.docx"
        mock_process.return_value = mock_doc

        processed = run_worker_once(repo=mock_job_repo)
        assert processed is True

    # 4. Poll GET /jobs/{id} after completion
    poll_res2 = client.get(f"/jobs/{job_id}")
    assert poll_res2.status_code == 200
    poll_data2 = poll_res2.json()
    assert poll_data2["status"] == "succeeded"
    assert poll_data2["outputs"]["docx"] is True
    assert poll_data2["download_url"] is not None


def test_duplicate_idempotency_key_returns_same_job_id(
    client: TestClient, mock_job_repo: InMemoryJobRepository
) -> None:
    """Duplicate requests with the same Idempotency-Key return the identical 202 job without creating duplicates."""
    payload = {"template_id": "sale_deed_plot_mr", "data": {}}
    idem_key = "idemp-unique-key-999"

    # First request
    res1 = client.post(
        "/api/v1/documents",
        json=payload,
        headers={"Idempotency-Key": idem_key},
    )
    assert res1.status_code == 202
    data1 = res1.json()
    job_id_1 = data1["job_id"]

    # Second request with duplicate key
    res2 = client.post(
        "/api/v1/documents",
        json=payload,
        headers={"Idempotency-Key": idem_key},
    )
    assert res2.status_code == 202
    data2 = res2.json()
    job_id_2 = data2["job_id"]

    # Must match exactly
    assert job_id_1 == job_id_2

    # Verify only ONE job exists in the repository
    all_jobs = mock_job_repo.list(TENANT_ID)
    assert len(all_jobs) == 1


def test_worker_crash_mid_job_visibility_timeout_recovery(
    mock_job_repo: InMemoryJobRepository,
) -> None:
    """Simulates a worker crashing mid-job; after visibility timeout, another worker safely reclaims it."""
    # Enqueue a job
    job = mock_job_repo.enqueue(
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={"template_id": "sale_deed_plot_mr"},
    )
    assert job.status == "queued"
    assert job.attempts == 0

    # Worker 1 claims job with 60 second visibility timeout
    claimed_w1 = mock_job_repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_w1 is not None
    assert claimed_w1.id == job.id
    assert claimed_w1.status == "running"
    assert claimed_w1.attempts == 1

    # Worker 1 "crashes" mid-job without calling update_state.
    # Worker 2 attempts claim immediately: must return None (job is protected by active visibility timeout)
    claimed_w2_early = mock_job_repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_w2_early is None

    # Simulate passage of time past visibility timeout (e.g. 65 seconds elapsed)
    now = datetime.datetime.now(datetime.timezone.utc)
    claimed_w1.locked_at = now - datetime.timedelta(seconds=65)

    # Worker 2 attempts claim now: visibility timeout expired, Worker 2 reclaims the orphaned job!
    claimed_w2 = mock_job_repo.claim_next(tenant_id=TENANT_ID, visibility_timeout_seconds=60)
    assert claimed_w2 is not None
    assert claimed_w2.id == job.id
    assert claimed_w2.attempts == 2

    # Worker 2 successfully finishes the job
    mock_job_repo.update_state(tenant_id=TENANT_ID, job_id=job.id, status="succeeded", state="COMPLETED")
    finished_job = mock_job_repo.get(TENANT_ID, job.id)
    assert finished_job.status == "succeeded"


def test_libreoffice_missing_handling(
    client: TestClient, mock_job_repo: InMemoryJobRepository
) -> None:
    """When LibreOffice is missing, worker sets safe CONVERTER_MISSING error without leaking paths."""
    # 1. Verify LibreOfficeNotFoundError in strict mode
    converter = LibreOfficePdfConverter(binary_path=None, strict=False)
    with pytest.raises(LibreOfficeNotFoundError):
        converter.convert_docx_to_pdf(b"dummy_docx_content", strict=True)

    # 2. Enqueue job
    job = mock_job_repo.enqueue(
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={"template_id": "sale_deed_plot_mr"},
    )

    # 3. Simulate worker encountering LibreOfficeNotFoundError
    with patch("app.worker.generation_pipeline.process_job", side_effect=LibreOfficeNotFoundError("soffice not found")):
        run_worker_once(repo=mock_job_repo)

    # 4. Check job status via GET /jobs/{id}
    res = client.get(f"/jobs/{job.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert data["retryable"] is False
    assert data["error"]["code"] == "CONVERTER_MISSING"
    assert "correlation_id" in data["error"]
    # Check that internal binary path / command details are NOT leaked
    assert "soffice" not in data["error"]["message"]


def test_transient_error_backoff_and_dead_letter_after_max_attempts(
    mock_job_repo: InMemoryJobRepository,
) -> None:
    """Transient errors are retried with exponential backoff and dead-lettered after max_attempts."""
    job = mock_job_repo.enqueue(
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload={"template_id": "sale_deed_plot_mr"},
    )

    timeout_exc = PdfConversionTimeoutError("PDF conversion timed out after 30s")

    # Attempt 1: Worker runs and encounters transient error
    with patch("app.worker.generation_pipeline.process_job", side_effect=timeout_exc):
        run_worker_once(repo=mock_job_repo, max_attempts=3)

    job1 = mock_job_repo.get(TENANT_ID, job.id)
    assert job1.status == "queued"
    assert job1.attempts == 1
    assert job1.error["code"] == "CONVERTER_TIMEOUT"
    assert "retry_in_seconds" in job1.error

    # Attempt 2: Reset run_at to now, simulate attempt 2
    job1.run_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)
    with patch("app.worker.generation_pipeline.process_job", side_effect=timeout_exc):
        run_worker_once(repo=mock_job_repo, max_attempts=3)

    job2 = mock_job_repo.get(TENANT_ID, job.id)
    assert job2.status == "queued"
    assert job2.attempts == 2

    # Attempt 3: Reset run_at to now, simulate attempt 3 (reaches max_attempts)
    job2.run_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)
    with patch("app.worker.generation_pipeline.process_job", side_effect=timeout_exc):
        run_worker_once(repo=mock_job_repo, max_attempts=3)

    job3 = mock_job_repo.get(TENANT_ID, job.id)
    assert job3.status == "dead"
    assert job3.attempts == 3
    assert job3.error["dead_letter"] is True
    assert job3.error["code"] == "CONVERTER_TIMEOUT"


def test_classify_job_exception_sanitization() -> None:
    """Verifies that all exception types produce safe codes, safe messages, and never leak PII/internals."""
    # Validation error -> non-transient
    code, msg, transient = classify_job_exception(ValueError("Corrupted tag at byte 0x4F: secret_internal_var"))
    assert code == "VALIDATION_FAILED"
    assert "secret_internal_var" not in msg
    assert transient is False

    # Missing LibreOffice -> non-transient
    code, msg, transient = classify_job_exception(LibreOfficeNotFoundError("Internal /usr/bin/soffice missing"))
    assert code == "CONVERTER_MISSING"
    assert "/usr/bin/soffice" not in msg
    assert transient is False

    # Timeout -> transient
    code, msg, transient = classify_job_exception(PdfConversionTimeoutError("Timeout in soffice.bin after 30s"))
    assert code == "CONVERTER_TIMEOUT"
    assert "soffice.bin" not in msg
    assert transient is True
