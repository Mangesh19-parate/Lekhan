"""Unit tests for security hardening and advisory catalog fixes."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from app.advisory.engine import advisory_rules_engine
from app.api import auth as auth_api
from app.config import Settings
from app.main import app

VALID_MASTER_KEY = base64.b64encode(b"m" * 32).decode("ascii")
VALID_INDEX_KEY = base64.b64encode(b"i" * 32).decode("ascii")


def test_settings_rejects_default_keys_in_prod_and_staging() -> None:
    """Deployed environments must fail fast if placeholder dev keys are used."""
    for env in ("staging", "prod"):
        with pytest.raises(ValueError, match="default dev placeholder"):
            Settings(ENV=env)

    # Explicit non-placeholder keys are accepted in prod
    prod_settings = Settings(
        ENV="prod",
        SECRET_KEY="a" * 64,
        MASTER_KEY=VALID_MASTER_KEY,
        INDEX_KEY=VALID_INDEX_KEY,
    )
    assert prod_settings.ENV == "prod"


def test_synthetic_users_disabled_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthetic dev accounts must never authenticate in deployed environments."""
    prod_settings = Settings(
        ENV="prod",
        SECRET_KEY="a" * 64,
        MASTER_KEY=VALID_MASTER_KEY,
        INDEX_KEY=VALID_INDEX_KEY,
    )
    monkeypatch.setattr(auth_api, "settings", prod_settings)

    assert auth_api._find_user_by_email("admin@lekhan.local") is None
    assert auth_api._find_user_by_id(auth_api.SYNTHETIC_USERS["admin@lekhan.local"]["id"]) is None


def test_unauthenticated_generate_spike_endpoint_removed() -> None:
    """Legacy unauthenticated /generate-spike endpoint must not be exposed."""
    client = TestClient(app)
    res = client.post("/api/v1/documents/generate-spike", json={})
    assert res.status_code in (404, 405)


def test_advisory_list_rules_returns_catalog() -> None:
    """list_rules returns all registered rules without dummy payload evaluation."""
    rules = advisory_rules_engine.list_rules()
    assert [r.id for r in rules] == [
        "ADVISORY_TDS_194IA",
        "ADVISORY_PAN_FORM_60",
        "ADVISORY_AGRICULTURAL_STATUS",
        "ADVISORY_MAHARERA_DISCLOSURE",
    ]
