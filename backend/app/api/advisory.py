"""Advisory Alerts REST API Endpoints (PRD FR-15, Features F-062)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.advisory.engine import advisory_rules_engine
from app.advisory.models import AdvisoryAlert
from app.api.auth import get_current_actor
from app.identity.policy import Actor

router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


class AdvisoryEvaluateRequest(BaseModel):
    template_id: str | None = None
    data: dict[str, Any]


@router.post(
    "/evaluate",
    response_model=list[AdvisoryAlert],
    summary="Evaluate lawyer-authored advisory rules",
)
def evaluate_advisory_alerts(
    payload: AdvisoryEvaluateRequest,
    actor: Actor = Depends(get_current_actor),
) -> list[AdvisoryAlert]:
    """Evaluates non-blocking compliance advisories (TDS, PAN, RERA, Agriculturalist check)."""
    return advisory_rules_engine.evaluate_payload(
        payload=payload.data,
        template_id=payload.template_id,
        tenant_id=actor.tenant_id,
    )
