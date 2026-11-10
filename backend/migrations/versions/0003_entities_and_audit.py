"""Entities and audit schema: parties, properties, matters, and hash-chained audit log.

Revision ID: 0003_entities_and_audit
Revises: 0002_auth_and_sessions
Create Date: 2026-11-09 20:20:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_entities_and_audit"
down_revision: Union[str, None] = "0002_auth_and_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PARTIES Table
    op.create_table(
        "parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("gender", sa.String(length=16), nullable=True),
        sa.Column("marital_status", sa.String(length=32), nullable=True),
        sa.Column("age_or_dob", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("names", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("occupations", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("addresses", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("contact_enc", sa.LargeBinary(), nullable=True),
        sa.Column("pan_enc", sa.LargeBinary(), nullable=True),
        sa.Column("pan_blind_index", sa.LargeBinary(), nullable=True),
        sa.Column("id_type", sa.String(length=32), nullable=True),
        sa.Column("id_enc", sa.LargeBinary(), nullable=True),
        sa.Column("id_blind_index", sa.LargeBinary(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("kind IN ('individual','company','firm','society')", name="chk_party_kind"),
        sa.CheckConstraint("gender IS NULL OR gender IN ('male','female','other')", name="chk_party_gender"),
    )
    op.create_index("ix_parties_tenant_id", "parties", ["tenant_id"])
    op.create_index("ix_parties_deleted_at", "parties", ["deleted_at"])

    # 2. PARTY_VERSIONS Table
    op.create_table(
        "party_versions",
        sa.Column("party_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("version", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. PROPERTIES Table
    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("area_value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("area_unit", sa.String(length=16), nullable=True),
        sa.Column("boundaries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rr_division", sa.String(length=64), nullable=True),
        sa.Column("rr_rate", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("category IN ('plot','flat','shop','agri','house_on_plot')", name="chk_property_category"),
        sa.CheckConstraint("area_unit IS NULL OR area_unit IN ('sqm','sqft','hectare_r','guntha','acre')", name="chk_property_area_unit"),
    )
    op.create_index("ix_properties_tenant_id", "properties", ["tenant_id"])
    op.create_index("ix_properties_deleted_at", "properties", ["deleted_at"])

    # 4. MATTERS Table
    op.create_table(
        "matters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("matter_no", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="open", nullable=False),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "matter_no", name="uq_matters_tenant_matter_no"),
        sa.CheckConstraint("status IN ('open','closed')", name="chk_matter_status"),
    )
    op.create_index("ix_matters_tenant_id", "matters", ["tenant_id"])

    # 5. MATTER_PARTIES Table
    op.create_table(
        "matter_parties",
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("party_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("role", sa.String(length=32), primary_key=True, nullable=False),
    )

    # 6. AUDIT_LOG Table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("prev_hash", sa.LargeBinary(length=32), nullable=True),
        sa.Column("hash", sa.LargeBinary(length=32), nullable=False),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_log_at", "audit_log", ["at"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("matter_parties")
    op.drop_table("matters")
    op.drop_table("properties")
    op.drop_table("party_versions")
    op.drop_table("parties")

