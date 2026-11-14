"""Add rate_limits table for database-backed distributed throttling.

Revision ID: 0007_rate_limits
Revises: 0006_enable_rls
Create Date: 2026-11-13 21:12:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_rate_limits"
down_revision: Union[str, None] = "0006_enable_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rate_limits",
        sa.Column("key", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column(
            "timestamps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("consecutive_failures", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_until", sa.Numeric(precision=18, scale=4), server_default=sa.text("0.0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("rate_limits")

