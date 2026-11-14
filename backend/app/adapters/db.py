"""PostgreSQL adapter using SQLAlchemy 2.0."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)

settings = get_settings()

# Engine configuration (connection pooling with recycling and fast failover timeout)
connect_args = {"connect_timeout": 2} if "psycopg" in settings.DATABASE_URL else {}
engine = create_engine(
    settings.DATABASE_URL,
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


def set_tenant_context(session: Session, tenant_id: uuid.UUID | None) -> None:
    """Sets local PostgreSQL session setting app.tenant_id for RLS enforcement."""
    try:
        bind = session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            if tenant_id is not None:
                session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
            else:
                session.execute(text("RESET app.tenant_id"))
    except Exception as exc:
        logger.debug("Could not set local app.tenant_id context: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
