"""Unit tests for PropertyRepository interfaces and multi-tenant isolation.

Fulfills AGENTS.md Hard Rule 6 (every query tenant-scoped) and verifies:
1. Protocol conformance of InMemoryPropertyRepository.
2. Tenant isolation on save, get, update, save_version, get_versions, list_all, search.
"""

import uuid
from decimal import Decimal

import pytest

from app.properties.models import PropertyRecord, PropertyVersionRecord
from app.properties.repository import InMemoryPropertyRepository, PropertyRepository

TENANT_1 = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_2 = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")


def test_property_repository_protocol_conformance() -> None:
    repo = InMemoryPropertyRepository()
    assert isinstance(repo, PropertyRepository)


def test_save_and_tenant_scoped_get() -> None:
    repo = InMemoryPropertyRepository()
    prop_id = uuid.uuid4()
    prop = PropertyRecord(
        id=prop_id,
        tenant_id=TENANT_1,
        category="plot",
        attrs={"mouza": "नागपूर", "khasra_no": "104/1"},
        area_value=Decimal("1500.00"),
        area_unit="sqft",
        boundaries={"east": "Road", "west": "Plot 105"},
        version=1,
    )
    repo.save(TENANT_1, prop)

    # Scoped to TENANT_1 returns property
    found = repo.get(TENANT_1, prop_id)
    assert found is not None
    assert found.attrs["mouza"] == "नागपूर"

    # Cross-tenant query returns None
    assert repo.get(TENANT_2, prop_id) is None


def test_save_mismatched_tenant_raises_value_error() -> None:
    repo = InMemoryPropertyRepository()
    prop = PropertyRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_1,
        category="flat",
        attrs={"flat_no": "201"},
    )
    with pytest.raises(ValueError):
        repo.save(TENANT_2, prop)


def test_update_tenant_isolation() -> None:
    repo = InMemoryPropertyRepository()
    prop_id = uuid.uuid4()
    prop = PropertyRecord(
        id=prop_id,
        tenant_id=TENANT_1,
        category="shop",
        attrs={"shop_no": "1"},
        version=1,
    )
    repo.save(TENANT_1, prop)

    prop.attrs = {"shop_no": "1-A"}
    # Cross-tenant update raises KeyError
    with pytest.raises(KeyError):
        repo.update(TENANT_2, prop)

    # Same-tenant update succeeds
    repo.update(TENANT_1, prop)
    updated = repo.get(TENANT_1, prop_id)
    assert updated is not None
    assert updated.attrs["shop_no"] == "1-A"


def test_save_and_get_versions_tenant_scoped() -> None:
    repo = InMemoryPropertyRepository()
    prop_id = uuid.uuid4()
    prop = PropertyRecord(
        id=prop_id,
        tenant_id=TENANT_1,
        category="plot",
        attrs={"layout": "A"},
        version=1,
    )
    repo.save(TENANT_1, prop)

    version_snap = PropertyVersionRecord(
        property_id=prop_id,
        version=1,
        data={"attrs": {"layout": "A"}},
    )

    # Save version under wrong tenant raises KeyError
    with pytest.raises(KeyError):
        repo.save_version(TENANT_2, version_snap)

    repo.save_version(TENANT_1, version_snap)

    # Get versions under wrong tenant returns empty
    assert repo.get_versions(TENANT_2, prop_id) == []

    # Get versions under correct tenant returns 1 snapshot
    vers = repo.get_versions(TENANT_1, prop_id)
    assert len(vers) == 1
    assert vers[0].version == 1


def test_search_and_list_all_tenant_scoped() -> None:
    repo = InMemoryPropertyRepository()
    p1 = PropertyRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_1,
        category="plot",
        attrs={"mouza": "Dharampeth"},
    )
    p2 = PropertyRecord(
        id=uuid.uuid4(),
        tenant_id=TENANT_2,
        category="plot",
        attrs={"mouza": "Dharampeth"},
    )
    repo.save(TENANT_1, p1)
    repo.save(TENANT_2, p2)

    # list_all respects tenant
    assert len(repo.list_all(TENANT_1)) == 1
    assert repo.list_all(TENANT_1)[0].id == p1.id
    assert len(repo.list_all(TENANT_2)) == 1
    assert repo.list_all(TENANT_2)[0].id == p2.id

    # search respects tenant
    matches1 = repo.search(TENANT_1, "Dharampeth")
    assert len(matches1) == 1
    assert matches1[0][0].id == p1.id
