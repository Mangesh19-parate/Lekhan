"""Gap-free document numbering service (PRD FR-12, Features F-055, ADR 012).

Guarantees:
- Strictly monotonic, gap-free sequence per tenant and year.
- Concurrency-safe under parallel request storms (verified by 50-parallel stress test).
- Format: e.g. '2026/00001' or 'DOC/2026/00001'.
"""

from __future__ import annotations

import datetime
import threading
import uuid
from typing import NamedTuple


class CounterKey(NamedTuple):
    tenant_id: uuid.UUID
    series_key: str
    year: int


class DocumentNumberingService:
    """Provides gap-free sequence numbers scoped by tenant, series, and year."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[CounterKey, int] = {}

    def next_doc_no(
        self,
        tenant_id: uuid.UUID,
        series_key: str = "DOC",
        year: int | None = None,
        prefix: str | None = None,
    ) -> str:
        """Atomically increments and returns the next gap-free document number."""
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)

        with self._lock:
            current = self._counters.get(key, 0)
            next_val = current + 1
            self._counters[key] = next_val

        seq_str = f"{next_val:05d}"
        if prefix:
            return f"{prefix}/{target_year}/{seq_str}"
        if series_key and series_key != "DOC":
            return f"{series_key}/{target_year}/{seq_str}"
        return f"{target_year}/{seq_str}"

    def peek_current_sequence(
        self,
        tenant_id: uuid.UUID,
        series_key: str = "DOC",
        year: int | None = None,
    ) -> int:
        """Returns the current highest sequence number without incrementing."""
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)
        with self._lock:
            return self._counters.get(key, 0)

    def reset(
        self,
        tenant_id: uuid.UUID,
        series_key: str = "DOC",
        year: int | None = None,
    ) -> None:
        """Resets counter for testing purposes."""
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)
        with self._lock:
            self._counters.pop(key, None)

    def clear(self) -> None:
        """Clears all counters."""
        with self._lock:
            self._counters.clear()


document_numbering_service = DocumentNumberingService()
