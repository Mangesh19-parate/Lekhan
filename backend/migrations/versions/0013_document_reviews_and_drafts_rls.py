"""Create document_reviews table and enable RLS on drafts and document_reviews.

Revision ID: 0013_document_reviews_and_drafts_rls
Revises: 0012_drafts
Create Date: 2026-11-22 14:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_document_reviews_and_drafts_rls"
down_revision: Union[str, None] = "0012_drafts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create document_reviews table
    op.create_table(
        "document_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("checklist", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalised_by", sa.String(128), nullable=True),
        sa.Column("finalised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "document_id", name="uq_doc_reviews_tenant_document"),
        sa.CheckConstraint("status IN ('draft','reviewed','finalised')", name="chk_review_status"),
    )

    op.create_index("ix_doc_reviews_tenant_doc", "document_reviews", ["tenant_id", "document_id"])

    # 2. Grant DML permissions to lekhan_app
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON document_reviews TO lekhan_app;
                GRANT SELECT, INSERT, UPDATE, DELETE ON drafts TO lekhan_app;
            END IF;
        END
        $$;
        """
    )

    # 3. Enforce Row-Level Security on both drafts and document_reviews
    for tbl in ("drafts", "document_reviews"):
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {tbl};")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {tbl}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
            """
        )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON document_reviews;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON drafts;")
    op.execute("ALTER TABLE drafts DISABLE ROW LEVEL SECURITY;")
    op.drop_table("document_reviews")
