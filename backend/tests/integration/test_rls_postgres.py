"""Real PostgreSQL integration tests for Row-Level Security (RLS) under the unprivileged `lekhan_app` role.

Verifies against PostgreSQL 16 (CI service container / local postgres):
1. The `lekhan_app` role has NOSUPERUSER and NOBYPASSRLS.
2. No-context queries (app.tenant_id unset or RESET) return zero rows across all tenant tables.
3. Tenant A can only read Tenant A rows; Tenant B rows are completely invisible.
4. Tenant A cannot UPDATE Tenant B rows (0 rows affected).
5. Tenant A cannot INSERT rows for Tenant B (fails with WITH CHECK policy violation).
6. Pre-auth SECURITY DEFINER functions (auth_lookup_user_by_email, auth_lookup_session_by_hash)
   work without tenant context, while direct table SELECTs return zero rows.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError

from app.config import get_settings
from app.shared.ids import uuid7

settings = get_settings()

ALEMBIC_INI_PATH = Path(__file__).parent.parent.parent / "alembic.ini"
TENANT_A = uuid.UUID("0193132e-504f-7a1b-8000-00000000000a")
TENANT_B = uuid.UUID("0193132e-504f-7a1b-8000-00000000000b")

TENANT_TABLES = [
    "parties",
    "properties",
    "matters",
    "documents",
    "jobs",
    "audit_log",
    "sessions",
    "users",
    "counters",
    "template_versions",
]


@pytest.fixture(scope="module")
def postgres_engine() -> Generator[Engine, None, None]:
    """Provides a connection to PostgreSQL 16 with migrations applied at head."""
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or settings.DATABASE_URL
    if "sqlite" in db_url:
        pytest.skip("PostgreSQL required for real RLS tests")

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL 16 database unreachable: {exc}")

    # Ensure all migrations are applied
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(ALEMBIC_INI_PATH.parent / "migrations"))
    command.upgrade(cfg, "head")

    yield engine


@pytest.fixture(scope="module")
def seeded_tenants(postgres_engine: Engine) -> dict[str, Any]:
    """Seeds test tenants and rows for Tenant A and Tenant B."""
    with postgres_engine.begin() as conn:
        # Create Tenants
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, name, slug, tier)
                VALUES
                    (:ta, 'Tenant Alpha Law', 'tenant-alpha', 'standard'),
                    (:tb, 'Tenant Beta Law', 'tenant-beta', 'standard')
                ON CONFLICT (id) DO NOTHING;
                """
            ),
            {"ta": TENANT_A, "tb": TENANT_B},
        )

        # Seed rows for Tenant A and Tenant B across tenant tables
        party_a_id = uuid7()
        party_b_id = uuid7()
        conn.execute(
            text(
                """
                INSERT INTO parties (id, tenant_id, kind, names, occupations, addresses)
                VALUES
                    (:pa, :ta, 'individual', '{"en": "Client Alpha"}', '{}', '{}'),
                    (:pb, :tb, 'individual', '{"en": "Client Beta"}', '{}', '{}')
                ON CONFLICT (id) DO NOTHING;
                """
            ),
            {"pa": party_a_id, "ta": TENANT_A, "pb": party_b_id, "tb": TENANT_B},
        )

        user_a_id = uuid7()
        user_b_id = uuid7()
        conn.execute(
            text(
                """
                INSERT INTO users (id, tenant_id, email, display_name, password_hash, role)
                VALUES
                    (:ua, :ta, 'drafter.a@alpha.local', 'Drafter Alpha', 'hash_a', 'drafter'),
                    (:ub, :tb, 'drafter.b@beta.local', 'Drafter Beta', 'hash_b', 'drafter')
                ON CONFLICT (id) DO NOTHING;
                """
            ),
            {"ua": user_a_id, "ta": TENANT_A, "ub": user_b_id, "tb": TENANT_B},
        )

        session_hash_a = b"hash_session_alpha_32bytes_1234"
        session_hash_b = b"hash_session_beta_32bytes_12345"
        now = "2026-11-14 12:00:00+00"
        conn.execute(
            text(
                """
                INSERT INTO sessions (id_hash, user_id, tenant_id, csrf_token_hash, created_at, last_seen_at, expires_at)
                VALUES
                    (:sa, :ua, :ta, :csrf_a, :now, :now, '2026-11-14 18:00:00+00'),
                    (:sb, :ub, :tb, :csrf_b, :now, :now, '2026-11-14 18:00:00+00')
                ON CONFLICT (id_hash) DO NOTHING;
                """
            ),
            {
                "sa": session_hash_a,
                "ua": user_a_id,
                "ta": TENANT_A,
                "csrf_a": b"csrf_a_32bytes_random_hash_1234",
                "sb": session_hash_b,
                "ub": user_b_id,
                "tb": TENANT_B,
                "csrf_b": b"csrf_b_32bytes_random_hash_1234",
                "now": now,
            },
        )

        doc_a_id = uuid7()
        doc_b_id = uuid7()
        conn.execute(
            text(
                """
                INSERT INTO documents (id, tenant_id, doc_no, language, engine_version, template_id, status, file_ref, data_snapshot)
                VALUES
                    (:da, :ta, 'DOC/A/001', 'mr', '1.0', 'plot_sale_deed', 'draft', 'ref/a.docx', '{}'),
                    (:db, :tb, 'DOC/B/001', 'mr', '1.0', 'plot_sale_deed', 'draft', 'ref/b.docx', '{}')
                ON CONFLICT (id) DO NOTHING;
                """
            ),
            {"da": doc_a_id, "ta": TENANT_A, "db": doc_b_id, "tb": TENANT_B},
        )

    return {
        "party_a_id": party_a_id,
        "party_b_id": party_b_id,
        "user_a_email": "drafter.a@alpha.local",
        "user_b_email": "drafter.b@beta.local",
        "session_hash_a": session_hash_a,
        "session_hash_b": session_hash_b,
        "doc_a_id": doc_a_id,
        "doc_b_id": doc_b_id,
    }


