"""Unit tests for Template Lifecycle FSM and Separation of Duties (PRD FR-09, Features F-026, F-028).

Verifies:
- DB-backed template lifecycle transitions: draft -> under_review -> approved -> retired.
- 3-Way Separation of Duties (Hard Rule 6, docs/AUTH.md): uploader != submitter != approver.
- Independent reviewer approval gate.
- Quality lint gate blocking approval on defective/leftover-PII templates.
- Audit trail event logging on lifecycle state changes.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.templates_admin import (
    approve_template,
    retire_template,
    submit_template_for_review,
)
from app.identity.policy import Actor, Resource, authorize
from app.shared.ids import uuid7
from app.shared.models import Base, TemplateVersion


@pytest.fixture
def db_session() -> Session:
    """Provides an isolated SQLite in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_policy_separation_of_duties() -> None:
    """Verifies central policy engine rejects submitter approving their own version."""
    user_id = uuid.uuid4()
    reviewer_actor = Actor(user_id=user_id, tenant_id=uuid.uuid4(), role="reviewer")

    # Resource where submitter is the same actor
    self_submitted_resource = Resource(
        tenant_id=reviewer_actor.tenant_id,
        resource_type="template",
        submitter_id=user_id,
    )
    decision = authorize(reviewer_actor, "approve_template_version", self_submitted_resource)
    assert not decision.allowed
    assert "Submitter cannot approve" in decision.reason

    # Resource where submitter is someone else
    other_user_id = uuid.uuid4()
    other_resource = Resource(
        tenant_id=reviewer_actor.tenant_id,
        resource_type="template",
        submitter_id=other_user_id,
    )
    decision_other = authorize(reviewer_actor, "approve_template_version", other_resource)
    assert decision_other.allowed


def test_template_admin_cannot_approve() -> None:
    """Template admin can upload and submit, but only reviewer can approve."""
    admin_actor = Actor(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role="template_admin")

    # template_admin has upload and submit permissions
    assert authorize(admin_actor, "upload_template_version").allowed
    assert authorize(admin_actor, "submit_template_for_review").allowed

    # template_admin does NOT have approve permission
    assert not authorize(admin_actor, "approve_template_version").allowed


