"""Unit tests for Document Quality inspection, System Settings persistence, and Drafts CRUD endpoints.

Verifies:
- POST /api/v1/documents/{id}/quality runs DocxLinter and leftover scanner.
- GET/PUT /api/v1/admin/settings is admin-only, persists to tenant, and logs audit events.
- Drafts CRUD: create, list, get, update, delete, with strict tenant scoping (cross-tenant 404).
"""

from __future__ import annotations

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.db import get_db
from app.api.admin import get_audit_service
from app.api.auth import get_current_actor, require_csrf
from app.audit.repository import InMemoryAuditRepository
from app.audit.service import AuditService
from app.identity.policy import Actor
from app.main import app
from app.shared.models import Base, Tenant, User

# In-memory SQLite with StaticPool so all sessions share the in-memory database
test_engine = create_engine(
    "sqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

TENANT_A = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_B = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")

ADMIN_A = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000010"),
    tenant_id=TENANT_A,
    role="admin",
)
DRAFTER_A = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000020"),
    tenant_id=TENANT_A,
    role="drafter",
)
DRAFTER_B = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000030"),
    tenant_id=TENANT_B,
    role="drafter",
)

current_actor = ADMIN_A


def override_get_current_actor() -> Actor:
    return current_actor


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


in_memory_audit_repo = InMemoryAuditRepository()


def override_get_audit_service() -> AuditService:
    return AuditService(repository=in_memory_audit_repo)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    tenant_a = Tenant(
        id=TENANT_A,
        name="Tenant A",
        settings={
            "retention_class": "matter_lifecycle",
            "digits_setting": "western",
            "idle_minutes": 30,
        },
    )
    tenant_b = Tenant(id=TENANT_B, name="Tenant B", settings={})
    user_a = User(
        id=ADMIN_A.user_id,
        tenant_id=TENANT_A,
        email="admin@a.com",
        display_name="Admin A",
        password_hash="dummy_hash",
        role="admin",
    )
    user_drafter = User(
        id=DRAFTER_A.user_id,
        tenant_id=TENANT_A,
        email="drafter@a.com",
        display_name="Drafter A",
        password_hash="dummy_hash",
        role="drafter",
    )
    user_b = User(
        id=DRAFTER_B.user_id,
        tenant_id=TENANT_B,
        email="drafter@b.com",
        display_name="Drafter B",
        password_hash="dummy_hash",
        role="drafter",
    )
    db.add_all([tenant_a, tenant_b, user_a, user_drafter, user_b])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def apply_dependency_overrides():
    app.dependency_overrides[get_current_actor] = override_get_current_actor
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_audit_service] = override_get_audit_service
    app.dependency_overrides[require_csrf] = lambda: None
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# --- 1. Document Quality Inspection Tests ---


def test_quality_inspection_on_approved_template():
    """Proves POST /api/v1/documents/{id}/quality runs DocxLinter and leftover scanner on approved template."""
    global current_actor
    current_actor = DRAFTER_A

    res = client.post("/api/v1/documents/sale_deed_plot_mr/quality")
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == "sale_deed_plot_mr"
    assert data["overall_status"] in ("Passed", "Failed")
    assert "score" in data
    assert "passed_checks" in data
    assert len(data["passed_checks"]) > 0
    assert "leftover_data" in data
    assert "blocking_errors" in data
    assert "warnings" in data


def test_quality_inspection_not_found():
    """Proves 404 for unknown document or template identifier."""
    global current_actor
    current_actor = DRAFTER_A

    res = client.post("/api/v1/documents/non_existent_doc_or_template/quality")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# --- 2. System Settings Persistence & Audit Tests ---


def test_get_system_settings_admin():
    """Proves GET /api/v1/admin/settings returns tenant settings for admin."""
    global current_actor
    current_actor = ADMIN_A

    res = client.get("/api/v1/admin/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["retention_class"] == "matter_lifecycle"
    assert data["digits_setting"] == "western"
    assert data["idle_minutes"] == 30
    assert data["tenant_id"] == str(TENANT_A)


def test_put_system_settings_admin_and_audited():
    """Proves PUT /api/v1/admin/settings persists settings to tenant and logs audit event."""
    global current_actor
    current_actor = ADMIN_A

    update_payload = {
        "retention_class": "limitation_12yr",
        "digits_setting": "devanagari",
        "idle_minutes": 45,
    }
    res = client.put("/api/v1/admin/settings", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["retention_class"] == "limitation_12yr"
    assert data["digits_setting"] == "devanagari"
    assert data["idle_minutes"] == 45

    # Verify audit event logged
    events = in_memory_audit_repo._logs.get(TENANT_A, [])
    assert any(e.action == "update_system_settings" for e in events)


def test_system_settings_forbidden_for_drafter():
    """Proves non-admin (drafter) is forbidden from reading or updating settings."""
    global current_actor
    current_actor = DRAFTER_A

    get_res = client.get("/api/v1/admin/settings")
    assert get_res.status_code == 403

    put_res = client.put("/api/v1/admin/settings", json={"idle_minutes": 60})
    assert put_res.status_code == 403


# --- 3. Drafts CRUD and Scoping Tests ---


def test_drafts_crud_lifecycle():
    """Proves Drafts CRUD: create, list, get, update, and delete with tenant scoping."""
    global current_actor
    current_actor = DRAFTER_A

    # 1. Create draft
    create_payload = {
        "title": "Sale Deed Plot 12 Wadi",
        "template_id": "sale_deed_plot_mr",
        "data": {
            "formData": {"property.mouza": "Wadi", "property.plot_no": "12"},
            "repeatersData": {"sellers": [{"full_name": "Ramesh Patil"}]},
        },
    }
    create_res = client.post("/api/v1/drafts", json=create_payload)
    assert create_res.status_code == 201
    draft_data = create_res.json()
    draft_id = draft_data["id"]
    assert draft_data["title"] == "Sale Deed Plot 12 Wadi"
    assert draft_data["template_id"] == "sale_deed_plot_mr"
    assert draft_data["tenant_id"] == str(TENANT_A)

    # 2. List drafts
    list_res = client.get("/api/v1/drafts")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(d["id"] == draft_id for d in items)

    # 3. Get single draft
    get_res = client.get(f"/api/v1/drafts/{draft_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Sale Deed Plot 12 Wadi"

    # 4. Update draft
    update_res = client.put(
        f"/api/v1/drafts/{draft_id}",
        json={"title": "Updated Plot 12 Wadi", "data": {"property.mouza": "Wadi East"}},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Plot 12 Wadi"

    # 5. Cross-tenant access from Tenant B returns 404
    current_actor = DRAFTER_B
    cross_res = client.get(f"/api/v1/drafts/{draft_id}")
    assert cross_res.status_code == 404

    # 6. Delete draft back as Tenant A
    current_actor = DRAFTER_A
    del_res = client.delete(f"/api/v1/drafts/{draft_id}")
    assert del_res.status_code == 204

    # 7. Confirm deleted
    confirm_res = client.get(f"/api/v1/drafts/{draft_id}")
    assert confirm_res.status_code == 404
