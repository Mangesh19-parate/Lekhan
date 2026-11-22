"""Locust load test suite for Lekhan API.

Simulates concurrent drafter and API traffic with documented p95 targets:
- Read / Health p95: < 200ms
- Computation / Preview p95: < 800ms
- Failure rate: < 1%

Run with:
    locust -f backend/tests/load/locustfile.py --headless -u 20 -r 2 -t 3m --host http://localhost:8000
"""

from locust import HttpUser, task, between


class LekhanApiUser(HttpUser):
    wait_time = between(1.0, 2.5)

    @task(3)
    def check_health(self) -> None:
        """Probe readiness and pool health."""
        self.client.get("/health/ready", name="/health/ready")

    @task(2)
    def convert_amount(self) -> None:
        """Helper conversion utility."""
        self.client.post(
            "/api/v1/helpers/amount-to-words",
            json={"amount": 750000, "language": "mr"},
            name="/api/v1/helpers/amount-to-words",
        )

    @task(1)
    def document_preview_or_metrics(self) -> None:
        """Simulate document drafting activity."""
        self.client.get(
            "/metrics",
            headers={"Authorization": "Bearer test-internal-token"},
            name="/metrics",
        )

