"""Enable PostgreSQL Row-Level Security (RLS) keyed on app.tenant_id.

Revision ID: 0006_enable_rls
Revises: 0005_audit_log_append_only
Create Date: 2026-11-13 21:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006_enable_rls"
down_revision: Union[str, None] = "0005_audit_log_append_only"
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
]


def upgrade() -> None:
    # 1. Enable and Force RLS on all tenant-scoped tables
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
            """
        )

    # 2. Templates table: allow platform templates (NULL tenant_id) or tenant-specific templates
    op.execute("ALTER TABLE templates ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE templates FORCE ROW LEVEL SECURITY;")
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


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON templates;")
    op.execute("ALTER TABLE templates NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE templates DISABLE ROW LEVEL SECURITY;")

    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
