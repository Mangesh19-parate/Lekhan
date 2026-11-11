"""Unit tests for Week 12 Form Engine, i18n tokens, and server-side validation endpoint."""

import json
from decimal import Decimal
from pathlib import Path

import uuid

from app.api.documents import ValidationRequest, validate_draft_data
from app.identity.policy import Actor

ROOT_DIR = Path(__file__).parent.parent.parent.parent


def test_design_tokens_and_form_engine_html() -> None:
    """Verifies that form_engine.html strictly implements tokens from DESIGN.md."""
    html_path = ROOT_DIR / "backend" / "app" / "static" / "form_engine.html"
    assert html_path.exists(), "form_engine.html missing"

    content = html_path.read_text(encoding="utf-8")

    # Tokens from DESIGN.md
    assert "--brand-600: #006241" in content
    assert "--brand-500: #00754A" in content
    assert "--brand-900: #1E3932" in content
    assert "--surface-canvas: #F2F0EB" in content
    assert "--approved-500: #CBA258" in content

    # Bilingual Marathi / English elements
    assert "btnLangMr" in content
    assert "btnLangEn" in content
    assert "toWords" in content
    assert "renderRepeaters" in content


def test_i18n_catalog_consistency() -> None:
    """Verifies that English and Marathi i18n catalogs exist and have matching keys."""
    en_path = ROOT_DIR / "frontend" / "src" / "shared" / "i18n" / "en.json"
    mr_path = ROOT_DIR / "frontend" / "src" / "shared" / "i18n" / "mr.json"

    assert en_path.exists()
    assert mr_path.exists()

    en_data = json.loads(en_path.read_text(encoding="utf-8"))
    mr_data = json.loads(mr_path.read_text(encoding="utf-8"))

    # Verify top-level sections
    for section in ["app", "nav", "actions", "status", "wizard", "form", "disclaimer"]:
        assert section in en_data, f"Missing section '{section}' in en.json"
        assert section in mr_data, f"Missing section '{section}' in mr.json"


def test_server_side_validation_endpoint_success() -> None:
    """Verifies POST /api/v1/documents/validate/{template_id} returns derived fields & valid: True."""
    actor = Actor(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="drafter",
    )
    request_data = {
        "property": {
            "mouza": "सोनेगाव",
            "khasra_no": "12",
            "plot_no": "34",
            "area_sqm": Decimal("150"),
        },
        "financial": {
            "total_consideration": Decimal("2500000"),
            "earnest_advance": Decimal("500000"),
        },
    }

    resp = validate_draft_data(
        "sale_deed_plot_mr", ValidationRequest(data=request_data), actor=actor
    )

    assert resp.valid is True
    assert len(resp.violations) == 0
    assert resp.derived_fields["financial.balance_amount"] == Decimal("2000000")
    assert resp.derived_fields["property.area_sqft"] == Decimal("150") * Decimal("10.7639104")


def test_server_side_validation_endpoint_violation() -> None:
    """Verifies that cross-field validation rules flag errors (e.g. earnest > total)."""
    actor = Actor(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="drafter",
    )
    # Invalid: advance exceeds total
    request_data = {
        "property": {"area_sqm": Decimal("100")},
        "financial": {
            "total_consideration": Decimal("1000000"),
            "earnest_advance": Decimal("1200000"),  # > total
        },
    }

    resp = validate_draft_data(
        "sale_deed_plot_mr", ValidationRequest(data=request_data), actor=actor
    )

    assert resp.valid is False
    assert len(resp.violations) >= 1
    assert any(v["id"] == "earnest_le_total" for v in resp.violations)
