"""Document Review FSM and Checklist Engine (PRD FR-10, Features F-058).

States:
- DRAFT ("draft"): Initial generated state.
- REVIEWED ("reviewed"): Checked against statutory checklist.
- FINALISED ("finalised"): Immutable permanent snapshot.

Hard Rules:
- AGENTS.md Rule 7: Never claim a document is "valid", "verified" or "legally approved".
  Use "Draft", "Reviewed", "Finalised".
- Disclaimers are attached to every review representation.
"""

from __future__ import annotations

import datetime
from enum import Enum

from pydantic import BaseModel, Field

DISCLAIMER_EN = (
    "Notice: Lekhan is a drafting assistant for legal professionals. "
    "This draft does not constitute legal advice and must be independently reviewed by an advocate."
)

DISCLAIMER_MR = (
    "सूचना: लेखन हे विधी व्यावसायिकांसाठी मसुदा साहाय्यक आहे. "
    "हा मसुदा कायदेशीर सल्ला नसून वकिलांनी स्वतः तपासून अंतिम करणे आवश्यक आहे."
)


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    FINALISED = "finalised"


class ReviewChecklist(BaseModel):
    """Mandatory verification checklist before marking a document as Reviewed."""

    parties_verified: bool = Field(
        ...,
        description="Names, ages, addresses, and legal capacities verified against official IDs",
    )
    property_schedule_verified: bool = Field(
        ...,
        description="Property survey / CTS / Gat / Khasra number, area, and boundaries verified against revenue record",
    )
    consideration_and_payment_verified: bool = Field(
        ...,
        description="Total consideration, earnest token, and payment instrument numbers confirmed",
    )
    no_unfilled_blanks: bool = Field(
        ...,
        description="Confirmed zero missing fields, unreplaced placeholders, or bracketed blanks",
    )
    reviewer_notes: str | None = Field(
        default=None,
        description="Optional advocate / reviewer notes and observations",
    )

    def is_complete(self) -> bool:
        """All checklist items must be affirmatively confirmed."""
        return (
            self.parties_verified is True
            and self.property_schedule_verified is True
            and self.consideration_and_payment_verified is True
            and self.no_unfilled_blanks is True
        )


class ReviewMetadata(BaseModel):
    """Review metadata record attached to a generated document."""

    status: ReviewStatus = ReviewStatus.DRAFT
    checklist: ReviewChecklist | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    finalised_by: str | None = None
    finalised_at: str | None = None
    disclaimer_en: str = DISCLAIMER_EN
    disclaimer_mr: str = DISCLAIMER_MR


class ReviewError(Exception):
    """Base exception for review workflow failures."""


class InvalidReviewTransitionError(ReviewError):
    """Raised when an illegal transition is attempted."""


class IncompleteChecklistError(ReviewError):
    """Raised when marking as reviewed without completing all checklist items."""


class DocumentFinalisedError(ReviewError):
    """Raised when attempting to modify or reopen an immutable finalised document."""


def transition_to_reviewed(
    current_status: ReviewStatus,
    checklist: ReviewChecklist,
    reviewer_id: str,
) -> ReviewMetadata:
    """Transitions a document from DRAFT to REVIEWED."""
    if current_status == ReviewStatus.FINALISED:
        raise DocumentFinalisedError("Finalised documents are immutable and cannot be re-reviewed.")
    if current_status != ReviewStatus.DRAFT:
        raise InvalidReviewTransitionError(
            f"Cannot review document currently in status '{current_status.value}'."
        )

    if not checklist.is_complete():
        raise IncompleteChecklistError(
            "All checklist items must be verified before marking document as reviewed."
        )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return ReviewMetadata(
        status=ReviewStatus.REVIEWED,
        checklist=checklist,
        reviewed_by=reviewer_id,
        reviewed_at=now_iso,
    )


def transition_to_finalised(
    current_status: ReviewStatus,
    finaliser_id: str,
    existing_meta: ReviewMetadata | None = None,
) -> ReviewMetadata:
    """Transitions a document from REVIEWED to FINALISED (permanent lock)."""
    if current_status == ReviewStatus.FINALISED:
        raise DocumentFinalisedError("Document is already finalised and locked.")
    if current_status != ReviewStatus.REVIEWED:
        raise InvalidReviewTransitionError(
            f"Document must be in 'reviewed' status before finalisation; current status is '{current_status.value}'."
        )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta = existing_meta.model_copy() if existing_meta else ReviewMetadata()
    meta.status = ReviewStatus.FINALISED
    meta.finalised_by = finaliser_id
    meta.finalised_at = now_iso
    return meta


def reopen_to_draft(
    current_status: ReviewStatus,
    reopened_by: str,
) -> ReviewMetadata:
    """Transitions a REVIEWED document back to DRAFT for corrections."""
    if current_status == ReviewStatus.FINALISED:
        raise DocumentFinalisedError("Finalised documents are immutable and cannot be re-opened.")
    if current_status == ReviewStatus.DRAFT:
        raise InvalidReviewTransitionError("Document is already in draft status.")

    return ReviewMetadata(
        status=ReviewStatus.DRAFT,
        checklist=None,
        reviewed_by=None,
        reviewed_at=None,
    )
