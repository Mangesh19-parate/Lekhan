"""Language pack protocol and base types for property legal drafting.

Strict compliance with docs/ARCHITECTURE.md Section 3.6.
"""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol, runtime_checkable

from app.shared.errors import InvalidAmountError

MAX_CONVEYANCING_AMOUNT = Decimal("1000000000000000")  # 10**15


def validate_and_quantize_amount(amount: Decimal | int) -> tuple[int, int]:
    """Validates money amount per PRD FR-08, rejecting negative, non-finite, float, and > 10**15 amounts.

    Returns:
        tuple of (integer_rupees, paise_0_to_99)
    Raises:
        InvalidAmountError with 422 status code on violation.
    """
    if isinstance(amount, float):
        raise InvalidAmountError(
            "Floating-point numbers are prohibited for legal money calculations. Use Decimal or int."
        )

    if isinstance(amount, Decimal):
        if not amount.is_finite():
            raise InvalidAmountError(f"Non-finite amount {amount} is prohibited in conveyancing.")
        d_amount = amount
    elif isinstance(amount, int):
        d_amount = Decimal(amount)
    else:
        try:
            d_amount = Decimal(str(amount))
            if not d_amount.is_finite():
                raise InvalidAmountError(f"Non-finite amount {amount} is prohibited in conveyancing.")
        except Exception as exc:
            raise InvalidAmountError(f"Invalid monetary amount: {amount}") from exc

    if d_amount < Decimal("0"):
        raise InvalidAmountError(f"Negative amounts are prohibited in conveyancing: {d_amount}")

    if d_amount > MAX_CONVEYANCING_AMOUNT:
        raise InvalidAmountError(f"Amount {d_amount} exceeds maximum conveyancing threshold of 10^15.")

    quantized = d_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer_part = int(quantized)
    paise_part = int((quantized - Decimal(integer_part)) * 100)
    return integer_part, paise_part


@runtime_checkable
class LanguagePack(Protocol):
    """Protocol implemented by each regional conveyancing language pack."""

    code: str
    name: str

    def number_to_words(self, n: Decimal | int, *, currency: bool = True) -> str:
        """Converts numerical amount to formal legal words (Indian grouping)."""
        ...

    def words_to_number(self, text: str) -> Decimal:
        """Inverse parser test oracle: parses legal words back to exact Decimal."""
        ...

    def format_date(self, d: datetime.date, style: str = "formal") -> str:
        """Formats dates in regional statutory conveyancing style."""
        ...

    def to_digits(self, s: str) -> str:
        """Converts Latin digits 0-9 to regional script digits (e.g. Devanagari)."""
        ...

    def to_western_digits(self, s: str) -> str:
        """Converts regional script digits back to standard Western Latin digits."""
        ...

    def honorific(self, gender: str, marital_status: str | None = None) -> str:
        """Returns statutory honorific (e.g. श्री., सौ., Mr., Mrs.)."""
        ...

    def join_names(self, names: list[str]) -> str:
        """Joins multiple party names with appropriate legal conjunctions."""
        ...

    def plural(self, count: int) -> bool:
        """Returns True if count implies plural grammar."""
        ...

    def format_currency(self, amount: Decimal | int) -> str:
        """Formats monetary amount with Indian grouping (e.g. 13,10,000)."""
        ...

    def format_area(self, area: Decimal, unit: str) -> str:
        """Formats land area with localized statutory unit suffix."""
        ...
