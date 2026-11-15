"""Document drafting, generation jobs, history, and download endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.repositories.documents import PostgresDocumentRepository
from app.adapters.repositories.jobs import PostgresJobRepository
from app.adapters.storage import default_storage
from app.api.auth import get_current_actor
from app.audit.service import audit_service
from app.generation.jobs import JobRepository
from app.generation.pipeline import GenerationPipelineFSM
from app.generation.provenance import verify_docx_provenance
from app.generation.repository import DocumentRepository
from app.identity.policy import Actor, Resource, authorize
from app.shared.errors import AppError
from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


# --- Dependencies ---


def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    """Provides the DocumentRepository scoped to the current database session."""
    return PostgresDocumentRepository(db)


def get_job_repo(db: Session = Depends(get_db)) -> JobRepository:
    """Provides the JobRepository scoped to the current database session."""
    return PostgresJobRepository(db)


def get_pipeline(
    repo: DocumentRepository = Depends(get_document_repo),
) -> GenerationPipelineFSM:
    """Provides GenerationPipelineFSM wired with the scoped DocumentRepository."""
    return GenerationPipelineFSM(repository=repo)


# --- Schemas ---


class JobEnqueueResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    state: str
    document_id: uuid.UUID | None = None
    doc_no: str | None = None
    download_url: str | None = None
    pdf_url: str | None = None
    job: dict[str, Any] | None = None


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


class ProvenanceVerificationResponse(BaseModel):
    valid: bool
    tampered: bool
    document_id: str | None = None
    tenant_id: str | None = None
    template_version_id: str | None = None
    template_sha256: str | None = None
    engine_version: str | None = None
    expected_document_hash: str | None = None
    actual_document_hash: str | None = None
    generated_at: str | None = None
    verified_at: str
    message: str


@router.post(
    "",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue document generation job asynchronously",
)
def create_document_generation_job(
    payload: dict[str, Any],
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    actor: Actor = Depends(get_current_actor),
    job_repo: JobRepository = Depends(get_job_repo),
) -> Any:
    """Enqueues document generation job asynchronously with 202 Accepted and idempotency deduplication."""
    # 1. Authorize action
    decision = authorize(actor, "create_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    # 2. Extract or assign deterministic document_id
    if "document_id" in payload:
        try:
            doc_id = uuid.UUID(str(payload["document_id"]))
        except (ValueError, TypeError):
            from app.shared.ids import uuid7

            doc_id = uuid7()
            payload["document_id"] = str(doc_id)
    else:
        from app.shared.ids import uuid7

        doc_id = uuid7()
        payload["document_id"] = str(doc_id)

    # 3. Enqueue in job queue (deduplicated by idempotency_key within tenant_id)
    job = job_repo.enqueue(
        tenant_id=actor.tenant_id,
        type="generate_docx",
        payload=payload,
        idempotency_key=idempotency_key,
    )

    # If existing job from idempotency has a document_id in payload, use it
    if "document_id" in job.payload:
        try:
            doc_id = uuid.UUID(str(job.payload["document_id"]))
        except (ValueError, TypeError):
            pass

    return JobEnqueueResponse(
        job_id=job.id,
        status=job.status,
        state=job.state or "REQUESTED",
        document_id=doc_id,
        job={"id": str(job.id), "state": job.state or "REQUESTED"},
        download_url=f"/api/v1/documents/{doc_id}/download",
        pdf_url=f"/api/v1/documents/{doc_id}/pdf",
    )


@router.get(
    "", response_model=DocumentHistoryResponse, summary="List document history with filters"
)
def list_document_history(
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status (draft, reviewed, finalised)"
    ),
    search: str | None = Query(
        None, description="Search term for doc_no or party/property content"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
) -> Any:
    """Retrieves paginated tenant document history with cross-tenant isolation (PRD FR-11, F-057)."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    docs, total = pipeline.list_documents(
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


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and data snapshot",
)
def get_document_details(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
) -> Any:
    """Retrieves document detail record and immutable data snapshot (cross-tenant yields 404)."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
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
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
) -> Response:
    """Retrieves document from object store and streams DOCX master attachment."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
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

    # Log download event per PRD FR-17
    audit_service.log_event(
        tenant_id=doc.tenant_id,
        action="download_document",
        entity="document",
        entity_id=str(doc.id),
        actor_id=actor.user_id,
        meta={"format": "docx", "doc_no": doc.doc_no},
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
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
) -> Response:
    """Converts/retrieves PDF convenience copy (ADR 010, PRD FR-13, Features F-056)."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
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
        pdf_bytes = pipeline.get_or_create_pdf(document_id, actor.tenant_id)
    except Exception as exc:
        cid = get_correlation_id()
        logger.exception(
            "Failed to generate PDF for document %s [cid=%s]: %s", document_id, cid, exc
        )
        raise AppError(
            message=f"PDF generation failed (Correlation ID: {cid}).",
            code="PDF_GENERATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # Log download event per PRD FR-17
    audit_service.log_event(
        tenant_id=doc.tenant_id,
        action="download_document",
        entity="document",
        entity_id=str(doc.id),
        actor_id=actor.user_id,
        meta={"format": "pdf", "doc_no": doc.doc_no},
    )

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


@router.post(
    "/verify",
    response_model=ProvenanceVerificationResponse,
    summary="Cryptographically verify provenance and integrity of an uploaded DOCX file",
)
async def verify_uploaded_docx(
    file: UploadFile = File(...),
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Extracts custom XML provenance and verifies against word/document.xml SHA-256."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    res = verify_docx_provenance(content)
    return ProvenanceVerificationResponse(
        valid=res.valid,
        tampered=res.tampered,
        document_id=res.document_id,
        tenant_id=res.tenant_id,
        template_version_id=res.template_version_id,
        template_sha256=res.template_sha256,
        engine_version=res.engine_version,
        expected_document_hash=res.expected_document_hash,
        actual_document_hash=res.actual_document_hash,
        generated_at=res.generated_at,
        verified_at=res.verified_at,
        message=res.message,
    )


@router.get(
    "/{document_id}/verify",
    response_model=ProvenanceVerificationResponse,
    summary="Cryptographically verify provenance and integrity of a stored document",
)
def verify_stored_document(
    document_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    pipeline: GenerationPipelineFSM = Depends(get_pipeline),
) -> Any:
    """Retrieves stored DOCX for tenant and verifies cryptographic provenance against tamper."""
    doc = pipeline.get_document(document_id, actor.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    resource = Resource(tenant_id=doc.tenant_id, resource_type="document")
    decision = authorize(actor, "view_document", resource)
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    docx_bytes = default_storage.get(doc.file_ref)
    if not docx_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file missing or expired.",
        )

    res = verify_docx_provenance(docx_bytes)
    return ProvenanceVerificationResponse(
        valid=res.valid,
        tampered=res.tampered,
        document_id=res.document_id,
        tenant_id=res.tenant_id,
        template_version_id=res.template_version_id,
        template_sha256=res.template_sha256,
        engine_version=res.engine_version,
        expected_document_hash=res.expected_document_hash,
        actual_document_hash=res.actual_document_hash,
        generated_at=res.generated_at,
        verified_at=res.verified_at,
        message=res.message,
    )


class ValidationRequest(BaseModel):
    data: dict[str, Any]


class ValidationResponse(BaseModel):
    valid: bool
    derived_fields: dict[str, Any]
    violations: list[dict[str, Any]]
    visibility: dict[str, bool]


@router.post(
    "/validate/{template_id}",
    response_model=ValidationResponse,
    summary="Validate draft form data with derived fields",
)
def validate_draft_data(
    template_id: str,
    payload: ValidationRequest,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Evaluates cross-field validation rules, derived fields, and visibility."""
    import json

    from app.templates.compiler import ManifestCompiler, ManifestRuntime
    from app.templates.validator import validate_template_id

    try:
        tmpl_dir = validate_template_id(template_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID: {err}",
        )

    manifest_path = tmpl_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{template_id}' not found."
        )

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
