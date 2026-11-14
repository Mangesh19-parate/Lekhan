"""FastAPI main entrypoint for Lekhan (Backend Core with Auth, Tenancy, and Jobs)."""

import hmac
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.db import engine, ping_db
from app.api.admin import router as admin_router
from app.api.advisory import router as advisory_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.parties import router as parties_router
from app.api.pilot import router as pilot_router
from app.api.portal import router as portal_router
from app.api.properties import router as properties_router
from app.api.review import router as review_router
from app.api.templates_admin import router as templates_admin_router
from app.config import get_settings
from app.lang_packs.marathi import number_to_words_mr
from app.observability import (
    ObservabilityMetricsMiddleware,
    OpenTelemetryTracingMiddleware,
    init_sentry,
    metrics_collector,
)
from app.shared.errors import AppError, problem_json_response
from app.shared.logging import get_correlation_id, get_logger, setup_logging
from app.shared.middleware import CorrelationIdMiddleware, RequestSizeLimitMiddleware

# Configure structured logging with correlation ID
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Initialize Sentry error reporting with PII scrubbing
init_sentry(environment=settings.ENV)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup warmup and graceful shutdown."""
    logger.info("Lekhan API started successfully [env=%s]", settings.ENV)
    yield
    logger.info("Graceful shutdown initiated: disposing database connection pools...")
    engine.dispose()
    logger.info("Database connection pools disposed cleanly.")


app = FastAPI(
    title="Lekhan API",
    description="Multilingual Property Legal Drafting API (Phase 1)",
    version="0.1.0",
    docs_url="/api/docs" if settings.is_dev else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.is_dev else None,
    lifespan=lifespan,
)

# 1. OpenTelemetry Tracing Middleware (zero-PII distributed traces)
app.add_middleware(OpenTelemetryTracingMiddleware)

# 2. Request payload size limit middleware (enforces MAX_REQUEST_SIZE_BYTES)
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_SIZE_BYTES)

# 3. Observability and Metrics middleware
app.add_middleware(ObservabilityMetricsMiddleware)

# 4. Correlation ID and structured logging middleware
app.add_middleware(CorrelationIdMiddleware)

# 5. CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)


# --- RFC 9457 Structured Error Contract Handlers (application/problem+json everywhere) ---


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Translates custom domain AppError to RFC 9457 problem+json."""
    return problem_json_response(
        status_code=exc.status_code,
        code=exc.code,
        detail=exc.message,
        errors=exc.errors,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Translates all FastAPI and Starlette HTTPExceptions to RFC 9457 problem+json."""
    code = f"HTTP_{exc.status_code}"
    detail_str = str(exc.detail) if exc.detail else "An HTTP error occurred."
    return problem_json_response(
        status_code=exc.status_code,
        code=code,
        detail=detail_str,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Translates Pydantic request validation errors into RFC 9457 problem+json."""
    clean_errors = [
        {"loc": [str(loc_item) for loc_item in err.get("loc", [])], "msg": str(err.get("msg", "")), "type": str(err.get("type", ""))}
        for err in exc.errors()
    ]
    return problem_json_response(
        status_code=422,
        code="VALIDATION_ERROR",
        detail="Request payload validation failed.",
        errors=clean_errors,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Translates database exceptions into RFC 9457 503 Service Unavailable problem+json."""
    cid = get_correlation_id()
    logger.error("Database failure on request %s [cid=%s]: %s", request.url.path, cid, exc)
    return problem_json_response(
        status_code=503,
        code="DATABASE_UNAVAILABLE",
        detail="Database service unavailable. Please retry shortly.",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled errors and ensures RFC 9457 500 problem+json is always returned."""
    cid = get_correlation_id()
    logger.exception("Unhandled server exception [cid=%s]: %s", cid, exc)
    return problem_json_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        detail="An unexpected internal server error occurred. Please contact support quoting the correlation ID.",
    )


# Include Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(documents_router)
app.include_router(parties_router)
app.include_router(properties_router)
app.include_router(review_router)
app.include_router(templates_admin_router)
app.include_router(pilot_router)
app.include_router(advisory_router)
app.include_router(portal_router)
app.include_router(admin_router)


# --- Health Probes (docs/PLAN.md Week 4) ---


@app.get("/health/live", summary="Liveness probe")
def health_live() -> dict[str, str]:
    """Basic liveness check verifying the HTTP process is running."""
    return {"status": "ok"}


@app.get("/health/ready", summary="Readiness probe")
def health_ready(response: Response) -> dict[str, Any]:
    """Readiness check verifying database connectivity."""
    db_ok = ping_db()
    if not db_ok:
        logger.warning("Readiness probe: database connection down")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "disconnected"}
    return {"status": "ready", "database": "connected"}


