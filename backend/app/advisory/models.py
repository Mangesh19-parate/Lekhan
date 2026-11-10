"""Advisory Alert Models (PRD FR-15, Features F-062).

Advocate-authored non-blocking advisory suggestions to alert drafters to statutory
compliance requirements, tax deductions, and registry checklists.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AdvisoryAlert(BaseModel):
    """Non-blocking advisory notice evaluated on draft payload."""

    id: str = Field(..., description="Unique advisory rule identifier")
    rule_name: str
    severity: Literal["advisory", "warning"] = "advisory"
    title_en: str
    title_mr: str
    advice_en: str
    advice_mr: str
    statutory_ref: str
    action_needed: str | None = None
