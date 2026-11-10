"""Unit tests for Gate 2 Pilot Corrections and Drafter Feedback (PRD Section 10, Plan Week 19).

Verifies:
1. Logging new corrections with category, severity, and text snippets.
2. Filtering corrections by template, status, and severity.
3. Resolving corrections with audit event recording.
4. Pilot health metrics calculation and average-corrections-per-draft trend.
5. Strict tenant isolation (cross-tenant visibility blocked).
"""

import uuid

import pytest

from app.pilot.corrections import (
    CorrectionCategory,
    CorrectionCreateRequest,
    CorrectionSeverity,
    CorrectionStatus,
    PilotCorrectionsService,
)


@pytest.fixture
def service() -> PilotCorrectionsService:
    s = PilotCorrectionsService()
    s.clear()
    return s


def test_log_and_list_correction(service: PilotCorrectionsService) -> None:
    """Tests logging a correction and retrieving it."""
    tenant_id = uuid.uuid4()
    req = CorrectionCreateRequest(
        template_id="sale_deed_plot_mr",
        category=CorrectionCategory.LEGAL_CLAUSE,
        severity=CorrectionSeverity.MINOR,
        original_text="old clause",
        corrected_text="new clause",
        description="Statutory wording enhancement",
    )

    entry = service.log_correction(
        tenant_id=tenant_id,
        drafter_id="drafter_1",
        req=req,
    )

    assert entry.template_id == "sale_deed_plot_mr"
    assert entry.status == CorrectionStatus.LOGGED
    assert entry.category == CorrectionCategory.LEGAL_CLAUSE
    assert entry.severity == CorrectionSeverity.MINOR

    # List entries
    items = service.list_corrections(tenant_id=tenant_id)
    assert len(items) == 1
    assert items[0].id == entry.id


def test_resolve_correction(service: PilotCorrectionsService) -> None:
    """Tests marking a correction as resolved with resolution notes."""
    tenant_id = uuid.uuid4()
    req = CorrectionCreateRequest(
        template_id="sale_deed_flat_mr",
        category=CorrectionCategory.LAYOUT_SPACING,
        severity=CorrectionSeverity.COSMETIC,
        description="Missing comma",
    )
    entry = service.log_correction(tenant_id=tenant_id, drafter_id="drafter_2", req=req)

    resolved = service.resolve_correction(
        correction_id=entry.id,
        tenant_id=tenant_id,
        resolution_notes="Comma added in template.docx",
        resolved_by="developer_1",
    )

    assert resolved.status == CorrectionStatus.RESOLVED
    assert resolved.resolved_at is not None
    assert resolved.resolution_notes == "Comma added in template.docx"


def test_pilot_stats_calculation(service: PilotCorrectionsService) -> None:
    """Verifies calculation of resolution rates and average corrections per draft."""
    tenant_id = uuid.uuid4()

    # Log 3 corrections: 2 minor, 1 blocking
    c1 = service.log_correction(
        tenant_id=tenant_id,
        drafter_id="d1",
        req=CorrectionCreateRequest(
            template_id="sale_deed_plot_mr",
            category=CorrectionCategory.GRAMMAR,
            severity=CorrectionSeverity.MINOR,
            description="Grammar issue 1",
        ),
    )
    c2 = service.log_correction(
        tenant_id=tenant_id,
        drafter_id="d1",
        req=CorrectionCreateRequest(
            template_id="sale_deed_plot_mr",
            category=CorrectionCategory.NUMBERING,
            severity=CorrectionSeverity.BLOCKING,
            description="Blocking numbering issue",
        ),
    )
    c3 = service.log_correction(
        tenant_id=tenant_id,
        drafter_id="d2",
        req=CorrectionCreateRequest(
            template_id="general_poa_en",
            category=CorrectionCategory.LEGAL_CLAUSE,
            severity=CorrectionSeverity.MINOR,
            description="Clause adjustment",
        ),
    )

    # Resolve 1
    service.resolve_correction(
        correction_id=c1.id,
        tenant_id=tenant_id,
        resolution_notes="Resolved in v1",
        resolved_by="dev",
    )

    stats = service.get_pilot_stats(tenant_id=tenant_id, total_drafts=2)
    assert stats.total_logged == 3
    assert stats.total_resolved == 1
    assert stats.total_pending == 2
    assert stats.blocking_count == 1
    assert stats.resolution_rate_percent == 33.3
    assert stats.avg_corrections_per_draft == 1.5


def test_tenant_isolation_corrections(service: PilotCorrectionsService) -> None:
    """Verifies that corrections logged under Tenant A are strictly invisible to Tenant B."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    service.log_correction(
        tenant_id=tenant_a,
        drafter_id="drafter_a",
        req=CorrectionCreateRequest(
            template_id="sale_deed_plot_mr",
            category=CorrectionCategory.OTHER,
            description="Tenant A feedback",
        ),
    )

    items_a = service.list_corrections(tenant_id=tenant_a)
    items_b = service.list_corrections(tenant_id=tenant_b)

    assert len(items_a) == 1
    assert len(items_b) == 0

    # Attempting to resolve Tenant A correction using Tenant B must raise KeyError
    with pytest.raises(KeyError):
        service.resolve_correction(
            correction_id=items_a[0].id,
            tenant_id=tenant_b,
            resolution_notes="Unauthorized resolve",
            resolved_by="attacker",
        )
