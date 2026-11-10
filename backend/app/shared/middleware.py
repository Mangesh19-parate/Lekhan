"""ASGI middleware for request lifecycle, correlation IDs, and error wrapping."""

from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.errors import problem_json_response
from app.shared.ids import uuid7_str
from app.shared.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Enforces X-Correlation-ID across every HTTP request and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        header_cid = request.headers.get("X-Correlation-ID")

        # Validate header if present, else generate fresh UUIDv7
        cid = header_cid.strip() if header_cid and header_cid.strip() else uuid7_str()
        token = correlation_id_ctx.set(cid)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = cid
            return response
        except Exception as exc:
            logger.exception("Unhandled request error caught in middleware")
            return problem_json_response(
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                detail="An unexpected error occurred. Please quote the correlation ID.",
            )
        finally:
            correlation_id_ctx.reset(token)

