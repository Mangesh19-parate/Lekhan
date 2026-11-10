"""Unit tests for background jobs queue and generation pipeline FSM v0."""

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.adapters.storage import LocalObjectStore, default_storage
from app.generation.jobs import job_queue
from app.generation.pipeline import generation_pipeline
from app.main import app

client = TestClient(app)

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000000")


@pytest.fixture(autouse=True)
def clean_state():
    job_queue.clear()
    generation_pipeline.clear()


SAMPLE_PAYLOAD = {
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


def test_job_idempotency_deduplication() -> None:
    """Submitting with identical Idempotency-Key returns existing job."""
    key = "IDEM-TEST-12345"
    job1 = job_queue.enqueue(TENANT_ID, "generate_docx", SAMPLE_PAYLOAD, idempotency_key=key)
    job2 = job_queue.enqueue(TENANT_ID, "generate_docx", SAMPLE_PAYLOAD, idempotency_key=key)

    assert job1.id == job2.id
    assert job1.idempotency_key == key


def test_generation_pipeline_fsm_transitions() -> None:
    """Verifies FSM: REQUESTED -> VALIDATED -> RENDERED -> VERIFIED -> STORED -> COMPLETED."""
    job = job_queue.enqueue(TENANT_ID, "generate_docx", SAMPLE_PAYLOAD)
    assert job.state == "REQUESTED"
    assert job.status == "queued"

    # Claim and execute
    claimed = job_queue.claim_next_job()
    assert claimed is not None
    assert claimed.status == "running"

    doc = generation_pipeline.process_job(claimed)

    assert claimed.status == "succeeded"
    assert claimed.state == "COMPLETED"
    assert doc.file_ref.endswith(".docx")
    assert default_storage.exists(doc.file_ref) is True


def test_api_document_creation_and_download() -> None:
    """Milestone test: Generates document via API and downloads resulting DOCX."""
    # 1. Login as drafter to obtain session cookie
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "drafter@lekhan.local", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 200
    cookie_val = login_res.cookies["lekhan_session"]

    # 2. Enqueue and generate document
    gen_res = client.post(
        "/api/v1/documents",
        json=SAMPLE_PAYLOAD,
        cookies={"lekhan_session": cookie_val},
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["status"] == "succeeded"
    assert gen_data["state"] == "COMPLETED"
    assert "download_url" in gen_data

    # 3. Download resulting DOCX
    download_url = gen_data["download_url"]
    dl_res = client.get(download_url, cookies={"lekhan_session": cookie_val})
    assert dl_res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in dl_res.headers["content-type"]
    assert len(dl_res.content) > 1000

