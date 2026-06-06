"""
DeploySense — Risk Engine Service

WHY THIS IS A SEPARATE SERVICE (architecture/02-microservices.md, Service 2):
The Risk Engine runs independently because:
  1. Risk computation is CPU-intensive (ML model inference in Phase 2)
  2. It must remain available even if the API Service is under load
  3. It scales independently based on risk evaluation volume
  4. Clear ownership boundary: risk logic vs API logic

PORT: 8001 (architecture doc: Service 2)
COMMUNICATION: REST (internal APIs, no external traffic)

RISK SCORING ALGORITHM:
Phase 1 (MVP): Weighted heuristic scoring (this implementation)
Phase 2: ML model (XGBoost/LightGBM) trained on historical outcomes
Phase 3: Online learning model that adapts per organization

RISK LEVELS (architecture/02-microservices.md):
  0-25:   LOW       → Auto-approve
  26-50:  MODERATE  → Approve + enhanced monitoring
  51-75:  HIGH      → Require manual approval
  76-100: CRITICAL  → Block deployment
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from deploysense.logging import get_logger, setup_logging

# ─── Risk Engine Metrics ─────────────────────────────────────────────────────

RISK_CALCULATIONS = Counter(
    "deploysense_risk_calculations_total",
    "Total risk calculations performed",
    ["risk_level"],
)

RISK_DURATION = Histogram(
    "deploysense_risk_calculation_duration_seconds",
    "Risk calculation duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

RISK_ERRORS = Counter(
    "deploysense_risk_engine_errors_total",
    "Total risk engine errors",
    ["error_type"],
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("risk_engine_starting")
    yield
    logger.info("risk_engine_shutting_down")
    from deploysense.database.session import engine
    await engine.dispose()


app = FastAPI(
    title="DeploySense Risk Engine",
    description="Internal service for deployment risk evaluation",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)


# ─── Health & Metrics ────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "risk-engine"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ─── Import Risk Routes ─────────────────────────────────────────────────────

from deploysense.risk_engine.routes import router as risk_router

app.include_router(risk_router)
