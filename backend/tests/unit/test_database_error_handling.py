"""Unit tests for database error handling and explicit repository injection."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.adapters.repositories.documents import PostgresDocumentRepository
from app.adapters.repositories.parties import PostgresPartyRepository
from app.audit.repository import InMemoryAuditRepository
from app.audit.service import AuditService
from app.generation.models import GeneratedDocumentRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.repository import (
    InMemoryDocumentRepository,
)
from app.main import app
from app.parties.models import PartyRecord
from app.parties.repository import (
    InMemoryPartyRepository,
)
from app.parties.service import PartyService
from app.properties.repository import (
    InMemoryPropertyRepository,
)
from app.properties.service import PropertyService

client = TestClient(app, raise_server_exceptions=False)
TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")


def test_database_failure_returns_503_problem_json() -> None:
    """Verifies that an unhandled database error produces an RFC 9457 503 Service Unavailable response."""
    # Simulate a database failure on an endpoint by mocking the repository or DB query to raise OperationalError
    with patch.object(
        PostgresPartyRepository,
        "search",
        side_effect=OperationalError("connection refused", {}, Exception("DB down")),
    ):
        # We need an authenticated drafter cookie/token or actor dependency
        # Test directly via the app client on parties search
        from app.api.auth import get_current_actor
        from app.identity.policy import Actor

        app.dependency_overrides[get_current_actor] = lambda: Actor(
            user_id=uuid.uuid4(),
            tenant_id=TENANT_ID,
            role="drafter",
        )
        try:
            res = client.get("/api/v1/parties/search?q=test")
            assert res.status_code == 503
            assert res.headers["content-type"] == "application/problem+json"
            assert "X-Correlation-ID" in res.headers

            data = res.json()
            assert data["status"] == 503
            assert data["code"] == "DATABASE_UNAVAILABLE"
            assert data["correlation_id"] == res.headers["X-Correlation-ID"]
            assert "Database service unavailable" in data["detail"]
        finally:
            app.dependency_overrides.pop(get_current_actor, None)


def test_postgres_party_repository_raises_on_db_failure() -> None:
    """Verifies PostgresPartyRepository raises SQLAlchemyError and does NOT swallow it."""
    repo = PostgresPartyRepository()
    party = PartyRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        kind="individual",
        gender="male",
        marital_status=None,
        age_or_dob=None,
        names={"en": "Test User"},
        occupations={},
        addresses={},
        pan_masked=None,
        version=1,
    )

    with patch(
        "app.adapters.repositories.parties.SessionLocal",
        side_effect=OperationalError("fail", {}, Exception("down")),
    ):
        with pytest.raises(SQLAlchemyError):
            repo.save(TENANT_ID, party)


def test_postgres_document_repository_raises_on_db_failure() -> None:
    """Verifies PostgresDocumentRepository raises SQLAlchemyError and does NOT swallow it."""
    repo = PostgresDocumentRepository()
    doc = GeneratedDocumentRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        template_version_id=uuid.uuid4(),
        doc_no="DOC-001",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={},
        input_hash=b"0" * 32,
        output_hash=b"1" * 32,
        file_ref="docs/test.docx",
        pdf_ref=None,
        status="draft",
        created_at="2026-11-13T00:00:00Z",
    )

    with patch(
        "app.adapters.repositories.documents.SessionLocal",
        side_effect=OperationalError("fail", {}, Exception("down")),
    ):
        with pytest.raises(SQLAlchemyError):
            repo.save(TENANT_ID, doc)


def test_in_memory_repository_injection_for_tests() -> None:
    """Verifies that tests can cleanly inject in-memory repositories conforming to the protocols."""
    party_repo = InMemoryPartyRepository()
    party_svc = PartyService(repository=party_repo)
    p = party_svc.create_party(
        tenant_id=TENANT_ID,
        kind="individual",
        names={"mr": "अनिल जोशी", "en": "Anil Joshi"},
    )
    assert party_svc.get_party(p.id, TENANT_ID) is not None

    prop_repo = InMemoryPropertyRepository()
    prop_svc = PropertyService(repository=prop_repo)
    prop = prop_svc.create_property(
        tenant_id=TENANT_ID,
        category="plot",
        attrs={"plot_no": "10"},
    )
    assert prop_svc.get_property(prop.id, TENANT_ID) is not None

    doc_repo = InMemoryDocumentRepository()
    pipeline = GenerationPipelineFSM(repository=doc_repo)
    test_doc = GeneratedDocumentRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        template_version_id=uuid.uuid4(),
        doc_no="DOC-999",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={},
        input_hash=b"0" * 32,
        output_hash=b"1" * 32,
        file_ref="docs/sample.docx",
        pdf_ref=None,
        status="draft",
        created_at="2026-11-13T00:00:00Z",
    )
    doc_repo.save(TENANT_ID, test_doc)
    assert pipeline.get_document(test_doc.id, TENANT_ID) == test_doc

    audit_repo = InMemoryAuditRepository()
    audit_svc = AuditService(repository=audit_repo)
    audit_svc.log_event(tenant_id=TENANT_ID, action="test_action", entity="test")
    assert len(audit_repo.get_chain(TENANT_ID)) == 1
    assert audit_repo.verify_chain(TENANT_ID) is True
