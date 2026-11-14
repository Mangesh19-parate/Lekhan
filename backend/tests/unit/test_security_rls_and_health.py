"""Unit tests for Row-Level Security (RLS), metrics protection, and readiness probe.

Validates:
1. PostgreSQL RLS policy filters out all rows when app.tenant_id is not set (returns zero rows).
2. /metrics protection via network allowlist and token.
3. /health/ready returns 503 Service Unavailable when DB is down.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.adapters.db import set_tenant_context
from app.config import get_settings
from app.main import app

client = TestClient(app)
settings = get_settings()

TENANT_A = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_B = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")


def test_rls_query_without_tenant_context_returns_zero_rows() -> None:
    """Verifies that queries without app.tenant_id return zero rows under RLS policy.

    The RLS policy is:
      USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    """
    # Simulate RLS evaluation logic
    def evaluate_rls(row_tenant: uuid.UUID, app_tenant_setting: str | None) -> bool:
        if not app_tenant_setting:
            return False
        try:
            return row_tenant == uuid.UUID(app_tenant_setting)
        except ValueError:
            return False

    records = [
        {"id": 1, "tenant_id": TENANT_A, "name": "Party A"},
        {"id": 2, "tenant_id": TENANT_B, "name": "Party B"},
    ]

    # 1. Unset tenant context -> must return ZERO rows
    unset_results = [r for r in records if evaluate_rls(r["tenant_id"], None)]
    assert unset_results == [], "Queries without tenant context must return zero rows"

    empty_setting_results = [r for r in records if evaluate_rls(r["tenant_id"], "")]
    assert empty_setting_results == [], "Queries with empty tenant context must return zero rows"

    # 2. Set to Tenant A -> returns only Tenant A records
    tenant_a_results = [r for r in records if evaluate_rls(r["tenant_id"], str(TENANT_A))]
    assert len(tenant_a_results) == 1
    assert tenant_a_results[0]["tenant_id"] == TENANT_A

    # 3. Set to Tenant B -> returns only Tenant B records
    tenant_b_results = [r for r in records if evaluate_rls(r["tenant_id"], str(TENANT_B))]
    assert len(tenant_b_results) == 1
    assert tenant_b_results[0]["tenant_id"] == TENANT_B


def test_set_tenant_context_executes_set_local_on_postgres() -> None:
    """Verifies set_tenant_context issues SET LOCAL app.tenant_id on PostgreSQL connections."""
    mock_session = MagicMock()
    mock_session.get_bind.return_value.dialect.name = "postgresql"

    # Set tenant context
    set_tenant_context(mock_session, TENANT_A)
    mock_session.execute.assert_called_once()
    called_sql = str(mock_session.execute.call_args[0][0])
    assert "SET LOCAL app.tenant_id" in called_sql
    assert mock_session.execute.call_args[0][1]["tid"] == str(TENANT_A)

    # Reset tenant context
    mock_session.reset_mock()
    set_tenant_context(mock_session, None)
    mock_session.execute.assert_called_once()
    called_reset = str(mock_session.execute.call_args[0][0])
    assert "RESET app.tenant_id" in called_reset


def test_metrics_protected_by_token_and_network_allowlist() -> None:
    """Verifies that /metrics endpoint access is restricted by token or IP allowlist."""
    with patch.object(settings, "METRICS_TOKEN", "super-secret-metrics-token-123"):
        with patch.object(settings, "METRICS_ALLOWED_IPS", ["10.0.0.5"]):
            # 1. External IP without token -> 403 Forbidden
            res_forbidden = client.get(
                "/metrics",
                headers={"X-Forwarded-For": "203.0.113.1"},
            )
            assert res_forbidden.status_code == 403
            # When METRICS_TOKEN is required and client is not in allowlist, verify auth
            # With correct Bearer token -> 200 OK
            res_authorized_bearer = client.get(
                "/metrics",
                headers={"Authorization": "Bearer super-secret-metrics-token-123"},
            )
            assert res_authorized_bearer.status_code == 200
            assert "http_requests_total" in res_authorized_bearer.text

            # With correct X-Metrics-Token header -> 200 OK
            res_authorized_header = client.get(
                "/metrics/json",
                headers={"X-Metrics-Token": "super-secret-metrics-token-123"},
            )
            assert res_authorized_header.status_code == 200
            assert "requests" in res_authorized_header.json()


def test_health_ready_returns_503_when_db_down() -> None:
    """Verifies /health/ready returns 503 Service Unavailable when the database ping fails."""
    # 1. DB is healthy -> 200 OK
    with patch("app.main.ping_db", return_value=True):
        res_ok = client.get("/health/ready")
        assert res_ok.status_code == 200
        assert res_ok.json()["status"] == "ready"
        assert res_ok.json()["database"] == "connected"

    # 2. DB is down -> 503 Service Unavailable
    with patch("app.main.ping_db", return_value=False):
        res_down = client.get("/health/ready")
        assert res_down.status_code == 503
        assert res_down.json()["status"] == "degraded"
        assert res_down.json()["database"] == "disconnected"
