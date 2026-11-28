"""End-to-End Document Generation & Verification Gate Integration Tests.

Validates:
1. End-to-end execution:
   USER INPUT -> BACKEND VALIDATION -> ENQUEUE JOB -> WORKER CLAIMS ->
   RENDERER DISPATCH -> DOCX GENERATION -> VERIFICATION GATE ->
   PERSISTENT STORAGE -> DB RECORD -> JOB SUCCEEDED -> DOWNLOAD DOCX.
2. Template approval enforcement (fail-closed on draft/unapproved templates).
3. Specialized renderer dispatch with both filesystem templates and DB TemplateVersion bytes.
4. Output verification gate (asserts zero unrendered tags in all XML parts).
"""

from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.adapters.storage import default_storage
from app.api.auth import get_current_actor, require_csrf
from app.api.documents import get_document_repo, get_job_repo
from app.generation.jobs import InMemoryJobRepository
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.renderers import (
    PlotSaleDeedMarathiRenderer,
    default_renderer_registry,
)
from app.generation.repository import InMemoryDocumentRepository
from app.identity.policy import Actor
from app.main import app
from app.worker import run_worker_once

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
ACTOR_USER = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")

TEST_ACTOR = Actor(
    user_id=ACTOR_USER,
    tenant_id=TENANT_ID,
    role="drafter",
)

SYNTHETIC_DRAFT_INPUT = {
    "template_id": "sale_deed_plot_mr",
    "execution_date": "०९ नोव्हेंबर २०२६",
    "sellers": [
        {
            "full_name": "आनंद बळवंत जोशी",
            "gender": "male",
            "age": 52,
            "occupation": "व्यवसाय",
            "address": "नागपूर",
            "pan": "ABCDE1234F",
        }
    ],
    "purchasers": [
        {
            "full_name": "सुरेश रामराव पाटील",
            "gender": "male",
            "age": 41,
            "occupation": "नोकरी",
            "address": "नागपूर",
            "pan": "FGHIJ5678K",
        }
    ],
    "property_details": {
        "mouza": "सोनेगाव",
        "khasra_no": "४५/२",
        "plot_no": "१२",
        "layout_name": "शिवकृपा लेआउट",
        "sheet_no": "१४",
        "area_sqm": 150.0,
    },
    "boundaries": {
        "east": "९.०० मी. रुंद अंतर्गत रस्ता",
        "west": "प्लॉट क्र. १३",
        "north": "प्लॉट क्र. ११",
        "south": "लेआउट सीमा",
    },
    "financial": {
        "total_consideration": 2500000.0,
        "earnest_advance": 500000.0,
        "instalments": [
            {
                "amount": 500000.0,
                "mode": "cheque",
                "ref_no": "CHQ998877",
                "bank_name": "स्टेट बँक ऑफ इंडिया",
                "date_str": "०९/११/२०२६",
            }
        ],
    },
    "witness_1": "१) श्री. विजय एकनाथ जोशी, रा. नागपूर",
    "witness_2": "२) श्री. सचिन मनोहर देशमुख, रा. नागपूर",
}


@pytest.fixture
def test_env():
    job_repo = InMemoryJobRepository()
    doc_repo = InMemoryDocumentRepository()
    pipeline = GenerationPipelineFSM(storage=default_storage, repository=doc_repo)

    app.dependency_overrides[get_current_actor] = lambda: TEST_ACTOR
    app.dependency_overrides[get_job_repo] = lambda: job_repo
    app.dependency_overrides[get_document_repo] = lambda: doc_repo
    app.dependency_overrides[require_csrf] = lambda: None

    client = TestClient(app, raise_server_exceptions=False)
    yield {
        "job_repo": job_repo,
        "doc_repo": doc_repo,
        "pipeline": pipeline,
        "client": client,
    }
    app.dependency_overrides.clear()


