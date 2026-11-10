"""Template Lifecycle Admin API Endpoints (PRD FR-09, Features F-028, Plan Week 22).

Provides:
- Template catalog discovery
- Live DocxLinter static quality inspection
- Template version upload (.docx and manifest.json)
- Approval workflow with strict separation of duties (submitter cannot approve)
- Status transitions: draft -> under_review -> approved -> retired
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.auth import get_current_actor
from app.audit.service import audit_service
from app.identity.policy import Actor, Resource, authorize
from app.templates.lint import DocxLinter

router = APIRouter(prefix="/api/v1/templates", tags=["templates_admin"])
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates-library"

# In-memory lifecycle tracking for submitters and approvers (backed by template_versions table in DB)
_TEMPLATE_LIFECYCLE_META: dict[str, dict[str, Any]] = {}


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
    submitted_by: str | None = None
    approved_by: str | None = None


@router.get("", response_model=list[TemplateSummary], summary="List all templates with status")
def list_templates(actor: Actor = Depends(get_current_actor)) -> list[TemplateSummary]:
    """Returns library templates with catalog metadata and lifecycle states."""
    results: list[TemplateSummary] = []
    if not TEMPLATES_DIR.exists():
        return results

    for item in sorted(TEMPLATES_DIR.iterdir()):
        if not item.is_dir():
            continue
        manifest_file = item / "manifest.json"
        if not manifest_file.exists():
            continue

        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            t_id = data.get("template_id", item.name)
            meta = _TEMPLATE_LIFECYCLE_META.get(t_id, {})
            current_status = meta.get("status", data.get("status", "draft"))

            results.append(
                TemplateSummary(
                    template_id=t_id,
                    name_en=data.get("name_en", item.name),
                    name_mr=data.get("name_mr", ""),
                    version=data.get("version", 1),
                    status=current_status,
                    language=data.get("language", "mr"),
                    document_type=data.get("document_type", "general"),
                    property_type=data.get("property_type", "general"),
                    has_docx=(item / "template.docx").exists(),
                    submitted_by=meta.get("submitted_by"),
                    approved_by=meta.get("approved_by"),
                )
            )
        except Exception:
            continue
    return results


@router.post("/{template_id}/lint", summary="Run DocxLinter against a template")
def lint_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
) -> dict[str, Any]:
    """Runs structural, tag, leftover, and font checks against template.docx."""
    tmpl_dir = TEMPLATES_DIR / template_id
    if not tmpl_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found.",
        )

    manifest_file = tmpl_dir / "manifest.json"
    docx_file = tmpl_dir / "template.docx"

    if not manifest_file.exists() or not docx_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template files missing.",
        )

    raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    docx_bytes = docx_file.read_bytes()

    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=raw_manifest)
    return report.to_dict()


@router.post("/upload", summary="Upload a new template version")
async def upload_template(
    template_id: str = Form(...),
    manifest_json: str = Form(...),
    docx_file: UploadFile = File(...),
    actor: Actor = Depends(get_current_actor),
) -> dict[str, Any]:
    """Uploads a new draft template version (.docx + manifest.json)."""
    decision = authorize(actor, "upload_template_version")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        manifest_data = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON manifest: {exc}")

    docx_bytes = await docx_file.read()

    # Pre-upload lint check
    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=manifest_data)

    target_dir = TEMPLATES_DIR / template_id
    target_dir.mkdir(parents=True, exist_ok=True)

    manifest_data["status"] = "draft"
    (target_dir / "manifest.json").write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
    (target_dir / "template.docx").write_bytes(docx_bytes)

    _TEMPLATE_LIFECYCLE_META[template_id] = {
        "status": "draft",
        "created_by": str(actor.user_id),
        "submitted_by": None,
        "approved_by": None,
    }

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_uploaded",
        entity="template",
        entity_id=template_id,
        meta={"can_approve": report.can_approve},
    )

    return {
        "template_id": template_id,
        "status": "draft",
        "lint_report": report.to_dict(),
        "message": "Template uploaded as draft version.",
    }


@router.post("/{template_id}/submit", summary="Submit template version for advocate review")
def submit_template_for_review(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
) -> dict[str, str]:
    """Transitions template from draft to under_review."""
    meta = _TEMPLATE_LIFECYCLE_META.setdefault(template_id, {"status": "draft"})
    current_status = meta.get("status", "draft")

    if current_status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit template in '{current_status}' status.",
        )

    meta["status"] = "under_review"
    meta["submitted_by"] = str(actor.user_id)

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_submitted_for_review",
        entity="template",
        entity_id=template_id,
        meta={"submitted_by": str(actor.user_id)},
    )
    return {"template_id": template_id, "status": "under_review"}


@router.post("/{template_id}/approve", summary="Approve template version (Separation of Duties enforced)")
def approve_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
) -> dict[str, str]:
    """Approves template version into production immutable status (PRD FR-09).

    Enforces Separation of Duties: Submitter CANNOT approve their own template version.
    """
    decision = authorize(actor, "approve_template_version")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    meta = _TEMPLATE_LIFECYCLE_META.setdefault(template_id, {"status": "draft"})
    current_status = meta.get("status", "draft")

    if current_status != "under_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template must be 'under_review' to approve; current status is '{current_status}'.",
        )

    # Separation of Duties check: submitter cannot approve
    submitter_id = meta.get("submitted_by")
    if submitter_id and submitter_id == str(actor.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Separation of duties violation: Submitter cannot approve their own template version.",
        )

    # Lint check: must pass cleanly
    tmpl_dir = TEMPLATES_DIR / template_id
    manifest_file = tmpl_dir / "manifest.json"
    docx_file = tmpl_dir / "template.docx"
    if manifest_file.exists() and docx_file.exists():
        raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        report = DocxLinter().lint(docx_file.read_bytes(), manifest=raw_manifest)
        if not report.can_approve or len(report.leftover_data) > 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template failed quality lint gate and cannot be approved.",
            )

    meta["status"] = "approved"
    meta["approved_by"] = str(actor.user_id)

    # Update manifest on disk
    if manifest_file.exists():
        raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        raw_manifest["status"] = "approved"
        manifest_file.write_text(json.dumps(raw_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_approved",
        entity="template",
        entity_id=template_id,
        meta={"approved_by": str(actor.user_id)},
    )
    return {"template_id": template_id, "status": "approved"}


@router.post("/{template_id}/retire", summary="Retire an approved template")
def retire_template(
    template_id: str,
    actor: Actor = Depends(get_current_actor),
) -> dict[str, str]:
    """Retires template from production library."""
    decision = authorize(actor, "retire_template")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    meta = _TEMPLATE_LIFECYCLE_META.setdefault(template_id, {"status": "draft"})
    meta["status"] = "retired"

    tmpl_dir = TEMPLATES_DIR / template_id
    manifest_file = tmpl_dir / "manifest.json"
    if manifest_file.exists():
        raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        raw_manifest["status"] = "retired"
        manifest_file.write_text(json.dumps(raw_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_service.log_event(
        tenant_id=actor.tenant_id,
        actor_id=actor.user_id,
        action="template_version_retired",
        entity="template",
        entity_id=template_id,
        meta={"retired_by": str(actor.user_id)},
    )
    return {"template_id": template_id, "status": "retired"}
