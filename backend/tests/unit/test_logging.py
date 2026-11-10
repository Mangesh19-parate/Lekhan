"""Unit tests for request correlation ID middleware and problem+json responses."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_correlation_id_generated_when_absent() -> None:
    """Verifies that an X-Correlation-ID is generated and returned in headers."""
    response = client.get("/health/live")
    assert response.status_code == 200
    cid = response.headers.get("X-Correlation-ID")
    assert cid is not None
    assert len(cid) == 36


def test_correlation_id_propagated_from_header() -> None:
    """Verifies that client-supplied X-Correlation-ID is preserved across request lifecycle."""
    custom_cid = "0193132e-504f-7a1b-8000-customcid123"
    response = client.get("/health/live", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_cid

