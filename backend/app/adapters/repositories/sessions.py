"""PostgreSQL implementation of the SessionRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with the `sessions` table.
Enforces strict tenant scoping on every query.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy.orm import Session

from app.identity.session_repository import SessionData
from app.shared.models import Session as SessionModel


def _to_data(model: SessionModel) -> SessionData:
    """Converts a SQLAlchemy SessionModel to domain SessionData."""
    return SessionData(
        id_hash=model.id_hash,
        user_id=model.user_id,
        tenant_id=model.tenant_id,
        csrf_token_hash=model.csrf_token_hash,
        created_at=model.created_at,
        last_seen_at=model.last_seen_at,
        expires_at=model.expires_at,
        user_agent=model.user_agent,
        ip=model.ip,
    )


class PostgresSessionRepository:
    """PostgreSQL session repository implementing SessionRepository."""

    def __init__(self, session: Session, idle_timeout_minutes: int = 30) -> None:
        self._session = session
        self._idle_timeout_minutes = idle_timeout_minutes

    def save(self, tenant_id: uuid.UUID, session: SessionData) -> SessionData:
        if session.tenant_id != tenant_id:
            raise ValueError(
                f"Session tenant_id {session.tenant_id} does not match parameter {tenant_id}"
            )

        db_session = (
            self._session.query(SessionModel)
            .filter(
                SessionModel.id_hash == session.id_hash,
                SessionModel.tenant_id == tenant_id,
            )
            .first()
        )
        if not db_session:
            db_session = SessionModel(
                id_hash=session.id_hash,
                user_id=session.user_id,
                tenant_id=session.tenant_id,
                csrf_token_hash=session.csrf_token_hash,
                created_at=session.created_at,
                last_seen_at=session.last_seen_at,
                expires_at=session.expires_at,
                user_agent=session.user_agent,
                ip=session.ip,
            )
            self._session.add(db_session)
        else:
            db_session.last_seen_at = session.last_seen_at
            db_session.expires_at = session.expires_at
            db_session.user_agent = session.user_agent
            db_session.ip = session.ip

        self._session.commit()
        self._session.refresh(db_session)
        return _to_data(db_session)

    def get(self, tenant_id: uuid.UUID, id_hash: bytes) -> SessionData | None:
        model = (
            self._session.query(SessionModel)
            .filter(
                SessionModel.id_hash == id_hash,
                SessionModel.tenant_id == tenant_id,
            )
            .first()
        )
        if not model:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        idle_cutoff = model.last_seen_at + datetime.timedelta(minutes=self._idle_timeout_minutes)
        if now > model.expires_at or now > idle_cutoff:
            self.delete(tenant_id, id_hash)
            return None

        return _to_data(model)

    def find_by_hash(self, tenant_id: uuid.UUID | None, id_hash: bytes) -> SessionData | None:
        query = self._session.query(SessionModel).filter(SessionModel.id_hash == id_hash)
        if tenant_id is not None:
            query = query.filter(SessionModel.tenant_id == tenant_id)
        model = query.first()
        if not model:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        idle_cutoff = model.last_seen_at + datetime.timedelta(minutes=self._idle_timeout_minutes)
        if now > model.expires_at or now > idle_cutoff:
            self.delete(model.tenant_id, id_hash)
            return None

        return _to_data(model)

    def touch(self, tenant_id: uuid.UUID, id_hash: bytes, last_seen_at: datetime.datetime) -> None:
        db_session = (
            self._session.query(SessionModel)
            .filter(
                SessionModel.id_hash == id_hash,
                SessionModel.tenant_id == tenant_id,
            )
            .first()
        )
        if db_session:
            db_session.last_seen_at = last_seen_at
            self._session.commit()

    def delete(self, tenant_id: uuid.UUID, id_hash: bytes) -> None:
        db_session = (
            self._session.query(SessionModel)
            .filter(
                SessionModel.id_hash == id_hash,
                SessionModel.tenant_id == tenant_id,
            )
            .first()
        )
        if db_session:
            self._session.delete(db_session)
            self._session.commit()

    def delete_all_for_user(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        (
            self._session.query(SessionModel)
            .filter(
                SessionModel.tenant_id == tenant_id,
                SessionModel.user_id == user_id,
            )
            .delete(synchronize_session=False)
        )
        self._session.commit()

    def delete_expired(self, tenant_id: uuid.UUID, now: datetime.datetime) -> int:
        idle_cutoff = now - datetime.timedelta(minutes=self._idle_timeout_minutes)
        deleted = (
            self._session.query(SessionModel)
            .filter(
                SessionModel.tenant_id == tenant_id,
                (SessionModel.expires_at <= now) | (SessionModel.last_seen_at <= idle_cutoff),
            )
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return int(deleted)
