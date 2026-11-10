"""Unit tests for UUIDv7 generation."""

import time
import uuid

from app.shared.ids import uuid7, uuid7_str


def test_uuid7_format_and_version() -> None:
    """Verifies that generated UUID matches RFC 9562 Version 7 specification."""
    u = uuid7()
    assert u.version == 7
    assert u.variant == uuid.RFC_4122

    u_str = uuid7_str()
    assert len(u_str) == 36
    assert uuid.UUID(u_str).version == 7


def test_uuid7_time_ordering() -> None:
    """Verifies that sequential UUIDv7 IDs maintain ascending temporal order."""
    ids: list[uuid.UUID] = []
    for _ in range(10):
        ids.append(uuid7())
        time.sleep(0.002)  # 2 ms separation to test timestamp progression

    # String / binary comparison must strictly preserve creation order
    sorted_ids = sorted(ids)
    assert ids == sorted_ids
