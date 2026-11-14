"""User repository interfaces and in-memory test double.

Enforces:
- Explicit UserRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- InMemoryUserRepository for fast, deterministic unit test execution.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Protocol

from app.identity.models import UserRecord


class UserRepository(Protocol):
    """Explicit repository interface for tenant user accounts."""

    def get_by_id(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> UserRecord | None:
        """Retrieves a user by id scoped strictly to tenant_id."""
        ...

    def get_by_email(self, tenant_id: uuid.UUID, email: str) -> UserRecord | None:
        """Retrieves a user by email scoped strictly to tenant_id."""
        ...

    def find_by_email(self, tenant_id: uuid.UUID | None, email: str) -> UserRecord | None:
        """Looks up a user by email, optionally scoped to tenant_id during authentication."""
        ...

    def create(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        """Persists a new user record within tenant_id."""
        ...

    def update(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        """Updates an existing user record within tenant_id."""
        ...

    def record_failed_login(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        locked_until: datetime.datetime | None = None,
    ) -> None:
        """Increments failed_logins counter and optionally sets account lockout timestamp."""
        ...

    def reset_failed_logins(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Resets failed_logins counter and clears lockout timestamp."""
        ...

    def list_all(self, tenant_id: uuid.UUID) -> list[UserRecord]:
        """Lists all user accounts belonging to tenant_id."""
        ...


class InMemoryUserRepository:
    """In-memory user repository for unit tests and local mocks."""

    def __init__(self, initial_users: list[UserRecord] | None = None) -> None:
        self._users: dict[uuid.UUID, UserRecord] = {}
        if initial_users:
            for u in initial_users:
                self._users[u.id] = u

    def get_by_id(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> UserRecord | None:
        user = self._users.get(user_id)
        if user and user.tenant_id == tenant_id:
            return user
        return None

    def get_by_email(self, tenant_id: uuid.UUID, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        for user in self._users.values():
            if user.tenant_id == tenant_id and user.email.strip().lower() == normalized:
                return user
        return None

    def find_by_email(self, tenant_id: uuid.UUID | None, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        for user in self._users.values():
            if tenant_id is not None and user.tenant_id != tenant_id:
                continue
            if user.email.strip().lower() == normalized:
                return user
        return None

    def create(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        if user.tenant_id != tenant_id:
            raise ValueError(f"User tenant {user.tenant_id} does not match {tenant_id}")
        self._users[user.id] = user
        return user

    def update(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        existing = self.get_by_id(tenant_id, user.id)
        if not existing:
            raise KeyError(f"User {user.id} not found for tenant {tenant_id}")
        self._users[user.id] = user
        return user

    def record_failed_login(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        locked_until: datetime.datetime | None = None,
    ) -> None:
        user = self.get_by_id(tenant_id, user_id)
        if user:
            user.failed_logins += 1
            if locked_until:
                user.locked_until = locked_until

    def reset_failed_logins(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        user = self.get_by_id(tenant_id, user_id)
        if user:
            user.failed_logins = 0
            user.locked_until = None

    def list_all(self, tenant_id: uuid.UUID) -> list[UserRecord]:
        return [u for u in self._users.values() if u.tenant_id == tenant_id]


def create_dev_user_repository() -> InMemoryUserRepository:
    """Creates an InMemoryUserRepository pre-populated with synthetic dev users for testing."""
    from app.shared.security import hash_password

    primary_tenant = uuid.UUID("0193132e-504f-7a1b-8000-000000000000")
    secondary_tenant = uuid.UUID("0193132e-504f-7a1b-8000-000000000099")

    synthetic = [
        UserRecord(
            id=uuid.UUID("0193132e-504f-7a1b-8000-000000000001"),
            tenant_id=primary_tenant,
            email="admin@lekhan.local",
            display_name="Senior Partner (Admin)",
            password_hash=hash_password("ValidPassword123!"),
            role="admin",
            ui_language="mr",
        ),
        UserRecord(
            id=uuid.UUID("0193132e-504f-7a1b-8000-000000000002"),
            tenant_id=primary_tenant,
            email="drafter@lekhan.local",
            display_name="Advocate Drafter (Nagpur)",
            password_hash=hash_password("ValidPassword123!"),
            role="drafter",
            ui_language="mr",
        ),
        UserRecord(
            id=uuid.UUID("0193132e-504f-7a1b-8000-000000000003"),
            tenant_id=primary_tenant,
            email="reviewer@lekhan.local",
            display_name="Reviewer Advocate",
            password_hash=hash_password("ValidPassword123!"),
            role="reviewer",
            ui_language="mr",
        ),
        UserRecord(
            id=uuid.UUID("0193132e-504f-7a1b-8000-000000000004"),
            tenant_id=primary_tenant,
            email="template_admin@lekhan.local",
            display_name="Template Administrator",
            password_hash=hash_password("ValidPassword123!"),
            role="template_admin",
            ui_language="en",
        ),
        UserRecord(
            id=uuid.UUID("0193132e-504f-7a1b-8000-000000000099"),
            tenant_id=secondary_tenant,
            email="other_tenant@lekhan.local",
            display_name="External Tenant User",
            password_hash=hash_password("ValidPassword123!"),
            role="drafter",
            ui_language="en",
        ),
    ]
    return InMemoryUserRepository(synthetic)

