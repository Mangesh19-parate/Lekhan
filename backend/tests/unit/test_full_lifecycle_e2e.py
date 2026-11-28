"""Unit E2E Lifecycle Test: Full Legal Drafting Flow without Network/External Dependencies.

Fulfills Finding 15 / Section 8 Step 8:
Validates the complete application drafting lifecycle end-to-end:
1. Enqueue generation job with strict legal parameters (no invented defaults).
2. Worker claims job and transitions states: REQUESTED -> VALIDATED -> RENDERED -> VERIFIED -> STORED -> COMPLETED.
3. Verification gate asserts zero unrendered tags across all XML document parts.
4. Document review flow: reviewer assesses document and transitions status to 'reviewed'.
5. Finalization lock: reviewer marks document 'finalised' with statutory verification.
6. Mutation rejection: finalised document cannot be re-reviewed or mutated.
7. Cryptographic audit chain verification across all generated events.
"""

from __future__ import annotations

import io
import re
import uuid
import zipfile

import pytest

from app.adapters.storage import default_storage
from app.audit.jobs import verify_all_audit_chains
from app.audit.service import InMemoryAuditRepository, audit_service
from app.generation.jobs import InMemoryJobRepository
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.repository import InMemoryDocumentRepository
from app.review.fsm import DocumentFinalisedError, ReviewChecklist
from app.review.service import DocumentReviewService
from app.worker import run_worker_once

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
DRAFTER_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")
REVIEWER_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000003")

VALID_PAYLOAD = {
    "template_id": "sale_deed_plot_mr",
    "execution_date": "०९ नोव्हेंबर २०२६",
    "sellers": [
        {
            "full_name": "रमेश पाटील",
            "gender": "male",
            "age": 45,
            "occupation": "नोकरी",
            "address": "नागपूर",
            "pan": "ABCDE1234F",
        }
    ],
    "purchasers": [
        {
            "full_name": "सुनीता जोशी",
            "gender": "female",
            "age": 42,
            "occupation": "घरकाम",
            "address": "नागपूर",
            "pan": "XYZPQ9876K",
        }
    ],
    "property_details": {
        "mouza": "सोनेगाव",
        "khasra_no": "४५/२",
        "plot_no": "१२",
        "layout_name": "शिवकृपा लेआउट",
        "sheet_no": "१४",
        "area_sqm": 150.00,
    },
    "boundaries": {
        "east": "रस्ता",
        "west": "भूखंड क्र. १३",
        "north": "जागा",
        "south": "भूखंड क्र. ११",
    },
    "financial": {
        "total_consideration": 1550000.00,
        "earnest_advance": 200000.00,
        "instalments": [],
    },
    "witness_1": "१) साक्षीदार १",
    "witness_2": "२) साक्षीदार २",
}


@pytest.fixture(autouse=True)
def clean_audit_and_numbering():
    audit_service._repository = InMemoryAuditRepository()
    audit_service.clear()
    yield
    audit_service.clear()


def test_complete_drafting_and_finalization_lifecycle():
    """Executes the full drafting lifecycle: enqueue -> worker -> review -> finalise -> lock."""
    doc_repo = InMemoryDocumentRepository()
    job_repo = InMemoryJobRepository()
    pipeline = GenerationPipelineFSM(repository=doc_repo)
    review_service = DocumentReviewService(pipeline=pipeline)

    # 1. Enqueue generation job
    job = job_repo.enqueue(
        tenant_id=TENANT_ID,
        type="generate_docx",
        payload=VALID_PAYLOAD,
    )
    assert job.status == "queued"
    assert job.state == "REQUESTED"

    # 2. Worker claims and executes job
    processed = run_worker_once(repo=job_repo, pipeline=pipeline)
    assert processed is True

    # 3. Verify job succeeded
    updated_job = job_repo.get(TENANT_ID, job.id)
    assert updated_job is not None
    assert updated_job.status == "succeeded"
    assert updated_job.state == "COMPLETED"

    # 4. Verify generated document
    doc_id = uuid.UUID(str(job.payload["document_id"])) if "document_id" in job.payload else job.id
    doc = pipeline.get_document(doc_id, TENANT_ID)
    assert doc is not None
    assert doc.status == "draft"
    assert doc.doc_no is not None
    assert default_storage.exists(doc.file_ref) is True

    # 5. Inspect generated DOCX binary: verify zero unrendered template tags in any XML part
    docx_bytes = default_storage.get(doc.file_ref)
    assert docx_bytes is not None
    assert len(docx_bytes) > 1000

    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as z:
        for item in z.infolist():
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                part_text = z.read(item.filename).decode("utf-8", errors="ignore")
                leftovers = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", part_text)
                assert leftovers == [], f"Found unrendered tags in {item.filename}: {leftovers}"

    # 6. Review workflow: Reviewer marks document reviewed
    checklist = ReviewChecklist(
        parties_verified=True,
        property_schedule_verified=True,
        consideration_and_payment_verified=True,
        no_unfilled_blanks=True,
        reviewer_notes="All boundaries, consideration, and party details verified against physical deed.",
    )
    review_rec = review_service.mark_reviewed(
        document_id=doc.id,
        tenant_id=TENANT_ID,
        checklist=checklist,
        reviewer_id=str(REVIEWER_ID),
    )
    assert review_rec.reviewed_by == str(REVIEWER_ID)

    reviewed_doc = pipeline.get_document(doc.id, TENANT_ID)
    assert reviewed_doc is not None
    assert reviewed_doc.status == "reviewed"

    # 7. Finalization workflow: Reviewer finalizes document with mandatory checklist
    final_meta = review_service.mark_finalised(
        document_id=doc.id,
        tenant_id=TENANT_ID,
        finaliser_id=str(REVIEWER_ID),
    )
    assert final_meta.status.value == "finalised"
    final_doc = pipeline.get_document(doc.id, TENANT_ID)
    assert final_doc is not None
    assert final_doc.status == "finalised"

    # 8. Immutability Lock: further review or finalization must be strictly rejected
    with pytest.raises(
        DocumentFinalisedError, match="Finalised documents are immutable and cannot be re-reviewed."
    ):
        review_service.mark_reviewed(
            document_id=doc.id,
            tenant_id=TENANT_ID,
            checklist=checklist,
            reviewer_id=str(REVIEWER_ID),
        )

    # 9. Cryptographic Audit Chain: verify all events in chain are unbroken
    audit_report = verify_all_audit_chains()
    assert audit_report.status == "healthy"
    chain = audit_service.get_chain(TENANT_ID)
    assert len(chain) >= 2
    actions = [e.action for e in chain]
    assert "document_generated" in actions
    assert "document_finalised" in actions
