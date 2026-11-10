"""Properties REST API Endpoints with Trigram Search & Versioned Reuse (PRD FR-14, F-060, F-061)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_actor
from app.identity.policy import Actor, authorize
from app.properties.service import property_service

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])


class PropertyCreatePayload(BaseModel):
    category: str = Field(..., description="plot, flat, shop, agricultural, na")
    attrs: dict[str, Any] = Field(
        ..., description="Attributes e.g. mouza, khasra_no, flat_no, etc."
    )
    area_value: Decimal | None = None
    area_unit: str | None = None
    boundaries: dict[str, str] | None = None
    rr_division: str | None = None
    rr_rate: Decimal | None = None


class PropertyReusePayload(BaseModel):
    overrides: dict[str, Any] | None = None


class PropertySearchMatch(BaseModel):
    property: dict[str, Any]
    similarity: float


@router.get(
    "/search", response_model=list[PropertySearchMatch], summary="Trigram search properties"
)
def search_properties(
    q: str = Query(..., min_length=2, description="Mouza, Khasra, layout, building, or CTS number"),
    category: str | None = Query(
        None, description="Optional category filter (plot, flat, shop, agricultural)"
    ),
    threshold: float = Query(0.25, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Executes Devanagari and English trigram search across tenant properties (PRD FR-14, F-061)."""
    matches = property_service.search_properties(
        tenant_id=actor.tenant_id,
        query=q,
        category=category,
        threshold=threshold,
        limit=limit,
    )
    return [
        PropertySearchMatch(
            property={
                "id": p.id,
                "category": p.category,
                "attrs": p.attrs,
                "area_value": p.area_value,
                "area_unit": p.area_unit,
                "boundaries": p.boundaries,
                "version": p.version,
            },
            similarity=sim,
        )
        for (p, sim) in matches
    ]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new property")
def create_property(
    payload: PropertyCreatePayload,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Creates a new property record."""
    decision = authorize(actor, "edit_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    prop = property_service.create_property(
        tenant_id=actor.tenant_id,
        category=payload.category,
        attrs=payload.attrs,
        area_value=payload.area_value,
        area_unit=payload.area_unit,
        boundaries=payload.boundaries,
        rr_division=payload.rr_division,
        rr_rate=payload.rr_rate,
        actor_id=actor.user_id,
    )
    return prop


@router.get("/{property_id}", summary="Get property by ID")
def get_property(
    property_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Retrieves property record ensuring tenant isolation."""
    prop = property_service.get_property(property_id, actor.tenant_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    return prop


@router.post(
    "/{property_id}/reuse", summary="Reuse property in a new matter with version preservation"
)
def reuse_property(
    property_id: uuid.UUID,
    payload: PropertyReusePayload,
    actor: Actor = Depends(get_current_actor),
) -> Any:
    """Reuses property entity, creating a new version if overrides are supplied (FR-14, F-060)."""
    try:
        prop = property_service.reuse_property(
            property_id=property_id,
            tenant_id=actor.tenant_id,
            overrides=payload.overrides,
            actor_id=actor.user_id,
        )
        return prop
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
