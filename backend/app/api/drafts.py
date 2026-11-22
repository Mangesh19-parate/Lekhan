"""Drafts REST API for managing in-progress legal drafting sessions."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.auth import get_current_actor
from app.identity.policy import Actor, Resource, authorize
from app.shared.ids import uuid7
from app.shared.models import Draft

router = APIRouter(prefix="/api/v1/drafts", tags=["drafts"])


# --- Schemas ---


class DraftResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    template_id: str | None = None
    data: dict[str, Any]
    created_at: str
    updated_at: str


class DraftCreatePayload(BaseModel):
    title: str = "Untitled Draft"
    template_id: str | None = None
    data: dict[str, Any] = {}


class DraftUpdatePayload(BaseModel):
    title: str | None = None
    template_id: str | None = None
    data: dict[str, Any] | None = None


def _format_draft(draft: Draft) -> DraftResponse:
    return DraftResponse(
        id=draft.id,
        tenant_id=draft.tenant_id,
        user_id=draft.user_id,
        title=draft.title,
        template_id=draft.template_id,
        data=draft.data or {},
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )


# --- Routes ---


@router.get("", response_model=list[DraftResponse], summary="List all in-progress drafts for current tenant")
def list_drafts(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> list[DraftResponse]:
    """Retrieves active in-progress drafting sessions for tenant. Drafters see only their own drafts."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    query = db.query(Draft).filter(Draft.tenant_id == actor.tenant_id)
    if actor.role == "drafter":
        query = query.filter(Draft.user_id == actor.user_id)

    drafts = query.order_by(Draft.updated_at.desc()).all()
    return [_format_draft(d) for d in drafts]


@router.post("", response_model=DraftResponse, status_code=status.HTTP_201_CREATED, summary="Create a new draft")
def create_draft(
    payload: DraftCreatePayload,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> DraftResponse:
    """Creates a new in-progress draft record with form and repeater data."""
    decision = authorize(actor, "create_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    draft = Draft(
        id=uuid7(),
        tenant_id=actor.tenant_id,
        user_id=actor.user_id,
        title=payload.title,
        template_id=payload.template_id,
        data=payload.data,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _format_draft(draft)


@router.get("/{draft_id}", response_model=DraftResponse, summary="Get a single draft by ID")
def get_draft(
    draft_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> DraftResponse:
    """Retrieves a single draft. Scoped strictly to the tenant; cross-tenant access returns 404."""
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.tenant_id == actor.tenant_id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    resource = Resource(tenant_id=draft.tenant_id, resource_type="draft", owner_id=draft.user_id)
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    return _format_draft(draft)


@router.put("/{draft_id}", response_model=DraftResponse, summary="Update an existing draft")
def update_draft(
    draft_id: uuid.UUID,
    payload: DraftUpdatePayload,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> DraftResponse:
    """Updates an existing draft's title, template_id, or form data."""
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.tenant_id == actor.tenant_id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    resource = Resource(tenant_id=draft.tenant_id, resource_type="draft", owner_id=draft.user_id)
    decision = authorize(actor, "edit_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    if payload.title is not None:
        draft.title = payload.title
    if payload.template_id is not None:
        draft.template_id = payload.template_id
    if payload.data is not None:
        draft.data = payload.data

    draft.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(draft)
    return _format_draft(draft)


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a draft")
def delete_draft(
    draft_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> Response:
    """Deletes an in-progress draft session. Scoped strictly to the tenant."""
    draft = (
        db.query(Draft)
        .filter(Draft.id == draft_id, Draft.tenant_id == actor.tenant_id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    resource = Resource(tenant_id=draft.tenant_id, resource_type="draft", owner_id=draft.user_id)
    decision = authorize(actor, "delete_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    db.delete(draft)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
