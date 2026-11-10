"""Unit tests for Document Review FSM and Service (PRD FR-10, Features F-058).

Verifies:
1. Review checklist enforcement (all 4 booleans required).
2. FSM transitions: draft -> reviewed -> finalised.
3. Immutability on finalisation (no edits or reopen).
4. Reopening from reviewed to draft.
5. AGENTS.md Hard Rule 7: no "valid" wording, mandatory bilingual disclaimers.
6. Tenant scoping and authorization enforcement.
"""

import uuid

import pytest

from app.generation.jobs import JobRecord
from app.generation.pipeline import generation_pipeline
from app.review.fsm import (
    DISCLAIMER_EN,
    DISCLAIMER_MR,
    DocumentFinalisedError,
    IncompleteChecklistError,
    InvalidReviewTransitionError,
    ReviewChecklist,
    ReviewMetadata,
    ReviewStatus,
    reopen_to_draft,
    transition_to_finalised,
    transition_to_reviewed,
)
from app.review.service import DocumentReviewService


@pytest.fixture
def clean_pipeline() -> None:
    generation_pipeline.clear()
    yield
    generation_pipeline.clear()


@pytest.fixture
def complete_checklist() -> ReviewChecklist:
    return ReviewChecklist(
        parties_verified=True,
        property_schedule_verified=True,
        consideration_and_payment_verified=True,
        no_unfilled_blanks=True,
        reviewer_notes="All revenue entries cross-checked with 7/12 extract.",
    )


def test_review_fsm_pure_transitions(complete_checklist: ReviewChecklist) -> None:
    """Tests state transitions at the pure FSM function layer."""
    # 1. draft -> reviewed
    meta_reviewed = transition_to_reviewed(
        current_status=ReviewStatus.DRAFT,
        checklist=complete_checklist,
        reviewer_id="advocate_user_1",
    )
    assert meta_reviewed.status == ReviewStatus.REVIEWED
    assert meta_reviewed.reviewed_by == "advocate_user_1"
    assert meta_reviewed.reviewed_at is not None
    assert meta_reviewed.disclaimer_en == DISCLAIMER_EN
    assert meta_reviewed.disclaimer_mr == DISCLAIMER_MR

    # 2. reviewed -> finalised
    meta_finalised = transition_to_finalised(
        current_status=meta_reviewed.status,
        finaliser_id="senior_advocate_1",
        existing_meta=meta_reviewed,
    )
    assert meta_finalised.status == ReviewStatus.FINALISED
    assert meta_finalised.finalised_by == "senior_advocate_1"
    assert meta_finalised.finalised_at is not None

    # 3. finalised -> cannot reopen or modify
    with pytest.raises(DocumentFinalisedError):
        reopen_to_draft(current_status=meta_finalised.status, reopened_by="user_2")

    with pytest.raises(DocumentFinalisedError):
        transition_to_reviewed(
            current_status=meta_finalised.status,
            checklist=complete_checklist,
            reviewer_id="user_2",
        )


def test_review_checklist_incomplete_rejection() -> None:
    """Verifies that unconfirmed checklist items strictly block review transition."""
    incomplete = ReviewChecklist(
        parties_verified=True,
        property_schedule_verified=False,  # Unverified schedule!
        consideration_and_payment_verified=True,
        no_unfilled_blanks=True,
    )
    assert incomplete.is_complete() is False

    with pytest.raises(IncompleteChecklistError):
        transition_to_reviewed(
            current_status=ReviewStatus.DRAFT,
            checklist=incomplete,
            reviewer_id="user_1",
        )


def test_cannot_skip_reviewed_to_finalised() -> None:
    """Verifies that a draft cannot jump directly to finalised without lawyer review."""
    with pytest.raises(InvalidReviewTransitionError):
        transition_to_finalised(
            current_status=ReviewStatus.DRAFT,
            finaliser_id="user_1",
        )


def test_reopen_reviewed_to_draft(complete_checklist: ReviewChecklist) -> None:
    """Verifies that a reviewed document can be safely reopened back to draft for edits."""
    meta_reviewed = transition_to_reviewed(
        current_status=ReviewStatus.DRAFT,
        checklist=complete_checklist,
        reviewer_id="user_1",
    )
    assert meta_reviewed.status == ReviewStatus.REVIEWED

    meta_reopened = reopen_to_draft(
        current_status=meta_reviewed.status,
        reopened_by="user_1",
    )
    assert meta_reopened.status == ReviewStatus.DRAFT
    assert meta_reopened.checklist is None


def test_document_review_service_integration(
    clean_pipeline: None,
    complete_checklist: ReviewChecklist,
) -> None:
    """Tests DocumentReviewService end-to-end with pipeline integration and tenant scoping."""
    service = DocumentReviewService(pipeline=generation_pipeline)
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    # Create dummy job payload
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_a,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "vendors": [
                {
                    "full_name": "Ramesh Rao",
                    "age": 45,
                    "address": "Nagpur",
                    "pan": "ABCDE1234F",
                    "aadhaar_last4": "1234",
                }
            ],
            "purchasers": [
                {
                    "full_name": "Suresh Deshmukh",
                    "age": 42,
                    "address": "Wardha",
                    "pan": "FGHIJ5678K",
                    "aadhaar_last4": "5678",
                }
            ],
            "property_details": {
                "plot_no": "42",
                "layout_name": "Shivaji Nagar",
                "mouza": "Babulkheda",
                "khasra_no": "11/2",
                "city_survey_no": "CTS-101",
                "area_sqm": "150.00",
                "boundaries": {
                    "east": "Road",
                    "west": "Plot 41",
                    "north": "Plot 30",
                    "south": "Plot 43",
                },
            },
            "financial_terms": {
                "total_consideration": "2500000",
                "advance_paid": "500000",
                "balance_amount": "2000000",
                "payment_mode": "RTGS",
            },
            "witnesses": [
                {"full_name": "Witness 1", "address": "Nagpur"},
                {"full_name": "Witness 2", "address": "Nagpur"},
            ],
        },
    )

    doc_record = generation_pipeline.process_job(job)
    assert doc_record.status == "draft"

    # Cross-tenant query MUST fail (return None)
    cross_tenant_record = service.get_review_record(doc_record.id, tenant_b)
    assert cross_tenant_record is None

    # Step 1: Mark as reviewed
    reviewed_meta = service.mark_reviewed(
        document_id=doc_record.id,
        tenant_id=tenant_a,
        checklist=complete_checklist,
        reviewer_id="reviewer_1",
    )
    assert reviewed_meta.status == ReviewStatus.REVIEWED
    assert doc_record.status == "reviewed"

    # Step 2: Finalise
    final_meta = service.mark_finalised(
        document_id=doc_record.id,
        tenant_id=tenant_a,
        finaliser_id="finaliser_1",
    )
    assert final_meta.status == ReviewStatus.FINALISED
    assert doc_record.status == "finalised"

    # Step 3: Attempt modification on finalised document must raise
    with pytest.raises(DocumentFinalisedError):
        service.reopen_for_edit(
            document_id=doc_record.id,
            tenant_id=tenant_a,
            actor_id="user_1",
        )


def test_rule_7_no_valid_claims_and_disclaimer_presence() -> None:
    """Verifies compliance with AGENTS.md Hard Rule 7."""
    valid_statuses = [s.value for s in ReviewStatus]
    assert "valid" not in valid_statuses
    assert "verified" not in valid_statuses
    assert "legally_approved" not in valid_statuses

    meta = ReviewMetadata()
    assert "does not constitute legal advice" in meta.disclaimer_en
    assert "कायदेशीर सल्ला नसून" in meta.disclaimer_mr
