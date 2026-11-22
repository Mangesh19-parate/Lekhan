"""Unit tests for DB-backed immutable templates, N+1 versioning, and 3-way separation of duties.

Fulfills PRD FR-09 and verifies:
1. Overwrite attempt on approved template version fails (raises PermissionError / DB immutability trigger).
2. Restart simulation: DB state persists and is retrieved cleanly across sessions without memory dependency.
3. Drafter submit -> 403 Forbidden (RBAC policy gate).
4. 3-way separation of duties: uploader != submitter != approver.
5. Approve with missing files -> fails with 422 Unprocessable Entity.
6. Upload ALWAYS creates version N+1 as draft.
"""

from __future__ import annotations

import datetime
import io
import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.storage import LocalObjectStore
from app.api.templates_admin import (
    approve_template,
    get_template_manifest,
    list_templates,
    submit_template_for_review,
    upload_template,
)
from app.identity.policy import Actor, authorize
from app.shared.ids import uuid7
from app.shared.models import Base, TemplateVersion


@pytest.fixture
def sqlite_db_engine():
    """Provides a fresh SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(sqlite_db_engine) -> Session:
    """Yields a database session."""
    session_factory = sessionmaker(bind=sqlite_db_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_overwrite_approved_version_attempt_fails(db_session: Session) -> None:
    """Verifies that an approved template version cannot be modified (except status -> retired)."""
    t_id = uuid.uuid4()
    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=t_id,
        template_key="immutable_deed",
        version=1,
        status="approved",
        manifest_json={"template_id": "immutable_deed", "version": 1},
        docx_sha256="abc123sha",
        docx_ref="templates/immutable_deed/v1/template.docx",
        created_by=uuid.uuid4(),
        submitted_by=uuid.uuid4(),
        approved_by=uuid.uuid4(),
        approved_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(tv)
    db_session.commit()

    # Attempt 1: Modifying docx_ref
    tv.docx_ref = "templates/hacked/template.docx"
    with pytest.raises(PermissionError, match="immutable"):
        db_session.commit()
    db_session.rollback()

    # Attempt 2: Modifying docx_sha256
    tv.docx_sha256 = "corrupted_sha"
    with pytest.raises(PermissionError, match="immutable"):
        db_session.commit()
    db_session.rollback()

    # Attempt 3: Demoting back to draft
    tv.status = "draft"
    with pytest.raises(PermissionError, match="immutable"):
        db_session.commit()
    db_session.rollback()

    # Transition to retired is permitted
    tv.status = "retired"
    db_session.commit()
    assert tv.status == "retired"

    # Once retired, no further modifications are permitted
    tv.status = "approved"
    with pytest.raises(PermissionError, match="Retired"):
        db_session.commit()
    db_session.rollback()


def test_restart_simulation_persists_state(sqlite_db_engine) -> None:
    """Simulates application restart by closing and reopening database sessions."""
    Session1 = sessionmaker(bind=sqlite_db_engine)
    sess1 = Session1()

    template_key = "restart_test_template"
    tv_id = uuid7()
    tv = TemplateVersion(
        id=tv_id,
        tenant_id=uuid.uuid4(),
        template_key=template_key,
        version=1,
        status="approved",
        manifest_json={"template_id": template_key, "doc_type": "gift_deed"},
        docx_sha256="feedface0123456789",
        docx_ref=f"templates/{template_key}/v1/template.docx",
        created_by=uuid.uuid4(),
        submitted_by=uuid.uuid4(),
        approved_by=uuid.uuid4(),
        approved_at=datetime.datetime.now(datetime.timezone.utc),
    )
    sess1.add(tv)
    sess1.commit()
    sess1.close()

    # Simulate restart: open completely new session
    Session2 = sessionmaker(bind=sqlite_db_engine)
    sess2 = Session2()

    loaded = sess2.query(TemplateVersion).filter(TemplateVersion.id == tv_id).first()
    assert loaded is not None
    assert loaded.template_key == template_key
    assert loaded.status == "approved"
    assert loaded.docx_sha256 == "feedface0123456789"
    assert loaded.manifest_json["doc_type"] == "gift_deed"
    sess2.close()


def test_drafter_submit_returns_403(db_session: Session) -> None:
    """Drafter role attempting to submit a template for review must be rejected with 403."""
    drafter_actor = Actor(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role="drafter")

    # Authorize directly rejects drafter for template submission
    decision = authorize(drafter_actor, "submit_template_for_review")
    assert not decision.allowed
    assert "lacks permission" in decision.reason

    # Calling submit route with drafter actor raises 403 HTTPException
    with pytest.raises(HTTPException) as exc_info:
        submit_template_for_review(template_id="any_template", actor=drafter_actor, db=db_session)
    assert exc_info.value.status_code == 403


def test_separation_of_duties_three_way(db_session: Session) -> None:
    """Enforces 3-way separation of duties: uploader != submitter != approver."""
    t_id = uuid.uuid4()
    uploader = Actor(user_id=uuid.uuid4(), tenant_id=t_id, role="template_admin")
    submitter = Actor(user_id=uuid.uuid4(), tenant_id=t_id, role="template_admin")
    approver = Actor(user_id=uuid.uuid4(), tenant_id=t_id, role="reviewer")

    template_key = "sod_deed"
    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=t_id,
        template_key=template_key,
        version=1,
        status="draft",
        manifest_json={"template_id": template_key},
        docx_sha256="",
        docx_ref="",
        created_by=uploader.user_id,
        submitted_by=None,
        approved_by=None,
    )
    db_session.add(tv)
    db_session.commit()

    # 1. Uploader cannot submit
    with pytest.raises(HTTPException) as exc_up_sub:
        submit_template_for_review(template_id=template_key, actor=uploader, db=db_session)
    assert exc_up_sub.value.status_code == 403
    assert "Uploader cannot submit" in exc_up_sub.value.detail

    # 2. Distinct user submits -> succeeds
    sub_res = submit_template_for_review(template_id=template_key, actor=submitter, db=db_session)
    assert sub_res["status"] == "under_review"

    # 3. Uploader cannot approve
    uploader_as_rev = Actor(user_id=uploader.user_id, tenant_id=t_id, role="reviewer")
    with pytest.raises(HTTPException) as exc_up_app:
        approve_template(template_id=template_key, actor=uploader_as_rev, db=db_session)
    assert exc_up_app.value.status_code == 403
    assert "Separation of duties violation" in exc_up_app.value.detail

    # 4. Submitter cannot approve
    submitter_as_rev = Actor(user_id=submitter.user_id, tenant_id=t_id, role="reviewer")
    with pytest.raises(HTTPException) as exc_sub_app:
        approve_template(template_id=template_key, actor=submitter_as_rev, db=db_session)
    assert exc_sub_app.value.status_code == 403
    assert "Separation of duties violation" in exc_sub_app.value.detail


def test_approve_with_missing_files_fails(db_session: Session) -> None:
    """Approval must fail with 422 if template docx file is missing in storage and on disk."""
    t_id = uuid.uuid4()
    uploader_id = uuid.uuid4()
    submitter_id = uuid.uuid4()
    approver = Actor(user_id=uuid.uuid4(), tenant_id=t_id, role="reviewer")

    template_key = "missing_files_template"
    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=t_id,
        template_key=template_key,
        version=1,
        status="under_review",
        manifest_json={"template_id": template_key},
        docx_sha256="expected_sha",
        docx_ref="templates/missing/v1/template.docx",
        created_by=uploader_id,
        submitted_by=submitter_id,
        approved_by=None,
    )
    db_session.add(tv)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        approve_template(template_id=template_key, actor=approver, db=db_session)
    assert exc_info.value.status_code == 422
    assert "missing in storage" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_creates_version_n_plus_one(db_session: Session, tmp_path: Path) -> None:
    """Verifies upload ALWAYS creates version N+1 as draft."""
    t_id = uuid.uuid4()
    uploader = Actor(user_id=uuid.uuid4(), tenant_id=t_id, role="template_admin")
    storage = LocalObjectStore(base_path=tmp_path / "storage")

    template_key = "version_seq_deed"
    manifest = json.dumps({"template_id": template_key, "name_en": "Sequential Deed"})
    dummy_bytes = b"PK\x03\x04test_docx_content"

    with patch("app.api.templates_admin.default_storage", storage), \
         patch("app.api.templates_admin.TEMPLATES_DIR", tmp_path / "lib"), \
         patch("app.api.templates_admin.check_structural_safety", return_value=[]), \
         patch("app.api.templates_admin.DocxLinter") as mock_linter:
        mock_report = MagicMock()
        mock_report.can_approve = True
        mock_report.to_dict.return_value = {}
        mock_linter.return_value.lint.return_value = mock_report

        # Upload 1 -> version 1
        f1 = UploadFile(filename="template.docx", file=io.BytesIO(dummy_bytes))
        res1 = await upload_template(
            template_id=template_key,
            manifest_json=manifest,
            docx_file=f1,
            actor=uploader,
            db=db_session,
        )
        assert res1["version"] == 1
        assert res1["status"] == "draft"

        # Upload 2 -> version 2
        f2 = UploadFile(filename="template.docx", file=io.BytesIO(dummy_bytes + b"_v2"))
        res2 = await upload_template(
            template_id=template_key,
            manifest_json=manifest,
            docx_file=f2,
            actor=uploader,
            db=db_session,
        )
        assert res2["version"] == 2
        assert res2["status"] == "draft"

        # Verify DB has both records
        records = (
            db_session.query(TemplateVersion)
            .filter(TemplateVersion.template_key == template_key)
            .order_by(TemplateVersion.version.asc())
            .all()
        )
        assert len(records) == 2
        assert records[0].version == 1
        assert records[1].version == 2
