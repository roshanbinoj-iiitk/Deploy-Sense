"""
DeploySense — Repository API Routes

WHY THIS EXISTS:
Repositories are the starting point. Before DeploySense can track deployments
or evaluate risk, it needs to know which GitHub repositories to monitor.

ENDPOINTS (maps to architecture/03-api-definitions.md section 3.1.4):
  GET    /repositories              — List connected repositories
  POST   /repositories              — Connect a GitHub repository
  GET    /repositories/{id}         — Get repository details
  DELETE /repositories/{id}         — Disconnect a repository
  POST   /repositories/{id}/sync    — Trigger manual sync

FLOW:
  1. User connects a repo via POST /repositories (provides owner + name)
  2. Worker Service syncs PR history in background
  3. Webhooks deliver real-time updates going forward
  4. Deployments are tracked per-service within the repo
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deploysense.api.auth import get_current_user
from deploysense.database import get_db_session
from deploysense.logging import get_logger
from deploysense.models import Repository, User

logger = get_logger(__name__)

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RepositoryCreate(BaseModel):
    """Request: Connect a GitHub repository."""
    owner: str = Field(..., min_length=1, max_length=255)
    repository: str = Field(..., min_length=1, max_length=255)


class RepositoryResponse(BaseModel):
    """Response: Repository information."""
    id: uuid.UUID
    owner: str
    repository_name: str
    default_branch: str
    status: str
    created_at: str  # ISO format

    model_config = {"from_attributes": True}


# ─── GET /repositories ──────────────────────────────────────────────────────

@router.get("/repositories", response_model=list[RepositoryResponse])
async def list_repositories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RepositoryResponse]:
    """
    List all connected repositories.

    FUTURE: Filter by organization_id from the authenticated user.
    For MVP, returns all repositories (single-tenant).
    """
    result = await db.execute(
        select(Repository).order_by(Repository.created_at.desc())
    )
    repos = result.scalars().all()

    return [
        RepositoryResponse(
            id=r.id,
            owner=r.owner,
            repository_name=r.repository_name,
            default_branch=r.default_branch or "main",
            status=r.status or "ACTIVE",
            created_at=r.created_at.isoformat(),
        )
        for r in repos
    ]


# ─── POST /repositories ─────────────────────────────────────────────────────

@router.post("/repositories", response_model=RepositoryResponse, status_code=201)
async def connect_repository(
    body: RepositoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RepositoryResponse:
    """
    Connect a GitHub repository to DeploySense.

    WHAT HAPPENS:
      1. Create repository record
      2. Worker Service picks it up on next sync cycle (or trigger manual)
      3. PR history is backfilled
      4. Webhook setup instruction returned (manual for MVP)

    TRADEOFF: We don't automatically install the GitHub webhook.
    That requires a GitHub App (not just OAuth). For MVP, the user
    manually adds the webhook URL in GitHub repository settings.

    FUTURE: GitHub App integration for automatic webhook installation.

    DUPLICATE CHECK: If owner+repo already exists, return 409.
    """
    # Check for duplicate
    existing = await db.execute(
        select(Repository).where(
            Repository.owner == body.owner,
            Repository.repository_name == body.repository,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Repository {body.owner}/{body.repository} is already connected",
        )

    repo = Repository(
        organization_id=user.organization_id,
        owner=body.owner,
        repository_name=body.repository,
        default_branch="main",
        status="CONNECTED",
    )
    db.add(repo)
    await db.flush()

    logger.info(
        "repository_connected",
        owner=body.owner,
        repository=body.repository,
        connected_by=user.github_username,
    )

    return RepositoryResponse(
        id=repo.id,
        owner=repo.owner,
        repository_name=repo.repository_name,
        default_branch=repo.default_branch or "main",
        status=repo.status or "CONNECTED",
        created_at=repo.created_at.isoformat(),
    )


# ─── GET /repositories/{id} ─────────────────────────────────────────────────

@router.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RepositoryResponse:
    """Get repository details by ID."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryResponse(
        id=repo.id,
        owner=repo.owner,
        repository_name=repo.repository_name,
        default_branch=repo.default_branch or "main",
        status=repo.status or "ACTIVE",
        created_at=repo.created_at.isoformat(),
    )


# ─── DELETE /repositories/{id} ──────────────────────────────────────────────

@router.delete("/repositories/{repo_id}", status_code=204)
async def disconnect_repository(
    repo_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Disconnect a repository from DeploySense.

    WHAT HAPPENS:
      - Repository status set to DISCONNECTED (soft delete)
      - Historical data is preserved for audit/analysis
      - No more syncs or webhook processing for this repo

    WHY soft delete:
      Hard deleting cascades to services → deployments → risk assessments.
      That's years of deployment intelligence data destroyed. We mark
      as DISCONNECTED and exclude from active queries.
    """
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.status = "DISCONNECTED"

    logger.info(
        "repository_disconnected",
        owner=repo.owner,
        repository=repo.repository_name,
        disconnected_by=user.github_username,
    )


# ─── POST /repositories/{id}/sync ───────────────────────────────────────────

@router.post("/repositories/{repo_id}/sync")
async def trigger_sync(
    repo_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Manually trigger a repository sync.

    PURPOSE: After connecting a new repo, the user can trigger an
    immediate sync instead of waiting for the 15-minute worker cycle.

    TRADEOFF: This is synchronous for MVP. In production, this should
    enqueue a background job and return a job_id for polling.
    """
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    logger.info(
        "repository_sync_triggered",
        owner=repo.owner,
        repository=repo.repository_name,
        triggered_by=user.github_username,
    )

    # TODO (Phase 1 Sprint 1): Actually call GitHub API and sync PRs
    # For now, acknowledge the request
    return {
        "status": "QUEUED",
        "repository": f"{repo.owner}/{repo.repository_name}",
        "message": "Sync will be processed shortly",
    }
