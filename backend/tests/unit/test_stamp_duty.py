"""Tests for statutory stamp duty and registration fee calculations (F-067)."""

from decimal import Decimal

from app.units.stamp_duty import (
    MAX_REGISTRATION_FEE_CONVEYANCE,
    calculate_maharashtra_stamp_duty,
)


def test_nagpur_nmc_stamp_duty_standard() -> None:
    """Tests 5% + 1% + 1% = 7% total duty on Nagpur urban plot with capped reg fee."""
    consideration = Decimal("5000000.00")  # ₹50 Lakhs
    result = calculate_maharashtra_stamp_duty(
        consideration=consideration,
        area_type="municipal_corporation",
        sole_female_purchaser=False,
    )

    assert result.chargeable_value == Decimal("5000000.00")
    assert result.base_duty_amount == Decimal("250000.00")  # 5%
    assert result.metro_cess_amount == Decimal("50000.00")  # 1%
    assert result.local_body_cess_amount == Decimal("50000.00")  # 1%
    assert result.female_rebate_amount == Decimal("0.00")
    assert result.total_stamp_duty == Decimal("350000.00")  # 7%
    assert result.registration_fee == MAX_REGISTRATION_FEE_CONVEYANCE  # Capped at ₹30,000


def test_female_purchaser_concession() -> None:
    """Tests 1% rebate for sole female purchaser under Maharashtra Women's Property Policy."""
    consideration = Decimal("2500000.00")  # ₹25 Lakhs
    result = calculate_maharashtra_stamp_duty(
        consideration=consideration,
        area_type="municipal_corporation",
        sole_female_purchaser=True,
    )

    assert result.female_rebate_amount == Decimal("25000.00")
    assert result.total_stamp_duty == Decimal("150000.00")  # 6% total (7% - 1%)
    assert result.registration_fee == Decimal("25000.00")  # 1% of 25 Lakhs (< ₹30,000)


def test_ready_reckoner_higher_value_wins() -> None:
    """When government ASR ready reckoner exceeds consideration, duty uses reckoner value."""
    consideration = Decimal("2000000.00")
    ready_reckoner = Decimal("2800000.00")  # Higher
    result = calculate_maharashtra_stamp_duty(
        consideration=consideration,
        ready_reckoner_value=ready_reckoner,
        area_type="municipal_corporation",
    )

    assert result.chargeable_value == Decimal("2800000.00")
    assert result.total_stamp_duty == Decimal("196000.00")  # 7% of 28 Lakhs
