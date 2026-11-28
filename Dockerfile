# ==============================================================================
# Multi-stage Production Dockerfile for Lekhan Backend (API & Worker)
# Adheres to:
# - Non-root execution (UID 10001)
# - Read-only root filesystem compatibility
# - Minimal attack surface (multi-stage python:3.12-slim-bookworm)
# - LibreOffice & Devanagari fonts for accurate DOCX -> PDF generation
# ==============================================================================

# Stage 1: Build virtualenv and install dependencies
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/pyproject.toml backend/README.md /build/backend/
COPY backend/app /build/backend/app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/build/backend"

# Stage 2: Hardened Runtime Container
FROM python:3.12-slim-bookworm AS runtime

# System runtime dependencies: libpq, LibreOffice (headless), Devanagari fonts, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-nogui \
    fonts-deva \
    fonts-lohit-deva \
    fonts-noto-core \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group (UID 10001)
RUN groupadd -g 10001 lekhan && \
    useradd -u 10001 -g lekhan -m -d /app -s /bin/bash lekhan

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    STORAGE_PATH=/var/storage \
    SOFFICE_BIN=soffice \
    HOME=/app

# Prepare application directories and mountpoints
WORKDIR /app/backend

RUN mkdir -p /var/storage /app/var /app/.cache /tmp && \
    chown -R lekhan:lekhan /app /var/storage /tmp

# Copy backend application code and approved templates
COPY --chown=lekhan:lekhan backend /app/backend
COPY --chown=lekhan:lekhan templates-library /app/templates-library

# Switch to non-root user
USER 10001:10001

# Healthcheck probing live API endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/live || exit 1

EXPOSE 8000

# Default command: FastAPI API server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
