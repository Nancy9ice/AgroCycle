# ── Backend — AgroCycle FastAPI API ──────────────────────────────────────────
# Multi-stage build: install heavy geo dependencies once, then copy only what
# the API needs at runtime.

# ── Stage 1: dependency install ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

# System packages needed to build / link geo wheels.
# rasterio and pyproj ship bundled GDAL/PROJ in their wheels, but we still
# need a C compiler and libgomp for some transitive numpy builds.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgomp1 \
        libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Runtime system libraries (shared objects, not compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# Copy only the runtime modules the API needs.
# Intentionally excludes: ingest/, tests/, docs/, specs/, scripts/, data/out/, data/sample/
COPY --chown=app:app api/        ./api/
COPY --chown=app:app engine/     ./engine/
COPY --chown=app:app common/     ./common/
COPY --chown=app:app transform/  ./transform/
COPY --chown=app:app schema/     ./schema/
COPY --chown=app:app data/fields/ ./data/fields/
COPY --chown=app:app data/reference/ ./data/reference/

EXPOSE 8000

# Uvicorn: 2 workers is plenty for a demo with read-only pre-aggregated data.
# Override PORT via the environment if the host uses a different port.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --no-access-log"]
