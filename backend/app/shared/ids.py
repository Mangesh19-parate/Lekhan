"""RFC 9562 UUIDv7 generator for time-ordered primary keys.

Encodes a 48-bit millisecond timestamp in the high bits, guaranteeing that
database indexes maintain sequential B-tree ordering for high insert performance.
"""

from __future__ import annotations

import secrets
import time
import uuid

_last_v7_timestamp = 0
_v7_sequence = 0


def uuid7() -> uuid.UUID:
    """Generates an RFC 9562 UUIDv7 with millisecond timestamp ordering."""
    global _last_v7_timestamp, _v7_sequence

    # Current epoch time in milliseconds
    current_ms = int(time.time() * 1000)

    if current_ms > _last_v7_timestamp:
        _last_v7_timestamp = current_ms
        _v7_sequence = secrets.randbits(12)
    else:
        # Same millisecond or clock moved backward: increment sequence
        _v7_sequence = (_v7_sequence + 1) & 0xFFF
        current_ms = _last_v7_timestamp

    # 48 bits of timestamp
    time_hi = (current_ms >> 16) & 0xFFFFFFFF
    time_mid = current_ms & 0xFFFF

    # 4 bits version (7) + 12 bits sequence
    time_hi_and_version = 0x7000 | (_v7_sequence & 0x0FFF)

    # 2 bits variant (10) + 62 bits randomness
    clock_seq_hi_and_reserved = 0x80 | (secrets.randbits(6))
    clock_seq_low = secrets.randbits(8)
    node = secrets.randbits(48)

    return uuid.UUID(
        fields=(
            time_hi,
            time_mid,
            time_hi_and_version,
            clock_seq_hi_and_reserved,
            clock_seq_low,
            node,
        )
    )


def uuid7_str() -> str:
    """Returns UUIDv7 as a canonical string."""
    return str(uuid7())
