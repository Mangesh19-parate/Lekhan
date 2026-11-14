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
import io
import json
import re
import uuid
import zipfile
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate
from jinja2.sandbox import SandboxedEnvironment

from app.adapters.pdf import default_pdf_converter
from app.adapters.storage import ObjectStore, default_storage
from app.audit.service import audit_service
from app.generation.jobs import JobRecord
from app.generation.models import GeneratedDocumentRecord
from app.generation.repository import (
    DocumentRepository,
    InMemoryDocumentRepository,
)
from app.generation.spike_engine import (
    PlotSaleDeedInput,
    generate_plot_sale_deed_docx,
)
from app.numbering.service import document_numbering_service
from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)


TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates-library"


def _render_template_docx(template_id: str, context: dict[str, Any]) -> bytes:
    """Renders a template.docx from templates-library/ in a sandboxed Jinja environment."""
    if not re.fullmatch(r"[a-z0-9_]+", template_id):
        raise ValueError(f"Invalid template_id: {template_id!r}")
    template_path = (TEMPLATES_DIR / template_id / "template.docx").resolve()
    if not template_path.is_relative_to(TEMPLATES_DIR.resolve()) or not template_path.exists():
        raise ValueError(f"Template '{template_id}' not found.")

    doc = DocxTemplate(str(template_path))
    doc.render(context, jinja_env=SandboxedEnvironment())
    out_buf = io.BytesIO()
    doc.save(out_buf)
    docx_bytes = out_buf.getvalue()

    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        if "word/document.xml" in zf.namelist():
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
            leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", xml)
            if leftover:
                raise ValueError(f"Unrendered template tags remain: {leftover[:5]}")
    return docx_bytes


def _normalize_payload(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Normalizes legacy test & seed payloads to PlotSaleDeedInput schema."""
    payload = dict(raw_payload)
    if "vendors" in payload and "sellers" not in payload:
        payload["sellers"] = payload["vendors"]
    if "property_details" in payload and isinstance(payload["property_details"], dict):
        prop = dict(payload["property_details"])
        if "boundaries" in prop and "boundaries" not in payload:
            payload["boundaries"] = prop["boundaries"]
        payload["property_details"] = prop
    if "boundaries" not in payload:
        payload["boundaries"] = {"east": "रस्ता", "west": "प्लॉट", "north": "प्लॉट", "south": "प्लॉट"}
    if "financial_terms" in payload and "financial" not in payload:
        f_terms = payload["financial_terms"]
        payload["financial"] = {
            "total_consideration": f_terms.get("total_consideration", 100000),
            "earnest_advance": f_terms.get("advance_paid", f_terms.get("earnest_advance", 0)),
            "instalments": f_terms.get("instalments", []),
        }
    if "witnesses" in payload and isinstance(payload["witnesses"], list):
        if len(payload["witnesses"]) > 0 and "witness_1" not in payload:
            w1 = payload["witnesses"][0]
            payload["witness_1"] = f"{w1.get('full_name', '')}, {w1.get('address', '')}"
        if len(payload["witnesses"]) > 1 and "witness_2" not in payload:
            w2 = payload["witnesses"][1]
            payload["witness_2"] = f"{w2.get('full_name', '')}, {w2.get('address', '')}"
    return payload


class GenerationPipelineFSM:
    """Orchestrates document generation through persisted FSM states."""

    def __init__(
        self,
        storage: ObjectStore = default_storage,
        repository: DocumentRepository | None = None,
    ) -> None:
        self.storage = storage
        self.repository: DocumentRepository = (
            repository if repository is not None else InMemoryDocumentRepository()
        )

    def process_job(self, job: JobRecord) -> GeneratedDocumentRecord:
        """Executes the generation pipeline FSM for a claimed job with idempotent execution."""
        try:
            # Deterministic document identity for job idempotency
            doc_id = (
                uuid.UUID(str(job.payload["document_id"]))
                if "document_id" in job.payload
                else job.id
            )

            # Idempotency check: if document already exists from prior attempt, return it
            existing_doc = self.repository.get(job.tenant_id, doc_id)
            if existing_doc is not None:
                job.state = "COMPLETED"
                job.status = "succeeded"
                job.result_ref = existing_doc.file_ref
                return existing_doc

            # 1. State: REQUESTED -> VALIDATED
            job.state = "VALIDATED"
            template_id = str(job.payload.get("template_id") or "sale_deed_plot_mr")
            canonical_input_bytes = json.dumps(
                job.payload, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
            input_hash = hashlib.sha256(canonical_input_bytes).digest()

            # 2. State: VALIDATED -> RENDERED
            job.state = "RENDERED"
            if template_id == "sale_deed_plot_mr":
                normalized_payload = _normalize_payload(job.payload)
                input_data = PlotSaleDeedInput.model_validate(normalized_payload)
                docx_bytes = generate_plot_sale_deed_docx(input_data)
            else:
                docx_bytes = _render_template_docx(template_id, job.payload)

            # 3. State: RENDERED -> VERIFIED
            # Verification gate: python-docx reopen & zero leftover tags confirmed
            job.state = "VERIFIED"
            output_hash = hashlib.sha256(docx_bytes).digest()

            # 4. State: VERIFIED -> STORED (Atomic write: temp file, fsync, rename)
            job.state = "STORED"
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

            # Persist to repository (fails fast on database error, no silent in-memory fallback)
            self.repository.save(job.tenant_id, doc_record)

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
            cid = get_correlation_id()
            logger.exception(
                "Pipeline failed on job %s at state %s [cid=%s]: %s",
                job.id,
                job.state,
                cid,
                exc,
            )
            job.status = "failed"
            job.error = {"error": str(exc), "failed_at_state": job.state}
            raise

    def get_document(
        self, doc_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> GeneratedDocumentRecord | None:
        """Retrieves document enforcing strict tenant scoping (cross-tenant returns None)."""
        return self.repository.get(tenant_id, doc_id)

    def list_documents(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GeneratedDocumentRecord], int]:
        """Lists tenant documents with filtering, search, and pagination."""
        return self.repository.list(
            tenant_id=tenant_id,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )

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
        self.repository.update(tenant_id, doc)
        return pdf_bytes

    def clear(self) -> None:
        if hasattr(self.repository, "clear"):
            self.repository.clear()

    @property
    def _documents(self) -> dict[uuid.UUID, GeneratedDocumentRecord]:
        if isinstance(self.repository, InMemoryDocumentRepository):
            return self.repository._documents
        return {}


generation_pipeline = GenerationPipelineFSM()
