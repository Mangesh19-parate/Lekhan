"""Template Lifecycle Admin API Endpoints (PRD FR-09, Features F-028, Plan Week 22).

Provides:
- DB-backed, immutable template versions
- Template catalog discovery
- Live DocxLinter static quality inspection
- Template version upload (.docx and manifest.json) creating version N+1
- Approval workflow with 3-way separation of duties (uploader != submitter != approver)
- Status transitions: draft -> under_review -> approved -> retired
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.storage import default_storage
from app.api.auth import get_current_actor
from app.audit.service import audit_service
from app.generation.renderers import default_renderer_registry
from app.identity.policy import Actor, authorize
from app.shared.ids import uuid7
from app.shared.logging import get_correlation_id, get_logger
from app.shared.models import TemplateVersion
from app.templates.lint import DocxLinter
from app.templates.lint.models import LintSeverity
from app.templates.lint.structural import MAX_COMPRESSED_SIZE_BYTES, check_structural_safety
from app.templates.validator import TEMPLATES_DIR, validate_template_id

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["templates_admin"])


class TemplateSummary(BaseModel):
    template_id: str
    name_en: str
    name_mr: str
    version: int
    status: str
    language: str
    document_type: str
    property_type: str
    has_docx: bool
    has_renderer: bool = False
    can_generate: bool = False
    submitted_by: str | None = None
    approved_by: str | None = None


@router.get("", response_model=list[TemplateSummary], summary="List all templates with status")
def list_templates(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> list[TemplateSummary]:
    """Returns library templates with catalog metadata and DB lifecycle states."""
    decision = authorize(actor, "view_template")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    results: list[TemplateSummary] = []
    seen_keys: set[str] = set()

    # 1. Fetch latest template version per template_key from DB
    db_records = (
        db.query(TemplateVersion)
        .order_by(TemplateVersion.template_key, TemplateVersion.version.desc())
        .all()
    )
    for tv in db_records:
        if tv.template_key in seen_keys:
            continue
        seen_keys.add(tv.template_key)
        m = tv.manifest_json or {}
        has_file = bool(tv.docx_ref and default_storage.exists(tv.docx_ref))
        has_renderer = default_renderer_registry.has_renderer(tv.template_key)
        can_generate = bool(tv.status == "approved" and has_file and has_renderer)
        results.append(
            TemplateSummary(
                template_id=tv.template_key,
                name_en=m.get("name_en", tv.template_key),
                name_mr=m.get("name_mr", ""),
                version=tv.version,
                status=tv.status,
                language=m.get("language", "mr"),
                document_type=m.get("document_type", "general"),
                property_type=m.get("property_type", "general"),
                has_docx=has_file,
                has_renderer=has_renderer,
                can_generate=can_generate,
                submitted_by=str(tv.submitted_by) if tv.submitted_by else None,
                approved_by=str(tv.approved_by) if tv.approved_by else None,
            )
        )

    # 2. Add local filesystem templates not yet recorded in DB (seed / disk discovery)
    if TEMPLATES_DIR.exists():
        for item in sorted(TEMPLATES_DIR.iterdir()):
            if not item.is_dir() or item.name in seen_keys:
                continue
            manifest_file = item / "manifest.json"
            if not manifest_file.exists():
                continue
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                t_id = data.get("template_id", item.name)
                if t_id in seen_keys:
                    continue
                seen_keys.add(t_id)
                has_docx = (item / "template.docx").exists()
                t_status = data.get("status", "draft")
                has_renderer = default_renderer_registry.has_renderer(t_id)
                can_generate = bool(t_status == "approved" and has_docx and has_renderer)
                results.append(
                    TemplateSummary(
                        template_id=t_id,
                        name_en=data.get("name_en", item.name),
                        name_mr=data.get("name_mr", ""),
                        version=data.get("version", 1),
                        status=t_status,
                        language=data.get("language", "mr"),
                        document_type=data.get("document_type", "general"),
                        property_type=data.get("property_type", "general"),
                        has_docx=has_docx,
                        has_renderer=has_renderer,
                        can_generate=can_generate,
                    )
                )
            except (json.JSONDecodeError, OSError, KeyError) as err:
                logger.warning(
                    "Skipping invalid template directory %s [cid=%s]: %s",
                    item,
                    get_correlation_id(),
                    err,
                )
                continue

    return results


@router.get("/{template_id}/manifest", summary="Get parsed manifest for a template")
def get_template_manifest(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieves full manifest JSON schema and validation rules for a template."""
    try:
        tmpl_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "view_template")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    # Check DB first for latest template version
    tv = (
        db.query(TemplateVersion)
        .filter(TemplateVersion.template_key == template_id)
        .order_by(TemplateVersion.version.desc())
        .first()
    )
    if tv and tv.manifest_json:
        return tv.manifest_json

    manifest_file = tmpl_dir / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manifest for template '{template_id}' not found.",
        )
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    return dict(data) if isinstance(data, dict) else {}


