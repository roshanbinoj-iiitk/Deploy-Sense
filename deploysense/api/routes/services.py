"""
DeploySense — Services API Routes

WHY THIS EXISTS:
Services represent deployable units (e.g., "payments-api", "auth-service").
A repository can contain multiple services (monorepo).
Risk scores and deployment tracking are per-service, not per-repo.

ENDPOINTS (maps to architecture/03-api-definitions.md section 3.1.3):
  GET    /services              — List all monitored services
  GET    /services/{name}       — Get service details
  GET    /services/{name}/health — Service health summary
  GET    /services/{name}/deployments — Deployment history for a service
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from deploysense.api.schemas import (
    DeploymentListResponse,
    DeploymentResponse,
    PaginationMeta,
    ServiceHealthResponse,
    ServiceResponse,
)
from deploysense.database import get_db_session
from deploysense.models import Deployment, MetricsSnapshot, Service

router = APIRouter()


# ─── GET /services ───────────────────────────────────────────────────────────


@router.get("/services", response_model=list[ServiceResponse])
async def list_services(
    db: AsyncSession = Depends(get_db_session),
) -> list[ServiceResponse]:
    """
    List all monitored services.

    PURPOSE: Dashboard sidebar showing all services with their
    stability scores and status at a glance.
    """
    result = await db.execute(select(Service).order_by(Service.name))
    services = result.scalars().all()
    return [ServiceResponse.model_validate(s) for s in services]


# ─── GET /services/{name} ───────────────────────────────────────────────────


@router.get("/services/{service_name}", response_model=ServiceResponse)
async def get_service(
    service_name: str,
    db: AsyncSession = Depends(get_db_session),
) -> ServiceResponse:
    """
    Get service details by name.

    WHY by name, not ID: Services are referenced by name everywhere
    (CLI, CI/CD, dashboards). UUIDs are internal identifiers.
    """
    result = await db.execute(select(Service).where(Service.name == service_name))
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    return ServiceResponse.model_validate(service)


# ─── GET /services/{name}/health ─────────────────────────────────────────────


@router.get("/services/{service_name}/health", response_model=ServiceHealthResponse)
async def get_service_health(
    service_name: str,
    db: AsyncSession = Depends(get_db_session),
) -> ServiceHealthResponse:
    """
    Service health summary combining latest metrics with deployment context.

    PURPOSE: Quick view of "is this service okay right now?"
    Combines the latest metrics snapshot (error rate, latency) with
    the most recent deployment version.

    WHY NOT just query Prometheus directly:
    DeploySense adds deployment context. Prometheus tells you error rate
    is 5%. DeploySense tells you error rate went from 0.1% to 5% right
    after deploying v2.1.0. That correlation is the value.
    """
    result = await db.execute(select(Service).where(Service.name == service_name))
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    # Get latest deployment version
    deploy_result = await db.execute(
        select(Deployment)
        .where(Deployment.service_id == service.id)
        .order_by(Deployment.created_at.desc())
        .limit(1)
    )
    latest_deploy = deploy_result.scalar_one_or_none()

    # Get latest metrics snapshot
    metrics_result = await db.execute(
        select(MetricsSnapshot)
        .where(MetricsSnapshot.service_id == service.id)
        .order_by(MetricsSnapshot.collected_at.desc())
        .limit(1)
    )
    latest_metrics = metrics_result.scalar_one_or_none()

    metrics_dict = None
    if latest_metrics:
        metrics_dict = {
            "error_rate": float(latest_metrics.error_rate) if latest_metrics.error_rate else None,
            "latency_p99_ms": float(latest_metrics.latency_p99_ms)
            if latest_metrics.latency_p99_ms
            else None,
            "request_rate_rps": float(latest_metrics.request_rate_rps)
            if latest_metrics.request_rate_rps
            else None,
        }

    return ServiceHealthResponse(
        service=service_name,
        status=service.status,
        current_version=latest_deploy.version if latest_deploy else None,
        metrics=metrics_dict,
    )


# ─── GET /services/{name}/deployments ────────────────────────────────────────


@router.get("/services/{service_name}/deployments", response_model=DeploymentListResponse)
async def get_service_deployments(
    service_name: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> DeploymentListResponse:
    """
    Deployment history for a specific service.

    PURPOSE: "Show me the last 20 deployments of payments-api."
    Used by the service detail page in the dashboard.
    """
    result = await db.execute(select(Service).where(Service.name == service_name))
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    query = (
        select(Deployment)
        .options(selectinload(Deployment.service))
        .where(Deployment.service_id == service.id)
        .order_by(Deployment.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    deploy_result = await db.execute(query)
    deployments = deploy_result.scalars().all()

    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count(Deployment.id)).where(Deployment.service_id == service.id)
    )
    total = count_result.scalar() or 0

    return DeploymentListResponse(
        data=[DeploymentResponse.model_validate(d) for d in deployments],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )
