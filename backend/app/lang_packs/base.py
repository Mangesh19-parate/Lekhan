"""Language pack protocol and base types for property legal drafting.

Strict compliance with docs/ARCHITECTURE.md Section 3.6.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable


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
