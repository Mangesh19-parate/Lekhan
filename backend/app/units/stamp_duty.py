"""Statutory Stamp Duty and Registration Fee Calculator.

Hard Rule 7: Never claim statutory rates are valid without legal verification.
Hard Rule 8: No floats for money or area. Use Decimal arithmetic exclusively.

All statutory rates, caps, and concessions are loaded dynamically from fee_rules.
If no verified rule matches for the given document date, jurisdiction, and instrument,
the calculator returns "rate not configured" and never fabricates numbers.
"""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.shared.models import FeeRule


class StampDutyBreakdown(BaseModel):
    """Itemized breakdown of statutory duties and fees."""

    status: str = Field(..., description="'ok' or 'rate not configured'")
    rule_id: str | None = Field(default=None, description="Matched verified fee_rule UUID")
    chargeable_value: Decimal | None = None
    rate: Decimal | None = None
    base_duty_amount: Decimal | None = None
    female_rebate_amount: Decimal | None = None
    concession_amount: Decimal | None = None
    total_stamp_duty: Decimal | None = None
    total_duty: Decimal | None = None
    jurisdiction: str
    instrument: str
    document_date: datetime.date
    source_url: str | None = None
    message: str | None = None
    area_type: str | None = None


def query_fee_rule(
    session: Session,
    jurisdiction: str,
    instrument: str,
    document_date: datetime.date,
) -> FeeRule | None:
    """Finds the most recent statutory fee rule active on the given document date."""
    stmt = (
        select(FeeRule)
        .where(
            FeeRule.jurisdiction == jurisdiction,
            FeeRule.instrument == instrument,
            FeeRule.effective_from <= document_date,
            or_(FeeRule.effective_to.is_(None), FeeRule.effective_to >= document_date),
        )
        .order_by(FeeRule.effective_from.desc())
        .limit(1)
    )
    return session.execute(stmt).scalars().first()


def calculate_stamp_duty(
    consideration: Decimal,
    ready_reckoner_value: Decimal = Decimal("0.00"),
    jurisdiction: str = "maharashtra:municipal_corporation",
    instrument: str = "conveyance_sale_deed",
    document_date: datetime.date | None = None,
    sole_female_purchaser: bool = False,
    db_session: Session | None = None,
    rule: FeeRule | None = None,
    area_type: str | None = None,
) -> StampDutyBreakdown:
    """Calculates statutory stamp duty / fees from verified fee_rules.

    Hard Rule 7: If no verified rule matches, returns 'rate not configured' and never a number.
    Hard Rule 8: Decimal arithmetic exclusively.
    """
    doc_date = document_date or datetime.date.today()

    # Normalize area_type to jurisdiction if provided
    resolved_jurisdiction = jurisdiction
    if area_type:
        resolved_jurisdiction = area_type if ":" in area_type else f"maharashtra:{area_type}"

    # Lookup rule if not supplied directly
    matched_rule: FeeRule | None = rule
    if matched_rule is None and db_session is not None:
        matched_rule = query_fee_rule(
            session=db_session,
            jurisdiction=resolved_jurisdiction,
            instrument=instrument,
            document_date=doc_date,
        )
    elif matched_rule is None:
        try:
            from app.adapters.db import SessionLocal

            with SessionLocal() as session:
                matched_rule = query_fee_rule(
                    session=session,
                    jurisdiction=resolved_jurisdiction,
                    instrument=instrument,
                    document_date=doc_date,
                )
        except Exception:
            matched_rule = None

    # Hard Rule 7: If no rule matches or rule is not verified by legal counsel, return "rate not configured"
    if matched_rule is None or matched_rule.verified_by is None or matched_rule.verified_at is None:
        return StampDutyBreakdown(
            status="rate not configured",
            rule_id=None,
            jurisdiction=resolved_jurisdiction,
            instrument=instrument,
            document_date=doc_date,
            area_type=area_type,
            message="Statutory rate not configured or unverified for document date.",
        )

    # Valid verified statutory rule found
    chargeable = max(consideration, ready_reckoner_value).quantize(
        Decimal("1.00"), rounding=ROUND_HALF_UP
    )
    raw_duty = (chargeable * matched_rule.rate).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
    base_duty = min(raw_duty, matched_rule.cap) if matched_rule.cap is not None else raw_duty

    # Concession (e.g. sole female purchaser)
    concession = Decimal("0.00")
    if (
        sole_female_purchaser
        and matched_rule.concession is not None
        and matched_rule.concession > Decimal("0")
    ):
        concession = (chargeable * matched_rule.concession).quantize(
            Decimal("1.00"), rounding=ROUND_HALF_UP
        )

    total_duty = max(Decimal("0.00"), base_duty - concession)

    return StampDutyBreakdown(
        status="ok",
        rule_id=str(matched_rule.id),
        chargeable_value=chargeable,
        rate=matched_rule.rate,
        base_duty_amount=base_duty,
        female_rebate_amount=concession,
        concession_amount=concession,
        total_stamp_duty=total_duty,
        total_duty=total_duty,
        jurisdiction=resolved_jurisdiction,
        instrument=instrument,
        document_date=doc_date,
        source_url=matched_rule.source_url,
        area_type=area_type,
    )


def calculate_maharashtra_stamp_duty(
    consideration: Decimal,
    ready_reckoner_value: Decimal = Decimal("0.00"),
    area_type: str = "municipal_corporation",
    jurisdiction: str | None = None,
    instrument: str = "conveyance_sale_deed",
    document_date: datetime.date | None = None,
    sole_female_purchaser: bool = False,
    db_session: Session | None = None,
    rule: FeeRule | None = None,
) -> StampDutyBreakdown:
    """Convenience wrapper for Maharashtra stamp duty calculation."""
    return calculate_stamp_duty(
        consideration=consideration,
        ready_reckoner_value=ready_reckoner_value,
        jurisdiction=jurisdiction or f"maharashtra:{area_type}",
        instrument=instrument,
        document_date=document_date,
        sole_female_purchaser=sole_female_purchaser,
        db_session=db_session,
        rule=rule,
        area_type=area_type,
    )
