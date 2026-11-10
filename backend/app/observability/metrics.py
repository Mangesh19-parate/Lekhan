"""Lightweight in-memory metrics collector and Prometheus exporter (PRD Section 10, Features F-071).

Tracks:
- HTTP request count and latency distribution.
- Document generation duration and success rates.
- PDF conversion counts and errors.
- Template linter runs and status.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Thread-safe application metrics registry with Prometheus text format exporter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._http_duration_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._http_duration_count: dict[tuple[str, str], int] = defaultdict(int)

        self._doc_generations: dict[tuple[str, str], int] = defaultdict(int)
        self._doc_gen_duration_sum: dict[str, float] = defaultdict(float)
        self._doc_gen_duration_count: dict[str, int] = defaultdict(int)

        self._pdf_conversions: dict[str, int] = defaultdict(int)
        self._lint_runs: dict[str, int] = defaultdict(int)

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Records HTTP request completion metrics."""
        with self._lock:
            self._http_requests[(method, endpoint, status_code)] += 1
            self._http_duration_sum[(method, endpoint)] += duration_seconds
            self._http_duration_count[(method, endpoint)] += 1

    def record_document_generation(
        self,
        template_id: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Records document generation metrics."""
        with self._lock:
            self._doc_generations[(template_id, status)] += 1
            self._doc_gen_duration_sum[template_id] += duration_seconds
            self._doc_gen_duration_count[template_id] += 1

    def record_pdf_conversion(self, status: str, duration_seconds: float = 0.0) -> None:
        """Records PDF conversion metrics."""
        with self._lock:
            self._pdf_conversions[status] += 1

    def record_lint_run(self, status: str) -> None:
        """Records template lint run metrics."""
        with self._lock:
            self._lint_runs[status] += 1

    def export_prometheus_text(self) -> str:
        """Generates standard Prometheus exposition format."""
        lines: list[str] = [
            "# HELP lekhan_http_requests_total Total number of HTTP requests processed",
            "# TYPE lekhan_http_requests_total counter",
        ]
        with self._lock:
            for (m, ep, code), count in sorted(self._http_requests.items()):
                lines.append(f'lekhan_http_requests_total{{method="{m}",endpoint="{ep}",status="{code}"}} {count}')

            lines.extend([
                "# HELP lekhan_http_request_duration_seconds Total latency of HTTP requests",
                "# TYPE lekhan_http_request_duration_seconds summary",
            ])
            for (m, ep), total_time in sorted(self._http_duration_sum.items()):
                c = self._http_duration_count[(m, ep)]
                lines.append(f'lekhan_http_request_duration_seconds_sum{{method="{m}",endpoint="{ep}"}} {total_time:.4f}')
                lines.append(f'lekhan_http_request_duration_seconds_count{{method="{m}",endpoint="{ep}"}} {c}')

            lines.extend([
                "# HELP lekhan_document_generations_total Total legal document generation jobs",
                "# TYPE lekhan_document_generations_total counter",
            ])
            for (tmpl, st), count in sorted(self._doc_generations.items()):
                lines.append(f'lekhan_document_generations_total{{template_id="{tmpl}",status="{st}"}} {count}')

            lines.extend([
                "# HELP lekhan_pdf_conversions_total Total PDF export conversions",
                "# TYPE lekhan_pdf_conversions_total counter",
            ])
            for st, count in sorted(self._pdf_conversions.items()):
                lines.append(f'lekhan_pdf_conversions_total{{status="{st}"}} {count}')

            lines.extend([
                "# HELP lekhan_template_lint_runs_total Total template lint operations",
                "# TYPE lekhan_template_lint_runs_total counter",
            ])
            for st, count in sorted(self._lint_runs.items()):
                lines.append(f'lekhan_template_lint_runs_total{{status="{st}"}} {count}')

        lines.append("")
        return "\n".join(lines)

    def export_json(self) -> dict[str, Any]:
        """Returns structured JSON summary of metrics."""
        with self._lock:
            return {
                "http_requests_total": sum(self._http_requests.values()),
                "document_generations_total": sum(self._doc_generations.values()),
                "pdf_conversions_total": sum(self._pdf_conversions.values()),
                "template_lint_runs_total": sum(self._lint_runs.values()),
                "endpoints": {
                    f"{m} {ep}": {
                        "count": self._http_duration_count[(m, ep)],
                        "avg_latency_ms": round(
                            (self._http_duration_sum[(m, ep)] / max(1, self._http_duration_count[(m, ep)])) * 1000, 2
                        ),
                    }
                    for (m, ep) in self._http_duration_sum
                },
            }

    def clear(self) -> None:
        """Resets all metrics."""
        with self._lock:
            self._http_requests.clear()
            self._http_duration_sum.clear()
            self._http_duration_count.clear()
            self._doc_generations.clear()
            self._doc_gen_duration_sum.clear()
            self._doc_gen_duration_count.clear()
            self._pdf_conversions.clear()
            self._lint_runs.clear()


metrics_collector = MetricsCollector()

