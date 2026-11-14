"""Unit tests for Document Diff Engine and Duplicate Party Detection (Features F-030, F-065, F-066)."""

import uuid

from app.parties.service import PartyService
from app.shared.diff import diff_legal_texts


def test_legal_text_diff_word_level() -> None:
    text_1 = "सदर मिळकत सर्व प्रकारच्या बोजापासून मुक्त आहे."
    text_2 = "सदर मिळकत सर्व प्रकारच्या बोजा, गहाण व जप्तीपासून मुक्त आहे."

    result = diff_legal_texts(text_1, text_2, granularity="word")
    assert result.similarity_ratio > 0.60
    assert result.total_additions > 0
    assert len(result.hunks) >= 2


def test_duplicate_party_detection_exact_pan() -> None:
    svc = PartyService()
    svc.clear()
    tenant_id = uuid.uuid4()

    # Create original party
    svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "आनंद जोशी", "en": "Anand Joshi"},
        pan_masked="ABCDE1234F",
    )

    # Detect duplicate by PAN
    dupes = svc.detect_duplicates(tenant_id=tenant_id, pan="ABCDE1234F")
    assert len(dupes) == 1
    assert dupes[0]["match_type"] == "exact_pan"
    assert dupes[0]["similarity"] == 1.0


def test_duplicate_party_detection_high_name_similarity() -> None:
    svc = PartyService()
    svc.clear()
    tenant_id = uuid.uuid4()

    svc.create_party(
        tenant_id=tenant_id,
        kind="individual",
        names={"mr": "सुरेश रामराव पाटील", "en": "Suresh Ramrao Patil"},
    )

    # Check variation in name
    dupes = svc.detect_duplicates(tenant_id=tenant_id, name="सुरेश पाटील", threshold=0.60)
    assert len(dupes) == 1
    assert dupes[0]["similarity"] >= 0.60