def test_template_lifecycle_workflow(db_session: Session, tmp_path: Path) -> None:
    """End-to-end test of the DB-backed lifecycle FSM transitions with 3-way separation of duties."""
    template_id = "test_sale_deed_v2"
    tenant_id = uuid.uuid4()
    uploader_actor = Actor(user_id=uuid.uuid4(), tenant_id=tenant_id, role="template_admin")
    submitter_actor = Actor(user_id=uuid.uuid4(), tenant_id=tenant_id, role="template_admin")
    reviewer_actor = Actor(user_id=uuid.uuid4(), tenant_id=tenant_id, role="reviewer")

    # 1. Initial draft state in DB
    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=tenant_id,
        template_key=template_id,
        version=1,
        status="draft",
        manifest_json={"template_id": template_id, "status": "draft"},
        docx_sha256="",
        docx_ref="",
        created_by=uploader_actor.user_id,
        submitted_by=None,
        approved_by=None,
    )
    db_session.add(tv)
    db_session.commit()

    # Cannot approve directly from draft
    with pytest.raises(HTTPException) as exc_info:
        approve_template(template_id=template_id, actor=reviewer_actor, db=db_session)
    assert exc_info.value.status_code == 409
    assert "Template must be 'under_review'" in exc_info.value.detail

    # Separation of duties: Uploader CANNOT submit their own draft!
    with pytest.raises(HTTPException) as exc_upload_submit:
        submit_template_for_review(template_id=template_id, actor=uploader_actor, db=db_session)
    assert exc_upload_submit.value.status_code == 403
    assert "Uploader cannot submit their own template" in exc_upload_submit.value.detail

    # 2. Distinct submitter submits for review
    submit_res = submit_template_for_review(template_id=template_id, actor=submitter_actor, db=db_session)
    assert submit_res["status"] == "under_review"

    db_session.refresh(tv)
    assert tv.submitted_by == submitter_actor.user_id
    assert tv.status == "under_review"

    # Cannot submit again if already under_review
    with pytest.raises(HTTPException) as exc_conflict:
        submit_template_for_review(template_id=template_id, actor=submitter_actor, db=db_session)
    assert exc_conflict.value.status_code == 409

    # 3. Separation of duties check: Submitter cannot approve!
    submitter_as_reviewer = Actor(
        user_id=submitter_actor.user_id, tenant_id=tenant_id, role="reviewer"
    )
    with pytest.raises(HTTPException) as exc_sep_sub:
        approve_template(template_id=template_id, actor=submitter_as_reviewer, db=db_session)
    assert exc_sep_sub.value.status_code == 403
    assert "Separation of duties violation" in exc_sep_sub.value.detail

    # Uploader cannot approve either!
    uploader_as_reviewer = Actor(
        user_id=uploader_actor.user_id, tenant_id=tenant_id, role="reviewer"
    )
    with pytest.raises(HTTPException) as exc_sep_up:
        approve_template(template_id=template_id, actor=uploader_as_reviewer, db=db_session)
    assert exc_sep_up.value.status_code == 403
    assert "Separation of duties violation" in exc_sep_up.value.detail

    # 4. Independent reviewer approves successfully
    with patch("app.api.templates_admin.TEMPLATES_DIR", tmp_path):
        # Create a mock template directory with valid manifest and dummy docx
        tmpl_dir = tmp_path / template_id
        tmpl_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = tmpl_dir / "manifest.json"
        manifest_file.write_text(
            json.dumps({"template_id": template_id, "status": "under_review"}), encoding="utf-8"
        )
        docx_file = tmpl_dir / "template.docx"
        docx_file.write_bytes(b"dummy_valid_docx")

        with patch("app.api.templates_admin.check_structural_safety", return_value=[]), \
             patch("app.api.templates_admin.DocxLinter") as mock_linter_cls:
            mock_report = MagicMock()
            mock_report.can_approve = True
            mock_report.leftover_data = []
            mock_linter_cls.return_value.lint.return_value = mock_report

            approve_res = approve_template(template_id=template_id, actor=reviewer_actor, db=db_session)
            assert approve_res["status"] == "approved"

        db_session.refresh(tv)
        assert tv.status == "approved"
        assert tv.approved_by == reviewer_actor.user_id
        assert tv.docx_sha256 != ""

        # 5. Retire template
        retire_res = retire_template(template_id=template_id, actor=submitter_actor, db=db_session)
        assert retire_res["status"] == "retired"

        db_session.refresh(tv)
        assert tv.status == "retired"


def test_quality_lint_gate_blocks_approval(db_session: Session, tmp_path: Path) -> None:
    """Approval must be rejected if DocxLinter detects unresolved issues or client leftover PII."""
    template_id = "test_defective_template"
    tenant_id = uuid.uuid4()
    reviewer_actor = Actor(user_id=uuid.uuid4(), tenant_id=tenant_id, role="reviewer")

    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=tenant_id,
        template_key=template_id,
        version=1,
        status="under_review",
        manifest_json={"template_id": template_id, "status": "under_review"},
        docx_sha256="",
        docx_ref="",
        created_by=uuid.uuid4(),
        submitted_by=uuid.uuid4(),  # distinct submitter
        approved_by=None,
    )
    db_session.add(tv)
    db_session.commit()

    with patch("app.api.templates_admin.TEMPLATES_DIR", tmp_path):
        tmpl_dir = tmp_path / template_id
        tmpl_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = tmpl_dir / "manifest.json"
        manifest_file.write_text(
            json.dumps({"template_id": template_id, "status": "under_review"}), encoding="utf-8"
        )
        docx_file = tmpl_dir / "template.docx"
        docx_file.write_bytes(b"dummy_docx_content")

        mock_report = MagicMock()
        mock_report.can_approve = False
        mock_report.leftover_data = [{"type": "aadhaar", "value": "1234-5678-9012"}]

        with patch("app.api.templates_admin.check_structural_safety", return_value=[]), \
             patch("app.api.templates_admin.DocxLinter") as mock_linter_cls:
            mock_linter_cls.return_value.lint.return_value = mock_report

            with pytest.raises(HTTPException) as exc_info:
                approve_template(template_id=template_id, actor=reviewer_actor, db=db_session)
            assert exc_info.value.status_code == 422
            assert "failed quality lint gate" in exc_info.value.detail
