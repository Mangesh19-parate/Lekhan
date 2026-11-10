"""Pilot Corrections & Drafter Feedback API Endpoints (PRD Section 10, Plan Week 19).

Provides endpoints for drafters and advocates to log corrections, track resolution, and review pilot statistics.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.auth import get_current_actor
from app.generation.pipeline import generation_pipeline
from app.identity.policy import Actor
from app.pilot.corrections import (
    CorrectionCreateRequest,
    CorrectionEntry,
    CorrectionSeverity,
    CorrectionStatus,
    PilotStats,
    pilot_corrections_service,
)

router = APIRouter(prefix="/api/v1/pilot", tags=["pilot"])


class TriageCorrectionRequest(BaseModel):
    notes: str | None = None


class ResolveCorrectionRequest(BaseModel):
    resolution_notes: str


@router.post(
    "/corrections",
    response_model=CorrectionEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Log a draft correction or layout feedback",
)
def log_pilot_correction(
    payload: CorrectionCreateRequest,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Logs a new correction entry from a pilot drafter or advocate."""
    return pilot_corrections_service.log_correction(
        tenant_id=actor.tenant_id,
        drafter_id=str(actor.user_id),
        req=payload,
    )


@router.get(
    "/corrections",
    response_model=list[CorrectionEntry],
    summary="List pilot corrections with optional filters",
)
def list_pilot_corrections(
    template_id: str | None = Query(None, description="Filter by template ID"),
    status_filter: CorrectionStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    severity: CorrectionSeverity | None = Query(None, description="Filter by severity"),
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Retrieves tenant-scoped pilot corrections log."""
    return pilot_corrections_service.list_corrections(
        tenant_id=actor.tenant_id,
        template_id=template_id,
        status=status_filter,
        severity=severity,
    )


@router.post(
    "/corrections/{correction_id}/triage",
    response_model=CorrectionEntry,
    summary="Triage a pilot correction",
)
def triage_pilot_correction(
    correction_id: uuid.UUID,
    payload: TriageCorrectionRequest,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Marks a correction as triaged with triage notes."""
    try:
        return pilot_corrections_service.triage_correction(
            correction_id=correction_id,
            tenant_id=actor.tenant_id,
            triaged_by=str(actor.user_id),
            notes=payload.notes,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correction {correction_id} not found.",
        )


@router.post(
    "/corrections/{correction_id}/resolve",
    response_model=CorrectionEntry,
    summary="Resolve a pilot correction",
)
def resolve_pilot_correction(
    correction_id: uuid.UUID,
    payload: ResolveCorrectionRequest,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Marks a correction as resolved with resolution notes."""
    try:
        return pilot_corrections_service.resolve_correction(
            correction_id=correction_id,
            tenant_id=actor.tenant_id,
            resolution_notes=payload.resolution_notes,
            resolved_by=str(actor.user_id),
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correction {correction_id} not found.",
        )


@router.get(
    "/stats",
    response_model=PilotStats,
    summary="Get pilot health metrics and correction trends",
)
def get_pilot_statistics(
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Returns pilot metrics, resolution rate, and corrections-per-draft trend."""
    _, total_drafts = generation_pipeline.list_documents(tenant_id=actor.tenant_id)
    return pilot_corrections_service.get_pilot_stats(
        tenant_id=actor.tenant_id,
        total_drafts=max(1, total_drafts),
    )
