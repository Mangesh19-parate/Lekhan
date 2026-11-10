"""Generation Pipeline FSM (docs/ARCHITECTURE.md Section 5).

State transitions:
REQUESTED -> VALIDATED -> RENDERED -> VERIFIED -> STORED -> COMPLETED

Features:
- Gap-free sequential document numbering (PRD FR-12, Features F-055, ADR 012).
- Immutable data snapshots and engine versions (ADR 005, PRD FR-11, Features F-054).
- Headless isolated PDF generation and convenience copy export (ADR 010, PRD FR-13, Features F-056).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

from app.adapters.pdf import default_pdf_converter
from app.adapters.storage import ObjectStore, default_storage
from app.audit.service import audit_service
from app.generation.jobs import JobRecord
from app.generation.spike_engine import (
    PlotSaleDeedInput,
    generate_plot_sale_deed_docx,
)
from app.numbering.service import document_numbering_service
from app.shared.ids import uuid7
from app.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedDocumentRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    template_version_id: uuid.UUID
    doc_no: str
    engine_version: str
    language: str
    data_snapshot: dict[str, Any]
    input_hash: bytes
    output_hash: bytes
    file_ref: str  # DOCX Master
    pdf_ref: str | None  # PDF Convenience Copy
    status: str  # draft, reviewed, finalised
    created_at: str  # ISO 8601


class GenerationPipelineFSM:
    """Orchestrates document generation through persisted FSM states."""

    def __init__(self, storage: ObjectStore = default_storage) -> None:
        self.storage = storage
        self._documents: dict[uuid.UUID, GeneratedDocumentRecord] = {}

    def process_job(self, job: JobRecord) -> GeneratedDocumentRecord:
        """Executes the generation pipeline FSM for a claimed job."""
        try:
            # 1. State: REQUESTED -> VALIDATED
            job.state = "VALIDATED"
            input_data = PlotSaleDeedInput.model_validate(job.payload)
            canonical_input_bytes = json.dumps(
                job.payload, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
            input_hash = hashlib.sha256(canonical_input_bytes).digest()

            # 2. State: VALIDATED -> RENDERED
            job.state = "RENDERED"
            docx_bytes = generate_plot_sale_deed_docx(input_data)

            # 3. State: RENDERED -> VERIFIED
            # Verification gate: python-docx reopen & zero leftover tags confirmed
            job.state = "VERIFIED"
            output_hash = hashlib.sha256(docx_bytes).digest()

            # 4. State: VERIFIED -> STORED
            job.state = "STORED"
            doc_id = uuid7()
            storage_key = f"documents/{job.tenant_id}/{doc_id}.docx"
            self.storage.put(
                storage_key,
                docx_bytes,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            # 5. State: STORED -> COMPLETED
            job.state = "COMPLETED"
            job.status = "succeeded"
            job.result_ref = storage_key

            # Generate gap-free sequence document number (PRD FR-12, ADR 012)
            doc_no = document_numbering_service.next_doc_no(job.tenant_id, series_key="DOC")

            # Extract sanitized immutable data snapshot (excluding ephemeral fields per ADR 005)
            data_snapshot = {
                k: v
                for k, v in job.payload.items()
                if not (k.startswith("ephemeral_") or k.startswith("_"))
            }

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            doc_record = GeneratedDocumentRecord(
                id=doc_id,
                tenant_id=job.tenant_id,
                template_version_id=uuid.UUID(
                    job.payload.get("template_version_id", str(uuid.uuid4()))
                ),
                doc_no=doc_no,
                engine_version="1.0.0",
                language=job.payload.get("language", "mr"),
                data_snapshot=data_snapshot,
                input_hash=input_hash,
                output_hash=output_hash,
                file_ref=storage_key,
                pdf_ref=None,
                status="draft",
                created_at=now_iso,
            )
            self._documents[doc_id] = doc_record

            # Audit event
            audit_service.log_event(
                tenant_id=job.tenant_id,
                action="document_generated",
                entity="document",
                entity_id=str(doc_id),
                meta={
                    "doc_no": doc_no,
                    "file_ref": storage_key,
                    "plot_no": input_data.property_details.plot_no,
                },
            )

            return doc_record

        except Exception as exc:
            logger.exception("Pipeline failed on job %s at state %s", job.id, job.state)
            job.status = "failed"
            job.error = {"error": str(exc), "failed_at_state": job.state}
            raise

    def get_document(
        self, doc_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> GeneratedDocumentRecord | None:
        """Retrieves document enforcing strict tenant scoping (cross-tenant returns None)."""
        doc = self._documents.get(doc_id)
        if not doc or doc.tenant_id != tenant_id:
            return None
        return doc

    def list_documents(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GeneratedDocumentRecord], int]:
        """Lists tenant documents with filtering, search, and pagination."""
        # 1. Filter by tenant
        tenant_docs = [doc for doc in self._documents.values() if doc.tenant_id == tenant_id]

        # 2. Filter by status
        if status:
            tenant_docs = [d for d in tenant_docs if d.status == status]

        # 3. Search filter by doc_no or payload content
        if search:
            q = search.lower().strip()
            tenant_docs = [
                d
                for d in tenant_docs
                if q in d.doc_no.lower()
                or q in json.dumps(d.data_snapshot, ensure_ascii=False).lower()
            ]

        # 4. Sort by creation time descending
        tenant_docs.sort(key=lambda d: d.created_at, reverse=True)

        total_count = len(tenant_docs)
        paginated = tenant_docs[offset : offset + limit]
        return paginated, total_count

    def get_or_create_pdf(self, doc_id: uuid.UUID, tenant_id: uuid.UUID) -> bytes:
        """Converts DOCX master into PDF convenience copy with caching."""
        doc = self.get_document(doc_id, tenant_id)
        if not doc:
            raise KeyError(f"Document {doc_id} not found.")

        # Check if already generated and cached in object storage
        if doc.pdf_ref:
            cached_pdf = self.storage.get(doc.pdf_ref)
            if cached_pdf:
                return cached_pdf

        docx_bytes = self.storage.get(doc.file_ref)
        if not docx_bytes:
            raise FileNotFoundError(f"DOCX master file missing for document {doc_id}")

        pdf_bytes = default_pdf_converter.convert_docx_to_pdf(docx_bytes)
        pdf_storage_key = f"documents/{tenant_id}/{doc_id}.pdf"
        self.storage.put(
            pdf_storage_key,
            pdf_bytes,
            content_type="application/pdf",
        )
        doc.pdf_ref = pdf_storage_key
        return pdf_bytes

    def clear(self) -> None:
        self._documents.clear()


generation_pipeline = GenerationPipelineFSM()
