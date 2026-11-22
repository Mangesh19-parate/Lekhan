"""Hardened Row-Level Security: lekhan_app role, WITH CHECK policies, and pre-auth SECURITY DEFINER functions.

Revision ID: 0010_rls_roles_and_functions
Revises: 0009_mfa_hardening
Create Date: 2026-11-14 13:38:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0010_rls_roles_and_functions"
down_revision: Union[str, None] = "0009_mfa_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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


def upgrade() -> None:
    # 1. Create the non-privileged application role if it doesn't already exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                CREATE ROLE lekhan_app WITH
                    NOSUPERUSER
                    NOCREATEDB
                    NOCREATEROLE
                    NOBYPASSRLS
                    LOGIN
                    PASSWORD 'lekhan_app_dev_password';
            END IF;
        END
        $$;
        """
    )

    # 2. Grant connection and schema usage
    op.execute("GRANT CONNECT ON DATABASE lekhan_db TO lekhan_app;")
    op.execute("GRANT USAGE ON SCHEMA public TO lekhan_app;")

    # 3. Grant DML permissions on existing and future tables
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lekhan_app;")
    # Audit log is strictly append-only (docs/DATABASE.md Section 6)
    op.execute("REVOKE UPDATE, DELETE ON audit_log FROM lekhan_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lekhan_app;")

    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lekhan_app;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO lekhan_app;"
    )

    # 4. Enforce RLS with both USING and WITH CHECK on all tenant tables
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
            """
        )

    # 5. Templates table policy (allow platform templates with NULL tenant_id or matching tenant)
    op.execute("ALTER TABLE templates ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE templates FORCE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON templates;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON templates
        FOR ALL
        USING (
            tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        );
        """
    )

    # 6. Pre-auth lookup functions: SECURITY DEFINER with fixed search_path to prevent hijacking
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_lookup_user_by_email(p_email text)
        RETURNS TABLE (
            id uuid,
            tenant_id uuid,
            email text,
            display_name text,
            password_hash text,
            role text,
            ui_language text,
            mfa_secret_enc bytea,
            mfa_recovery_codes jsonb,
            active boolean,
            failed_logins integer,
            locked_until timestamp with time zone,
            created_at timestamp with time zone
        )
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT
                u.id,
                u.tenant_id,
                u.email,
                u.display_name,
                u.password_hash,
                u.role,
                u.ui_language,
                u.mfa_secret_enc,
                u.mfa_recovery_codes,
                u.active,
                u.failed_logins,
                u.locked_until,
                u.created_at
            FROM users u
            WHERE lower(u.email) = lower(trim(p_email))
            LIMIT 1;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_user_by_email(text) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_user_by_email(text) TO lekhan_app;")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_lookup_session_by_hash(p_id_hash bytea)
        RETURNS TABLE (
            id_hash bytea,
            user_id uuid,
            tenant_id uuid,
            csrf_token_hash bytea,
            created_at timestamp with time zone,
            last_seen_at timestamp with time zone,
            expires_at timestamp with time zone,
            user_agent text,
            ip text,
            mfa_pending boolean
        )
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT
                s.id_hash,
                s.user_id,
                s.tenant_id,
                s.csrf_token_hash,
                s.created_at,
                s.last_seen_at,
                s.expires_at,
                s.user_agent,
                s.ip,
                s.mfa_pending
            FROM sessions s
            WHERE s.id_hash = p_id_hash
            LIMIT 1;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_session_by_hash(bytea) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_session_by_hash(bytea) TO lekhan_app;")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_session_by_hash(bytea);")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_user_by_email(text);")

    # Revert policies back to USING-only
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
            """
        )

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON templates;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON templates
        USING (
            tenant_id IS NULL
            OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        );
        """
    )

    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM lekhan_app;")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM lekhan_app;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM lekhan_app;")
    op.execute("REVOKE CONNECT ON DATABASE lekhan_db FROM lekhan_app;")
    op.execute("DROP ROLE IF EXISTS lekhan_app;")