@router.post("/{template_id}/lint", summary="Run DocxLinter against a template")
def lint_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Runs structural, tag, leftover, and font checks against template.docx."""
    try:
        tmpl_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "lint_template")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    docx_bytes: bytes | None = None
    raw_manifest: dict[str, Any] | None = None

    # Check DB for latest version
    tv = (
        db.query(TemplateVersion)
        .filter(TemplateVersion.template_key == template_id)
        .order_by(TemplateVersion.version.desc())
        .first()
    )
    if tv:
        raw_manifest = tv.manifest_json
        if tv.docx_ref:
            docx_bytes = default_storage.get(tv.docx_ref)

    if docx_bytes is None:
        docx_file = tmpl_dir / "template.docx"
        if docx_file.exists():
            docx_bytes = docx_file.read_bytes()

    if raw_manifest is None:
        manifest_file = tmpl_dir / "manifest.json"
        if manifest_file.exists():
            raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    if docx_bytes is None or raw_manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' files missing.",
        )

    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=raw_manifest)
    return report.to_dict()


@router.post("/upload", summary="Upload a new template version")
async def upload_template(
    template_id: str = Form(...),
    manifest_json: str = Form(...),
    docx_file: UploadFile = File(...),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Uploads a new draft template version (.docx + manifest.json) as version N+1."""
    try:
        target_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "upload_template_version")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        manifest_data = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON manifest: {exc}"
        )

    # 1. Filename and extension validation
    filename = (docx_file.filename or "").lower()
    if not filename.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File upload rejected: only .docx templates are supported (macros/.docm prohibited).",
        )

    # 2. MIME type validation
    allowed_mimes = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
        "application/zip",
        "application/x-zip-compressed",
    }
    content_type = (docx_file.content_type or "").lower()
    if content_type and content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload rejected: invalid MIME type '{docx_file.content_type}'.",
        )

    docx_bytes = await docx_file.read()

    # 3. File size check (5 MB limit per docs/API.md and AGENTS.md Rule 7)
    if len(docx_bytes) > MAX_COMPRESSED_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload rejected: size ({len(docx_bytes)} bytes) exceeds 5 MB limit.",
        )

    # 4. Structural security inspection (zip bomb, macros, external relationships, safe XML)
    structural_findings = check_structural_safety(docx_bytes)
    critical_errors = [f.message for f in structural_findings if f.severity == LintSeverity.ERROR]
    if critical_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Structural security validation rejected upload: {'; '.join(critical_errors)}",
        )

    # Pre-upload lint check
    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=manifest_data)

    # Always create version N+1
    max_ver = (
        db.query(func.max(TemplateVersion.version))
        .filter(TemplateVersion.template_key == template_id)
        .scalar()
    )
    next_version = (max_ver or 0) + 1

    manifest_data["status"] = "draft"
    manifest_data["version"] = next_version

    # Store bytes in ObjectStore atomically
    storage_key = f"templates/{template_id}/v{next_version}/template.docx"
    default_storage.put(
        storage_key,
        docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    docx_sha256 = hashlib.sha256(docx_bytes).hexdigest()

    tv = TemplateVersion(
        id=uuid7(),
        tenant_id=actor.tenant_id,
        template_key=template_id,
        version=next_version,
        status="draft",
        manifest_json=manifest_data,
        docx_sha256=docx_sha256,
        docx_ref=storage_key,
        created_by=actor.user_id,
        submitted_by=None,
        approved_by=None,
        approved_at=None,
    )
    db.add(tv)
    db.commit()
    db.refresh(tv)

    # Sync to local templates-library directory as fallback
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "manifest.json").write_text(
            json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (target_dir / "template.docx").write_bytes(docx_bytes)
    except OSError as err:
        logger.warning("Could not sync template to local disk directory: %s", err)

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_uploaded",
        entity="template",
        entity_id=template_id,
        meta={"version": next_version, "can_approve": report.can_approve},
    )

    return {
        "template_id": template_id,
        "version": next_version,
        "status": "draft",
        "lint_report": report.to_dict(),
        "message": f"Template uploaded as draft version {next_version}.",
    }


