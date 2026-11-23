"""Create SECURITY DEFINER function for cross-tenant job claiming under least-privilege RLS.

Revision ID: 0014_worker_job_claiming_function
Revises: 0013_document_reviews_and_drafts_rls
Create Date: 2026-11-22 19:45:00.000000

"""

import os
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "0014_worker_job_claiming_function"
down_revision: Union[str, None] = "0013_document_reviews_and_drafts_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Synchronize lekhan_app password from environment or secret file if present
    secrets_dir = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))
    app_pw_file = secrets_dir / "app_db_password"
    app_password = None
    if app_pw_file.is_file():
        app_password = app_pw_file.read_text(encoding="utf-8").strip()
    elif "LEKHAN_APP_PASSWORD" in os.environ:
        app_password = os.environ["LEKHAN_APP_PASSWORD"]

    if app_password:
        escaped_pw = app_password.replace("'", "''")
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                    EXECUTE format('ALTER ROLE lekhan_app WITH PASSWORD %L', '{escaped_pw}');
                END IF;
            END
            $$;
            """
        )

    # 2. Create SECURITY DEFINER function for atomic, least-privilege cross-tenant job claiming
    op.execute(
        """
        CREATE OR REPLACE FUNCTION claim_next_job(
            p_visibility_timeout_seconds integer DEFAULT 300,
            p_max_attempts integer DEFAULT 3
        )
        RETURNS TABLE (
            id uuid,
            tenant_id uuid,
            type text,
            payload jsonb,
            status text,
            state text,
            run_at timestamp with time zone,
            attempts integer,
            locked_at timestamp with time zone,
            idempotency_key text,
            error jsonb,
            created_at timestamp with time zone
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
            v_now timestamp with time zone := clock_timestamp();
            v_cutoff timestamp with time zone := v_now - (p_visibility_timeout_seconds || ' seconds')::interval;
            v_job_id uuid;
        BEGIN
            -- 1. Dead-letter stale jobs that crashed and exceeded max attempts
            UPDATE jobs
            SET status = 'dead',
                error = jsonb_build_object(
                    'code', 'MAX_ATTEMPTS_EXCEEDED',
                    'message', 'Job exceeded maximum retry attempts during background execution'
                )
            WHERE status = 'running'
              AND locked_at <= v_cutoff
              AND attempts >= p_max_attempts;

            -- 2. Atomically find and lock the next eligible job across tenants
            SELECT j.id INTO v_job_id
            FROM jobs j
            WHERE (
                (j.status = 'queued' AND j.run_at <= v_now AND j.attempts < p_max_attempts)
                OR
                (j.status = 'running' AND j.locked_at <= v_cutoff AND j.attempts < p_max_attempts)
            )
            ORDER BY j.run_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1;

            IF v_job_id IS NULL THEN
                RETURN;
            END IF;

            -- 3. Transition to running, increment attempts, and update locked_at
            RETURN QUERY
            UPDATE jobs
            SET status = 'running',
                locked_at = v_now,
                attempts = jobs.attempts + 1
            WHERE jobs.id = v_job_id
            RETURNING
                jobs.id,
                jobs.tenant_id,
                jobs.type,
                jobs.payload,
                jobs.status,
                jobs.state,
                jobs.run_at,
                jobs.attempts,
                jobs.locked_at,
                jobs.idempotency_key,
                jobs.error,
                jobs.created_at;
        END;
        $$;
        """
    )

    op.execute("REVOKE ALL ON FUNCTION claim_next_job(integer, integer) FROM PUBLIC;")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                GRANT EXECUTE ON FUNCTION claim_next_job(integer, integer) TO lekhan_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS claim_next_job(integer, integer);")
