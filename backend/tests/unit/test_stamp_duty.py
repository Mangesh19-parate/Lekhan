"""Tests for statutory stamp duty and fee calculations from fee_rules (F-067).

Hard Rule 7: Never claim statutory rates are valid without legal verification.
If no verified rule matches, returns 'rate not configured', never a number.
Hard Rule 8: Decimal arithmetic exclusively.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.shared.ids import uuid7
from app.shared.models import Base, FeeRule
from app.units.stamp_duty import (
    calculate_maharashtra_stamp_duty,
    calculate_stamp_duty,
)


@pytest.fixture
def db_session() -> Session:
    """Provides an isolated SQLite in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_unverified_rule_returns_rate_not_configured_no_numbers(db_session: Session) -> None:
    """Seeded TODO(lawyer) unverified rows return 'rate not configured' and never a number."""
    unverified_rule = FeeRule(
        id=uuid7(),
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.050000"),
        cap=None,
        concession=Decimal("0.010000"),
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://igrmaharashtra.gov.in",
        verified_by=None,  # Unverified!
        verified_at=None,  # Unverified!
        notes="TODO(lawyer): statutory rate pending verification by legal counsel",
    )
    db_session.add(unverified_rule)
    db_session.commit()

    result = calculate_maharashtra_stamp_duty(
        consideration=Decimal("5000000.00"),
        area_type="municipal_corporation",
        document_date=datetime.date(2024, 6, 1),
        db_session=db_session,
    )

    assert result.status == "rate not configured"
    assert result.rule_id is None
    # Crucial: NEVER return a number when unverified
    assert result.chargeable_value is None
    assert result.rate is None
    assert result.base_duty_amount is None
    assert result.total_stamp_duty is None
    assert result.total_duty is None
    assert result.female_rebate_amount is None


def test_no_matching_rule_returns_rate_not_configured_no_numbers(db_session: Session) -> None:
    """When no rule exists in the database for the instrument/date, return 'rate not configured'."""
    result = calculate_maharashtra_stamp_duty(
        consideration=Decimal("5000000.00"),
        area_type="gram_panchayat",
        document_date=datetime.date(2024, 6, 1),
        db_session=db_session,
    )

    assert result.status == "rate not configured"
    assert result.rule_id is None
    assert result.total_stamp_duty is None


def test_verified_rule_returns_duty_and_rule_id(db_session: Session) -> None:
    """When a verified rule exists, calculate exact duty and return matched rule ID."""
    rule_id = uuid7()
    verified_rule = FeeRule(
        id=rule_id,
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.050000"),  # 5%
        cap=None,
        concession=Decimal("0.010000"),
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://example.gov.in/gazette/2024-01",
        verified_by="Adv. Deshmukh (Bar Council MAH/1234/2010)",
        verified_at=datetime.datetime(2024, 1, 5, 12, 0, tzinfo=datetime.timezone.utc),
        notes="Verified against official Maharashtra Gazette",
    )
    db_session.add(verified_rule)
    db_session.commit()

    result = calculate_maharashtra_stamp_duty(
        consideration=Decimal("5000000.00"),  # ₹50 Lakhs
        area_type="municipal_corporation",
        document_date=datetime.date(2024, 6, 1),
        sole_female_purchaser=False,
        db_session=db_session,
    )

    assert result.status == "ok"
    assert result.rule_id == str(rule_id)
    assert result.chargeable_value == Decimal("5000000.00")
    assert result.rate == Decimal("0.050000")
    assert result.base_duty_amount == Decimal("250000.00")  # 5% of 50L
    assert result.total_stamp_duty == Decimal("250000.00")
    assert result.female_rebate_amount == Decimal("0.00")


def test_female_purchaser_concession_from_rule(db_session: Session) -> None:
    """Verified rule concession (1% rebate) applied for sole female purchaser."""
    rule_id = uuid7()
    verified_rule = FeeRule(
        id=rule_id,
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.050000"),  # 5%
        cap=None,
        concession=Decimal("0.010000"),  # 1% concession
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://example.gov.in/gazette/2024-01",
        verified_by="Adv. Deshmukh",
        verified_at=datetime.datetime(2024, 1, 5, 12, 0, tzinfo=datetime.timezone.utc),
    )
    db_session.add(verified_rule)
    db_session.commit()

    result = calculate_maharashtra_stamp_duty(
        consideration=Decimal("2500000.00"),  # ₹25 Lakhs
        area_type="municipal_corporation",
        document_date=datetime.date(2024, 6, 1),
        sole_female_purchaser=True,
        db_session=db_session,
    )

    assert result.status == "ok"
    assert result.rule_id == str(rule_id)
    assert result.chargeable_value == Decimal("2500000.00")
    assert result.base_duty_amount == Decimal("125000.00")  # 5% of 25L
    assert result.female_rebate_amount == Decimal("25000.00")  # 1% concession
    assert result.total_stamp_duty == Decimal("100000.00")  # 125,000 - 25,000


