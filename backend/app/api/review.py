"""Document Review API Endpoints (PRD FR-10, Features F-058).

Exposes review checklist submission, status queries, finalisation lock, and reopen actions.
Uses scoped database sessions and PostgresDocumentRepository to ensure consistent state.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.repositories.documents import PostgresDocumentRepository
from app.api.auth import get_current_actor
from app.audit.service import audit_service
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.repository import DocumentRepository
from app.identity.policy import Actor, Resource, authorize
from app.review.fsm import (
    DocumentFinalisedError,
    IncompleteChecklistError,
    InvalidReviewTransitionError,
    ReviewChecklist,
    ReviewMetadata,
)
from app.review.service import document_review_service

router = APIRouter(prefix="/api/v1/documents", tags=["review"])


def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    return PostgresDocumentRepository(db)


def get_pipeline(repo: DocumentRepository = Depends(get_document_repo)) -> GenerationPipelineFSM:
    return GenerationPipelineFSM(repository=repo)


@router.get(
    "/{document_id}/review",
    response_model=ReviewMetadata,
    summary="Get document review status and checklist",
)
def get_document_review_status(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieves current review state and checklist with statutory disclaimers."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    record = document_review_service.get_review_record(document_id, actor.tenant_id, session=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return record


@router.post(
    "/{document_id}/review",
    response_model=ReviewMetadata,
    summary="Submit review checklist and mark document as reviewed",
)
def mark_document_as_reviewed(
    document_id: uuid.UUID,
    checklist: ReviewChecklist,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
    db: Session = Depends(get_db),
) -> Any:
    """Verifies statutory checklist and transitions draft to reviewed."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "review_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        return document_review_service.mark_reviewed(
            document_id=document_id,
            tenant_id=actor.tenant_id,
            checklist=checklist,
            reviewer_id=str(actor.user_id),
            session=db,
        )
    except IncompleteChecklistError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except (InvalidReviewTransitionError, DocumentFinalisedError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{document_id}/finalise",
    response_model=ReviewMetadata,
    summary="Finalise reviewed document into immutable state",
)
def finalise_document(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
    db: Session = Depends(get_db),
) -> Any:
    """Locks reviewed document as finalised. Subsequent edits or reviews are prohibited."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "finalize_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        res = document_review_service.mark_finalised(
            document_id=document_id,
            tenant_id=actor.tenant_id,
            finaliser_id=str(actor.user_id),
            session=db,
        )
        audit_service.log_event(
            tenant_id=doc.tenant_id,
            action="finalise_document",
            entity="document",
            entity_id=str(document_id),
            actor_id=actor.user_id,
            meta={"doc_no": doc.doc_no, "finalised_by": str(actor.user_id)},
        )
        return res
    except (InvalidReviewTransitionError, DocumentFinalisedError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{document_id}/reopen",
    response_model=ReviewMetadata,
    summary="Reopen reviewed document back to draft for revisions",
)
def reopen_document_to_draft(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
    db: Session = Depends(get_db),
) -> Any:
    """Reopens a reviewed document back to draft. Finalised documents cannot be reopened."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "edit_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        return document_review_service.reopen_for_edit(
            document_id=document_id,
            tenant_id=actor.tenant_id,
            actor_id=str(actor.user_id),
            session=db,
        )
    except (InvalidReviewTransitionError, DocumentFinalisedError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
