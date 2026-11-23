"""Unit tests for JobRepository interfaces, idempotency, and multi-tenant isolation.

Fulfills AGENTS.md Hard Rule 6 (every query tenant-scoped) and verifies:
1. Protocol conformance of InMemoryJobRepository.
2. Tenant isolation on enqueue, get, update_state, claim_next, and list.
3. Per-tenant idempotency deduplication.
"""

import uuid

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def raises(exc: type[Exception]):
            class _Ctx:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    return exc_type is not None and issubclass(exc_type, exc)
            return _Ctx()
    pytest = _MockPytest()  # type: ignore[assignment]

from app.generation.jobs import InMemoryJobRepository, JobRepository

TENANT_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_2 = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")


def test_job_repository_protocol_conformance() -> None:
    repo = InMemoryJobRepository()
    assert isinstance(repo, JobRepository)


def test_enqueue_and_tenant_scoped_get() -> None:
    repo = InMemoryJobRepository()
    job = repo.enqueue(TENANT_1, "generate_docx", {"doc_type": "sale_deed"})

    assert job.status == "queued"
    assert job.state == "REQUESTED"
    assert job.tenant_id == TENANT_1

    # Same tenant returns job
    found = repo.get(TENANT_1, job.id)
    assert found is not None
    assert found.id == job.id

    # Cross tenant returns None
    assert repo.get(TENANT_2, job.id) is None


def test_per_tenant_idempotency_isolation() -> None:
    repo = InMemoryJobRepository()
    key = "IDEM-TEST-100"

    j1 = repo.enqueue(TENANT_1, "generate_docx", {"mouza": "Nagpur"}, idempotency_key=key)
    # Re-enqueuing in TENANT_1 returns same job
    j1_dup = repo.enqueue(TENANT_1, "generate_docx", {"mouza": "Nagpur"}, idempotency_key=key)
    assert j1.id == j1_dup.id

    # Enqueuing in TENANT_2 with same idempotency key creates a separate job
    j2 = repo.enqueue(TENANT_2, "generate_docx", {"mouza": "Pune"}, idempotency_key=key)
    assert j2.id != j1.id
    assert j2.tenant_id == TENANT_2


def test_update_state_tenant_isolation() -> None:
    repo = InMemoryJobRepository()
    job = repo.enqueue(TENANT_1, "generate_docx", {})

    # Cross-tenant update raises KeyError
    with pytest.raises(KeyError):
        repo.update_state(TENANT_2, job.id, status="succeeded", state="COMPLETED")

    # Same-tenant update succeeds
    repo.update_state(TENANT_1, job.id, status="succeeded", state="COMPLETED")
    updated = repo.get(TENANT_1, job.id)
    assert updated is not None
    assert updated.status == "succeeded"
    assert updated.state == "COMPLETED"


def test_claim_next_tenant_scoped() -> None:
    repo = InMemoryJobRepository()
    j1 = repo.enqueue(TENANT_1, "generate_docx", {})
    j2 = repo.enqueue(TENANT_2, "generate_docx", {})

    # Claim for TENANT_2 claims j2, not j1
    claimed = repo.claim_next(tenant_id=TENANT_2)
    assert claimed is not None
    assert claimed.id == j2.id
    assert claimed.status == "running"

    # Claim for TENANT_1 claims j1
    claimed_1 = repo.claim_next(tenant_id=TENANT_1)
    assert claimed_1 is not None
    assert claimed_1.id == j1.id


def test_list_tenant_scoped() -> None:
    repo = InMemoryJobRepository()
    repo.enqueue(TENANT_1, "job1", {})
    repo.enqueue(TENANT_1, "job2", {})
    repo.enqueue(TENANT_2, "job3", {})

    assert len(repo.list(TENANT_1)) == 2
    assert len(repo.list(TENANT_2)) == 1


def test_claim_next_enforces_max_attempts() -> None:
    import datetime
    repo = InMemoryJobRepository()
    job = repo.enqueue(TENANT_1, "generate_docx", {})

    # Simulate a job that crashed after 3 attempts and timed out
    repo._jobs[job.id].status = "running"
    repo._jobs[job.id].attempts = 3
    repo._jobs[job.id].locked_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=600)

    # Calling claim_next must NOT claim this job; it must dead-letter it
    claimed = repo.claim_next(tenant_id=TENANT_1, visibility_timeout_seconds=300, max_attempts=3)
    assert claimed is None
    assert repo._jobs[job.id].status == "dead"
    assert repo._jobs[job.id].error is not None
    assert repo._jobs[job.id].error["code"] == "MAX_ATTEMPTS_EXCEEDED"


def test_claim_next_reclaims_timed_out_job_under_max_attempts() -> None:
    import datetime
    repo = InMemoryJobRepository()
    job = repo.enqueue(TENANT_1, "generate_docx", {})

    # Simulate a crashed job with 1 attempt
    repo._jobs[job.id].status = "running"
    repo._jobs[job.id].attempts = 1
    repo._jobs[job.id].locked_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=600)

    # Calling claim_next must reclaim it and increment attempts
    claimed = repo.claim_next(tenant_id=TENANT_1, visibility_timeout_seconds=300, max_attempts=3)
    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.attempts == 2
    assert claimed.status == "running"