def test_ready_reckoner_higher_value_wins(db_session: Session) -> None:
    """When government ASR ready reckoner exceeds consideration, duty uses reckoner value."""
    rule_id = uuid7()
    verified_rule = FeeRule(
        id=rule_id,
        jurisdiction="maharashtra:municipal_council",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.040000"),
        cap=None,
        concession=Decimal("0.000000"),
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://example.gov.in/gazette/2024-01",
        verified_by="Adv. Deshmukh",
        verified_at=datetime.datetime(2024, 1, 5, 12, 0, tzinfo=datetime.timezone.utc),
    )
    db_session.add(verified_rule)
    db_session.commit()

    consideration = Decimal("2000000.00")
    ready_reckoner = Decimal("2800000.00")  # Higher

    result = calculate_maharashtra_stamp_duty(
        consideration=consideration,
        ready_reckoner_value=ready_reckoner,
        area_type="municipal_council",
        document_date=datetime.date(2024, 6, 1),
        db_session=db_session,
    )

    assert result.status == "ok"
    assert result.rule_id == str(rule_id)
    assert result.chargeable_value == Decimal("2800000.00")
    assert result.total_stamp_duty == Decimal("112000.00")  # 4% of 28L


def test_date_based_rule_selection(db_session: Session) -> None:
    """The calculator selects the rule effective on the document date."""
    rule_old_id = uuid7()
    rule_old = FeeRule(
        id=rule_old_id,
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.050000"),  # 5%
        cap=None,
        concession=None,
        effective_from=datetime.date(2020, 1, 1),
        effective_to=datetime.date(2023, 12, 31),
        source_url="https://example.gov.in/gazette/2020",
        verified_by="Adv. Deshmukh",
        verified_at=datetime.datetime(2020, 1, 10, 0, 0, tzinfo=datetime.timezone.utc),
    )

    rule_new_id = uuid7()
    rule_new = FeeRule(
        id=rule_new_id,
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        rate=Decimal("0.060000"),  # 6%
        cap=None,
        concession=None,
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://example.gov.in/gazette/2024",
        verified_by="Adv. Deshmukh",
        verified_at=datetime.datetime(2024, 1, 10, 0, 0, tzinfo=datetime.timezone.utc),
    )

    db_session.add_all([rule_old, rule_new])
    db_session.commit()

    # 1. Document dated in 2023 picks old rule
    result_2023 = calculate_stamp_duty(
        consideration=Decimal("1000000.00"),
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        document_date=datetime.date(2023, 6, 15),
        db_session=db_session,
    )
    assert result_2023.status == "ok"
    assert result_2023.rule_id == str(rule_old_id)
    assert result_2023.total_stamp_duty == Decimal("50000.00")  # 5%

    # 2. Document dated in 2024 picks new rule
    result_2024 = calculate_stamp_duty(
        consideration=Decimal("1000000.00"),
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        document_date=datetime.date(2024, 6, 15),
        db_session=db_session,
    )
    assert result_2024.status == "ok"
    assert result_2024.rule_id == str(rule_new_id)
    assert result_2024.total_stamp_duty == Decimal("60000.00")  # 6%

    # 3. Document dated before any effective rule returns unconfigured
    result_2019 = calculate_stamp_duty(
        consideration=Decimal("1000000.00"),
        jurisdiction="maharashtra:municipal_corporation",
        instrument="conveyance_sale_deed",
        document_date=datetime.date(2019, 1, 1),
        db_session=db_session,
    )
    assert result_2019.status == "rate not configured"
    assert result_2019.rule_id is None
    assert result_2019.total_stamp_duty is None


def test_statutory_cap_applied(db_session: Session) -> None:
    """When a statutory rule has a cap, duty is capped."""
    rule_id = uuid7()
    reg_rule = FeeRule(
        id=rule_id,
        jurisdiction="maharashtra",
        instrument="registration_fee",
        rate=Decimal("0.010000"),  # 1%
        cap=Decimal("30000.00"),  # Capped at ₹30,000
        concession=None,
        effective_from=datetime.date(2024, 1, 1),
        effective_to=None,
        source_url="https://example.gov.in/gazette/2024",
        verified_by="Adv. Deshmukh",
        verified_at=datetime.datetime(2024, 1, 10, 0, 0, tzinfo=datetime.timezone.utc),
    )
    db_session.add(reg_rule)
    db_session.commit()

    result = calculate_stamp_duty(
        consideration=Decimal("5000000.00"),  # 1% of 50L = 50,000, capped at 30,000
        jurisdiction="maharashtra",
        instrument="registration_fee",
        document_date=datetime.date(2024, 6, 1),
        db_session=db_session,
    )
    assert result.status == "ok"
    assert result.rule_id == str(rule_id)
    assert result.total_duty == Decimal("30000.00")
