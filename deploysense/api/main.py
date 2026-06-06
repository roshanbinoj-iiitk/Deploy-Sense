"""
DeploySense — API Service Entry Point

WHY THIS EXISTS:
This is the main FastAPI application for the API Service (Service 1).
It handles all external-facing HTTP traffic:
  - Authentication (GitHub OAuth)
  - Webhook ingestion (GitHub, ArgoCD, Prometheus)
  - Deployment CRUD
  - Dashboard APIs
  - WebSocket connections

ARCHITECTURE DECISIONS:

1. FastAPI over Flask/Django:
   - Async-native (matches our asyncpg database driver)
   - Auto-generates OpenAPI docs (API-first development)
   - Pydantic validation built-in (type safety at the boundary)
   - Dependency injection system (clean testability)

2. Lifespan handler over @app.on_event:
   - @app.on_event is deprecated in FastAPI 0.109+
   - Lifespan gives us proper startup/shutdown lifecycle
   - Resources (DB pool, Redis) are created once, cleaned up properly

3. /health and /metrics at root, not behind /api/v1:
   - Kubernetes probes need a stable path that doesn't change with API versions
   - Prometheus scrapes /metrics — shouldn't require auth

PORT: 8000 (architecture doc: Service 1)
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)
from starlette.requests import Request
from starlette.responses import Response

from deploysense.core import get_settings
from deploysense.logging import get_logger, setup_logging

# ─── Application Metrics ─────────────────────────────────────────────────────
# These are the custom Prometheus metrics for the API Service.
# They map directly to architecture/07-observability.md

REQUEST_COUNT = Counter(
    "deploysense_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "deploysense_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

WEBHOOK_COUNT = Counter(
    "deploysense_github_webhook_events_total",
    "Total GitHub webhook events received",
    ["event_type"],
)

logger = get_logger(__name__)


# ─── Application Lifespan ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup: Initialize logging, verify DB connectivity, warm caches.
    Shutdown: Close DB connections, flush metrics.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging()
    settings = get_settings()
    logger.info(
        "api_service_starting",
        environment=settings.environment,
        debug=settings.debug,
    )

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("api_service_shutting_down")
    from deploysense.database.session import engine
    await engine.dispose()


# ─── FastAPI Application ─────────────────────────────────────────────────────

app = FastAPI(
    title="DeploySense",
    description="Deployment Intelligence Platform — predicts deployment risk and evaluates deployment health",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
# Allow all origins in development, restrict in production.
# WHY: Frontend dashboard needs to call the API from a different origin.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if get_settings().is_development else ["https://app.deploysense.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Security Middleware (Phase 3) ───────────────────────────────────────────
# Rate limiting + security headers. Applied after CORS.

from deploysense.api.security import apply_security_middleware

apply_security_middleware(app)


# ─── Middleware: Metrics ─────────────────────────────────────────────────────

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Record request count and latency for every HTTP request."""
    import time

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    path = request.url.path
    # Normalize path to avoid high-cardinality labels
    # /api/v1/deployments/abc123 → /api/v1/deployments/{id}
    if path.startswith("/api/"):
        parts = path.split("/")
        if len(parts) > 4:
            parts[4] = "{id}"
        path = "/".join(parts)

    REQUEST_COUNT.labels(
        method=request.method,
        path=path,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        path=path,
    ).observe(duration)

    return response


# ─── Health Check ────────────────────────────────────────────────────────────
# Kubernetes liveness + readiness probes hit this endpoint.
# If the service can respond, it's alive. For readiness, we'd check DB
# connectivity — but for MVP, a simple 200 is sufficient.

@app.get("/health", tags=["infrastructure"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for Kubernetes probes.

    Returns 200 if the service is running.
    Kubernetes liveness probe: GET /health
    Kubernetes readiness probe: GET /health
    """
    return {"status": "healthy", "service": "api-service"}


# ─── Prometheus Metrics ──────────────────────────────────────────────────────

@app.get("/metrics", tags=["infrastructure"])
async def prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Exposes all custom application metrics in Prometheus exposition format.
    Scraped by Prometheus every 15s (see infra/prometheus/prometheus.yml).
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ─── API Routes ──────────────────────────────────────────────────────────────
# Import and include routers from the api package.
# Each router handles a specific domain (deployments, risk, services, etc.)

from deploysense.api.routes import admin, ai, alerts, auth, deployments, repositories, services, webhooks

app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(deployments.router, prefix="/api/v1", tags=["deployments"])
app.include_router(services.router, prefix="/api/v1", tags=["services"])
app.include_router(repositories.router, prefix="/api/v1", tags=["repositories"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(ai.router, prefix="/api/v1", tags=["ai-analysis"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])


# ─── WebSocket (Phase 2) ────────────────────────────────────────────────────
# Real-time event streaming for the dashboard.

from fastapi import WebSocket, WebSocketDisconnect
from deploysense.api.websocket import ws_manager

@app.websocket("/ws/deployments")
async def websocket_deployments(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time deployment events.

    EVENTS STREAMED:
      - deployment.created / deployment.updated
      - risk.updated
      - alert.created
      - analysis.completed

    CLIENT USAGE:
      const ws = new WebSocket('ws://localhost:8000/ws/deployments');
      ws.onmessage = (e) => { const event = JSON.parse(e.data); ... };
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send pings or subscribe
            data = await websocket.receive_text()
            # Future: Parse subscription filters here
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ─── Dashboard Routes (Sprint 3) ────────────────────────────────────────────
# Server-rendered dashboard UI using Jinja2 templates.

from deploysense.dashboard.routes import router as dashboard_router

app.include_router(dashboard_router, tags=["dashboard"])

# ─── Static Files ────────────────────────────────────────────────────────────

from starlette.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="deploysense/static"), name="static")


# ─── Root ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["infrastructure"])
async def root() -> dict[str, str]:
    """Root endpoint — returns service info."""
    return {
        "service": "deploysense-api",
        "version": "0.2.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "websocket": "/ws/deployments",
    }
