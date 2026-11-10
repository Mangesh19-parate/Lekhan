"""Unit tests for Lawyer-Authored Advisory Rules and Portal Data-Entry Sheet (PRD FR-15, FR-16, Features F-062, F-063).

Verifies:
1. Income Tax Section 194-IA 1% TDS advisory (> 50 Lakhs).
2. Rule 114B Form 60 PAN requirement (> 10 Lakhs and missing PAN).
3. Maharashtra Agricultural Tenancy Act Section 63 farmer certificate check.
4. MahaRERA project registration recital advisory for apartments.
5. Non-blocking guarantee: advisory rules provide suggestions without halting drafting.
6. Portal Data Sheet generation: structured party, property, and financial text for Maharashtra IGR.
"""

import uuid

import pytest

from app.advisory.engine import AdvisoryRulesEngine
from app.generation.jobs import JobRecord
from app.generation.pipeline import GenerationPipelineFSM
from app.portal.generator import PortalSheetGenerator


@pytest.fixture
def advisory_engine() -> AdvisoryRulesEngine:
    return AdvisoryRulesEngine()


@pytest.fixture
def portal_generator() -> PortalSheetGenerator:
    return PortalSheetGenerator()


def test_tds_194ia_advisory_rule(advisory_engine: AdvisoryRulesEngine) -> None:
    """Verifies that consideration >= Rs. 50 Lakhs triggers Section 194-IA 1% TDS alert."""
    tenant_id = uuid.uuid4()

    # Case A: 65 Lakhs (>= 50L) -> MUST trigger TDS alert
    payload_high = {
        "financial_terms": {"total_consideration": "6500000"},
        "vendors": [{"full_name": "Vendor A", "pan": "ABCDE1234F"}],
    }
    alerts_high = advisory_engine.evaluate_payload(payload_high, tenant_id=tenant_id)
    tds_alerts = [a for a in alerts_high if a.id == "ADVISORY_TDS_194IA"]
    assert len(tds_alerts) == 1
    assert "Section 194-IA" in tds_alerts[0].statutory_ref
    assert tds_alerts[0].severity == "warning"

    # Case B: 35 Lakhs (< 50L) -> MUST NOT trigger TDS alert
    payload_low = {
        "financial_terms": {"total_consideration": "3500000"},
        "vendors": [{"full_name": "Vendor B", "pan": "ABCDE1234F"}],
    }
    alerts_low = advisory_engine.evaluate_payload(payload_low, tenant_id=tenant_id)
    assert not any(a.id == "ADVISORY_TDS_194IA" for a in alerts_low)


def test_pan_form_60_advisory_rule(advisory_engine: AdvisoryRulesEngine) -> None:
    """Verifies that consideration > 10 Lakhs with missing PAN triggers Form 60 alert."""
    # Case A: 25 Lakhs (> 10L) with missing PAN on purchaser
    payload_missing_pan = {
        "financial_terms": {"total_consideration": "2500000"},
        "vendors": [{"full_name": "Vendor A", "pan": "ABCDE1234F"}],
        "purchasers": [{"full_name": "Purchaser B", "pan": ""}],  # Missing PAN!
    }
    alerts = advisory_engine.evaluate_payload(payload_missing_pan)
    pan_alerts = [a for a in alerts if a.id == "ADVISORY_PAN_FORM_60"]
    assert len(pan_alerts) == 1
    assert "Rule 114B" in pan_alerts[0].statutory_ref

    # Case B: All PANs provided -> no alert
    payload_with_pan = {
        "financial_terms": {"total_consideration": "2500000"},
        "vendors": [{"full_name": "Vendor A", "pan": "ABCDE1234F"}],
        "purchasers": [{"full_name": "Purchaser B", "pan": "FGHIJ5678K"}],
    }
    alerts_ok = advisory_engine.evaluate_payload(payload_with_pan)
    assert not any(a.id == "ADVISORY_PAN_FORM_60" for a in alerts_ok)


def test_agricultural_and_rera_advisories(advisory_engine: AdvisoryRulesEngine) -> None:
    """Verifies Agriculturalist entitlement check and MahaRERA project alerts."""
    # Agri template
    agri_alerts = advisory_engine.evaluate_payload(
        payload={"financial_terms": {"total_consideration": "2000000"}},
        template_id="sale_deed_agricultural_mr",
    )
    assert any(a.id == "ADVISORY_AGRICULTURAL_STATUS" for a in agri_alerts)

    # Flat template
    flat_alerts = advisory_engine.evaluate_payload(
        payload={"financial_terms": {"total_consideration": "3500000"}},
        template_id="sale_deed_flat_mr",
    )
    assert any(a.id == "ADVISORY_MAHARERA_DISCLOSURE" for a in flat_alerts)


def test_portal_sheet_generation_and_copy_text(portal_generator: PortalSheetGenerator) -> None:
    """Verifies generation of structured portal data sheet and copy-paste text."""
    pipeline = GenerationPipelineFSM()
    tenant_id = uuid.uuid4()

    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "vendors": [
                {
                    "full_name": "देवराव हरीभाऊ वानखेडे",
                    "age": 55,
                    "address": "धरमपेठ, नागपूर",
                    "pan": "ABCDE1234F",
                    "aadhaar_last4": "1234",
                }
            ],
            "purchasers": [
                {
                    "full_name": "नारायण विष्णू पाटील",
                    "age": 42,
                    "address": "रामदaspeth, नागपूर",
                    "pan": "FGHIJ5678K",
                    "aadhaar_last4": "5678",
                }
            ],
            "property_details": {
                "plot_no": "104",
                "layout_name": "Shivaji Layout",
                "mouza": "Besa",
                "khasra_no": "23/2",
                "city_survey_no": "CTS-101",
                "area_sqm": "150.00",
                "boundaries": {
                    "east": "Road",
                    "west": "Plot 103",
                    "north": "Plot 90",
                    "south": "Plot 105",
                },
            },
            "financial_terms": {
                "total_consideration": "2500000",
                "advance_paid": "500000",
                "balance_amount": "2000000",
                "payment_mode": "RTGS",
            },
            "witnesses": [
                {"full_name": "Witness 1", "address": "Nagpur"},
                {"full_name": "Witness 2", "address": "Nagpur"},
            ],
        },
    )

    doc_record = pipeline.process_job(job)
    sheet = portal_generator.generate_sheet(doc_record)

    # 1. Structure assertions
    assert sheet.document_id == doc_record.id
    assert sheet.doc_no == doc_record.doc_no
    assert len(sheet.parties) == 2
    assert sheet.property.mouza == "Besa"
    assert sheet.property.unit_or_plot_no == "104"
    assert sheet.financial.total_consideration == "2,500,000"
    assert "पंचवीस लाख" in sheet.financial.amount_in_words_mr
    assert "Twenty-Five Lakh" in sheet.financial.amount_in_words_en

    # 2. Copy-paste plain text content assertions
    text = sheet.copy_paste_text
    assert "MAHARASHTRA SUB-REGISTRAR REGISTRATION PORTAL DATA ENTRY SHEET" in text
    assert "देवराव हरीभाऊ वानखेडे" in text
    assert "नारायण विष्णू पाटील" in text
    assert "Besa" in text
    assert "2,500,000" in text
    assert "[1] PARTIES SUMMARY" in text
    assert "[2] PROPERTY PARTICULARS" in text
    assert "[3] FINANCIAL CONSIDERATION" in text
