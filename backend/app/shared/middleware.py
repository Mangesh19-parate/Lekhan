"""ASGI middleware for request lifecycle, correlation IDs, security headers, and size limits."""

from __future__ import annotations

import uuid
from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.errors import problem_json_response
from app.shared.ids import uuid7_str
from app.shared.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)


class PayloadTooLargeError(Exception):
    """Raised when request payload exceeds configured max_bytes limit."""

    pass


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Enforces X-Correlation-ID across every HTTP request and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        header_cid = request.headers.get("X-Correlation-ID")

        # Validate UUID format per RFC 4122/9562; regenerate if malformed
        cid: str
        if header_cid:
            try:
                parsed = uuid.UUID(header_cid.strip())
                cid = str(parsed)
            except (ValueError, AttributeError):
                cid = uuid7_str()
        else:
            cid = uuid7_str()

        token = correlation_id_ctx.set(cid)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = cid
            return response
        except SQLAlchemyError as db_exc:
            logger.error("Database failure caught in middleware [cid=%s]: %s", cid, db_exc)
            return problem_json_response(
                status_code=503,
                code="DATABASE_UNAVAILABLE",
                detail="Database service unavailable. Please retry shortly.",
            )
        except Exception:
            logger.exception("Unhandled request error caught in middleware [cid=%s]", cid)
            return problem_json_response(
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                detail="An unexpected error occurred. Please quote the correlation ID.",
            )
        finally:
            correlation_id_ctx.reset(token)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces maximum HTTP request body size limits on both Content-Length and streamed/chunked requests."""

    def __init__(self, app: Any, max_bytes: int = 10 * 1024 * 1024) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # 1. Quick upfront check on Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return problem_json_response(
                        status_code=413,
                        code="PAYLOAD_TOO_LARGE",
                        detail=f"Request body size exceeds maximum limit of {self.max_bytes} bytes.",
                    )
            except ValueError:
                pass

        # 2. Active byte counter on streamed/chunked request bodies
        total_received = 0
        original_receive = request._receive

        async def limited_receive() -> dict[str, Any]:
            nonlocal total_received
            message = await original_receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                total_received += len(chunk)
                if total_received > self.max_bytes:
                    raise PayloadTooLargeError(
                        f"Request body size exceeds maximum limit of {self.max_bytes} bytes."
                    )
            return dict(message)

        request._receive = limited_receive

        try:
            return await call_next(request)
        except PayloadTooLargeError as exc:
            return problem_json_response(
                status_code=413,
                code="PAYLOAD_TOO_LARGE",
                detail=str(exc),
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces defense-in-depth security headers (CSP, HSTS, nosniff, frame-ancestors none)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self';"
        )
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response
