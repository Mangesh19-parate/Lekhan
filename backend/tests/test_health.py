"""Health check tests verifying liveness and readiness."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_live() -> None:
    """Verifies that liveness probe returns HTTP 200 with status ok and X-Correlation-ID."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Correlation-ID" in response.headers


def test_health_ready() -> None:
    """Verifies that readiness probe returns HTTP 200."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] in ("ready", "degraded")
