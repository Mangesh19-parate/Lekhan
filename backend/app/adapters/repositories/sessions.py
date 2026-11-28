"""PostgreSQL implementation of the SessionRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with the `sessions` table.
Enforces strict tenant scoping on every query.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.identity.session_repository import SessionData
from app.shared.logging import get_logger
from app.shared.models import Session as SessionModel

logger = get_logger(__name__)


def _to_data(model: SessionModel) -> SessionData:
    """Converts a SQLAlchemy SessionModel to domain SessionData."""
    expires_at = model.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    created_at = model.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=datetime.timezone.utc)
    last_seen_at = model.last_seen_at
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=datetime.timezone.utc)
    return SessionData(
        id_hash=model.id_hash,
        user_id=model.user_id,
        tenant_id=model.tenant_id,
        csrf_token_hash=model.csrf_token_hash,
        created_at=created_at,
        last_seen_at=last_seen_at,
        expires_at=expires_at,
        user_agent=model.user_agent,
        ip=model.ip,
        mfa_pending=getattr(model, "mfa_pending", False),
    )


class PostgresSessionRepository:
    """PostgreSQL session repository implementing SessionRepository."""

    def __init__(self, session: Session, idle_timeout_minutes: int | None = None) -> None:
        self._session = session
        self._idle_timeout_minutes = (
            idle_timeout_minutes
            if idle_timeout_minutes is not None
            else get_settings().SESSION_IDLE_MINUTES
        )

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
                mfa_pending=session.mfa_pending,
            )
            self._session.add(db_session)
        else:
            db_session.last_seen_at = session.last_seen_at
            db_session.expires_at = session.expires_at
            db_session.user_agent = session.user_agent
            db_session.ip = session.ip
            db_session.mfa_pending = session.mfa_pending

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
        expires_at = model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
        last_seen_at = model.last_seen_at
        if last_seen_at.tzinfo is None:
            last_seen_at = last_seen_at.replace(tzinfo=datetime.timezone.utc)
        idle_cutoff = last_seen_at + datetime.timedelta(minutes=self._idle_timeout_minutes)
        if now > expires_at or now > idle_cutoff:
            self.delete(tenant_id, id_hash)
            return None

        return _to_data(model)

    def find_by_hash(self, tenant_id: uuid.UUID | None, id_hash: bytes) -> SessionData | None:
        if tenant_id is None:
            # Pre-auth lookup: invoke narrow SECURITY DEFINER function on PostgreSQL
            try:
                bind = self._session.get_bind()
                if bind and bind.dialect.name == "postgresql":
                    row = (
                        self._session.execute(
                            text("SELECT * FROM auth_lookup_session_by_hash(:hash)"),
                            {"hash": id_hash},
                        )
                        .mappings()
                        .first()
                    )
                    if row:
                        now = datetime.datetime.now(datetime.timezone.utc)
                        idle_cutoff = row["last_seen_at"] + datetime.timedelta(
                            minutes=self._idle_timeout_minutes
                        )
                        if now > row["expires_at"] or now > idle_cutoff:
                            self.delete(row["tenant_id"], id_hash)
                            return None
                        return SessionData(
                            id_hash=row["id_hash"],
                            user_id=row["user_id"],
                            tenant_id=row["tenant_id"],
                            csrf_token_hash=row["csrf_token_hash"],
                            created_at=row["created_at"],
                            last_seen_at=row["last_seen_at"],
                            expires_at=row["expires_at"],
                            user_agent=row["user_agent"],
                            ip=row["ip"],
                            mfa_pending=row["mfa_pending"],
                        )
                    return None
            except Exception as exc:
                logger.debug("auth_lookup_session_by_hash query fallback: %s", exc)

        query = self._session.query(SessionModel).filter(SessionModel.id_hash == id_hash)
        if tenant_id is not None:
            query = query.filter(SessionModel.tenant_id == tenant_id)
        model = query.first()
        if not model:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
        last_seen_at = model.last_seen_at
        if last_seen_at.tzinfo is None:
            last_seen_at = last_seen_at.replace(tzinfo=datetime.timezone.utc)
        idle_cutoff = last_seen_at + datetime.timedelta(minutes=self._idle_timeout_minutes)
        if now > expires_at or now > idle_cutoff:
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
