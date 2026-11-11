"""PostgreSQL adapter using SQLAlchemy 2.0."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Engine configuration (connection pooling with recycling and fast failover timeout)
connect_args = {"connect_timeout": 2} if "psycopg" in settings.DATABASE_URL else {}
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


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
    except Exception as exc:
        logger.warning("Database ping failed: %s", exc)
        return False
