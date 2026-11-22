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

from app.config import get_settings
from app.identity.session_repository import (
    InMemorySessionRepository,
    SessionData,
    SessionRepository,
)
from app.shared.security import (
    generate_opaque_token,
    hash_token,
    verify_csrf_token,
)

settings = get_settings()

COOKIE_NAME = "lekhan_session"
IDLE_TIMEOUT_MINUTES = settings.SESSION_IDLE_MINUTES
ABSOLUTE_TIMEOUT_HOURS = settings.SESSION_ABSOLUTE_HOURS


class SessionStore:
    """Session management store delegating to SessionRepository."""

    def __init__(self, repo: SessionRepository | None = None) -> None:
        self._repo = repo or InMemorySessionRepository()

    @property
    def repo(self) -> SessionRepository:
        return self._repo

    @repo.setter
    def repo(self, new_repo: SessionRepository) -> None:
        self._repo = new_repo

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
        self._repo.save(tenant_id, session_data)
        return session_token, csrf_token

    def get_session(self, session_token: str) -> SessionData | None:
        """Validates and refreshes session sliding idle window."""
        id_hash = hash_token(session_token)
        session = self._repo.find_by_hash(None, id_hash)
        if not session:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)

        # Check absolute timeout
        if now > session.expires_at:
            self._repo.delete(session.tenant_id, id_hash)
            return None

        # Check sliding idle timeout (30 minutes)
        idle_limit = session.last_seen_at + datetime.timedelta(minutes=IDLE_TIMEOUT_MINUTES)
        if now > idle_limit:
            self._repo.delete(session.tenant_id, id_hash)
            return None

        # Refresh last seen sliding window
        self._repo.touch(session.tenant_id, id_hash, now)
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
        session = self._repo.find_by_hash(None, id_hash)
        if session:
            self._repo.delete(session.tenant_id, id_hash)

    def delete_all_for_user(self, user_id: uuid.UUID, tenant_id: uuid.UUID | None = None) -> None:
        """Revokes all active sessions for a user (password change / lockout)."""
        if tenant_id is not None:
            self._repo.delete_all_for_user(tenant_id, user_id)
        elif isinstance(self._repo, InMemorySessionRepository):
            to_del = [
                (s.tenant_id, s.id_hash)
                for s in self._repo._sessions.values()
                if s.user_id == user_id
            ]
            for tid, h in to_del:
                self._repo.delete(tid, h)

    def clear(self) -> None:
        """Clears all sessions (test cleanup)."""
        if isinstance(self._repo, InMemorySessionRepository):
            self._repo.clear()


# Global singleton instance for backwards-compatible test helpers
session_store = SessionStore()
