"""Login throttling and account lockout service.

Enforces:
- 5 attempts per 15 minutes per (account, IP) -> 429 RATE_LIMITED
- 10 consecutive failures locks account for 15 minutes -> 423 LOCKED
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

MAX_ATTEMPTS_PER_WINDOW = 5
WINDOW_SECONDS = 15 * 60  # 15 minutes
MAX_CONSECUTIVE_FAILURES = 10
LOCKOUT_SECONDS = 15 * 60  # 15 minutes


@dataclass
class AttemptTracker:
    timestamps: list[float] = field(default_factory=list)
    consecutive_failures: int = 0
    locked_until: float = 0.0


class LoginThrottler:
    """Thread-safe in-memory login throttler and brute-force protector."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._trackers: dict[str, AttemptTracker] = {}

    def is_locked(self, key: str) -> tuple[bool, int]:
        """Checks if account or IP key is currently locked out."""
        with self._lock:
            tracker = self._trackers.get(key)
            if not tracker:
                return False, 0

            now = time.time()
            if tracker.locked_until > now:
                remaining = int(tracker.locked_until - now)
                return True, remaining

            # Check rate limiting within sliding window
            cutoff = now - WINDOW_SECONDS
            tracker.timestamps = [t for t in tracker.timestamps if t > cutoff]
            if len(tracker.timestamps) >= MAX_ATTEMPTS_PER_WINDOW:
                oldest = tracker.timestamps[0]
                remaining = int((oldest + WINDOW_SECONDS) - now)
                return True, max(1, remaining)

            return False, 0

    def record_failure(self, key: str) -> tuple[bool, int]:
        """Records a failed login attempt and applies lockout if thresholds exceeded."""
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
        """Resets failure counters upon successful authentication."""
        with self._lock:
            if key in self._trackers:
                self._trackers[key].consecutive_failures = 0
                self._trackers[key].timestamps.clear()
                self._trackers[key].locked_until = 0.0

    def reset(self) -> None:
        """Clears all tracking state (used in test fixtures)."""
        with self._lock:
            self._trackers.clear()


# Global singleton instance
login_throttler = LoginThrottler()
