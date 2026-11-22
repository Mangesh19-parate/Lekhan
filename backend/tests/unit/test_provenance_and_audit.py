"""Tests for document cryptographic provenance, tamper detection, and signed audit trail."""

from __future__ import annotations

import io
import json
import uuid
import zipfile

import docx
import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_actor
from app.audit.export import create_signed_audit_export, verify_signed_audit_export
from app.audit.jobs import verify_all_audit_chains
from app.audit.repository import InMemoryAuditRepository
from app.audit.service import AuditService, audit_service
from app.config import get_settings
from app.generation.pipeline import generation_pipeline
from app.generation.provenance import (
    PROVENANCE_XML_PATH,
    extract_docx_provenance,
    stamp_docx_provenance,
    verify_docx_provenance,
)
from app.generation.repository import InMemoryDocumentRepository
from app.identity.policy import Actor
from app.main import app

settings = get_settings()


def _create_sample_docx(body_text: str = "This is an authentic draft deed.") -> bytes:
    doc = docx.Document()
    doc.add_heading("Sale Deed Draft", level=1)
    doc.add_paragraph(body_text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def reset_audit_and_documents() -> None:
    audit_service._repository = InMemoryAuditRepository()
    generation_pipeline.repository = InMemoryDocumentRepository()


def test_docx_provenance_stamping_and_invisibility() -> None:
    """Provenance is embedded in customXml/provenance.xml and invisible in visible text."""
    raw_docx = _create_sample_docx("Sample legal text without secret stamps.")
    doc_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    tv_id = uuid.uuid4()
    tmpl_sha = "abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    stamped_docx = stamp_docx_provenance(
        docx_bytes=raw_docx,
        document_id=doc_id,
        tenant_id=tenant_id,
        template_version_id=tv_id,
        template_sha256=tmpl_sha,
        engine_version="1.0.0",
    )

    # 1. Custom XML part must exist inside archive
    with zipfile.ZipFile(io.BytesIO(stamped_docx), "r") as zf:
        assert PROVENANCE_XML_PATH in zf.namelist()

    # 2. Extract record and verify all attributes
    prov = extract_docx_provenance(stamped_docx)
    assert prov is not None
    assert prov.document_id == str(doc_id)
    assert prov.tenant_id == str(tenant_id)
    assert prov.template_version_id == str(tv_id)
    assert prov.template_sha256 == tmpl_sha
    assert prov.engine_version == "1.0.0"
    assert len(prov.document_hash) == 64

    # 3. Invisibility check: python-docx must NOT see any provenance XML in paragraphs
    doc_opened = docx.Document(io.BytesIO(stamped_docx))
    full_text = " ".join([p.text for p in doc_opened.paragraphs])
    assert str(doc_id) not in full_text
    assert tmpl_sha not in full_text
    assert "provenance" not in full_text.lower()
    assert "Sample legal text without secret stamps." in full_text


def test_docx_provenance_verification_authentic_and_tampered() -> None:
    """Verifies that tampering with word/document.xml is instantly detected."""
    raw_docx = _create_sample_docx("Authentic consideration amount: Rs. 50,00,000/-")
    doc_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    tv_id = uuid.uuid4()
    tmpl_sha = "f00dbaba" * 8

    stamped_docx = stamp_docx_provenance(
        docx_bytes=raw_docx,
        document_id=doc_id,
        tenant_id=tenant_id,
        template_version_id=tv_id,
        template_sha256=tmpl_sha,
    )

    # Authentic check
    res_auth = verify_docx_provenance(stamped_docx)
    assert res_auth.valid is True
    assert res_auth.tampered is False
    assert res_auth.document_id == str(doc_id)
    assert res_auth.expected_document_hash == res_auth.actual_document_hash

    # Tamper with document body text inside word/document.xml
    in_zip = zipfile.ZipFile(io.BytesIO(stamped_docx), "r")
    files = {name: in_zip.read(name) for name in in_zip.namelist()}
    in_zip.close()

    tampered_doc_xml = files["word/document.xml"].replace(
        b"50,00,000", b"10,00,000"
    )
    assert tampered_doc_xml != files["word/document.xml"]
    files["word/document.xml"] = tampered_doc_xml

    tampered_buf = io.BytesIO()
    with zipfile.ZipFile(tampered_buf, "w") as out_zip:
        for fname, content in files.items():
            out_zip.writestr(fname, content)
    tampered_docx = tampered_buf.getvalue()

    # Tampered check
    res_tampered = verify_docx_provenance(tampered_docx)
    assert res_tampered.valid is False
    assert res_tampered.tampered is True
    assert res_tampered.expected_document_hash != res_tampered.actual_document_hash
    assert "Tamper alert" in res_tampered.message


def test_nightly_audit_chain_verification_job() -> None:
    """Nightly job verifies multi-tenant chains and triggers alerts if any chain is broken."""
    repo = InMemoryAuditRepository()
    t1 = uuid.uuid4()
    t2 = uuid.uuid4()

    # Tenant 1: clean chain
    svc1 = AuditService(repository=repo)
    svc1.log_event(tenant_id=t1, action="create_doc", entity="doc", entity_id="1")
    svc1.log_event(tenant_id=t1, action="download_doc", entity="doc", entity_id="1")

    # Tenant 2: clean chain
    svc1.log_event(tenant_id=t2, action="login", entity="user", entity_id="u1")
    svc1.log_event(tenant_id=t2, action="finalise", entity="doc", entity_id="d2")

    # Run check -> healthy
    report_healthy = verify_all_audit_chains(audit_repo=repo)
    assert report_healthy.status == "healthy"
    assert report_healthy.tenants_checked == 2
    assert len(report_healthy.broken_tenants) == 0

    # Tamper with Tenant 2's first record
    t2_records = repo._logs[t2]
    # Invalidate hash
    t2_records[0].hash = b"broken_hash_00000000000000000000"

    # Run check -> broken
    report_broken = verify_all_audit_chains(audit_repo=repo)
    assert report_broken.status == "broken"
    assert str(t2) in report_broken.broken_tenants
    assert str(t1) not in report_broken.broken_tenants


