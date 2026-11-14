"""Unit tests for UserRepository interfaces, tenant isolation, and dev seeding.

Fulfills AGENTS.md Hard Rule 6 (every query tenant-scoped) and verifies:
1. Protocol conformance of InMemoryUserRepository.
2. Multi-tenant isolation on get_by_id, get_by_email, create, update.
3. Argon2id password hash verification on dev seed accounts.
4. Failed login tracking and lockout resets.
"""

import datetime
import uuid

import pytest

from app.identity.models import UserRecord
from app.identity.repository import UserRepository, create_dev_user_repository, InMemoryUserRepository
from app.shared.security import hash_password, verify_password


TENANT_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_2 = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")


def test_user_repository_protocol_conformance() -> None:
    repo = InMemoryUserRepository()
    assert isinstance(repo, UserRepository)


def test_create_and_tenant_scoped_lookup() -> None:
    repo = InMemoryUserRepository()
    user_id = uuid.uuid4()
    user = UserRecord(
        id=user_id,
        tenant_id=TENANT_1,
        email="lawyer@tenant1.local",
        display_name="Advocate One",
        password_hash=hash_password("ValidPassword123!"),
        role="drafter",
    )
    repo.create(TENANT_1, user)

    # Scoped to TENANT_1 succeeds
    found = repo.get_by_id(TENANT_1, user_id)
    assert found is not None
    assert found.email == "lawyer@tenant1.local"

    # Cross-tenant lookup returns None
    assert repo.get_by_id(TENANT_2, user_id) is None
    assert repo.get_by_email(TENANT_2, "lawyer@tenant1.local") is None


def test_create_mismatched_tenant_raises_value_error() -> None:
    repo = InMemoryUserRepository()
    user = UserRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_1,
        email="test@tenant1.local",
        display_name="Test",
        password_hash="hash",
    )
    with pytest.raises(ValueError):
        repo.create(TENANT_2, user)


def test_update_tenant_isolation() -> None:
    repo = InMemoryUserRepository()
    user_id = uuid.uuid4()
    user = UserRecord(
        id=user_id,
        tenant_id=TENANT_1,
        email="drafter@tenant1.local",
        display_name="Initial Name",
        password_hash="hash",
    )
    repo.create(TENANT_1, user)

    user.display_name = "Updated Name"
    # Update under wrong tenant fails
    with pytest.raises(KeyError):
        repo.update(TENANT_2, user)

    # Update under correct tenant succeeds
    repo.update(TENANT_1, user)
    updated = repo.get_by_id(TENANT_1, user_id)
    assert updated is not None
    assert updated.display_name == "Updated Name"


def test_failed_login_and_lockout_tracking() -> None:
    repo = InMemoryUserRepository()
    user_id = uuid.uuid4()
    user = UserRecord(
        id=user_id,
        tenant_id=TENANT_1,
        email="user@test.local",
        display_name="User",
        password_hash="hash",
    )
    repo.create(TENANT_1, user)

    assert user.failed_logins == 0
    assert user.locked_until is None

    lock_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    repo.record_failed_login(TENANT_1, user_id, locked_until=lock_time)
    assert user.failed_logins == 1
    assert user.locked_until == lock_time

    repo.reset_failed_logins(TENANT_1, user_id)
    assert user.failed_logins == 0
    assert user.locked_until is None


def test_dev_seed_repository_has_valid_argon2_hashes() -> None:
    repo = create_dev_user_repository()
    admin = repo.find_by_email(None, "admin@lekhan.local")
    assert admin is not None
    assert admin.role == "admin"
    assert verify_password(admin.password_hash, "ValidPassword123!") is True
    assert verify_password(admin.password_hash, "WrongPassword") is False

