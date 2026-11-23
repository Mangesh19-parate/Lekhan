"""Document Review Service (PRD FR-10, Features F-058).

Handles business logic for document review lifecycles, tenant isolation, and audit logging.
Persists review metadata, reviewer checklist, and finalizer identity to PostgreSQL with
concurrency locking (FOR UPDATE) to prevent simultaneous finalization races.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy.orm import Session

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
from app.shared.ids import uuid7
from app.shared.logging import get_logger

logger = get_logger(__name__)


class DocumentReviewService:
    """Manages document review transitions, checklists, and immutability."""

    def __init__(self, pipeline: GenerationPipelineFSM | None = None) -> None:
        if pipeline is not None:
            self.pipeline = pipeline
        else:
            try:
                from app.adapters.repositories.documents import PostgresDocumentRepository
                self.pipeline = GenerationPipelineFSM(repository=PostgresDocumentRepository())
            except Exception:
                self.pipeline = GenerationPipelineFSM()
        self._reviews: dict[uuid.UUID, ReviewMetadata] = {}

    def _get_db_session(self, session: Session | None = None) -> tuple[Session | None, bool]:
        if session is not None:
            return session, False
        try:
            from app.adapters.db import SessionLocal
            return SessionLocal(), True
        except Exception:
            return None, False

    def _get_document(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        session: Session | None = None,
    ) -> Any:
        """Retrieves document from session-bound PostgreSQL repository or fallback pipeline."""
        if session is not None:
            try:
                from app.adapters.repositories.documents import PostgresDocumentRepository
                doc = PostgresDocumentRepository(session=session).get(tenant_id, document_id)
                if doc:
                    return doc
            except Exception:
                pass
        return self.pipeline.get_document(document_id, tenant_id)

    def get_review_record(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        session: Session | None = None,
    ) -> ReviewMetadata | None:
        """Retrieves review metadata ensuring tenant isolation."""
        db, should_close = self._get_db_session(session)
        if db is not None:
            try:
                from app.shared.models import DocumentReview as DocumentReviewModel
                rev_model = (
                    db.query(DocumentReviewModel)
                    .filter(
                        DocumentReviewModel.document_id == document_id,
                        DocumentReviewModel.tenant_id == tenant_id,
                    )
                    .first()
                )
                if rev_model:
                    checklist_obj = (
                        ReviewChecklist.model_validate(rev_model.checklist)
                        if rev_model.checklist
                        else None
                    )
                    return ReviewMetadata(
                        status=ReviewStatus(rev_model.status),
                        checklist=checklist_obj,
                        reviewed_by=rev_model.reviewed_by,
                        reviewed_at=rev_model.reviewed_at.isoformat() if rev_model.reviewed_at else None,
                        finalised_by=rev_model.finalised_by,
                        finalised_at=rev_model.finalised_at.isoformat() if rev_model.finalised_at else None,
                    )
            except Exception as e:
                logger.debug("Database review fetch unavailable: %s", e)
            finally:
                if should_close:
                    db.close()

        doc = self._get_document(document_id, tenant_id, session)
        if not doc:
            return None
        return self._reviews.get(document_id, ReviewMetadata(status=ReviewStatus(doc.status)))

    def mark_reviewed(
        self,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        checklist: ReviewChecklist,
        reviewer_id: str,
        session: Session | None = None,
    ) -> ReviewMetadata:
        """Submits document review with completed checklist."""
        doc = self._get_document(document_id, tenant_id, session)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self.get_review_record(document_id, tenant_id, session) or ReviewMetadata(
            status=ReviewStatus(doc.status)
        )
        new_meta = transition_to_reviewed(
            current_status=current_meta.status,
            checklist=checklist,
            reviewer_id=reviewer_id,
        )

        db, should_close = self._get_db_session(session)
        if db is not None:
            try:
                from app.shared.models import Document as DocumentModel
                from app.shared.models import DocumentReview as DocumentReviewModel

                # Lock the document row to prevent concurrent modification
                db_doc = (
                    db.query(DocumentModel)
                    .filter(
                        DocumentModel.id == document_id,
                        DocumentModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                if db_doc:
                    db_doc.status = new_meta.status.value

                db_rev = (
                    db.query(DocumentReviewModel)
                    .filter(
                        DocumentReviewModel.document_id == document_id,
                        DocumentReviewModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                checklist_dict = checklist.model_dump()
                if not db_rev:
                    db_rev = DocumentReviewModel(
                        id=uuid7(),
                        tenant_id=tenant_id,
                        document_id=document_id,
                        status=new_meta.status.value,
                        checklist=checklist_dict,
                        reviewed_by=reviewer_id,
                        reviewed_at=now_dt,
                    )
                    db.add(db_rev)
                else:
                    db_rev.status = new_meta.status.value
                    db_rev.checklist = checklist_dict
                    db_rev.reviewed_by = reviewer_id
                    db_rev.reviewed_at = now_dt

                # Ensure review transition is committed to database
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error("Database review persistence error: %s", e)
                from app.config import get_settings
                if get_settings().ENV in ("prod", "staging"):
                    raise RuntimeError(f"Database review persistence error: {e}") from e
            finally:
                if should_close:
                    db.close()

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
        session: Session | None = None,
    ) -> ReviewMetadata:
        """Locks document as finalised. Output becomes permanently immutable."""
        doc = self._get_document(document_id, tenant_id, session)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self.get_review_record(document_id, tenant_id, session) or ReviewMetadata(
            status=ReviewStatus(doc.status)
        )
        new_meta = transition_to_finalised(
            current_status=current_meta.status,
            finaliser_id=finaliser_id,
            existing_meta=current_meta,
        )

        db, should_close = self._get_db_session(session)
        if db is not None:
            try:
                from app.shared.models import Document as DocumentModel
                from app.shared.models import DocumentReview as DocumentReviewModel

                db_doc = (
                    db.query(DocumentModel)
                    .filter(
                        DocumentModel.id == document_id,
                        DocumentModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                if db_doc:
                    db_doc.status = new_meta.status.value

                db_rev = (
                    db.query(DocumentReviewModel)
                    .filter(
                        DocumentReviewModel.document_id == document_id,
                        DocumentReviewModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                if not db_rev:
                    db_rev = DocumentReviewModel(
                        id=uuid7(),
                        tenant_id=tenant_id,
                        document_id=document_id,
                        status=new_meta.status.value,
                        finalised_by=finaliser_id,
                        finalised_at=now_dt,
                    )
                    db.add(db_rev)
                else:
                    db_rev.status = new_meta.status.value
                    db_rev.finalised_by = finaliser_id
                    db_rev.finalised_at = now_dt

                # Ensure finalisation transition is committed to database
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error("Database finalization error: %s", e)
                from app.config import get_settings
                if get_settings().ENV in ("prod", "staging"):
                    raise RuntimeError(f"Database finalization error: {e}") from e
            finally:
                if should_close:
                    db.close()

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
        session: Session | None = None,
    ) -> ReviewMetadata:
        """Reopens a reviewed document back to draft for revisions."""
        doc = self._get_document(document_id, tenant_id, session)
        if not doc:
            raise KeyError(f"Document {document_id} not found.")

        current_meta = self.get_review_record(document_id, tenant_id, session) or ReviewMetadata(
            status=ReviewStatus(doc.status)
        )
        new_meta = reopen_to_draft(
            current_status=current_meta.status,
            reopened_by=actor_id,
        )

        db, should_close = self._get_db_session(session)
        if db is not None:
            try:
                from app.shared.models import Document as DocumentModel
                from app.shared.models import DocumentReview as DocumentReviewModel

                db_doc = (
                    db.query(DocumentModel)
                    .filter(
                        DocumentModel.id == document_id,
                        DocumentModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                if db_doc:
                    db_doc.status = new_meta.status.value

                db_rev = (
                    db.query(DocumentReviewModel)
                    .filter(
                        DocumentReviewModel.document_id == document_id,
                        DocumentReviewModel.tenant_id == tenant_id,
                    )
                    .with_for_update()
                    .first()
                )
                if db_rev:
                    db_rev.status = new_meta.status.value

                # Ensure reopen transition is committed to database
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error("Database reopen error: %s", e)
                from app.config import get_settings
                if get_settings().ENV in ("prod", "staging"):
                    raise RuntimeError(f"Database reopen error: {e}") from e
            finally:
                if should_close:
                    db.close()

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
