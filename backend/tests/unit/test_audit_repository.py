"""Unit tests for AuditRepository Protocol, InMemory and Postgres implementations.

Validates:
- Pure Python protocol adherence
- Cryptographic SHA-256 hash chaining
- Tamper detection
- Strict tenant scoping (every method takes tenant_id, cross-tenant isolation)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.adapters.repositories.audit import PostgresAuditRepository
from app.audit.repository import (
    AuditRecord,
    AuditRepository,
    InMemoryAuditRepository,
    compute_audit_hash,
)
from app.audit.service import AuditService


def test_protocol_conformance() -> None:
    """Verifies that InMemory and Postgres repositories implement AuditRepository."""
    assert issubclass(InMemoryAuditRepository, AuditRepository)
    assert issubclass(PostgresAuditRepository, AuditRepository)


def test_in_memory_audit_repository_hash_chaining() -> None:
    """Verifies SHA-256 append, link verification, and chain integrity."""
    repo = InMemoryAuditRepository()
    svc = AuditService(repository=repo)
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    rec1 = svc.log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="document_created",
        entity="document",
        entity_id="DOC-001",
        meta={"source": "api"},
    )
    assert rec1.id == 1
    assert rec1.prev_hash is None
    assert len(rec1.hash) == 32

    rec2 = svc.log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="document_updated",
        entity="document",
        entity_id="DOC-001",
        meta={"changes": ["title"]},
    )
    assert rec2.id == 2
    assert rec2.prev_hash == rec1.hash
    assert rec2.hash != rec1.hash

    assert repo.verify_chain(tenant_id) is True
    assert svc.verify_chain(tenant_id) is True

    # Check chain retrieval
    chain = repo.get_chain(tenant_id)
    assert len(chain) == 2
    assert chain[0].id == 1
    assert chain[1].id == 2


def test_audit_repository_tamper_detection() -> None:
    """Verifies that modifying any record breaks cryptographic verification."""
    repo = InMemoryAuditRepository()
    svc = AuditService(repository=repo)
    tenant_id = uuid.uuid4()

    svc.log_event(tenant_id=tenant_id, action="a1", entity="e1")
    svc.log_event(tenant_id=tenant_id, action="a2", entity="e2")
    svc.log_event(tenant_id=tenant_id, action="a3", entity="e3")
    assert repo.verify_chain(tenant_id) is True

    # Tamper with internal record meta
    repo._logs[tenant_id][1].meta["tampered"] = True
    assert repo.verify_chain(tenant_id) is False

    # Fix meta, but tamper with prev_hash link
    del repo._logs[tenant_id][1].meta["tampered"]
    repo._logs[tenant_id][2].prev_hash = b"\x00" * 32
    assert repo.verify_chain(tenant_id) is False


def test_audit_multi_tenant_isolation() -> None:
    """Verifies that audit chains are strictly segregated per tenant."""
    repo = InMemoryAuditRepository()
    svc = AuditService(repository=repo)
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    svc.log_event(tenant_id=tenant_a, action="create", entity="doc_a")
    svc.log_event(tenant_id=tenant_b, action="create", entity="doc_b")

    chain_a = repo.get_chain(tenant_a)
    chain_b = repo.get_chain(tenant_b)

    assert len(chain_a) == 1
    assert chain_a[0].tenant_id == tenant_a
    assert chain_a[0].prev_hash is None

    assert len(chain_b) == 1
    assert chain_b[0].tenant_id == tenant_b
    assert chain_b[0].prev_hash is None

    # Cross-tenant append check
    cross_rec = AuditRecord(
        id=99,
        tenant_id=tenant_a,
        actor_id=None,
        action="invalid",
        entity="test",
        entity_id=None,
        at=datetime.now(timezone.utc),
        meta={},
        prev_hash=None,
        hash=b"x" * 32,
    )
    with pytest.raises(ValueError, match="Cross-tenant"):
        repo.append(tenant_id=tenant_b, record=cross_rec)


def test_postgres_audit_repository_mocked_session() -> None:
    """Verifies PostgresAuditRepository interactions with SQLAlchemy session."""
    mock_session = MagicMock()
    repo = PostgresAuditRepository(session=mock_session)
    tenant_id = uuid.uuid4()

    now = datetime.now(timezone.utc)
    rec = AuditRecord(
        id=1,
        tenant_id=tenant_id,
        actor_id=None,
        action="audit_test",
        entity="test",
        entity_id=None,
        at=now,
        meta={"key": "val"},
        prev_hash=None,
        hash=b"\x01" * 32,
    )

    # Cross-tenant check
    with pytest.raises(ValueError, match="Cross-tenant"):
        repo.append(tenant_id=uuid.uuid4(), record=rec)

    # Append test
    persisted = repo.append(tenant_id=tenant_id, record=rec)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert persisted.tenant_id == tenant_id


def test_postgres_audit_repository_tamper_detection() -> None:
    """Verifies PostgresAuditRepository detects tampered rows in the database."""
    from app.shared.models import AuditLog as AuditLogModel

    mock_session = MagicMock()
    repo = PostgresAuditRepository(session=mock_session)
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. Create a valid cryptographic chain of 2 rows
    hash1 = compute_audit_hash(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_1",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": True},
        prev_hash=None,
    )
    row1 = AuditLogModel(
        id=1,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_1",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": True},
        prev_hash=None,
        hash=hash1,
    )

    hash2 = compute_audit_hash(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_2",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": True},
        prev_hash=hash1,
    )
    row2 = AuditLogModel(
        id=2,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_2",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": True},
        prev_hash=hash1,
        hash=hash2,
    )

    mock_session.execute.return_value.scalars.return_value.all.return_value = [row1, row2]
    assert repo.verify_audit_chain(tenant_id) is True

    # 2. Tamper with row2's meta in database
    tampered_row2 = AuditLogModel(
        id=2,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_2",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": False, "tampered": True},  # Modified meta!
        prev_hash=hash1,
        hash=hash2,
    )
    mock_session.execute.return_value.scalars.return_value.all.return_value = [row1, tampered_row2]
    assert repo.verify_audit_chain(tenant_id) is False

    # 3. Tamper with broken prev_hash link
    tampered_link_row2 = AuditLogModel(
        id=2,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="action_2",
        entity="doc",
        entity_id="DOC-1",
        at=now,
        meta={"valid": True},
        prev_hash=b"\x00" * 32,  # Corrupted previous hash link!
        hash=hash2,
    )
    mock_session.execute.return_value.scalars.return_value.all.return_value = [row1, tampered_link_row2]
    assert repo.verify_audit_chain(tenant_id) is False


def test_audit_log_model_prevents_updates_and_deletes() -> None:
    """Verifies SQLAlchemy model listeners block UPDATE and DELETE on AuditLog."""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from app.shared.models import AuditLog as AuditLogModel, Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    tenant_id = uuid.uuid4()
    entry = AuditLogModel(
        tenant_id=tenant_id,
        actor_id=None,
        action="create",
        entity="doc",
        entity_id="D-1",
        at=datetime.now(timezone.utc),
        meta={},
        prev_hash=None,
        hash=b"1" * 32,
    )
    session.add(entry)
    session.commit()

    # Attempting to update a row must raise PermissionError
    entry.action = "tampered_action"
    with pytest.raises(PermissionError, match="audit_log is append-only"):
        session.commit()

    session.rollback()

    # Attempting to delete a row without test cleanup flag must raise PermissionError
    with pytest.raises(PermissionError, match="audit_log is append-only"):
        session.delete(entry)
        session.commit()

    session.close()


def test_admin_api_verify_audit_chain_endpoint() -> None:
    """Verifies that /api/v1/admin/audit/verify returns verification status."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.auth import get_current_actor
    from app.api.admin import get_audit_repo
    from app.identity.policy import Actor

    client = TestClient(app)
    mock_actor = Actor(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="admin@example.com",
        role="admin",
        ui_language="mr",
    )
    mock_repo = MagicMock()
    mock_repo.verify_audit_chain.return_value = True

    app.dependency_overrides[get_current_actor] = lambda: mock_actor
    app.dependency_overrides[get_audit_repo] = lambda: mock_repo
    try:
        res = client.get("/api/v1/admin/audit/verify")
        assert res.status_code == 200
        data = res.json()
        assert data["chain_valid"] is True
        assert data["tamper_detected"] is False

        # When chain is tampered:
        mock_repo.verify_audit_chain.return_value = False
        res2 = client.get("/api/v1/admin/audit/verify")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["chain_valid"] is False
        assert data2["tamper_detected"] is True
    finally:
        app.dependency_overrides.pop(get_current_actor, None)
        app.dependency_overrides.pop(get_audit_repo, None)

