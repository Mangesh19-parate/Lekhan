"""Unit tests for Week 6 domain entities, optimistic locking, and audit hash-chaining."""

import uuid
from decimal import Decimal
import pytest

from app.audit.service import audit_service
from app.matters.service import matter_service
from app.parties.service import party_service
from app.properties.service import property_service
from app.shared.concurrency import OptimisticLockError

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
ACTOR_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000010")


@pytest.fixture(autouse=True)
def clean_services() -> None:
    party_service.clear()
    property_service.clear()
    matter_service.clear()
    audit_service.clear()


# --- 1. Multi-Lingual Party Storage Tests ---

def test_party_multi_lingual_names_and_addresses() -> None:
    """Verifies that names and addresses are stored per script without auto-transliteration."""
    party = party_service.create_party(
        tenant_id=TENANT_ID,
        kind="individual",
        gender="male",
        names={
            "mr": {"full": "श्री. रमेश विठ्ठलराव पाटील", "father": "विठ्ठलराव पाटील"},
            "en": {"full": "Mr. Ramesh Vitthalrao Patil", "father": "Vitthalrao Patil"},
        },
        addresses={
            "mr": "प्लॉट क्र. २२, त्रिमूर्ती नगर, नागपूर",
            "en": "Plot No. 22, Trimurti Nagar, Nagpur",
        },
        pan_masked="ABCDE1234F",
        actor_id=ACTOR_ID,
    )

    assert party.version == 1
    assert party.names["mr"]["full"] == "श्री. रमेश विठ्ठलराव पाटील"
    assert party.names["en"]["full"] == "Mr. Ramesh Vitthalrao Patil"
    assert party.addresses["mr"] == "प्लॉट क्र. २२, त्रिमूर्ती नगर, नागपूर"
    assert party.addresses["en"] == "Plot No. 22, Trimurti Nagar, Nagpur"


# --- 2. Optimistic Locking & Version Archiving Tests ---

def test_party_optimistic_locking_and_version_snapshot() -> None:
    """Verifies optimistic locking increments version and archives prior snapshot in party_versions."""
    party = party_service.create_party(
        tenant_id=TENANT_ID,
        kind="individual",
        names={"mr": {"full": "रमेश पाटील"}, "en": {"full": "Ramesh Patil"}},
        actor_id=ACTOR_ID,
    )
    assert party.version == 1

    # Successful update with matching expected_version=1
    updated = party_service.update_party(
        party_id=party.id,
        tenant_id=TENANT_ID,
        expected_version=1,
        names={"mr": {"full": "रमेश विठ्ठलराव पाटील"}, "en": {"full": "Ramesh Vitthalrao Patil"}},
        actor_id=ACTOR_ID,
    )
    assert updated.version == 2

    # Check version snapshot in party_versions
    versions = party_service.get_versions(party.id)
    assert len(versions) == 1
    assert versions[0].version == 1
    assert versions[0].data["names"]["mr"]["full"] == "रमेश पाटील"

    # Conflicting update with stale expected_version=1 MUST raise OptimisticLockError
    with pytest.raises(OptimisticLockError) as exc_info:
        party_service.update_party(
            party_id=party.id,
            tenant_id=TENANT_ID,
            expected_version=1,  # Stale version! Current is 2
            names={"mr": {"full": "नवीन नाव"}},
            actor_id=ACTOR_ID,
        )
    assert exc_info.value.status_code == 412


# --- 3. Property Entity & Exact Decimal Handling ---

def test_property_creation_with_decimal_measurements() -> None:
    """Verifies exact Decimal handling for area and Ready Reckoner rates."""
    prop = property_service.create_property(
        tenant_id=TENANT_ID,
        category="plot",
        attrs={"mouza": "सोनेगाव", "khasra_no": "४५/२", "plot_no": "१२"},
        area_value=Decimal("150.0000"),
        area_unit="sqm",
        boundaries={"east": "रस्ता", "west": "भूखंड क्र. १३", "north": "जागा", "south": "भूखंड क्र. ११"},
        rr_division="सोनेगाव-१",
        rr_rate=Decimal("25000.00"),
        actor_id=ACTOR_ID,
    )

    assert prop.version == 1
    assert isinstance(prop.area_value, Decimal)
    assert prop.area_value == Decimal("150.0000")
    assert prop.rr_rate == Decimal("25000.00")


# --- 4. Matters & MatterParties Association ---

def test_matter_creation_and_party_association() -> None:
    """Verifies matters creation, uniqueness, and party role association."""
    matter = matter_service.create_matter(
        tenant_id=TENANT_ID,
        matter_no="MAT-2026-001",
        title="Plot Sale Deed - Ramesh Patil to Sunita Joshi",
        actor_id=ACTOR_ID,
    )

    party_seller_id = uuid.uuid4()
    party_buyer_id = uuid.uuid4()

    matter_service.assign_party(matter.id, party_seller_id, "seller")
    matter_service.assign_party(matter.id, party_buyer_id, "buyer")

    parties = matter_service.get_matter_parties(matter.id)
    assert len(parties) == 2
    roles = {p.role for p in parties}
    assert roles == {"seller", "buyer"}

    # Duplicate matter_no in same tenant must fail
    with pytest.raises(ValueError):
        matter_service.create_matter(
            tenant_id=TENANT_ID,
            matter_no="MAT-2026-001",
            title="Duplicate matter",
        )


# --- 5. Audit Log Hash Chaining & Tamper Detection ---

def test_audit_log_hash_chain_and_tamper_detection() -> None:
    """Verifies SHA-256 hash chaining and proves tamper detection."""
    # 1. Record series of audit events
    rec1 = audit_service.log_event(
        tenant_id=TENANT_ID,
        action="party_created",
        entity="party",
        entity_id="P-001",
        actor_id=ACTOR_ID,
    )
    rec2 = audit_service.log_event(
        tenant_id=TENANT_ID,
        action="party_updated",
        entity="party",
        entity_id="P-001",
        actor_id=ACTOR_ID,
    )
    rec3 = audit_service.log_event(
        tenant_id=TENANT_ID,
        action="document_generated",
        entity="document",
        entity_id="DOC-001",
        actor_id=ACTOR_ID,
    )

    # Hash chaining verification
    assert rec2.prev_hash == rec1.hash
    assert rec3.prev_hash == rec2.hash
    assert audit_service.verify_audit_chain(TENANT_ID) is True

    # 2. Simulate malicious row tampering (e.g., someone changes entity_id in rec2)
    rec2.entity_id = "TAMPERED_ENTITY_ID"

    # 3. Verification must fail immediately!
    assert audit_service.verify_audit_chain(TENANT_ID) is False

