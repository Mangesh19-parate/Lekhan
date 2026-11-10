"""Unit tests for Trigram Search in Marathi/English and Party/Property Reuse (PRD FR-14, Features F-060, F-061).

Verifies:
1. Devanagari Unicode trigram similarity (tolerant of matra and spelling variants).
2. English trigram similarity.
3. Multi-field party and property search ranking.
4. Past document immutability: past generated documents carry immutable data snapshots
   and remain completely untouched when parties or properties are updated in subsequent matters.
5. Strict cross-tenant isolation in search and reuse.
"""

import uuid

import pytest

from app.generation.jobs import JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.parties.service import PartyService
from app.properties.service import PropertyService
from app.shared.trigram import trigram_similarity


@pytest.fixture
def clean_services():
    p_svc = PartyService()
    prop_svc = PropertyService()
    pipeline = GenerationPipelineFSM()
    p_svc.clear()
    prop_svc.clear()
    pipeline.clear()
    return {"parties": p_svc, "properties": prop_svc, "pipeline": pipeline}


def test_devanagari_trigram_similarity() -> None:
    """Verifies that Devanagari trigram calculation handles spelling and matra variants."""
    # 1. Matra / vowel variation (कशिनाथ vs काशिनाथ)
    sim1 = trigram_similarity("कशिनाथ", "काशिनाथ")
    assert sim1 > 0.45, f"Expected similarity > 0.45, got {sim1}"

    # 2. Suffix variation (देशमुख vs देशमुखे)
    sim2 = trigram_similarity("देशमुख", "देशमुखे")
    assert sim2 > 0.60, f"Expected similarity > 0.60, got {sim2}"

    # 3. Exact match
    sim_exact = trigram_similarity("रामदासपेठ", "रामदासपेठ")
    assert sim_exact == 1.0

    # 4. Unrelated Devanagari strings
    sim_diff = trigram_similarity("रामदासपेठ", "सोमवारीपेठ")
    assert sim_diff < 0.50


def test_english_trigram_similarity() -> None:
    """Verifies that English trigram calculation handles Indian name spelling variations."""
    # Transliteration variant (Wankhede vs Wankhade)
    sim = trigram_similarity("Wankhede", "Wankhade")
    assert sim > 0.55, f"Expected similarity > 0.55, got {sim}"

    # Substring match (e.g. Deshmukh in Rajesh Deshmukh)
    sim_sub = trigram_similarity("Deshmukh", "Rajesh Deshmukh")
    assert sim_sub > 0.40


def test_party_trigram_search(clean_services) -> None:
    """Tests multi-field party search across Marathi and English fields."""
    p_svc = clean_services["parties"]
    tenant_id = uuid.uuid4()

    # Create 3 parties
    p1 = p_svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "काशिनाथ दामोदर पाटील", "en": "Kashinath Damodar Patil"},
        addresses={"mr": "रामदासपेठ, नागपूर", "en": "Ramdaspeth, Nagpur"},
        pan_masked="ABCDE1234F",
    )
    p2 = p_svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "गजानन मारोतराव वानखेडे", "en": "Gajanan Marotrao Wankhede"},
        addresses={"mr": "धरमपेठ, नागपूर", "en": "Dharampeth, Nagpur"},
        pan_masked="FGHIJ5678K",
    )
    p3 = p_svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "रमेश विष्णू देशमुख", "en": "Ramesh Vishnu Deshmukh"},
        addresses={"mr": "वर्धा", "en": "Wardha"},
        pan_masked="KLMNO9012P",
    )

    # Search in Marathi with slight variation "कशिनाथ" -> should match p1 highest
    matches_mr = p_svc.search_parties(tenant_id=tenant_id, query="कशिनाथ")
    assert len(matches_mr) >= 1
    assert matches_mr[0][0].id == p1.id

    # Search in English "Wankhade" -> should match p2 highest
    matches_en = p_svc.search_parties(tenant_id=tenant_id, query="Wankhade")
    assert len(matches_en) >= 1
    assert matches_en[0][0].id == p2.id

    # Search by PAN masked
    matches_pan = p_svc.search_parties(tenant_id=tenant_id, query="KLMNO")
    assert len(matches_pan) >= 1
    assert matches_pan[0][0].id == p3.id


def test_property_trigram_search(clean_services) -> None:
    """Tests property search by mouza, khasra, or layout."""
    prop_svc = clean_services["properties"]
    tenant_id = uuid.uuid4()

    prop1 = prop_svc.create_property(
        tenant_id=tenant_id,
        category="plot",
        attrs={
            "mouza": "Babulkheda",
            "khasra_no": "23/1",
            "plot_no": "104",
            "layout": "NIT Layout",
        },
    )
    prop2 = prop_svc.create_property(
        tenant_id=tenant_id,
        category="flat",
        attrs={"mouza": "Besa", "building": "Sai Residency", "flat_no": "301"},
    )

    # Search mouza "Babulkhed" -> should match prop1
    matches = prop_svc.search_properties(tenant_id=tenant_id, query="Babulkhed")
    assert len(matches) >= 1
    assert matches[0][0].id == prop1.id

    # Search with category filter
    matches_flats = prop_svc.search_properties(tenant_id=tenant_id, query="Sai", category="flat")
    assert len(matches_flats) == 1
    assert matches_flats[0][0].id == prop2.id


