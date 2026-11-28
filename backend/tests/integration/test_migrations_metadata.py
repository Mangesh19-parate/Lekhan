"""Integration test: compare Alembic migrations to SQLAlchemy models.

Verifies:
1. `alembic upgrade head` runs cleanly on PostgreSQL 16.
2. `compare_metadata` reports zero drift between migrations and `app.shared.models.Base.metadata`.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Generator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.shared.models import Base

ALEMBIC_INI_PATH = Path(__file__).parent.parent.parent / "alembic.ini"


def _build_alembic_config(db_url: str, schema: str | None = None) -> Config:
    """Builds an Alembic Config instance pointing to the test database and migrations."""
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(ALEMBIC_INI_PATH.parent / "migrations"))
    if schema:
        cfg.set_main_option("version_table_schema", schema)
    return cfg


@pytest.fixture(scope="module")
def throwaway_postgres_engine() -> Generator[tuple[Engine, str | None], None, None]:
    """Provides a connection to a throwaway PostgreSQL 16 database or schema."""
    test_db_url = os.getenv("TEST_DATABASE_URL")
    container = None

    if test_db_url:
        engine = create_engine(test_db_url)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            pytest.skip(f"TEST_DATABASE_URL unreachable: {exc}")
        yield engine, None
        return

    # Attempt testcontainers if available
    try:
        from testcontainers.postgres import PostgresContainer  # type: ignore[import-not-found]

        container = PostgresContainer("postgres:16")
        container.start()
        engine = create_engine(container.get_connection_url())
        yield engine, None
        container.stop()
        return
    except Exception:
        pass

    # Fall back to local docker compose dev postgres on localhost:5432
    settings = get_settings()
    try:
        base_engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"connect_timeout": 2},
        )
        # Test basic connectivity
        with base_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(
            f"Postgres 16 not reachable (neither testcontainers nor docker compose available): {exc}"
        )
        return

    # Create an isolated throwaway schema for this test module run
    schema_name = f"test_migration_{uuid.uuid4().hex[:8]}"
    with base_engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        conn.commit()

    # Create engine configured with search_path set to throwaway schema
    schema_url = f"{settings.DATABASE_URL}?options=-csearch_path%3D{schema_name}"
    schema_engine = create_engine(schema_url)

    try:
        yield schema_engine, schema_name
    finally:
        with base_engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            conn.commit()


def test_migrations_compare_metadata_zero_diff(
    throwaway_postgres_engine: tuple[Engine, str | None],
) -> None:
    """Runs alembic upgrade head on Postgres 16 and asserts compare_metadata has zero diff."""
    engine, schema = throwaway_postgres_engine
    db_url = str(engine.url)

    # 1. Run migrations to head
    cfg = _build_alembic_config(db_url=db_url, schema=schema)
    command.upgrade(cfg, "head")

    # 2. Compare migrated database against Base.metadata
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn,
            opts={
                "compare_type": True,
                "compare_server_default": True,
            },
        )
        diff = compare_metadata(ctx, Base.metadata)

    # 3. Assert zero schema drift
    assert diff == [], f"Alembic migration drift detected between models and DB:\n{diff}"