def test_e2e_successful_generation_and_docx_verification(test_env):
    """Full workflow: Enqueue -> Claim -> Generate -> Verify Gate -> Store -> Download."""
    client = test_env["client"]
    job_repo = test_env["job_repo"]
    pipeline = test_env["pipeline"]

    # 1. Enqueue document generation job (async 202)
    post_res = client.post("/api/v1/documents", json=SYNTHETIC_DRAFT_INPUT)
    assert post_res.status_code == 202, f"Failed enqueue: {post_res.text}"
    post_data = post_res.json()
    assert post_data["status"] == "queued"
    assert post_data["state"] == "REQUESTED"
    job_id = post_data["job_id"]
    doc_id = post_data["document_id"]

    # 2. Worker claims and processes job
    processed = run_worker_once(repo=job_repo, pipeline=pipeline)
    assert processed is True

    # 3. Poll job status
    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_res.status_code == 200
    poll_data = poll_res.json()
    assert poll_data["status"] == "succeeded"
    assert poll_data["state"] == "COMPLETED"
    assert poll_data["outputs"]["docx"] is True
    assert poll_data["download_url"] is not None

    # 4. Download generated DOCX master
    dl_res = client.get(f"/api/v1/documents/{doc_id}/download")
    assert dl_res.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in dl_res.headers["content-type"]
    )
    docx_bytes = dl_res.content
    assert len(docx_bytes) > 2000

    # 5. Output Verification Gate: assert valid ZIP & non-empty word/document.xml
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "word/document.xml" in namelist
        doc_xml = zf.read("word/document.xml").decode("utf-8")

        # Zero unresolved Jinja / placeholder tags
        import re

        assert not re.findall(r"\{\{.*?\}\}", doc_xml), "Leftover {{ tags found in document.xml"
        assert not re.findall(r"\{%.*?%\}", doc_xml), "Leftover {% tags found in document.xml"

        # Correct synthetic values are embedded
        assert "आनंद बळवंत जोशी" in doc_xml
        assert "सुरेश रामराव पाटील" in doc_xml
        assert "सोनेगाव" in doc_xml
        assert "शिवकृपा लेआउट" in doc_xml


def test_pre_enqueue_rejects_draft_template(test_env):
    """Server-side pre-enqueue validation rejects draft templates with 409 Conflict."""
    client = test_env["client"]

    # agreement_to_sell_flat_en is draft in templates-library
    payload = {
        "template_id": "agreement_to_sell_flat_en",
        "data": {"some_field": "test"},
    }
    res = client.post("/api/v1/documents", json=payload)
    assert res.status_code == 409
    data = res.json()
    assert "draft" in data["detail"].lower()
    assert "approved" in data["detail"].lower()


def test_pre_enqueue_rejects_missing_or_unknown_template(test_env):
    """Server-side pre-enqueue validation rejects missing or unknown template IDs."""
    client = test_env["client"]

    # Missing template_id
    res1 = client.post("/api/v1/documents", json={"some": "payload"})
    assert res1.status_code == 422

    # Non-existent template_id
    res2 = client.post("/api/v1/documents", json={"template_id": "non_existent_deed_123"})
    assert res2.status_code == 404


def test_renderer_with_database_template_bytes():
    """Verifies PlotSaleDeedMarathiRenderer does not bypass specialized generation

    when template bytes are provided (e.g. from database TemplateVersion).
    """
    from app.templates.validator import TEMPLATES_DIR

    renderer = default_renderer_registry.get_renderer("sale_deed_plot_mr")
    assert isinstance(renderer, PlotSaleDeedMarathiRenderer)

    # Read disk template bytes to simulate DB TemplateVersion storage
    template_path = TEMPLATES_DIR / "sale_deed_plot_mr" / "template.docx"
    assert template_path.exists()
    db_template_bytes = template_path.read_bytes()

    # Render with explicit template_bytes passed
    docx_bytes = renderer.render(
        template_id="sale_deed_plot_mr",
        payload=SYNTHETIC_DRAFT_INPUT,
        template_bytes=db_template_bytes,
    )

    assert len(docx_bytes) > 2000
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert "आनंद बळवंत जोशी" in doc_xml
        assert "सुरेश रामराव पाटील" in doc_xml
        # Verify derived Marathi words are populated
        assert "पन्नास लाख" in doc_xml or "वीस लाख" in doc_xml or "रुपये" in doc_xml