def test_lekhan_app_role_has_nobypassrls(postgres_engine: Engine) -> None:
    """Verifies that the application role lekhan_app is NOSUPERUSER and NOBYPASSRLS."""
    with postgres_engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT rolname, rolsuper, rolbypassrls
                FROM pg_catalog.pg_roles
                WHERE rolname = 'lekhan_app';
                """
                )
            )
            .mappings()
            .first()
        )

        assert row is not None, "lekhan_app role must exist"
        assert row["rolsuper"] is False, "lekhan_app must be NOSUPERUSER"
        assert row["rolbypassrls"] is False, "lekhan_app must be NOBYPASSRLS"


def test_no_context_queries_return_zero_rows_under_rls(
    postgres_engine: Engine, seeded_tenants: dict[str, Any]
) -> None:
    """Verifies that when app.tenant_id is not set, queries under lekhan_app return zero rows."""
    with postgres_engine.connect() as conn:
        conn.execute(text("SET ROLE lekhan_app;"))
        conn.execute(text("RESET app.tenant_id;"))

        # Check every tenant table
        for table in TENANT_TABLES:
            count = conn.execute(text(f"SELECT count(*) FROM {table};")).scalar()
            assert count == 0, f"Table {table} must return 0 rows when app.tenant_id is unset"


def test_tenant_a_isolation_and_cross_tenant_invisible(
    postgres_engine: Engine, seeded_tenants: dict[str, Any]
) -> None:
    """Verifies that Tenant A can only see and access Tenant A rows."""
    with postgres_engine.connect() as conn:
        conn.execute(text("SET ROLE lekhan_app;"))
        conn.execute(text("SET LOCAL app.tenant_id = :tid;"), {"tid": str(TENANT_A)})

        # 1. SELECT on parties returns Client Alpha and zero rows for Client Beta
        parties = conn.execute(text("SELECT id, tenant_id FROM parties;")).mappings().all()
        assert len(parties) == 1
        assert parties[0]["tenant_id"] == TENANT_A
        assert parties[0]["id"] == seeded_tenants["party_a_id"]

        # 2. SELECT on documents returns only Tenant A document
        docs = conn.execute(text("SELECT id, tenant_id FROM documents;")).mappings().all()
        assert len(docs) == 1
        assert docs[0]["tenant_id"] == TENANT_A
        assert docs[0]["id"] == seeded_tenants["doc_a_id"]

        # 3. SELECT on users returns only Tenant A user
        users = conn.execute(text("SELECT id, tenant_id, email FROM users;")).mappings().all()
        assert len(users) == 1
        assert users[0]["tenant_id"] == TENANT_A
        assert users[0]["email"] == seeded_tenants["user_a_email"]


def test_cross_tenant_update_blocked(
    postgres_engine: Engine, seeded_tenants: dict[str, Any]
) -> None:
    """Verifies that Tenant A cannot update Tenant B rows (0 rows affected)."""
    with postgres_engine.connect() as conn:
        conn.execute(text("SET ROLE lekhan_app;"))
        conn.execute(text("SET LOCAL app.tenant_id = :tid;"), {"tid": str(TENANT_A)})

        result = conn.execute(
            text("UPDATE parties SET kind = 'company' WHERE id = :pb;"),
            {"pb": seeded_tenants["party_b_id"]},
        )
        assert result.rowcount == 0, "Tenant A cannot update Tenant B rows"


def test_cross_tenant_insert_violates_with_check(
    postgres_engine: Engine, seeded_tenants: dict[str, Any]
) -> None:
    """Verifies that Tenant A attempting to INSERT a row with Tenant B tenant_id fails with RLS policy error."""
    with postgres_engine.connect() as conn:
        conn.execute(text("SET ROLE lekhan_app;"))
        conn.execute(text("SET LOCAL app.tenant_id = :tid;"), {"tid": str(TENANT_A)})

        with pytest.raises(DBAPIError) as exc_info:
            conn.execute(
                text(
                    """
                    INSERT INTO parties (id, tenant_id, kind, names, occupations, addresses)
                    VALUES (:id, :tb, 'individual', '{"en": "Rogue Party"}', '{}', '{}');
                    """
                ),
                {"id": uuid7(), "tb": TENANT_B},
            )
        assert "row-level security policy" in str(exc_info.value).lower()


def test_pre_auth_security_definer_lookups_succeed_without_tenant_context(
    postgres_engine: Engine, seeded_tenants: dict[str, Any]
) -> None:
    """Verifies auth_lookup_user_by_email and auth_lookup_session_by_hash work pre-auth without tenant context."""
    with postgres_engine.connect() as conn:
        conn.execute(text("SET ROLE lekhan_app;"))
        conn.execute(text("RESET app.tenant_id;"))

        # 1. Direct table SELECT returns 0 rows due to RLS
        direct_user = conn.execute(
            text("SELECT * FROM users WHERE email = :email;"),
            {"email": seeded_tenants["user_a_email"]},
        ).first()
        assert direct_user is None, "Direct table SELECT must return None under RLS with no context"

        direct_session = conn.execute(
            text("SELECT * FROM sessions WHERE id_hash = :hash;"),
            {"hash": seeded_tenants["session_hash_a"]},
        ).first()
        assert direct_session is None, (
            "Direct session SELECT must return None under RLS with no context"
        )

        # 2. Narrow SECURITY DEFINER functions succeed and return the records safely
        fn_user = (
            conn.execute(
                text("SELECT * FROM auth_lookup_user_by_email(:email);"),
                {"email": seeded_tenants["user_a_email"]},
            )
            .mappings()
            .first()
        )
        assert fn_user is not None
        assert fn_user["email"] == seeded_tenants["user_a_email"]
        assert fn_user["tenant_id"] == TENANT_A

        fn_session = (
            conn.execute(
                text("SELECT * FROM auth_lookup_session_by_hash(:hash);"),
                {"hash": seeded_tenants["session_hash_a"]},
            )
            .mappings()
            .first()
        )
        assert fn_session is not None
        assert fn_session["tenant_id"] == TENANT_A
        assert fn_session["id_hash"] == seeded_tenants["session_hash_a"]
