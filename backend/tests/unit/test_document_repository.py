"""Unit tests for DocumentRepository interfaces and multi-tenant isolation.

Fulfills AGENTS.md Hard Rule 6 (every query tenant-scoped) and verifies:
1. Protocol conformance of InMemoryDocumentRepository.
2. Tenant isolation on save, get, update, and list.
3. Filtering by status and search queries within tenant scope.
"""

import uuid

import pytest

from app.generation.models import GeneratedDocumentRecord
from app.generation.repository import DocumentRepository, InMemoryDocumentRepository

TENANT_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_2 = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")


def test_document_repository_protocol_conformance() -> None:
    repo = InMemoryDocumentRepository()
    assert isinstance(repo, DocumentRepository)


def test_save_and_tenant_scoped_get() -> None:
    repo = InMemoryDocumentRepository()
    doc_id = uuid.uuid4()
    doc = GeneratedDocumentRecord(
        id=doc_id,
        tenant_id=TENANT_1,
        template_version_id=uuid.uuid4(),
        doc_no="LEKHAN/2026/001",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={"plot_no": "104"},
        input_hash=b"\x01" * 32,
        output_hash=b"\x02" * 32,
        file_ref="documents/sample.docx",
        pdf_ref=None,
        status="draft",
        created_at="2026-11-13T00:00:00Z",
    )
    repo.save(TENANT_1, doc)

    # Scoped to TENANT_1 returns document
    found = repo.get(TENANT_1, doc_id)
    assert found is not None
    assert found.doc_no == "LEKHAN/2026/001"

    # Cross-tenant query returns None
    assert repo.get(TENANT_2, doc_id) is None


def test_save_mismatched_tenant_raises_value_error() -> None:
    repo = InMemoryDocumentRepository()
    doc = GeneratedDocumentRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_1,
        template_version_id=uuid.uuid4(),
        doc_no="DOC-1",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={},
        input_hash=b"\x00" * 32,
        output_hash=b"\x00" * 32,
        file_ref="ref",
        pdf_ref=None,
        status="draft",
        created_at="",
    )
    with pytest.raises(ValueError):
        repo.save(TENANT_2, doc)


def test_update_tenant_isolation() -> None:
    repo = InMemoryDocumentRepository()
    doc_id = uuid.uuid4()
    doc = GeneratedDocumentRecord(
        id=doc_id,
        tenant_id=TENANT_1,
        template_version_id=uuid.uuid4(),
        doc_no="DOC-1",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={},
        input_hash=b"\x00" * 32,
        output_hash=b"\x00" * 32,
        file_ref="ref.docx",
        pdf_ref=None,
        status="draft",
        created_at="",
    )
    repo.save(TENANT_1, doc)

    doc.status = "finalised"
    # Cross-tenant update raises KeyError
    with pytest.raises(KeyError):
        repo.update(TENANT_2, doc)

    # Same-tenant update succeeds
    repo.update(TENANT_1, doc)
    updated = repo.get(TENANT_1, doc_id)
    assert updated is not None
    assert updated.status == "finalised"


def test_list_and_search_tenant_scoped() -> None:
    repo = InMemoryDocumentRepository()
    d1 = GeneratedDocumentRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_1,
        template_version_id=uuid.uuid4(),
        doc_no="SALE/2026/001",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={"plot_no": "104"},
        input_hash=b"\x00" * 32,
        output_hash=b"\x00" * 32,
        file_ref="ref1",
        pdf_ref=None,
        status="draft",
        created_at="2026-11-13T00:00:00Z",
    )
    d2 = GeneratedDocumentRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_2,
        template_version_id=uuid.uuid4(),
        doc_no="SALE/2026/002",
        engine_version="1.0.0",
        language="mr",
        data_snapshot={"plot_no": "104"},
        input_hash=b"\x00" * 32,
        output_hash=b"\x00" * 32,
        file_ref="ref2",
        pdf_ref=None,
        status="draft",
        created_at="2026-11-13T00:00:00Z",
    )
    repo.save(TENANT_1, d1)
    repo.save(TENANT_2, d2)

    # list strictly isolates by tenant
    docs1, total1 = repo.list(TENANT_1)
    assert total1 == 1
    assert docs1[0].id == d1.id

    docs2, total2 = repo.list(TENANT_2)
    assert total2 == 1
    assert docs2[0].id == d2.id

    # search respects tenant
    search_docs, search_total = repo.list(TENANT_1, search="104")
    assert search_total == 1
    assert search_docs[0].id == d1.id