# --- Observability Metrics (docs/PLAN.md Week 18, PRD Section 10) ---


def verify_metrics_access(
    request: Request,
    authorization: str | None = Header(None),
    x_metrics_token: str | None = Header(None, alias="X-Metrics-Token"),
) -> None:
    """Protects /metrics endpoints via network IP allowlist or secret token."""
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "127.0.0.1")
    )

    token_valid = False
    if settings.METRICS_TOKEN:
        bearer_token = None
        if authorization and authorization.startswith("Bearer "):
            bearer_token = authorization.split("Bearer ", 1)[1].strip()
        supplied = x_metrics_token or bearer_token
        if supplied and hmac.compare_digest(supplied, settings.METRICS_TOKEN):
            token_valid = True

    ip_allowed = client_ip in settings.METRICS_ALLOWED_IPS or (
        not request.headers.get("X-Forwarded-For")
        and client_ip in ("127.0.0.1", "::1", "localhost", "testclient")
    )

    if not (token_valid or ip_allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Metrics endpoint access is restricted by policy.",
        )


@app.get(
    "/metrics",
    summary="Prometheus metrics exposition",
    response_class=Response,
    dependencies=[Depends(verify_metrics_access)],
)
def get_prometheus_metrics() -> Response:
    """Returns metrics in Prometheus text exposition format."""
    text_data = metrics_collector.export_prometheus_text()
    return Response(content=text_data, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get(
    "/metrics/json",
    summary="JSON metrics summary",
    dependencies=[Depends(verify_metrics_access)],
)
def get_metrics_json() -> dict[str, Any]:
    """Returns structured JSON summary of application metrics."""
    return metrics_collector.export_json()


# --- Live Calculation Helper ---


@app.get("/api/v1/helpers/amount-to-words", summary="Live Marathi Amount in Words")
def amount_to_words(amount: int) -> dict[str, str]:
    """Returns the live Marathi currency amount in words."""
    words = number_to_words_mr(amount, currency=True)
    return {"amount": str(amount), "words_mr": words}


# --- Standalone Interactive Form UI (Week 7 Milestone & Week 12 Form Engine) ---


@app.get("/form", response_class=HTMLResponse, summary="Schema-Driven Form Engine UI")
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def get_form_engine_ui() -> str:
    """Serves the complete schema-driven dynamic drafting form styled per DESIGN.md."""
    from pathlib import Path

    html_path = Path(__file__).parent / "static" / "form_engine.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Lekhan Form Engine</h1>"


@app.get(
    "/templates/admin", response_class=HTMLResponse, summary="Template Admin & Lifecycle Dashboard"
)
def get_template_admin_ui() -> str:
    """Serves the template admin and DocxLinter audit dashboard."""
    from pathlib import Path

    html_path = Path(__file__).parent / "static" / "template_admin.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Template Admin</h1>"


@app.get("/pilot", response_class=HTMLResponse, summary="Gate 2 Pilot Drafter Dashboard")
def get_pilot_ui() -> str:
    """Serves the Gate 2 Pilot Drafter Feedback & Corrections Dashboard."""
    from pathlib import Path

    html_path = Path(__file__).parent / "static" / "pilot_dashboard.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Lekhan Pilot Dashboard</h1>"


@app.get("/spike", response_class=HTMLResponse, summary="Interactive Spike Drafting Form")
def get_spike_ui() -> str:
    """Serves the bilingual Marathi drafting form styled per DESIGN.md."""
    from pathlib import Path

    html_path = Path(__file__).parent / "static" / "spike.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Lekhan Drafting UI</h1><p>Visit /api/docs for OpenAPI documentation.</p>"