def test_signed_audit_export_and_tamper_detection() -> None:
    """Audit export generates HMAC-SHA256 signature and detects payload alterations."""
    repo = InMemoryAuditRepository()
    tid = uuid.uuid4()
    svc = AuditService(repository=repo)
    svc.log_event(tenant_id=tid, action="gen_doc", entity="doc", entity_id="101")
    svc.log_event(tenant_id=tid, action="review_doc", entity="doc", entity_id="101")

    records = repo.get_chain(tid)
    secret = "test-secret-key-for-signing-audits-32b"

    export_envelope = create_signed_audit_export(
        tenant_id=tid,
        records=records,
        chain_valid=True,
        secret_key=secret,
    )

    assert export_envelope["signature_algorithm"] == "HMAC-SHA256"
    assert len(export_envelope["signature"]) == 64
    assert export_envelope["payload"]["record_count"] == 2

    # Verification passes
    assert verify_signed_audit_export(export_envelope, secret) is True
    # Verification with wrong secret fails
    assert verify_signed_audit_export(export_envelope, "wrong-secret") is False

    # Tamper with an action in records
    tampered_export = json.loads(json.dumps(export_envelope))
    tampered_export["payload"]["records"][0]["action"] = "forged_action"
    assert verify_signed_audit_export(tampered_export, secret) is False


def test_api_document_verify_endpoints() -> None:
    """API endpoints POST /documents/verify and GET /documents/{id}/verify work seamlessly."""
    raw_docx = _create_sample_docx("Sample text for API verification.")
    doc_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    tv_id = uuid.uuid4()

    stamped_docx = stamp_docx_provenance(
        docx_bytes=raw_docx,
        document_id=doc_id,
        tenant_id=tenant_id,
        template_version_id=tv_id,
        template_sha256="12345" * 12,
    )

    actor = Actor(user_id=uuid.uuid4(), tenant_id=tenant_id, role="drafter")
    app.dependency_overrides[get_current_actor] = lambda: actor

    client = TestClient(app)
    try:
        # Test POST /api/v1/documents/verify with authentic DOCX
        resp_post = client.post(
            "/api/v1/documents/verify",
            files={"file": ("draft.docx", stamped_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp_post.status_code == 200
        data = resp_post.json()
        assert data["valid"] is True
        assert data["tampered"] is False
        assert data["document_id"] == str(doc_id)

        # Test POST /api/v1/documents/verify with tampered DOCX
        tampered_docx = stamped_docx.replace(b"Sample", b"Simple")
        resp_tampered = client.post(
            "/api/v1/documents/verify",
            files={"file": ("draft.docx", tampered_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp_tampered.status_code == 200
        data_tampered = resp_tampered.json()
        assert data_tampered["valid"] is False
        assert data_tampered["tampered"] is True
    finally:
        app.dependency_overrides.pop(get_current_actor, None)


def test_api_download_and_finalise_audit_logging() -> None:
    """Document downloads and finalisation log audit events to the audit trail."""
    from app.adapters.storage import default_storage
    from app.generation.models import GeneratedDocumentRecord
    from app.review.fsm import ReviewChecklist
    from app.review.service import document_review_service

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    # Save document in repository and storage
    storage_key = f"documents/{tenant_id}/{doc_id}.docx"
    docx_bytes = _create_sample_docx("Sample for download and finalise test")
    default_storage.put(storage_key, docx_bytes)

    doc_record = GeneratedDocumentRecord(
        id=doc_id,
        tenant_id=tenant_id,
        template_version_id=uuid.uuid4(),
        doc_no="DOC/2026/0001",
        engine_version="1.0.0",
        language="en",
        data_snapshot={},
        input_hash=b"0" * 32,
        output_hash=b"1" * 32,
        file_ref=storage_key,
        status="draft",
        created_at="2026-11-14T10:00:00Z",
    )
    generation_pipeline.repository.save(tenant_id, doc_record)

    actor = Actor(user_id=user_id, tenant_id=tenant_id, role="admin")
    app.dependency_overrides[get_current_actor] = lambda: actor
    client = TestClient(app)

    try:
        # 1. Download DOCX
        resp_docx = client.get(f"/api/v1/documents/{doc_id}/docx")
        assert resp_docx.status_code == 200

        # Check audit trail for download_document (docx)
        events = audit_service.get_chain(tenant_id)
        assert any(
            e.action == "download_document" and e.meta.get("format") == "docx"
            for e in events
        )

        # 2. Advance document to reviewed so it can be finalised
        checklist = ReviewChecklist(
            parties_identified=True,
            title_search_attached=True,
            consideration_matches=True,
            encumbrances_disclosed=True,
            statutory_notes_acknowledged=True,
        )
        document_review_service.mark_reviewed(doc_id, tenant_id, checklist, str(user_id))

        # 3. Finalise document via API
        resp_fin = client.post(f"/api/v1/documents/{doc_id}/finalise")
        assert resp_fin.status_code == 200

        # Check audit trail for finalise_document
        events = audit_service.get_chain(tenant_id)
        assert any(
            e.action == "finalise_document" and e.entity_id == str(doc_id)
            for e in events
        )
    finally:
        app.dependency_overrides.pop(get_current_actor, None)
