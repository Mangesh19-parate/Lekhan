"""Job status and background worker polling endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.repositories.jobs import PostgresJobRepository
from app.api.auth import get_current_actor
from app.api.documents import get_job_repo
from app.generation.jobs import JobRepository
from app.identity.policy import Actor, authorize

router = APIRouter(tags=["jobs"])


class JobDetailResponse(BaseModel):
    id: uuid.UUID
    status: str
    state: str
    document_id: uuid.UUID | None = None
    attempts: int = 0
    error: dict[str, Any] | None = None
    retryable: bool = False
    outputs: dict[str, bool] = Field(default_factory=dict)
    download_url: str | None = None
    pdf_url: str | None = None


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get background job status and pipeline state",
)
def get_job_status(
    job_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    job_repo: JobRepository = Depends(get_job_repo),
) -> Any:
    """Retrieves current job status, pipeline state, and outputs strictly scoped to tenant."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    job = job_repo.get(tenant_id=actor.tenant_id, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    doc_id: uuid.UUID | None = None
    if "document_id" in job.payload:
        try:
            doc_id = uuid.UUID(str(job.payload["document_id"]))
        except (ValueError, TypeError):
            pass

    outputs: dict[str, bool] = {
        "docx": job.status == "succeeded",
        "pdf": False,
    }

    retryable = (
        job.status in ("queued", "running")
        or (job.status == "failed" and bool(job.error and job.error.get("retryable", False)))
    )

    return JobDetailResponse(
        id=job.id,
        status=job.status,
        state=job.state or "REQUESTED",
        document_id=doc_id,
        attempts=job.attempts,
        error=job.error,
        retryable=retryable,
        outputs=outputs,
        download_url=f"/api/v1/documents/{doc_id}/download" if (job.status == "succeeded" and doc_id) else None,
        pdf_url=f"/api/v1/documents/{doc_id}/pdf" if (job.status == "succeeded" and doc_id) else None,
    )
