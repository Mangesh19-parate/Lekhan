"""Session management service.

Handles:
- Opaque random cookie generation
- SHA-256 hashing for database storage
- Sliding idle timeout (30 mins) and absolute timeout (12 hours)
- Session rotation on login and password change
- CSRF token issuance and verification
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from app.config import get_settings
from app.shared.security import (
    generate_opaque_token,
    hash_token,
    verify_csrf_token,
)

settings = get_settings()

COOKIE_NAME = "lekhan_session"
IDLE_TIMEOUT_MINUTES = settings.SESSION_IDLE_MINUTES
ABSOLUTE_TIMEOUT_HOURS = settings.SESSION_ABSOLUTE_HOURS


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


class SessionStore:
    """Session management store.

    Maintains active sessions with sliding and absolute timeouts.
    """

    def __init__(self) -> None:
        # In-memory session registry (backed by PostgreSQL in DB adapter)
        self._sessions: dict[bytes, SessionData] = {}

    def create_session(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> tuple[str, str]:
        """Creates a new session, returning (raw_session_token, raw_csrf_token)."""
        session_token = generate_opaque_token(32)
        csrf_token = generate_opaque_token(32)

        id_hash = hash_token(session_token)
        csrf_hash = hash_token(csrf_token)

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)

        session_data = SessionData(
            id_hash=id_hash,
            user_id=user_id,
            tenant_id=tenant_id,
            csrf_token_hash=csrf_hash,
            created_at=now,
            last_seen_at=now,
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
        )
        self._sessions[id_hash] = session_data
        return session_token, csrf_token

    def get_session(self, session_token: str) -> SessionData | None:
        """Validates and refreshes session sliding idle window."""
        id_hash = hash_token(session_token)
        session = self._sessions.get(id_hash)
        if not session:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)

        # Check absolute timeout
        if now > session.expires_at:
            self.delete_session(session_token)
            return None

        # Check sliding idle timeout (30 minutes)
        idle_limit = session.last_seen_at + datetime.timedelta(minutes=IDLE_TIMEOUT_MINUTES)
        if now > idle_limit:
            self.delete_session(session_token)
            return None

        # Refresh last seen sliding window
        session.last_seen_at = now
        return session

    def validate_csrf(self, session_token: str, supplied_csrf: str) -> bool:
        """Verifies supplied CSRF token against session hash in constant time."""
        session = self.get_session(session_token)
        if not session or not supplied_csrf:
            return False
        return verify_csrf_token(session.csrf_token_hash, supplied_csrf)

    def delete_session(self, session_token: str) -> None:
        """Revokes a specific session (logout)."""
        id_hash = hash_token(session_token)
        self._sessions.pop(id_hash, None)

    def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revokes all active sessions for a user (password change / lockout)."""
        to_delete = [id_hash for id_hash, s in self._sessions.items() if s.user_id == user_id]
        for h in to_delete:
            self._sessions.pop(h, None)

    def clear(self) -> None:
        """Clears all sessions (test cleanup)."""
        self._sessions.clear()


# Global singleton instance
session_store = SessionStore()
