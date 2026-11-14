"""ASGI middleware for request lifecycle, correlation IDs, and error wrapping."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from sqlalchemy.exc import SQLAlchemyError
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
    """Enforces maximum HTTP request body size limits (default: 10 MB per settings)."""

    def __init__(self, app: Any, max_bytes: int = 10 * 1024 * 1024) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
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

        return await call_next(request)
