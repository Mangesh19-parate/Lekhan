"""Statutory Stamp Duty and Registration Fee Calculator for Maharashtra.

Governed by:
- Maharashtra Stamp Act, Schedule I, Article 25 (Conveyance)
- Maharashtra Registration Rules (Govt of Maharashtra IGR)

Never uses floats (AGENTS.md Hard Rule 8). Uses Decimal arithmetic exclusively.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field

# Statutory limits & rates for Maharashtra
MAX_REGISTRATION_FEE_CONVEYANCE = Decimal("30000.00")
REGISTRATION_FEE_PERCENT = Decimal("0.01")  # 1%


class StampDutyBreakdown(BaseModel):
    """Itemized breakdown of statutory duties and fees."""

    chargeable_value: Decimal = Field(
        ..., description="Higher of consideration or ready reckoner value"
    )
    base_duty_percent: Decimal
    base_duty_amount: Decimal
    metro_cess_amount: Decimal
    local_body_cess_amount: Decimal
    female_rebate_amount: Decimal
    total_stamp_duty: Decimal
    registration_fee: Decimal
    total_government_charges: Decimal
    area_type: str
    statutory_citation: str = Field(
        default="Maharashtra Stamp Act, 1958, Sched. I, Art. 25 & IGR Notification 2024"
    )


def calculate_maharashtra_stamp_duty(
    consideration: Decimal,
    ready_reckoner_value: Decimal = Decimal("0.00"),
    area_type: Literal[
        "municipal_corporation", "municipal_council", "gram_panchayat"
    ] = "municipal_corporation",
    sole_female_purchaser: bool = False,
) -> StampDutyBreakdown:
    """Calculates statutory stamp duty and registration fee under Maharashtra Stamp Act.

    Args:
        consideration: Agreed deed consideration amount in INR.
        ready_reckoner_value: Annual Statement of Rates (ASR) government market value.
        area_type: Jurisdiction ('municipal_corporation' e.g. NMC, 'municipal_council', 'gram_panchayat').
        sole_female_purchaser: 1% concession under Maharashtra Women's Property Policy if eligible.

    Returns:
        StampDutyBreakdown containing itemized duties, cess, registration fee, and total.
    """
    chargeable = max(consideration, ready_reckoner_value).quantize(
        Decimal("1.00"), rounding=ROUND_HALF_UP
    )

    # Base stamp duty percent by jurisdiction
    if area_type == "municipal_corporation":
        base_rate = Decimal("0.05")  # 5%
        metro_rate = Decimal("0.01")  # 1% Metro Cess
        local_body_rate = Decimal("0.01")  # 1% Local Body Tax / Surcharge
    elif area_type == "municipal_council":
        base_rate = Decimal("0.05")
        metro_rate = Decimal("0.00")
        local_body_rate = Decimal("0.01")
    else:  # gram_panchayat / rural
        base_rate = Decimal("0.03")  # 3%
        metro_rate = Decimal("0.00")
        local_body_rate = Decimal("0.01")  # Zilla Parishad cess

    base_amount = (chargeable * base_rate).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
    metro_amount = (chargeable * metro_rate).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
    local_body_amount = (chargeable * local_body_rate).quantize(
        Decimal("1.00"), rounding=ROUND_HALF_UP
    )

    # 1% rebate for sole female purchaser (applied against base duty)
    if sole_female_purchaser and base_amount > 0:
        female_rebate = (chargeable * Decimal("0.01")).quantize(
            Decimal("1.00"), rounding=ROUND_HALF_UP
        )
    else:
        female_rebate = Decimal("0.00")

    total_stamp_duty = base_amount + metro_amount + local_body_amount - female_rebate

    # Registration fee: 1% of chargeable value, capped at ₹30,000 for conveyance
    raw_reg_fee = (chargeable * REGISTRATION_FEE_PERCENT).quantize(
        Decimal("1.00"), rounding=ROUND_HALF_UP
    )
    reg_fee = min(raw_reg_fee, MAX_REGISTRATION_FEE_CONVEYANCE)

    total_charges = total_stamp_duty + reg_fee

    return StampDutyBreakdown(
        chargeable_value=chargeable,
        base_duty_percent=base_rate * Decimal("100"),
        base_duty_amount=base_amount,
        metro_cess_amount=metro_amount,
        local_body_cess_amount=local_body_amount,
        female_rebate_amount=female_rebate,
        total_stamp_duty=total_stamp_duty,
        registration_fee=reg_fee,
        total_government_charges=total_charges,
        area_type=area_type,
    )
