"""Document Review Service (PRD FR-10, Features F-058).

Handles business logic for document review lifecycles, tenant isolation, and audit logging.
"""

from __future__ import annotations

import uuid

from app.audit.service import audit_service
from app.generation.pipeline import GenerationPipelineFSM, generation_pipeline
from app.review.fsm import (
    ReviewChecklist,
    ReviewMetadata,
    ReviewStatus,
    reopen_to_draft,
    transition_to_finalised,
    transition_to_reviewed,
)


class DocumentReviewService:
    """Manages document review transitions, checklists, and immutability."""

    def __init__(self, pipeline: GenerationPipelineFSM = generation_pipeline) -> None:
        self.pipeline = pipeline
        self._reviews: dict[uuid.UUID, ReviewMetadata] = {}

    def get_review_record(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> ReviewMetadata | None:
        """Retrieves review metadata ensuring tenant isolation."""
        doc = self.pipeline.get_document(document_id, tenant_id)
        if not doc:
            return None
        return self._reviews.get(document_id, ReviewMetadata(status=ReviewStatus(doc.status)))

    def mark_reviewed(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        checklist: ReviewChecklist,
        reviewer_id: str,
    ) -> ReviewMetadata:
        """Submits document review with completed checklist."""
        doc = self.pipeline.get_document(document_id, tenant_id)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self._reviews.get(
            document_id,
            ReviewMetadata(status=ReviewStatus(doc.status)),
        )
        new_meta = transition_to_reviewed(
            current_status=current_meta.status,
            checklist=checklist,
            reviewer_id=reviewer_id,
        )

        self._reviews[document_id] = new_meta
        doc.status = new_meta.status.value

        audit_service.log_event(
            tenant_id=tenant_id,
            action="document_marked_reviewed",
            entity="document",
            entity_id=str(document_id),
            meta={"reviewed_by": reviewer_id, "notes": checklist.reviewer_notes},
        )
        return new_meta

    def mark_finalised(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        finaliser_id: str,
    ) -> ReviewMetadata:
        """Locks document as finalised. Output becomes permanently immutable."""
        doc = self.pipeline.get_document(document_id, tenant_id)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self._reviews.get(
            document_id,
            ReviewMetadata(status=ReviewStatus(doc.status)),
        )
        new_meta = transition_to_finalised(
            current_status=current_meta.status,
            finaliser_id=finaliser_id,
            existing_meta=current_meta,
        )

        self._reviews[document_id] = new_meta
        doc.status = new_meta.status.value

        audit_service.log_event(
            tenant_id=tenant_id,
            action="document_finalised",
            entity="document",
            entity_id=str(document_id),
            meta={"finalised_by": finaliser_id},
        )
        return new_meta

    def reopen_for_edit(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        actor_id: str,
    ) -> ReviewMetadata:
        """Reopens a reviewed document back to draft for revisions."""
        doc = self.pipeline.get_document(document_id, tenant_id)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self._reviews.get(
            document_id,
            ReviewMetadata(status=ReviewStatus(doc.status)),
        )
        new_meta = reopen_to_draft(
            current_status=current_meta.status,
            reopened_by=actor_id,
        )

        self._reviews[document_id] = new_meta
        doc.status = new_meta.status.value

        audit_service.log_event(
            tenant_id=tenant_id,
            action="document_reopened_to_draft",
            entity="document",
            entity_id=str(document_id),
            meta={"reopened_by": actor_id},
        )
        return new_meta

    def clear(self) -> None:
        self._reviews.clear()


document_review_service = DocumentReviewService()
