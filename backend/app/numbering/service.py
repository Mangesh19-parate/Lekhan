"""Gap-free document numbering service (PRD FR-12, Features F-055, ADR 012).

Guarantees:
- Strictly monotonic, gap-free sequence per tenant and year.
- Concurrency-safe under parallel request storms using PostgreSQL row upsert / locks.
- In-memory lock fallback when running in standalone unit test environments.
- Format: e.g. '2026/00001' or 'DOC/2026/00001'.
"""

from __future__ import annotations

import datetime
import threading
import uuid
from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.shared.logging import get_logger

logger = get_logger(__name__)


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
        session: Session | None = None,
    ) -> str:
        """Atomically increments and returns the next gap-free document number.

        Uses PostgreSQL atomic UPSERT if a database connection is available,
        otherwise falls back to in-memory lock for isolated unit tests.
        """
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)

        next_val: int | None = None

        # Try database allocation if session provided
        active_session = session
        if active_session is not None:
            try:
                # PostgreSQL atomic UPSERT returning incremented value
                stmt = text(
                    """
                    INSERT INTO counters (tenant_id, key, year, value)
                    VALUES (:tenant_id, :key, :year, 1)
                    ON CONFLICT (tenant_id, key, year)
                    DO UPDATE SET value = counters.value + 1
                    RETURNING value;
                    """
                )
                result = active_session.execute(
                    stmt,
                    {
                        "tenant_id": tenant_id,
                        "key": series_key,
                        "year": target_year,
                    },
                )
                row = result.fetchone()
                if row:
                    next_val = int(row[0])
                    active_session.flush()
            except Exception as e:
                logger.error("Database counter allocation failed: %s", e)
                from app.config import get_settings

                if get_settings().ENV in ("prod", "staging"):
                    raise RuntimeError(
                        f"Database counter allocation failed in {get_settings().ENV}: {e}"
                    ) from e
                next_val = None

        # Fallback to thread-safe in-memory store
        if next_val is None:
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
        session: Session | None = None,
    ) -> int:
        """Returns the current highest sequence number without incrementing."""
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)

        active_session = session
        should_close = False
        if active_session is None:
            try:
                from app.adapters.db import SessionLocal

                active_session = SessionLocal()
                should_close = True
            except Exception:
                active_session = None

        if active_session is not None:
            try:
                stmt = text(
                    "SELECT value FROM counters WHERE tenant_id = :tenant_id AND key = :key AND year = :year"
                )
                row = active_session.execute(
                    stmt,
                    {"tenant_id": tenant_id, "key": series_key, "year": target_year},
                ).fetchone()
                if row:
                    return int(row[0])
                return 0
            except Exception as exc:
                logger.debug("Database counter lookup failed: %s", exc)
            finally:
                if should_close:
                    active_session.close()

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

    def set_counter(
        self,
        tenant_id: uuid.UUID,
        series_key: str = "DOC",
        year: int | None = None,
        value: int = 0,
    ) -> None:
        """Sets counter explicitly for testing/drill purposes."""
        target_year = year or datetime.datetime.now(datetime.timezone.utc).year
        key = CounterKey(tenant_id=tenant_id, series_key=series_key, year=target_year)
        with self._lock:
            self._counters[key] = value

    def get_counter(
        self,
        tenant_id: uuid.UUID,
        series_key: str = "DOC",
        year: int | None = None,
    ) -> int:
        """Gets current counter value for testing/drill purposes."""
        return self.peek_current_sequence(tenant_id=tenant_id, series_key=series_key, year=year)

    def clear(self) -> None:
        """Clears all counters."""
        with self._lock:
            self._counters.clear()


document_numbering_service = DocumentNumberingService()
