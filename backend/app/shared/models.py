"""SQLAlchemy 2.0 declarative base and architectural mixins.

Adheres strictly to docs/DATABASE.md conventions:
- UUIDv7 primary keys
- Enforced tenant_id
- UTC timestamps
- Soft deletion support (deleted_at)
- Optimistic locking (version integer)
- Exact Decimal money (numeric(18,2)) and area (numeric(18,4))
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.shared.ids import uuid7


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy entities."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class UUIDv7PKMixin:
    """Primary key mixin using time-ordered UUIDv7."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        sort_order=-10,
    )


class TenantScopedMixin:
    """Enforces tenant isolation on every domain table (AGENTS.md rule 6)."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        sort_order=-9,
    )


class TimestampMixin:
    """UTC creation, update, and soft-delete timestamps."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )


class VersionedMixin:
    """Optimistic locking version counter."""

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


# --- Core Organization & Auth Entities ---

class Tenant(Base, UUIDv7PKMixin):
    """Tenant organization entity."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    feature_flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    users: Mapped[list[User]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class User(Base, UUIDv7PKMixin, TenantScopedMixin):
    """User account entity with role-based access control."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        CheckConstraint("role IN ('admin','template_admin','reviewer','drafter')", name="chk_user_role"),
        CheckConstraint("ui_language IN ('en','mr','hi')", name="chk_user_ui_language"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="drafter", nullable=False)
    ui_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    mfa_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")
    sessions: Mapped[list[Session]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Server-side session storage (docs/AUTH.md Section 3)."""

    __tablename__ = "sessions"

    id_hash: Mapped[bytes] = mapped_column(LargeBinary(32), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    csrf_token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="sessions")


# --- Entities: Parties, Properties, Matters, Audit (docs/DATABASE.md) ---

class Party(Base, UUIDv7PKMixin, TenantScopedMixin, TimestampMixin, VersionedMixin):
    """Party entity storing names and addresses per language (never auto-transliterated)."""

    __tablename__ = "parties"
    __table_args__ = (
        CheckConstraint("kind IN ('individual','company','firm','society')", name="chk_party_kind"),
        CheckConstraint("gender IS NULL OR gender IN ('male','female','other')", name="chk_party_gender"),
    )

    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    age_or_dob: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    names: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    occupations: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    addresses: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    contact_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    pan_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    pan_blind_index: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, index=True)
    id_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    id_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    id_blind_index: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    versions: Mapped[list[PartyVersion]] = relationship("PartyVersion", back_populates="party", cascade="all, delete-orphan")


class PartyVersion(Base):
    """Immutable audit trail of past party revisions."""

    __tablename__ = "party_versions"

    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parties.id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    party: Mapped[Party] = relationship("Party", back_populates="versions")


class Property(Base, UUIDv7PKMixin, TenantScopedMixin, VersionedMixin):
    """Property entity (plots, flats, shops, agricultural land)."""

    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint("category IN ('plot','flat','shop','agri','house_on_plot')", name="chk_property_category"),
        CheckConstraint("area_unit IS NULL OR area_unit IN ('sqm','sqft','hectare_r','guntha','acre')", name="chk_property_area_unit"),
    )

    category: Mapped[str] = mapped_column(String(32), nullable=False)
    attrs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    area_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    area_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    boundaries: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    rr_division: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rr_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Matter(Base, UUIDv7PKMixin, TenantScopedMixin):
    """Legal drafting matter / file container."""

    __tablename__ = "matters"
    __table_args__ = (
        UniqueConstraint("tenant_id", "matter_no", name="uq_matters_tenant_matter_no"),
        CheckConstraint("status IN ('open','closed')", name="chk_matter_status"),
    )

    matter_no: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    parties: Mapped[list[MatterParty]] = relationship("MatterParty", back_populates="matter", cascade="all, delete-orphan")


class MatterParty(Base):
    """Associates parties with matters under specific transaction roles."""

    __tablename__ = "matter_parties"

    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parties.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(32), primary_key=True)

    matter: Mapped[Matter] = relationship("Matter", back_populates="parties")
    party: Mapped[Party] = relationship("Party")


class AuditLog(Base):
    """Append-only audit trail with cryptographic SHA-256 hash chaining."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    prev_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32), nullable=True)
    hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)


# --- Week 7 Entities: Templates, TemplateVersions, Documents, Jobs, Counters ---

class Template(Base, UUIDv7PKMixin):
    """Template header (metadata). May belong to a tenant or platform library (NULL tenant_id)."""

    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "doc_type", "property_category", "language", "name", name="uq_templates_identity"),
        CheckConstraint("language IN ('mr','en','hi')", name="chk_template_language"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    property_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    versions: Mapped[list[TemplateVersion]] = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")


class TemplateVersion(Base, UUIDv7PKMixin):
    """Immutable template revision. Once status is approved, it cannot be modified."""

    __tablename__ = "template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_template_version"),
        CheckConstraint("status IN ('draft','under_review','approved','retired')", name="chk_template_version_status"),
        CheckConstraint("status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)", name="chk_approved_requires_approver"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_schema: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    compiled_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    file_sha256: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    lint_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    template: Mapped[Template] = relationship("Template", back_populates="versions")


class Document(Base, UUIDv7PKMixin, TenantScopedMixin, VersionedMixin):
    """Drafted legal deed record produced by the generation pipeline."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "doc_no", name="uq_documents_tenant_doc_no"),
        CheckConstraint("status IN ('draft','reviewed','finalised')", name="chk_document_status"),
    )

    matter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=True)
    template_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("template_versions.id"), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), default="0.1.0", nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    doc_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    input_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32), nullable=True)
    output_hash: Mapped[bytes | None] = mapped_column(LargeBinary(32), nullable=True)
    docx_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Job(Base, UUIDv7PKMixin, TenantScopedMixin):
    """PostgreSQL background job queue (FOR UPDATE SKIP LOCKED)."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_jobs_tenant_idempotency"),
        CheckConstraint("status IN ('queued','running','succeeded','failed','dead')", name="chk_job_status"),
    )

    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    run_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Counter(Base):
    """Gap-free sequence counter per tenant and year."""

    __tablename__ = "counters"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
