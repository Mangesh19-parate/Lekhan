"""Parties REST API Endpoints with Trigram Search & Versioned Reuse (PRD FR-14, F-060, F-061)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.repositories.parties import PostgresPartyRepository
from app.api.auth import get_current_actor
from app.identity.policy import Actor, authorize
from app.parties.repository import PartyRepository
from app.parties.service import PartyService

router = APIRouter(prefix="/api/v1/parties", tags=["parties"])


# --- Dependencies ---


def get_party_repo(db: Session = Depends(get_db)) -> PartyRepository:
    """Provides the PartyRepository scoped to the current database session."""
    return PostgresPartyRepository(db)


def get_party_service(repo: PartyRepository = Depends(get_party_repo)) -> PartyService:
    """Provides PartyService wired with the scoped PartyRepository."""
    return PartyService(repository=repo)


# --- Schemas ---


class PartyCreatePayload(BaseModel):
    kind: str = Field(..., description="individual or company")
    names: dict[str, str] = Field(
        ..., description="Names per language, e.g. {'mr': '...', 'en': '...'}"
    )
    gender: str | None = None
    marital_status: str | None = None
    age_or_dob: dict[str, Any] | None = None
    occupations: dict[str, str] | None = None
    addresses: dict[str, str] | None = None
    pan_masked: str | None = None


class PartyReusePayload(BaseModel):
    overrides: dict[str, Any] | None = None


class PartySearchMatch(BaseModel):
    party: dict[str, Any]
    similarity: float


@router.get(
    "/search",
    response_model=list[PartySearchMatch],
    summary="Trigram search parties in Marathi and English",
)
def search_parties(
    q: str = Query(
        ..., min_length=2, description="Name, PAN, or address fragment in Marathi or English"
    ),
    threshold: float = Query(0.25, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
    actor: Actor = Depends(get_current_actor),
    service: PartyService = Depends(get_party_service),
) -> Any:
    """Executes Devanagari and English trigram search across tenant parties (PRD FR-14, F-061)."""
    matches = service.search_parties(
        tenant_id=actor.tenant_id,
        query=q,
        threshold=threshold,
        limit=limit,
    )
    return [
        PartySearchMatch(
            party={
                "id": p.id,
                "kind": p.kind,
                "names": p.names,
                "gender": p.gender,
                "age_or_dob": p.age_or_dob,
                "occupations": p.occupations,
                "addresses": p.addresses,
                "pan_masked": p.pan_masked,
                "version": p.version,
            },
            similarity=sim,
        )
        for (p, sim) in matches
    ]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new party")
def create_party(
    payload: PartyCreatePayload,
    actor: Actor = Depends(get_current_actor),
    service: PartyService = Depends(get_party_service),
) -> Any:
    """Creates a new party under tenant."""
    decision = authorize(actor, "edit_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    party = service.create_party(
        tenant_id=actor.tenant_id,
        kind=payload.kind,
        names=payload.names,
        gender=payload.gender,
        marital_status=payload.marital_status,
        age_or_dob=payload.age_or_dob,
        occupations=payload.occupations,
        addresses=payload.addresses,
        pan_masked=payload.pan_masked,
        actor_id=actor.user_id,
    )
    return party


@router.get("/{party_id}", summary="Get party by ID")
def get_party(
    party_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    service: PartyService = Depends(get_party_service),
) -> Any:
    """Retrieves party record ensuring tenant isolation."""
    party = service.get_party(party_id, actor.tenant_id)
    if not party:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party not found.")
    return party


@router.post("/{party_id}/reuse", summary="Reuse party in a new matter with version preservation")
def reuse_party(
    party_id: uuid.UUID,
    payload: PartyReusePayload,
    actor: Actor = Depends(get_current_actor),
    service: PartyService = Depends(get_party_service),
) -> Any:
    """Reuses party entity, creating a new version if overrides are supplied (FR-14, F-060)."""
    try:
        party = service.reuse_party(
            party_id=party_id,
            tenant_id=actor.tenant_id,
            overrides=payload.overrides,
            actor_id=actor.user_id,
        )
        return party
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party not found.")


class DuplicateCheckPayload(BaseModel):
    name: str | None = None
    pan: str | None = None
    threshold: float = Field(0.85, ge=0.0, le=1.0)


@router.post("/detect-duplicates", summary="Detect duplicate parties by PAN or name (Feature F-065)")
def detect_duplicate_parties(
    payload: DuplicateCheckPayload,
    actor: Actor = Depends(get_current_actor),
    service: PartyService = Depends(get_party_service),
) -> list[dict[str, Any]]:
    """Detects potential duplicate parties within tenant scope (Feature F-065)."""
    return service.detect_duplicates(
        tenant_id=actor.tenant_id,
        name=payload.name,
        pan=payload.pan,
        threshold=payload.threshold,
    )
