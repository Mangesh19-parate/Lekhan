"""PostgreSQL adapter using SQLAlchemy 2.0 with strict RLS tenant context listeners."""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)

settings = get_settings()

# ContextVar tracking the active tenant ID for RLS enforcement across transactions
current_tenant_id_ctx: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)


def set_current_tenant_id(tenant_id: uuid.UUID | None) -> contextvars.Token[uuid.UUID | None]:
    """Sets the active tenant ID for the current context."""
    return current_tenant_id_ctx.set(tenant_id)


def get_current_tenant_id() -> uuid.UUID | None:
    """Gets the active tenant ID from the current context."""
    return current_tenant_id_ctx.get()


# Engine configuration: prefer APP_DATABASE_URL (lekhan_app role) for application runtime
db_url = settings.APP_DATABASE_URL or settings.DATABASE_URL
connect_args = {"connect_timeout": 2} if "psycopg" in db_url else {}

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@event.listens_for(Session, "after_begin")
def _set_tenant_id_on_begin(session: Session, transaction: Any, connection: Connection) -> None:
    """Sets app.tenant_id on PostgreSQL connection at the start of EVERY transaction.

    Failure to set it raises immediately (never swallowed), guaranteeing no-context
    queries return zero rows under RLS.
    """
    if connection.dialect.name == "postgresql":
        tid = current_tenant_id_ctx.get()
        if tid is not None:
            connection.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tid)})
        else:
            connection.execute(text("RESET app.tenant_id"))


def set_tenant_context(session: Session, tenant_id: uuid.UUID | None) -> None:
    """Sets PostgreSQL session setting app.tenant_id for RLS enforcement; raises on failure."""
    current_tenant_id_ctx.set(tenant_id)
    bind = session.get_bind()
    if bind and bind.dialect.name == "postgresql":
        if tenant_id is not None:
            session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        else:
            session.execute(text("RESET app.tenant_id"))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    token = current_tenant_id_ctx.set(None)
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        try:
            current_tenant_id_ctx.reset(token)
        except ValueError:
            current_tenant_id_ctx.set(None)


def ping_db() -> bool:
    """Executes a lightweight query to verify PostgreSQL connectivity."""
    if settings.is_test:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, OSError) as exc:
        logger.warning(
            "Database ping failed [cid=%s]: %s",
            get_correlation_id(),
            exc,
        )
        return False
