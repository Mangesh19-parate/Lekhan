"""PostgreSQL implementation of the UserRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with the `users` table.
Enforces strict tenant scoping on every query.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.identity.models import UserRecord
from app.shared.models import User as UserModel


def _to_record(model: UserModel) -> UserRecord:
    """Converts a SQLAlchemy UserModel to a pure domain UserRecord."""
    return UserRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        email=model.email,
        display_name=model.display_name,
        password_hash=model.password_hash,
        role=model.role,
        ui_language=model.ui_language,
        mfa_secret_enc=model.mfa_secret_enc,
        active=model.active,
        failed_logins=model.failed_logins,
        locked_until=model.locked_until,
        created_at=model.created_at,
    )


class PostgresUserRepository:
    """PostgreSQL user repository implementing UserRepository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> UserRecord | None:
        model = (
            self._session.query(UserModel)
            .filter(
                UserModel.id == user_id,
                UserModel.tenant_id == tenant_id,
            )
            .first()
        )
        return _to_record(model) if model else None

    def get_by_email(self, tenant_id: uuid.UUID, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        model = (
            self._session.query(UserModel)
            .filter(
                UserModel.tenant_id == tenant_id,
                func.lower(UserModel.email) == normalized,
            )
            .first()
        )
        return _to_record(model) if model else None

    def find_by_email(self, tenant_id: uuid.UUID | None, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        query = self._session.query(UserModel).filter(func.lower(UserModel.email) == normalized)
        if tenant_id is not None:
            query = query.filter(UserModel.tenant_id == tenant_id)
        model = query.first()
        return _to_record(model) if model else None

    def create(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        if user.tenant_id != tenant_id:
            raise ValueError(f"User tenant_id {user.tenant_id} does not match parameter {tenant_id}")
        db_user = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email.strip().lower(),
            display_name=user.display_name,
            password_hash=user.password_hash,
            role=user.role,
            ui_language=user.ui_language,
            mfa_secret_enc=user.mfa_secret_enc,
            active=user.active,
            failed_logins=user.failed_logins,
            locked_until=user.locked_until,
            created_at=user.created_at,
        )
        self._session.add(db_user)
        self._session.commit()
        self._session.refresh(db_user)
        return _to_record(db_user)

    def update(self, tenant_id: uuid.UUID, user: UserRecord) -> UserRecord:
        db_user = (
            self._session.query(UserModel)
            .filter(
                UserModel.id == user.id,
                UserModel.tenant_id == tenant_id,
            )
            .first()
        )
        if not db_user:
            raise KeyError(f"User {user.id} not found for tenant {tenant_id}")

        db_user.email = user.email.strip().lower()
        db_user.display_name = user.display_name
        db_user.password_hash = user.password_hash
        db_user.role = user.role
        db_user.ui_language = user.ui_language
        db_user.mfa_secret_enc = user.mfa_secret_enc
        db_user.active = user.active
        db_user.failed_logins = user.failed_logins
        db_user.locked_until = user.locked_until

        self._session.commit()
        self._session.refresh(db_user)
        return _to_record(db_user)

    def record_failed_login(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        locked_until: datetime.datetime | None = None,
    ) -> None:
        db_user = (
            self._session.query(UserModel)
            .filter(
                UserModel.id == user_id,
                UserModel.tenant_id == tenant_id,
            )
            .first()
        )
        if db_user:
            db_user.failed_logins += 1
            if locked_until:
                db_user.locked_until = locked_until
            self._session.commit()

    def reset_failed_logins(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        db_user = (
            self._session.query(UserModel)
            .filter(
                UserModel.id == user_id,
                UserModel.tenant_id == tenant_id,
            )
            .first()
        )
        if db_user:
            db_user.failed_logins = 0
            db_user.locked_until = None
            self._session.commit()

    def list_all(self, tenant_id: uuid.UUID) -> list[UserRecord]:
        models = (
            self._session.query(UserModel)
            .filter(UserModel.tenant_id == tenant_id)
            .all()
        )
        return [_to_record(m) for m in models]
