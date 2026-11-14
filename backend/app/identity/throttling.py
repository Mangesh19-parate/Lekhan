"""Login throttling and account lockout service with database persistence.

Enforces:
- 5 attempts per 15 minutes per (account, IP) -> 429 RATE_LIMITED
- 10 consecutive failures locks account for 15 minutes -> 423 LOCKED
- Backed by PostgreSQL `rate_limits` table (or in-memory test fallback)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from decimal import Decimal
from threading import Lock
from typing import Callable, Protocol

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.shared.logging import get_logger
from app.shared.models import RateLimit as RateLimitModel

logger = get_logger(__name__)

MAX_ATTEMPTS_PER_WINDOW = 5
WINDOW_SECONDS = 15 * 60  # 15 minutes
MAX_CONSECUTIVE_FAILURES = 10
LOCKOUT_SECONDS = 15 * 60  # 15 minutes


class Throttler(Protocol):
    """Protocol for login throttling and rate limiting."""

    def is_locked(self, key: str) -> tuple[bool, int]: ...

    def record_failure(self, key: str) -> tuple[bool, int]: ...

    def record_success(self, key: str) -> None: ...

    def reset(self) -> None: ...


@dataclass
class AttemptTracker:
    timestamps: list[float] = field(default_factory=list)
    consecutive_failures: int = 0
    locked_until: float = 0.0


class InMemoryThrottler:
    """Thread-safe in-memory login throttler for local unit tests."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._trackers: dict[str, AttemptTracker] = {}

    def is_locked(self, key: str) -> tuple[bool, int]:
        with self._lock:
            tracker = self._trackers.get(key)
            if not tracker:
                return False, 0

            now = time.time()
            if tracker.locked_until > now:
                remaining = int(tracker.locked_until - now)
                return True, remaining

            cutoff = now - WINDOW_SECONDS
            tracker.timestamps = [t for t in tracker.timestamps if t > cutoff]
            if len(tracker.timestamps) >= MAX_ATTEMPTS_PER_WINDOW:
                oldest = tracker.timestamps[0]
                remaining = int((oldest + WINDOW_SECONDS) - now)
                return True, max(1, remaining)

            return False, 0

    def record_failure(self, key: str) -> tuple[bool, int]:
        with self._lock:
            now = time.time()
            tracker = self._trackers.setdefault(key, AttemptTracker())

            cutoff = now - WINDOW_SECONDS
            tracker.timestamps = [t for t in tracker.timestamps if t > cutoff]
            tracker.timestamps.append(now)
            tracker.consecutive_failures += 1

            if tracker.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                tracker.locked_until = now + LOCKOUT_SECONDS
                return True, LOCKOUT_SECONDS

            return False, 0

    def record_success(self, key: str) -> None:
        with self._lock:
            if key in self._trackers:
                self._trackers[key].consecutive_failures = 0
                self._trackers[key].timestamps.clear()
                self._trackers[key].locked_until = 0.0

    def reset(self) -> None:
        with self._lock:
            self._trackers.clear()


class DatabaseThrottler:
    """PostgreSQL-backed distributed throttler using `rate_limits` table."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory
        self._fallback = InMemoryThrottler()

    def is_locked(self, key: str) -> tuple[bool, int]:
        try:
            with self._session_factory() as session:
                entry = session.query(RateLimitModel).filter(RateLimitModel.key == key).first()
                if not entry:
                    return False, 0

                now = time.time()
                locked_until = float(entry.locked_until)
                if locked_until > now:
                    remaining = int(locked_until - now)
                    return True, remaining

                cutoff = now - WINDOW_SECONDS
                timestamps = [float(t) for t in (entry.timestamps or []) if float(t) > cutoff]
                if len(timestamps) >= MAX_ATTEMPTS_PER_WINDOW:
                    oldest = timestamps[0]
                    remaining = int((oldest + WINDOW_SECONDS) - now)
                    return True, max(1, remaining)

                return False, 0
        except SQLAlchemyError as exc:
            logger.debug("Database throttler fallback to memory: %s", exc)
            return self._fallback.is_locked(key)

    def record_failure(self, key: str) -> tuple[bool, int]:
        try:
            with self._session_factory() as session:
                entry = (
                    session.query(RateLimitModel)
                    .filter(RateLimitModel.key == key)
                    .with_for_update()
                    .first()
                )
                now = time.time()
                cutoff = now - WINDOW_SECONDS

                if not entry:
                    entry = RateLimitModel(
                        key=key,
                        timestamps=[now],
                        consecutive_failures=1,
                        locked_until=Decimal("0.0"),
                    )
                    session.add(entry)
                    session.commit()
                    return False, 0

                timestamps = [float(t) for t in (entry.timestamps or []) if float(t) > cutoff]
                timestamps.append(now)
                entry.timestamps = timestamps
                entry.consecutive_failures += 1

                is_locked = False
                lock_duration = 0
                if entry.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    entry.locked_until = round(now + LOCKOUT_SECONDS, 4)
                    is_locked = True
                    lock_duration = LOCKOUT_SECONDS

                session.commit()
                return is_locked, lock_duration
        except SQLAlchemyError as exc:
            logger.debug("Database throttler failure recording fallback to memory: %s", exc)
            return self._fallback.record_failure(key)

    def record_success(self, key: str) -> None:
        try:
            with self._session_factory() as session:
                entry = session.query(RateLimitModel).filter(RateLimitModel.key == key).first()
                if entry:
                    entry.consecutive_failures = 0
                    entry.timestamps = []
                    entry.locked_until = 0.0
                    session.commit()
        except SQLAlchemyError as exc:
            logger.debug("Database throttler reset failure fallback: %s", exc)
            self._fallback.record_success(key)

    def reset(self) -> None:
        try:
            with self._session_factory() as session:
                session.query(RateLimitModel).delete()
                session.commit()
        except SQLAlchemyError:
            pass
        self._fallback.reset()


# Global distributed login throttler instance
login_throttler: Throttler = DatabaseThrottler()
