"""Portal Data-Entry Sheet REST API Endpoints (PRD FR-16, Features F-063, Goal G6)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth import get_current_actor
from app.generation.pipeline import generation_pipeline
from app.identity.policy import Actor, Resource, authorize
from app.portal.generator import portal_sheet_generator
from app.portal.models import PortalDataSheet

router = APIRouter(prefix="/api/v1/documents", tags=["portal_sheet"])


@router.get(
    "/{document_id}/portal-sheet",
    response_model=PortalDataSheet,
    summary="Get structured portal data-entry sheet for Maharashtra IGR / PDE",
)
def get_document_portal_sheet(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Produces assistive portal data sheet from document snapshot (PRD FR-16, F-063)."""
    doc = generation_pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    return portal_sheet_generator.generate_sheet(doc)


@router.get(
    "/{document_id}/portal-sheet/text",
    response_class=Response,
    summary="Download plain-text formatted copy-paste sheet for registration portal",
)
def download_portal_sheet_text(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Response:
    """Streams plain text portal entry sheet directly formatted for copy-paste."""
    doc = generation_pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    sheet = portal_sheet_generator.generate_sheet(doc)
    safe_doc_no = doc.doc_no.replace("/", "_")
    filename = f"Portal_Entry_Sheet_{safe_doc_no}.txt"

    return Response(
        content=sheet.copy_paste_text,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )

