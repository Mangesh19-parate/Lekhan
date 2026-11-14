"""Unit tests for SessionRepository interfaces and multi-tenant isolation.

Fulfills AGENTS.md Hard Rule 6 (every query tenant-scoped) and verifies:
1. Protocol conformance of InMemorySessionRepository.
2. Tenant isolation on get, save, delete, delete_all_for_user, delete_expired.
3. Sliding window touch and expiration handling.
"""

import datetime
import uuid

import pytest

from app.identity.session_repository import (
    InMemorySessionRepository,
    SessionData,
    SessionRepository,
)

TENANT_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_2 = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")
USER_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000010")


def test_session_repository_protocol_conformance() -> None:
    repo = InMemorySessionRepository()
    assert isinstance(repo, SessionRepository)


def test_save_and_tenant_scoped_lookup() -> None:
    repo = InMemorySessionRepository()
    now = datetime.datetime.now(datetime.timezone.utc)
    id_hash = b"\x01" * 32
    csrf_hash = b"\x02" * 32

    session = SessionData(
        id_hash=id_hash,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=csrf_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )
    repo.save(TENANT_1, session)

    # Scoped to TENANT_1 returns session
    found = repo.get(TENANT_1, id_hash)
    assert found is not None
    assert found.user_id == USER_1

    # Cross-tenant query returns None
    assert repo.get(TENANT_2, id_hash) is None
    assert repo.find_by_hash(TENANT_2, id_hash) is None


def test_save_mismatched_tenant_raises_value_error() -> None:
    repo = InMemorySessionRepository()
    now = datetime.datetime.now(datetime.timezone.utc)
    session = SessionData(
        id_hash=b"\x03" * 32,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=b"\x04" * 32,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )
    with pytest.raises(ValueError):
        repo.save(TENANT_2, session)


def test_touch_sliding_window() -> None:
    repo = InMemorySessionRepository()
    now = datetime.datetime.now(datetime.timezone.utc)
    id_hash = b"\x05" * 32
    session = SessionData(
        id_hash=id_hash,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=b"\x06" * 32,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )
    repo.save(TENANT_1, session)

    later = now + datetime.timedelta(minutes=10)
    repo.touch(TENANT_1, id_hash, later)

    updated = repo.get(TENANT_1, id_hash)
    assert updated is not None
    assert updated.last_seen_at == later


def test_delete_and_delete_all_for_user_tenant_scoped() -> None:
    repo = InMemorySessionRepository()
    now = datetime.datetime.now(datetime.timezone.utc)
    h1 = b"\x10" * 32
    h2 = b"\x20" * 32

    s1 = SessionData(
        id_hash=h1,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=b"\x11" * 32,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )
    s2 = SessionData(
        id_hash=h2,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=b"\x22" * 32,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(hours=12),
    )
    repo.save(TENANT_1, s1)
    repo.save(TENANT_1, s2)

    # Delete under wrong tenant does not delete
    repo.delete(TENANT_2, h1)
    assert repo.get(TENANT_1, h1) is not None

    # Delete all under wrong tenant does not delete
    repo.delete_all_for_user(TENANT_2, USER_1)
    assert repo.get(TENANT_1, h1) is not None
    assert repo.get(TENANT_1, h2) is not None

    # Delete all under correct tenant deletes all
    repo.delete_all_for_user(TENANT_1, USER_1)
    assert repo.get(TENANT_1, h1) is None
    assert repo.get(TENANT_1, h2) is None


def test_delete_expired_tenant_scoped() -> None:
    repo = InMemorySessionRepository()
    now = datetime.datetime.now(datetime.timezone.utc)
    h1 = b"\x30" * 32

    expired_session = SessionData(
        id_hash=h1,
        user_id=USER_1,
        tenant_id=TENANT_1,
        csrf_token_hash=b"\x31" * 32,
        created_at=now - datetime.timedelta(hours=2),
        last_seen_at=now - datetime.timedelta(hours=2),
        expires_at=now - datetime.timedelta(hours=1),
    )
    repo.save(TENANT_1, expired_session)

    # Delete expired for TENANT_2 removes 0
    deleted = repo.delete_expired(TENANT_2, now)
    assert deleted == 0
    assert repo.get(TENANT_1, h1) is not None

    # Delete expired for TENANT_1 removes 1
    deleted = repo.delete_expired(TENANT_1, now)
    assert deleted == 1
    assert repo.get(TENANT_1, h1) is None
