# DeploySense — Multi-Stage Dockerfile
#
# ARCHITECTURE DECISIONS:
#
# 1. Multi-stage build: Separates build dependencies from runtime.
#    Build stage installs dev tools, final stage only has production deps.
#    Result: ~150MB image instead of ~800MB.
#
# 2. Single Dockerfile for all services: Uses BUILD_ARG to select which
#    service to run. This is simpler than 3 separate Dockerfiles at MVP scale.
#    When services have different dependency needs, they'll get their own.
#
# 3. Python 3.13-slim: Alpine causes C extension build issues with asyncpg.
#    Slim is ~120MB but avoids glibc compatibility problems.
#
# 4. Non-root user: Container runs as uid 1000, not root.
#    Kubernetes PSP/SecurityContext enforces this in production.
#
# USAGE:
#   docker build --build-arg SERVICE=api -t deploysense-api .
#   docker build --build-arg SERVICE=risk-engine -t deploysense-risk-engine .
#   docker build --build-arg SERVICE=worker -t deploysense-worker .

# ─── Stage 1: Build ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency spec first (Docker layer caching)
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install .

# ─── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.13-slim

# Which service to run: api | risk-engine | worker
ARG SERVICE=api
ENV SERVICE=${SERVICE}

WORKDIR /app

# Install runtime deps only (libpq for asyncpg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r deploysense && useradd -r -g deploysense deploysense

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY deploysense/ /app/deploysense/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

# Set ownership
RUN chown -R deploysense:deploysense /app

USER deploysense

# Health check (API and Risk Engine only)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port (API=8000, Risk Engine=8001)
EXPOSE 8000 8001

# Entry point based on SERVICE arg
CMD if [ "$SERVICE" = "api" ]; then \
        uvicorn deploysense.api.main:app --host 0.0.0.0 --port 8000; \
    elif [ "$SERVICE" = "risk-engine" ]; then \
        uvicorn deploysense.risk_engine.main:app --host 0.0.0.0 --port 8001; \
    elif [ "$SERVICE" = "worker" ]; then \
        python -m deploysense.worker.main; \
    else \
        echo "Unknown service: $SERVICE" && exit 1; \
    fi
