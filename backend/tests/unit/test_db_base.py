"""Unit tests for SQLAlchemy models, mixins, and UUIDv7 defaults."""

from app.shared.models import Tenant


def test_tenant_model_instantiation() -> None:
    """Verifies Tenant entity defaults and field mappings."""
    tenant = Tenant(name="Nagpur Legal Associates")
    assert tenant.name == "Nagpur Legal Associates"
    assert tenant.settings == {}
    assert tenant.feature_flags == {}
