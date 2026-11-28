"""Create drafts table for in-progress drafting sessions.

Revision ID: 0012_drafts
Revises: 0011_fee_rules
Create Date: 2026-11-15 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_drafts"
down_revision: Union[str, None] = "0011_fee_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False, server_default="Untitled Draft"),
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column(
            "data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index("ix_drafts_tenant_id", "drafts", ["tenant_id"])
    op.create_index("ix_drafts_tenant_updated", "drafts", ["tenant_id", "updated_at"])
    op.create_index("ix_drafts_user_id", "drafts", ["user_id"])

    # Grant permissions to lekhan_app
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON drafts TO lekhan_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("drafts")
