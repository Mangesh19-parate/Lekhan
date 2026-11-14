"""Audit log append-only triggers and revoke mutation grants.

Revision ID: 0005_audit_log_append_only
Revises: 0004_templates_and_jobs
Create Date: 2026-11-13 20:55:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005_audit_log_append_only"
down_revision: Union[str, None] = "0004_templates_and_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PostgreSQL Trigger Function preventing UPDATE or DELETE on audit_log
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE operations are prohibited';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    # 2. Attach trigger on audit_log
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log;
        CREATE TRIGGER trg_audit_log_append_only
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )
    # 3. Revoke UPDATE, DELETE, and TRUNCATE grants from PUBLIC
    op.execute(
        """
        DO $$
        BEGIN
            REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM PUBLIC;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation();")

