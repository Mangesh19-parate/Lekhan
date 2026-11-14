"""Session repository interfaces and in-memory test double.

Enforces:
- Explicit SessionRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- InMemorySessionRepository for deterministic testing.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SessionData:
    """Active session metadata."""

    id_hash: bytes
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    csrf_token_hash: bytes
    created_at: datetime.datetime
    last_seen_at: datetime.datetime
    expires_at: datetime.datetime
    user_agent: str | None = None
    ip: str | None = None


@runtime_checkable
class SessionRepository(Protocol):
    """Explicit repository interface for tenant session persistence."""

    def save(self, tenant_id: uuid.UUID, session: SessionData) -> SessionData:
        """Persists a new or updated session for tenant_id."""
        ...

    def get(self, tenant_id: uuid.UUID, id_hash: bytes) -> SessionData | None:
        """Retrieves an active session strictly scoped to tenant_id."""
        ...

    def find_by_hash(self, tenant_id: uuid.UUID | None, id_hash: bytes) -> SessionData | None:
        """Looks up a session by id_hash, optionally scoped to tenant_id."""
        ...

    def touch(self, tenant_id: uuid.UUID, id_hash: bytes, last_seen_at: datetime.datetime) -> None:
        """Updates the sliding window last_seen_at timestamp for tenant_id session."""
        ...

    def delete(self, tenant_id: uuid.UUID, id_hash: bytes) -> None:
        """Revokes a session for tenant_id."""
        ...

    def delete_all_for_user(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Revokes all active sessions for a user within tenant_id."""
        ...

    def delete_expired(self, tenant_id: uuid.UUID, now: datetime.datetime) -> int:
        """Removes expired sessions belonging to tenant_id."""
        ...


class InMemorySessionRepository:
    """In-memory session repository for fast unit tests."""

    def __init__(self) -> None:
        self._sessions: dict[bytes, SessionData] = {}

    def save(self, tenant_id: uuid.UUID, session: SessionData) -> SessionData:
        if session.tenant_id != tenant_id:
            raise ValueError(f"Session tenant_id {session.tenant_id} does not match {tenant_id}")
        self._sessions[session.id_hash] = session
        return session

    def get(self, tenant_id: uuid.UUID, id_hash: bytes) -> SessionData | None:
        session = self._sessions.get(id_hash)
        if session and session.tenant_id == tenant_id:
            return session
        return None

    def find_by_hash(self, tenant_id: uuid.UUID | None, id_hash: bytes) -> SessionData | None:
        session = self._sessions.get(id_hash)
        if session:
            if tenant_id is not None and session.tenant_id != tenant_id:
                return None
            return session
        return None

    def touch(self, tenant_id: uuid.UUID, id_hash: bytes, last_seen_at: datetime.datetime) -> None:
        session = self.get(tenant_id, id_hash)
        if session:
            session.last_seen_at = last_seen_at

    def delete(self, tenant_id: uuid.UUID, id_hash: bytes) -> None:
        session = self._sessions.get(id_hash)
        if session and session.tenant_id == tenant_id:
            self._sessions.pop(id_hash, None)

    def delete_all_for_user(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        to_del = [
            h
            for h, s in self._sessions.items()
            if s.tenant_id == tenant_id and s.user_id == user_id
        ]
        for h in to_del:
            self._sessions.pop(h, None)

    def delete_expired(self, tenant_id: uuid.UUID, now: datetime.datetime) -> int:
        to_del = [
            h for h, s in self._sessions.items() if s.tenant_id == tenant_id and s.expires_at <= now
        ]
        for h in to_del:
            self._sessions.pop(h, None)
        return len(to_del)

    def clear(self) -> None:
        """Clears all sessions (test cleanup helper)."""
        self._sessions.clear()
