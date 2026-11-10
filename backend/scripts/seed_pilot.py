"""Synthetic Data Seeding Script for Gate 2 Pilot Drafters (PRD Section 10, Plan Week 19).

Strict compliance with AGENTS.md Hard Rule 1:
Zero real personal data. All names, PANs, Aadhaar numbers, and addresses are strictly synthetic.
"""

from __future__ import annotations

import uuid
from app.generation.jobs import JobRecord
from app.generation.pipeline import generation_pipeline
from app.pilot.corrections import (
    CorrectionCategory,
    CorrectionCreateRequest,
    CorrectionSeverity,
    pilot_corrections_service,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)

# Fixed synthetic tenant ID for pilot testing
PILOT_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")

# 3 Synthetic pilot drafter personas
PILOT_DRAFTERS = [
    {
        "id": "drafter_senior",
        "name": "Advocate V. Joshi",
        "role": "Senior Conveyancing Advocate (Vidarbha)",
        "email": "v.joshi.pilot@synthetic-lekhan.local",
    },
    {
        "id": "drafter_typist",
        "name": "Associate S. Kulkarni",
        "role": "Registry Deed Drafter (Nagpur Sub-Registrar)",
        "email": "s.kulkarni.pilot@synthetic-lekhan.local",
    },
    {
        "id": "drafter_junior",
        "name": "Advocate P. Deshmukh",
        "role": "Junior Legal Associate (Agri & Residential)",
        "email": "p.deshmukh.pilot@synthetic-lekhan.local",
    },
]


def seed_pilot_environment() -> dict[str, int]:
    """Populates synthetic documents and initial feedback corrections for Gate 2 pilot."""
    docs_created = 0

    # 1. Generate sample draft for Pilot Drafter 1 (Marathi Plot Sale Deed)
    job1 = JobRecord(
        id=uuid.uuid4(),
        tenant_id=PILOT_TENANT_ID,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "vendors": [{"full_name": "Kashinath D. Patil (Synthetic)", "age": 52, "address": "Ramdaspeth, Nagpur", "pan": "ABCDE1234F", "aadhaar_last4": "1234"}],
            "purchasers": [{"full_name": "Gajanan M. Wankhede (Synthetic)", "age": 44, "address": "Dharampeth, Nagpur", "pan": "FGHIJ5678K", "aadhaar_last4": "5678"}],
            "property_details": {
                "plot_no": "104",
                "layout_name": "NIT Approved Layout",
                "mouza": "Babulkheda",
                "khasra_no": "23/1",
                "city_survey_no": "CTS-402",
                "area_sqm": "175.00",
                "boundaries": {"east": "Internal 9M Road", "west": "Plot 103", "north": "Plot 92", "south": "Plot 105"},
            },
            "financial_terms": {"total_consideration": "4200000", "advance_paid": "1000000", "balance_amount": "3200000", "payment_mode": "RTGS"},
            "witnesses": [{"full_name": "Synthetic Witness 1", "address": "Nagpur"}, {"full_name": "Synthetic Witness 2", "address": "Nagpur"}],
        },
    )
    doc1 = generation_pipeline.process_job(job1)
    docs_created += 1

    # 2. Seed pilot corrections reflecting 4-week pilot triage flow
    c1 = pilot_corrections_service.log_correction(
        tenant_id=PILOT_TENANT_ID,
        drafter_id="drafter_senior",
        req=CorrectionCreateRequest(
            template_id="sale_deed_plot_mr",
            document_id=doc1.id,
            category=CorrectionCategory.LEGAL_CLAUSE,
            severity=CorrectionSeverity.MINOR,
            original_text="सदर मिळकत सर्व प्रकारच्या बोजापासून मुक्त आहे.",
            corrected_text="सदर मिळकत सर्व प्रकारच्या बोजा, गहाण, लीन, वाद व जप्तीपासून मुक्त आहे.",
            description="Add statutory recital covering court attachment ('जप्तीपासून मुक्त') per Vidarbha precedent.",
        ),
    )
    pilot_corrections_service.resolve_correction(
        correction_id=c1.id,
        tenant_id=PILOT_TENANT_ID,
        resolution_notes="Updated template encumbrance recital to include court attachment, mortgage, lien and claim warranties.",
        resolved_by="lead_advocate",
    )

    c2 = pilot_corrections_service.log_correction(
        tenant_id=PILOT_TENANT_ID,
        drafter_id="drafter_typist",
        req=CorrectionCreateRequest(
            template_id="sale_deed_flat_mr",
            document_id=None,
            category=CorrectionCategory.LAYOUT_SPACING,
            severity=CorrectionSeverity.COSMETIC,
            original_text="मजला क्र. {{ property.floor_no }} फ्लॅट क्र.",
            corrected_text="मजला क्र. {{ property.floor_no }}, फ्लॅट क्र.",
            description="Add a comma separator between floor number and flat number in header line.",
        ),
    )
    pilot_corrections_service.resolve_correction(
        correction_id=c2.id,
        tenant_id=PILOT_TENANT_ID,
        resolution_notes="Verified comma separator formatting in flat deed schedule.",
        resolved_by="lead_developer",
    )

    c3 = pilot_corrections_service.log_correction(
        tenant_id=PILOT_TENANT_ID,
        drafter_id="drafter_junior",
        req=CorrectionCreateRequest(
            template_id="general_poa_mr",
            document_id=None,
            category=CorrectionCategory.NUMBERING,
            severity=CorrectionSeverity.COSMETIC,
            original_text="1. अधिकार ...",
            corrected_text="१. अधिकार ...",
            description="Ensure list numbers use Western digits consistently per digits_setting.",
        ),
    )
    pilot_corrections_service.resolve_correction(
        correction_id=c3.id,
        tenant_id=PILOT_TENANT_ID,
        resolution_notes="Verified manifest digits_setting is set to 'western' across all clauses.",
        resolved_by="lead_developer",
    )

    c4 = pilot_corrections_service.log_correction(
        tenant_id=PILOT_TENANT_ID,
        drafter_id="drafter_typist",
        req=CorrectionCreateRequest(
            template_id="portal_sheet",
            document_id=doc1.id,
            category=CorrectionCategory.OTHER,
            severity=CorrectionSeverity.MINOR,
            description="Provide a 1-click clipboard copy button for Sub-Registrar / PDE data-entry text.",
        ),
    )
    pilot_corrections_service.resolve_correction(
        correction_id=c4.id,
        tenant_id=PILOT_TENANT_ID,
        resolution_notes="Added 1-click Copy PDE Sheet button in Form Engine UI and drafting view.",
        resolved_by="lead_developer",
    )

    c5 = pilot_corrections_service.log_correction(
        tenant_id=PILOT_TENANT_ID,
        drafter_id="drafter_senior",
        req=CorrectionCreateRequest(
            template_id="form_engine",
            document_id=None,
            category=CorrectionCategory.OTHER,
            severity=CorrectionSeverity.COSMETIC,
            description="Enable Ctrl+Enter keyboard shortcut for rapid draft generation without mouse scrolling.",
        ),
    )
    pilot_corrections_service.resolve_correction(
        correction_id=c5.id,
        tenant_id=PILOT_TENANT_ID,
        resolution_notes="Added global Ctrl+Enter / Cmd+Enter form submission listener across UI pages.",
        resolved_by="lead_developer",
    )

    logger.info("Pilot environment seeded: %d docs, 5 corrections resolved", docs_created)
    return {"documents_seeded": docs_created, "corrections_seeded": 5, "corrections_resolved": 5}


if __name__ == "__main__":
    result = seed_pilot_environment()
    print("Seed complete:", result)

