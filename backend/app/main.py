"""FastAPI main entrypoint for Lekhan (Backend Core with Auth, Tenancy, and Jobs)."""

from typing import Any
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.adapters.db import ping_db
from app.api.advisory import router as advisory_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.parties import router as parties_router
from app.api.pilot import router as pilot_router
from app.api.portal import router as portal_router
from app.api.properties import router as properties_router
from app.api.review import router as review_router
from app.api.templates_admin import router as templates_admin_router
from app.observability import ObservabilityMetricsMiddleware, init_sentry, metrics_collector
from app.config import get_settings
from app.generation.spike_engine import (
    PlotSaleDeedInput,
    SpikeGenerationError,
    generate_plot_sale_deed_docx,
)
from app.lang_packs.marathi import number_to_words_mr
from app.shared.logging import get_logger, setup_logging
from app.shared.middleware import CorrelationIdMiddleware

# Configure structured logging with correlation ID
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Initialize Sentry error reporting with PII scrubbing
init_sentry(environment=settings.ENV)

app = FastAPI(
    title="Lekhan API",
    description="Multilingual Property Legal Drafting API (Phase 1)",
    version="0.1.0",
    docs_url="/api/docs" if settings.is_dev else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.is_dev else None,
)

# Observability and Metrics middleware
app.add_middleware(ObservabilityMetricsMiddleware)

# Correlation ID and structured logging middleware
app.add_middleware(CorrelationIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(parties_router)
app.include_router(properties_router)
app.include_router(review_router)
app.include_router(templates_admin_router)
app.include_router(pilot_router)
app.include_router(advisory_router)
app.include_router(portal_router)


# --- Health Probes (docs/PLAN.md Week 4) ---

@app.get("/health/live", summary="Liveness probe")
def health_live() -> dict[str, str]:
    """Basic liveness check verifying the HTTP process is running."""
    return {"status": "ok"}


@app.get("/health/ready", summary="Readiness probe")
def health_ready() -> dict[str, Any]:
    """Readiness check verifying database connectivity."""
    db_ok = ping_db()
    if not db_ok and not settings.is_test:
        logger.warning("Readiness probe: database connection degraded")
        return {"status": "degraded", "database": "disconnected"}
    return {"status": "ready", "database": "connected" if db_ok else "mocked"}


# --- Observability Metrics (docs/PLAN.md Week 18, PRD Section 10) ---

@app.get("/metrics", summary="Prometheus metrics exposition", response_class=Response)
def get_prometheus_metrics() -> Response:
    """Returns metrics in Prometheus text exposition format."""
    text_data = metrics_collector.export_prometheus_text()
    return Response(content=text_data, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/metrics/json", summary="JSON metrics summary")
def get_metrics_json() -> dict[str, Any]:
    """Returns structured JSON summary of application metrics."""
    return metrics_collector.export_json()


# --- Live Calculation Helper ---

@app.get("/api/v1/helpers/amount-to-words", summary="Live Marathi Amount in Words")
def amount_to_words(amount: int) -> dict[str, str]:
    """Returns the live Marathi currency amount in words."""
    words = number_to_words_mr(amount, currency=True)
    return {"amount": str(amount), "words_mr": words}


# --- Generation Direct Endpoint (Spike legacy compatibility) ---

@app.post(
    "/api/v1/documents/generate-spike",
    summary="Generate Marathi Plot Sale Deed Direct",
    response_class=Response,
)
def generate_spike_document(payload: PlotSaleDeedInput) -> Response:
    """Renders the approved Marathi Plot Sale Deed template directly into a DOCX file."""
    try:
        docx_bytes = generate_plot_sale_deed_docx(payload)
    except SpikeGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("Document generation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {e}",
        ) from e

    filename = f"Sale_Deed_Plot_{payload.property_details.plot_no}_{payload.property_details.mouza}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


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


@app.get("/templates/admin", response_class=HTMLResponse, summary="Template Admin & Lifecycle Dashboard")
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