@router.post("/{template_id}/submit", summary="Submit template version for advocate review")
def submit_template_for_review(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Transitions template from draft to under_review with separation of duties (uploader != submitter)."""
    try:
        validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "submit_template_for_review")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    tv = (
        db.query(TemplateVersion)
        .filter(TemplateVersion.template_key == template_id)
        .order_by(TemplateVersion.version.desc())
        .first()
    )
    if not tv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found.",
        )

    if tv.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit template in '{tv.status}' status.",
        )

    # Separation of duties: uploader cannot submit
    tv_created = str(tv.created_by) if tv.created_by else ""
    actor_id_str = str(actor.user_id)
    if tv_created and tv_created == actor_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Separation of duties violation: Uploader cannot submit their own template version for review.",
        )

    tv.status = "under_review"
    tv.submitted_by = actor.user_id
    db.commit()
    db.refresh(tv)

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_submitted_for_review",
        entity="template",
        entity_id=template_id,
        meta={"version": tv.version, "submitted_by": str(actor.user_id)},
    )
    return {"template_id": template_id, "version": tv.version, "status": "under_review"}


@router.post(
    "/{template_id}/approve", summary="Approve template version (Separation of Duties enforced)"
)
def approve_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approves template version into immutable production status (PRD FR-09).

    Enforces 3-way Separation of Duties: Uploader != Submitter != Approver.
    Re-runs structural + lint verification on stored bytes and verifies SHA-256.
    """
    try:
        tmpl_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "approve_template_version")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    tv = (
        db.query(TemplateVersion)
        .filter(TemplateVersion.template_key == template_id)
        .order_by(TemplateVersion.version.desc())
        .first()
    )
    if not tv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found.",
        )

    if tv.status != "under_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template must be 'under_review' to approve; current status is '{tv.status}'.",
        )

    # 3-way Separation of Duties: Approver cannot be uploader or submitter
    actor_id_str = str(actor.user_id)
    tv_created = str(tv.created_by) if tv.created_by else ""
    tv_submitted = str(tv.submitted_by) if tv.submitted_by else ""
    if actor_id_str in (tv_created, tv_submitted):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Separation of duties violation: Submitter and uploader cannot approve their own template version.",
        )

    # Fetch stored bytes from ObjectStore
    docx_bytes = default_storage.get(tv.docx_ref) if tv.docx_ref else None
    if docx_bytes is None:
        docx_file = tmpl_dir / "template.docx"
        if docx_file.exists():
            docx_bytes = docx_file.read_bytes()
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template docx file missing in storage.",
            )

    # SHA-256 calculation & verification
    current_sha256 = hashlib.sha256(docx_bytes).hexdigest()
    if tv.docx_sha256 and tv.docx_sha256 != current_sha256:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stored template bytes SHA-256 mismatch.",
        )

    # Re-run structural security checks on stored bytes
    structural_findings = check_structural_safety(docx_bytes)
    critical_errors = [f.message for f in structural_findings if f.severity == LintSeverity.ERROR]
    if critical_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Structural security validation rejected approval: {'; '.join(critical_errors)}",
        )

    # Re-run DocxLinter on stored bytes + manifest
    raw_manifest = tv.manifest_json or {}
    report = DocxLinter().lint(docx_bytes, manifest=raw_manifest)
    if not report.can_approve or len(report.leftover_data) > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Template failed quality lint gate and cannot be approved.",
        )

    # Mark approved and record immutable SHA-256 and approval timestamp
    tv.status = "approved"
    tv.approved_by = actor.user_id
    tv.approved_at = datetime.datetime.now(datetime.timezone.utc)
    tv.docx_sha256 = current_sha256
    db.commit()
    db.refresh(tv)

    # Sync manifest on disk if present
    manifest_file = tmpl_dir / "manifest.json"
    if manifest_file.exists():
        try:
            m_disk = json.loads(manifest_file.read_text(encoding="utf-8"))
            m_disk["status"] = "approved"
            manifest_file.write_text(
                json.dumps(m_disk, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_approved",
        entity="template",
        entity_id=template_id,
        meta={"version": tv.version, "approved_by": actor_id_str, "sha256": current_sha256},
    )
    return {"template_id": template_id, "version": tv.version, "status": "approved"}


@router.post("/{template_id}/retire", summary="Retire an approved template")
def retire_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retires template from production library."""
    try:
        tmpl_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    decision = authorize(actor, "retire_template")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    tv = (
        db.query(TemplateVersion)
        .filter(TemplateVersion.template_key == template_id)
        .order_by(TemplateVersion.version.desc())
        .first()
    )
    if not tv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found.",
        )

    tv.status = "retired"
    db.commit()
    db.refresh(tv)

    manifest_file = tmpl_dir / "manifest.json"
    if manifest_file.exists():
        try:
            raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            raw_manifest["status"] = "retired"
            manifest_file.write_text(
                json.dumps(raw_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_retired",
        entity="template",
        entity_id=template_id,
        meta={"version": tv.version, "retired_by": str(actor.user_id)},
    )
    return {"template_id": template_id, "version": tv.version, "status": "retired"}
