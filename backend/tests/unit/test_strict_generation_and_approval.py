"""Unit tests for Step 5: Strict rendering, no invented defaults, and template approval enforcement."""

import uuid

import pytest

from app.generation.jobs import JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.repository import InMemoryDocumentRepository

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000000")

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


def test_missing_boundaries_raises_error():
    """Missing boundaries must raise ValueError; cannot invent defaults."""
    payload = dict(VALID_PAYLOAD)
    del payload["boundaries"]

    fsm = GenerationPipelineFSM(repository=InMemoryDocumentRepository())
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        job_type="generate_docx",
        payload=payload,
        status="running",
    )
    with pytest.raises(ValueError, match="boundaries"):
        fsm.process_job(job)


def test_missing_consideration_raises_error():
    """Missing total_consideration must raise ValueError; cannot invent defaults."""
    payload = dict(VALID_PAYLOAD)
    payload["financial"] = {"earnest_advance": 200000.00}

    fsm = GenerationPipelineFSM(repository=InMemoryDocumentRepository())
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        job_type="generate_docx",
        payload=payload,
        status="running",
    )
    with pytest.raises(ValueError, match="total_consideration"):
        fsm.process_job(job)


def test_missing_template_id_raises_error():
    """Missing template_id must fail; cannot default to sale_deed_plot_mr implicitly."""
    payload = dict(VALID_PAYLOAD)
    del payload["template_id"]

    fsm = GenerationPipelineFSM(repository=InMemoryDocumentRepository())
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        job_type="generate_docx",
        payload=payload,
        status="running",
    )
    with pytest.raises(ValueError, match="template_id"):
        fsm.process_job(job)


def test_draft_template_rejected():
    """Unapproved/draft templates must be rejected at generation gate."""
    payload = dict(VALID_PAYLOAD)
    # agreement_to_sell_flat_en is a draft template
    payload["template_id"] = "agreement_to_sell_flat_en"

    fsm = GenerationPipelineFSM(repository=InMemoryDocumentRepository())
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        job_type="generate_docx",
        payload=payload,
        status="running",
    )
    with pytest.raises(ValueError, match="approved"):
        fsm.process_job(job)


def test_approved_template_succeeds():
    """Approved template (sale_deed_plot_mr) with full valid payload succeeds."""
    fsm = GenerationPipelineFSM(repository=InMemoryDocumentRepository())
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        job_type="generate_docx",
        payload=VALID_PAYLOAD,
        status="running",
    )
    doc = fsm.process_job(job)
    assert doc is not None
    assert doc.doc_no is not None
    assert doc.status == "draft"
