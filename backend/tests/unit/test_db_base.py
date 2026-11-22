"""Unit tests for SQLAlchemy models, mixins, and UUIDv7 defaults."""

from sqlalchemy.orm import configure_mappers

from app.shared.models import Tenant, User, Document, Base


def test_configure_mappers_relationships() -> None:
    """Verifies that all model mappers configure without NoForeignKeysError."""
    # Calling configure_mappers compiles all model relationships (e.g. Tenant.users).
    # If ForeignKey('tenants.id') is missing from TenantScopedMixin or User, this raises NoForeignKeysError.
    configure_mappers()


def test_tenant_model_instantiation() -> None:
    """Verifies Tenant entity defaults and field mappings."""
    tenant = Tenant(name="Nagpur Legal Associates")
    assert tenant.name == "Nagpur Legal Associates"
    assert tenant.settings == {}
    assert tenant.feature_flags == {}


def test_document_file_ref_compatibility() -> None:
    """Verifies Document.file_ref synonym works for both keyword args and property access."""
    from app.shared.ids import uuid7

    t_id = uuid7()
    tv_id = uuid7()
    doc = Document(
        tenant_id=t_id,
        template_version_id=tv_id,
        language="mr",
        data_snapshot={},
        file_ref="documents/sample.docx",
    )
    assert doc.file_ref == "documents/sample.docx"
    assert doc.docx_ref == "documents/sample.docx"

    doc.file_ref = "documents/updated.docx"
    assert doc.file_ref == "documents/updated.docx"
    assert doc.docx_ref == "documents/updated.docx"


