"""Portal Data-Entry Sheet Models (PRD FR-16, Features F-063, Goal G6).

Structures property and party data for seamless entry into the Maharashtra
Sub-Registrar / IGR Public Data Entry (PDE) and SARATHI portals without double entry.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class PortalParty(BaseModel):
    role: str = Field(..., description="Executant / Claimant / Vendor / Purchaser")
    name_mr: str
    name_en: str
    age: int | None = None
    pan_masked: str | None = None
    aadhaar_last4: str | None = None
    address: str
    mobile: str | None = None


class PortalProperty(BaseModel):
    category: str
    district: str = "Nagpur"
    taluka: str = "Nagpur"
    mouza: str
    khasra_survey_cts: str
    unit_or_plot_no: str
    floor_no: str | None = None
    building_name: str | None = None
    area_metric: str
    boundaries: dict[str, str] = Field(default_factory=dict)


class PortalFinancial(BaseModel):
    total_consideration: str
    amount_in_words_mr: str
    amount_in_words_en: str
    earnest_amount: str | None = None
    balance_amount: str | None = None
    payment_mode: str | None = None


class PortalDataSheet(BaseModel):
    document_id: uuid.UUID
    doc_no: str
    document_type: str
    parties: list[PortalParty]
    property: PortalProperty
    financial: PortalFinancial
    copy_paste_text: str = Field(
        ..., description="Plain-text formatted block for direct portal copy-paste"
    )
