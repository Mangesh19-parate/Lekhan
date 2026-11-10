"""Observability middleware measuring HTTP request latency and logging with correlation IDs."""

from __future__ import annotations

import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.metrics import metrics_collector
from app.shared.logging import get_correlation_id


class ObservabilityMetricsMiddleware(BaseHTTPMiddleware):
    """Measures request duration and increments metric counters."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        start_time = time.perf_counter()
        correlation_id = get_correlation_id()

        response: Response | None = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start_time
            # Standardize endpoint path to avoid high-cardinality ID paths
            endpoint = request.url.path
            metrics_collector.record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=status_code,
                duration_seconds=duration,
            )
            if response is not None:
                response.headers["X-Correlation-ID"] = correlation_id
