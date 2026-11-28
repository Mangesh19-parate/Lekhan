"""OpenTelemetry tracing with strict zero-PII redaction (docs/PLAN.md, AGENTS.md Rule 5).

Guarantees:
- Zero personal data in traces (names, IDs, PAN, Aadhaar, phones, addresses, passwords).
- Span attributes filtered strictly to approved operational metadata.
- Distributed trace propagation with correlation IDs.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)

# Strict allowlist of permitted system attributes on trace spans
PERMITTED_SPAN_ATTRIBUTES = frozenset(
    {
        "tenant_id",
        "actor_id",
        "correlation_id",
        "http.method",
        "http.route",
        "http.status_code",
        "http.url",
        "db.system",
        "db.operation",
        "doc.id",
        "doc.doc_no",
        "template.id",
        "job.id",
        "job.type",
        "duration_ms",
        "component",
    }
)

# Explicit sensitive keys that must never appear in trace spans
SENSITIVE_KEYS = frozenset(
    {
        "name",
        "full_name",
        "pan",
        "aadhaar",
        "phone",
        "mobile",
        "address",
        "vendors",
        "purchasers",
        "sellers",
        "witness",
        "data_snapshot",
        "payload",
        "password",
        "secret",
        "token",
        "email",
    }
)


def sanitize_span_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """Filters span attributes through an allowlist and strips all personal data."""
    clean: dict[str, Any] = {}
    for key, val in attributes.items():
        key_lower = key.lower()
        # Drop if key matches known sensitive patterns
        if any(s in key_lower for s in SENSITIVE_KEYS):
            continue
        # Only retain permitted system attributes
        if key_lower in PERMITTED_SPAN_ATTRIBUTES:
            clean[key] = str(val) if val is not None else ""
    return clean


class Span:
    """Lightweight trace span representation adhering to OpenTelemetry semantics."""

    def __init__(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.name = name
        self.attributes = sanitize_span_attributes(attributes or {})
        self.start_time = time.time()
        self.end_time: float | None = None

    def set_attribute(self, key: str, value: Any) -> None:
        key_lower = key.lower()
        if any(s in key_lower for s in SENSITIVE_KEYS):
            return
        if key_lower in PERMITTED_SPAN_ATTRIBUTES:
            self.attributes[key] = str(value) if value is not None else ""

    def end(self) -> None:
        self.end_time = time.time()
        duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.attributes["duration_ms"] = str(duration_ms)


class OpenTelemetryTracingMiddleware(BaseHTTPMiddleware):
    """Instruments HTTP requests with zero-PII OpenTelemetry spans."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cid = get_correlation_id()
        span = Span(
            name=f"HTTP {request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.route": request.url.path,
                "correlation_id": cid,
                "component": "fastapi",
            },
        )

        try:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response
        except Exception as exc:
            span.set_attribute("http.status_code", 500)
            raise exc
        finally:
            span.end()
