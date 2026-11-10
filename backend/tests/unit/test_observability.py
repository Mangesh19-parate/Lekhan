"""Unit tests for Observability, Metrics, and Sentry PII Redaction (PRD Section 10, Features F-071).

Verifies:
1. Sentry PII scrubbing strictly removes Aadhaar, PAN, names, addresses (AGENTS.md Hard Rule 5).
2. Metrics collector tracks HTTP latency and counts accurately.
3. Prometheus text format export complies with standard format.
4. JSON metrics summary returns endpoint averages.
"""

from app.observability.metrics import MetricsCollector
from app.observability.sentry import sentry_before_send


def test_sentry_pii_scrubbing() -> None:
    """Verifies that personal identifiers are completely redacted from Sentry payloads."""
    raw_payload = {
        "event_id": "12345",
        "user_id": "usr_99",
        "request": {
            "data": {
                "full_name": "Rajesh Deshmukh",
                "pan": "ABCDE1234F",
                "aadhaar_last4": "5678",
                "address": "Plot 42, Wardha Road, Nagpur",
                "phone": "+91-9876543210",
                "property_details": {
                    "plot_no": "42",
                    "mouza": "Besa",
                },
            }
        },
        "breadcrumbs": {
            "values": [
                {
                    "message": "Form submission started",
                    "data": {"vendors": [{"name": "Private Client"}]},
                }
            ]
        },
    }

    sanitized = sentry_before_send(raw_payload, hint={})

    # Verify sensitive fields are replaced
    req_data = sanitized["request"]["data"]
    assert req_data["full_name"] == "[REDACTED_PII]"
    assert req_data["pan"] == "[REDACTED_PII]"
    assert req_data["aadhaar_last4"] == "[REDACTED_PII]"
    assert req_data["address"] == "[REDACTED_PII]"
    assert req_data["phone"] == "[REDACTED_PII]"

    # Non-sensitive structure preserved
    assert req_data["property_details"]["plot_no"] == "42"

    # Breadcrumb PII scrubbed
    crumb_data = sanitized["breadcrumbs"]["values"][0]["data"]
    assert crumb_data["vendors"] == "[REDACTED_PII]"


def test_metrics_collector_and_prometheus_export() -> None:
    """Verifies metric collection, Prometheus formatting, and JSON export."""
    collector = MetricsCollector()

    # Record sample metrics
    collector.record_http_request("GET", "/health/live", 200, 0.005)
    collector.record_http_request("GET", "/health/live", 200, 0.007)
    collector.record_http_request("POST", "/api/v1/documents", 201, 0.045)
    collector.record_document_generation("sale_deed_plot_mr", "succeeded", 0.040)
    collector.record_pdf_conversion("succeeded", 0.080)
    collector.record_lint_run("passed")

    # 1. Prometheus text format export
    prom_text = collector.export_prometheus_text()
    assert (
        'lekhan_http_requests_total{method="GET",endpoint="/health/live",status="200"} 2'
        in prom_text
    )
    assert (
        'lekhan_http_requests_total{method="POST",endpoint="/api/v1/documents",status="201"} 1'
        in prom_text
    )
    assert (
        'lekhan_document_generations_total{template_id="sale_deed_plot_mr",status="succeeded"} 1'
        in prom_text
    )
    assert 'lekhan_pdf_conversions_total{status="succeeded"} 1' in prom_text
    assert 'lekhan_template_lint_runs_total{status="passed"} 1' in prom_text

    # 2. JSON summary export
    json_summary = collector.export_json()
    assert json_summary["http_requests_total"] == 3
    assert json_summary["document_generations_total"] == 1
    assert json_summary["pdf_conversions_total"] == 1
    assert "GET /health/live" in json_summary["endpoints"]
    assert json_summary["endpoints"]["GET /health/live"]["count"] == 2
