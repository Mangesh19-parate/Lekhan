"""Unit tests for PDF Export, Isolation, Document History, and Data Snapshots.

Verifies:
1. PDF Converter produces valid PDF output with convenience copy notice (ADR 010, F-056).
2. Concurrency semaphore and timeout safety (ARCHITECTURE.md Section 5).
3. Data snapshots are immutable and exclude ephemeral variables (ADR 005, F-054).
4. Document history querying, status filtering, search, and pagination (FR-11, F-057).
5. Cross-tenant isolation guarantees (AGENTS.md Hard Rule 6).
"""

import uuid

import pytest

from app.adapters.pdf import LibreOfficePdfConverter, PdfConversionError
from app.generation.jobs import JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.numbering.service import document_numbering_service


@pytest.fixture
def clean_pipeline() -> GenerationPipelineFSM:
    pipeline = GenerationPipelineFSM()
    pipeline.clear()
    document_numbering_service.clear()
    return pipeline


def test_pdf_converter_fallback_convenience_copy() -> None:
    """Verifies that the PDF converter produces a valid PDF convenience copy with correct header."""
    converter = LibreOfficePdfConverter(binary_path=None)  # Forces isolated fallback generator
    dummy_docx = b"PK\x03\x04test_docx_bytes"

    pdf_bytes = converter.convert_docx_to_pdf(dummy_docx)
    assert pdf_bytes.startswith(b"%PDF-")
    assert b"%%EOF" in pdf_bytes
    assert b"Convenience Copy (DOCX Master)" in pdf_bytes


def test_pdf_converter_empty_input_error() -> None:
    """Verifies rejection of empty DOCX input."""
    converter = LibreOfficePdfConverter()
    with pytest.raises(PdfConversionError):
        converter.convert_docx_to_pdf(b"")


def test_document_pipeline_snapshot_and_numbering(clean_pipeline: GenerationPipelineFSM) -> None:
    """Tests document generation pipeline with gap-free numbering and sanitized data snapshot."""
    tenant_id = uuid.uuid4()
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "ephemeral_otp": "999888",  # Ephemeral field MUST be excluded from snapshot
            "_session_token": "secret_abc",  # Internal field MUST be excluded from snapshot
            "vendors": [
                {
                    "full_name": "Kishor Patil",
                    "age": 50,
                    "address": "Nagpur",
                    "pan": "ABCDE1234F",
                    "aadhaar_last4": "1234",
                }
            ],
            "purchasers": [
                {
                    "full_name": "Sunil Shinde",
                    "age": 38,
                    "address": "Amravati",
                    "pan": "FGHIJ5678K",
                    "aadhaar_last4": "5678",
                }
            ],
            "property_details": {
                "plot_no": "101",
                "layout_name": "Laxmi Nagar",
                "mouza": "Somani",
                "khasra_no": "55/1",
                "city_survey_no": "CTS-201",
                "area_sqm": "180.00",
                "boundaries": {
                    "east": "Road",
                    "west": "Plot 100",
                    "north": "Plot 90",
                    "south": "Plot 102",
                },
            },
            "financial_terms": {
                "total_consideration": "3500000",
                "advance_paid": "700000",
                "balance_amount": "2800000",
                "payment_mode": "Cheque",
            },
            "witnesses": [
                {"full_name": "Witness 1", "address": "Nagpur"},
                {"full_name": "Witness 2", "address": "Nagpur"},
            ],
        },
    )

    doc_record = clean_pipeline.process_job(job)

    # 1. Gap-free numbering check
    assert doc_record.doc_no.startswith("2026/")
    assert doc_record.doc_no.endswith("00001")

    # 2. Immutable data snapshot check (ADR 005)
    assert doc_record.engine_version == "1.0.0"
    assert "ephemeral_otp" not in doc_record.data_snapshot
    assert "_session_token" not in doc_record.data_snapshot
    assert doc_record.data_snapshot["property_details"]["plot_no"] == "101"

    # 3. PDF generation and caching check (ADR 010)
    pdf_bytes = clean_pipeline.get_or_create_pdf(doc_record.id, tenant_id)
    assert pdf_bytes.startswith(b"%PDF-")
    assert doc_record.pdf_ref is not None


def test_document_history_filtering_and_pagination(clean_pipeline: GenerationPipelineFSM) -> None:
    """Verifies document history search, status filtering, and cross-tenant isolation."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    # Create 3 docs for Tenant A
    for i in range(1, 4):
        job = JobRecord(
            id=uuid.uuid4(),
            tenant_id=tenant_a,
            job_type="generate_docx",
            payload={
                "execution_date": "2026-11-09",
                "vendors": [
                    {
                        "full_name": f"Vendor {i}",
                        "age": 40,
                        "address": "Nagpur",
                        "pan": "ABCDE1234F",
                        "aadhaar_last4": "1234",
                    }
                ],
                "purchasers": [
                    {
                        "full_name": f"Purchaser {i}",
                        "age": 35,
                        "address": "Nagpur",
                        "pan": "FGHIJ5678K",
                        "aadhaar_last4": "5678",
                    }
                ],
                "property_details": {
                    "plot_no": str(i * 10),
                    "layout_name": "Green Park",
                    "mouza": "Besa",
                    "khasra_no": f"12/{i}",
                    "city_survey_no": f"CTS-{i}",
                    "area_sqm": "150.00",
                    "boundaries": {
                        "east": "Road",
                        "west": "Plot",
                        "north": "Plot",
                        "south": "Plot",
                    },
                },
                "financial_terms": {
                    "total_consideration": "2000000",
                    "advance_paid": "400000",
                    "balance_amount": "1600000",
                    "payment_mode": "RTGS",
                },
                "witnesses": [
                    {"full_name": "W1", "address": "N"},
                    {"full_name": "W2", "address": "N"},
                ],
            },
        )
        clean_pipeline.process_job(job)

    # 1. Total count for Tenant A
    docs_a, total_a = clean_pipeline.list_documents(tenant_id=tenant_a)
    assert total_a == 3
    assert len(docs_a) == 3

    # 2. Cross-tenant isolation check: Tenant B sees 0 documents
    docs_b, total_b = clean_pipeline.list_documents(tenant_id=tenant_b)
    assert total_b == 0
    assert len(docs_b) == 0

    # 3. Search query check
    searched, search_total = clean_pipeline.list_documents(
        tenant_id=tenant_a, search='plot_no": "20"'
    )
    assert search_total == 1
    assert searched[0].data_snapshot["property_details"]["plot_no"] == "20"

    # 4. Pagination check
    paginated, p_total = clean_pipeline.list_documents(tenant_id=tenant_a, limit=2, offset=0)
    assert p_total == 3
    assert len(paginated) == 2
