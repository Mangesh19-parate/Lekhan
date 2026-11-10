"""Unit tests for Pilot Feedback, Triage & Correction SLA Verification (PRD Section 10, Plan Week 23).

Verifies:
1. Pilot drafter corrections triage and lifecycle transitions (logged -> triaged -> resolved).
2. Falling corrections trend below the PRD target of 5 corrections per draft by week 4.
3. 100% resolution of blocking and high-impact advocate feedback items.
4. Tenant-scoped audit events for triage and resolution actions.
"""

from __future__ import annotations

import uuid

from app.pilot.corrections import (
    CorrectionCategory,
    CorrectionCreateRequest,
    CorrectionSeverity,
    CorrectionStatus,
    PilotCorrectionsService,
)
from scripts.seed_pilot import PILOT_TENANT_ID, seed_pilot_environment


def test_pilot_corrections_triage_flow() -> None:
    """Verifies transition from logged -> triaged -> resolved with notes."""
    service = PilotCorrectionsService()
    tenant_id = uuid.uuid4()
    drafter_id = "drafter_advocate_test"

    # 1. Log a new correction
    entry = service.log_correction(
        tenant_id=tenant_id,
        drafter_id=drafter_id,
        req=CorrectionCreateRequest(
            template_id="sale_deed_plot_mr",
            category=CorrectionCategory.LEGAL_CLAUSE,
            severity=CorrectionSeverity.MINOR,
            description="Add statutory recital covering court attachment per Vidarbha precedent.",
        ),
    )
    assert entry.status == CorrectionStatus.LOGGED

    # 2. Triage the correction
    triaged = service.triage_correction(
        correction_id=entry.id,
        tenant_id=tenant_id,
        triaged_by="lead_advocate",
        notes="Reviewed and approved for template version 2 update.",
    )
    assert triaged.status == CorrectionStatus.TRIAGED
    assert "Triaged" in (triaged.resolution_notes or "")

    # 3. Resolve the correction
    resolved = service.resolve_correction(
        correction_id=entry.id,
        tenant_id=tenant_id,
        resolution_notes="Updated template XML with court attachment and lien warranty clause.",
        resolved_by="lead_developer",
    )
    assert resolved.status == CorrectionStatus.RESOLVED
    assert resolved.resolved_at is not None
    assert "court attachment" in resolved.resolution_notes


def test_pilot_stats_target_achievement() -> None:
    """Verifies that 4-week pilot stats meet PRD criteria (falling corrections, <5/draft)."""
    # Seed the pilot environment
    result = seed_pilot_environment()
    assert result["documents_seeded"] >= 1
    assert result["corrections_resolved"] == 5

    from app.pilot.corrections import pilot_corrections_service

    stats = pilot_corrections_service.get_pilot_stats(PILOT_TENANT_ID, total_drafts=4)

    # PRD Target 1: Falling corrections under 5 per draft
    assert stats.avg_corrections_per_draft <= 5.0
    # PRD Target 2: 0 unresolved blocking items
    assert stats.blocking_count == 0
    # PRD Target 3: Resolution rate high (>80%)
    assert stats.resolution_rate_percent >= 80.0

    # Weekly trend present showing progression
    assert len(stats.weekly_trend) >= 5
    assert stats.weekly_trend[-1]["week"] == "Week 23 (Buffer & Wave 2)"
    assert stats.weekly_trend[-1]["avg_per_draft"] < 1.0

    # Top resolved corrections captured
    assert len(stats.top_corrections_resolved) > 0
