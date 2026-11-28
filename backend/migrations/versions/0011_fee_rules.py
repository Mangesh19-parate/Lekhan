"""Statutory fee rules for stamp duty and registration fee calculations.

Revision ID: 0011_fee_rules
Revises: 0010_rls_roles_and_functions
Create Date: 2026-11-14 13:51:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_fee_rules"
down_revision: Union[str, None] = "0010_rls_roles_and_functions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create fee_rules table
    op.create_table(
        "fee_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("jurisdiction", sa.String(64), nullable=False),
        sa.Column("instrument", sa.String(64), nullable=False),
        sa.Column("rate", sa.Numeric(10, 4), nullable=False),
        sa.Column("cap", sa.Numeric(14, 2), nullable=True),
        sa.Column("concession", sa.Numeric(10, 4), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("verified_by", sa.String(128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(512), nullable=True),
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

    # 2. Indexes for fast date and jurisdiction/instrument lookups
    op.create_index(
        "ix_fee_rules_lookup",
        "fee_rules",
        ["jurisdiction", "instrument", "effective_from"],
    )

    # 3. Grant SELECT on fee_rules to the unprivileged app role
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                GRANT SELECT ON fee_rules TO lekhan_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_fee_rules_lookup", "fee_rules")
    op.drop_table("fee_rules")
