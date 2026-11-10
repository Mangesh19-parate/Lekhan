"""Document drafting, generation jobs, history, and download endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.adapters.storage import default_storage
from app.api.auth import get_current_actor
from app.generation.jobs import job_queue
from app.generation.pipeline import generation_pipeline
from app.generation.spike_engine import PlotSaleDeedInput
from app.identity.policy import Actor, Resource, authorize
from app.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class JobEnqueueResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    state: str
    document_id: uuid.UUID | None = None
    doc_no: str | None = None
    download_url: str | None = None
    pdf_url: str | None = None


class DocumentSummaryItem(BaseModel):
    id: uuid.UUID
    doc_no: str
    status: str
    language: str
    engine_version: str
    created_at: str
    docx_download_url: str
    pdf_download_url: str


class DocumentHistoryResponse(BaseModel):
    items: list[DocumentSummaryItem]
    total: int
    limit: int
    offset: int


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    doc_no: str
    status: str
    language: str
    engine_version: str
    template_version_id: uuid.UUID
    data_snapshot: dict[str, Any]
    created_at: str
    docx_download_url: str
    pdf_download_url: str


@router.post("", response_model=JobEnqueueResponse, summary="Enqueue document generation job")
def create_document_generation_job(
    payload: PlotSaleDeedInput,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Enqueues document generation job with idempotency deduplication."""
    # 1. Authorize action
    decision = authorize(actor, "create_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    # 2. Enqueue in job queue
    raw_payload = payload.model_dump(mode="json")
    job = job_queue.enqueue(
        tenant_id=actor.tenant_id,
        job_type="generate_docx",
        payload=raw_payload,
        idempotency_key=idempotency_key,
    )

    # 3. Synchronous execution for dev/immediate responses
    doc = generation_pipeline.process_job(job)

    return JobEnqueueResponse(
        job_id=job.id,
        status=job.status,
        state=job.state,
        document_id=doc.id,
        doc_no=doc.doc_no,
        download_url=f"/api/v1/documents/{doc.id}/download",
        pdf_url=f"/api/v1/documents/{doc.id}/pdf",
    )


@router.get("", response_model=DocumentHistoryResponse, summary="List document history with filters")
def list_document_history(
    status_filter: str | None = Query(None, alias="status", description="Filter by status (draft, reviewed, finalised)"),
    search: str | None = Query(None, description="Search term for doc_no or party/property content"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Retrieves paginated tenant document history with cross-tenant isolation (PRD FR-11, F-057)."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    docs, total = generation_pipeline.list_documents(
        tenant_id=actor.tenant_id,
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )

    items = [
        DocumentSummaryItem(
            id=d.id,
            doc_no=d.doc_no,
            status=d.status,
            language=d.language,
            engine_version=d.engine_version,
            created_at=d.created_at,
            docx_download_url=f"/api/v1/documents/{d.id}/download",
            pdf_download_url=f"/api/v1/documents/{d.id}/pdf",
        )
        for d in docs
    ]
    return DocumentHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document details and data snapshot")
def get_document_details(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Retrieves document detail record and immutable data snapshot (cross-tenant yields 404)."""
    doc = generation_pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    return DocumentDetailResponse(
        id=doc.id,
        doc_no=doc.doc_no,
        status=doc.status,
        language=doc.language,
        engine_version=doc.engine_version,
        template_version_id=doc.template_version_id,
        data_snapshot=doc.data_snapshot,
        created_at=doc.created_at,
        docx_download_url=f"/api/v1/documents/{doc.id}/download",
        pdf_download_url=f"/api/v1/documents/{doc.id}/pdf",
    )


@router.get("/{document_id}/download", summary="Download generated document DOCX (Master)")
def download_document(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Response:
    """Retrieves document from object store and streams DOCX master attachment."""
    doc = generation_pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "download_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    docx_bytes = default_storage.get(doc.file_ref)
    if not docx_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file missing or expired.",
        )

    safe_doc_no = doc.doc_no.replace("/", "_")
    filename = f"Draft_{safe_doc_no}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Lekhan-Master-Format": "docx",
        },
    )


@router.get("/{document_id}/pdf", summary="Download generated document PDF (Convenience Copy)")
def download_document_pdf(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Response:
    """Converts/retrieves PDF convenience copy (ADR 010, PRD FR-13, Features F-056)."""
    doc = generation_pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "download_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        pdf_bytes = generation_pipeline.get_or_create_pdf(document_id, actor.tenant_id)
    except Exception as exc:
        logger.exception("Failed to generate PDF for document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        ) from exc

    safe_doc_no = doc.doc_no.replace("/", "_")
    filename = f"Convenience_Copy_{safe_doc_no}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Lekhan-Document-Type": "convenience-copy",
            "X-Lekhan-Master-Format": "docx",
        },
    )


class ValidationRequest(BaseModel):
    data: dict[str, Any]


class ValidationResponse(BaseModel):
    valid: bool
    derived_fields: dict[str, Any]
    violations: list[dict[str, Any]]
    visibility: dict[str, bool]


@router.post("/validate/{template_id}", response_model=ValidationResponse, summary="Validate draft form data with derived fields")
def validate_draft_data(
    template_id: str,
    payload: ValidationRequest,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Evaluates cross-field validation rules, derived fields, and visibility."""
    import json
    from pathlib import Path
    from app.templates.compiler import ManifestCompiler, ManifestRuntime

    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / template_id / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{template_id}' not found.")

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    runtime = ManifestRuntime()

    derived_context = runtime.evaluate_derived_fields(compiled, payload.data)
    violations = runtime.validate(compiled, derived_context)
    visibility = runtime.evaluate_visibility(compiled, derived_context)

    # Extract just the derived field outputs
    derived_outputs: dict[str, Any] = {}
    for d_name in compiled.evaluation_order:
        parts = d_name.split(".")
        curr: Any = derived_context
        for p in parts:
            if isinstance(curr, dict):
                curr = curr.get(p)
            else:
                curr = None
                break
        derived_outputs[d_name] = curr

    return ValidationResponse(
        valid=len(violations) == 0,
        derived_fields=derived_outputs,
        violations=violations,
        visibility=visibility,
    )