def test_past_document_immutability_on_reuse(clean_services) -> None:
    """Verifies that reusing and updating a party/property leaves prior documents 100% untouched (FR-14, F-060)."""
    p_svc = clean_services["parties"]
    prop_svc = clean_services["properties"]
    pipeline = clean_services["pipeline"]
    tenant_id = uuid.uuid4()

    # 1. Create initial party and property (version 1)
    party = p_svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "अनिल जोशी", "en": "Anil Joshi"},
        addresses={"mr": "जुना पत्ता, नागपूर", "en": "Old Address, Nagpur"},
    )
    assert party.version == 1

    prop = prop_svc.create_property(
        tenant_id=tenant_id,
        category="plot",
        attrs={
            "plot_no": "10",
            "layout_name": "Old Layout A",
            "mouza": "Besa",
            "khasra_no": "5/1",
            "city_survey_no": "CTS-1",
            "area_sqm": "150.00",
        },
    )
    assert prop.version == 1

    # 2. Generate First Document (Matter 1)
    job1 = JobRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "vendors": [
                {
                    "full_name": party.names["mr"],
                    "age": 45,
                    "address": party.addresses["mr"],
                    "pan": "ABCDE1234F",
                    "aadhaar_last4": "1234",
                }
            ],
            "purchasers": [
                {
                    "full_name": "Purchaser 1",
                    "age": 35,
                    "address": "Wardha",
                    "pan": "FGHIJ5678K",
                    "aadhaar_last4": "5678",
                }
            ],
            "property_details": {
                "plot_no": prop.attrs["plot_no"],
                "layout_name": prop.attrs["layout_name"],
                "mouza": prop.attrs["mouza"],
                "khasra_no": prop.attrs["khasra_no"],
                "city_survey_no": prop.attrs["city_survey_no"],
                "area_sqm": prop.attrs["area_sqm"],
                "boundaries": {"east": "Road", "west": "Plot", "north": "Plot", "south": "Plot"},
            },
            "financial_terms": {
                "total_consideration": "2000000",
                "advance_paid": "400000",
                "balance_amount": "1600000",
                "payment_mode": "RTGS",
            },
            "witnesses": [{"full_name": "W1", "address": "N"}, {"full_name": "W2", "address": "N"}],
        },
    )
    doc1 = pipeline.process_job(job1)
    assert doc1.data_snapshot["vendors"][0]["address"] == "जुना पत्ता, नागपूर"
    assert doc1.data_snapshot["property_details"]["layout_name"] == "Old Layout A"

    # 3. Now reuse Party and Property in a new matter with updated details (creating version 2)
    party_v2 = p_svc.reuse_party(
        party_id=party.id,
        tenant_id=tenant_id,
        overrides={"addresses": {"mr": "नवीन पत्ता, पुणे", "en": "New Address, Pune"}},
    )
    assert party_v2.version == 2
    assert party_v2.addresses["mr"] == "नवीन पत्ता, पुणे"

    prop_v2 = prop_svc.reuse_property(
        property_id=prop.id,
        tenant_id=tenant_id,
        overrides={"attrs": {"layout_name": "New Renovated Layout B"}},
    )
    assert prop_v2.version == 2
    assert prop_v2.attrs["layout_name"] == "New Renovated Layout B"

    # 4. Verify historical versions were archived
    party_history = p_svc.get_versions(party.id)
    assert len(party_history) == 1
    assert party_history[0].version == 1

    prop_history = prop_svc.get_versions(prop.id)
    assert len(prop_history) == 1
    assert prop_history[0].version == 1

    # 5. CRITICAL CHECK: Verify First Document (doc1) has NOT mutated at all!
    doc1_refetched = pipeline.get_document(doc1.id, tenant_id)
    assert doc1_refetched is not None
    assert doc1_refetched.data_snapshot["vendors"][0]["address"] == "जुना पत्ता, नागपूर"
    assert doc1_refetched.data_snapshot["property_details"]["layout_name"] == "Old Layout A"


def test_cross_tenant_search_isolation(clean_services) -> None:
    """Verifies that search queries never leak parties across tenants."""
    p_svc = clean_services["parties"]
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    p_svc.create_party(
        tenant_id=tenant_a,
        kind="individual",
        names={"mr": "गोविंदराव मुंडले", "en": "Govindrao Mundle"},
    )

    # Searching from Tenant B must return 0 results
    matches_b = p_svc.search_parties(tenant_id=tenant_b, query="मुंडले")
    assert len(matches_b) == 0

    # Searching from Tenant A returns the match
    matches_a = p_svc.search_parties(tenant_id=tenant_a, query="मुंडले")
    assert len(matches_a) == 1
