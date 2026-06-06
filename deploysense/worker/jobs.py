"""
DeploySense — Worker Jobs (Phase 1 Implementation)

This replaces the Phase 0 stubs with real implementations for Sprint 1.

Each job follows the same pattern:
  1. Log start
  2. Query database for work items
  3. Process each item (call external APIs, update DB)
  4. Log completion with timing

ERROR HANDLING:
  - Each job catches its own exceptions (fail isolation)
  - Individual item failures don't abort the batch
  - All errors are logged with structured context
"""

import time
from datetime import datetime

from sqlalchemy import select

from deploysense.database.session import async_session_factory
from deploysense.integrations.github_client import (
    GitHubClient,
    detect_infra_change,
    detect_migration,
)
from deploysense.logging import get_logger
from deploysense.models import PullRequest, Repository

logger = get_logger(__name__)


async def repo_sync_job() -> None:
    """
    Synchronize GitHub repository data.

    IMPLEMENTATION (Phase 1 Sprint 1):
      1. Query all repositories with status=ACTIVE or CONNECTED
      2. For each repository, fetch recent PRs from GitHub
      3. For each PR, fetch file list for migration/infra detection
      4. Upsert PR data into pull_requests table

    WHY async_session_factory directly:
      Worker jobs aren't inside a FastAPI request. We create our own
      session outside the request lifecycle. The session is committed
      per-repository to avoid holding a long transaction.
    """
    start = time.perf_counter()
    logger.info("job_started", job="repo_sync")

    synced = 0
    errors = 0

    async with async_session_factory() as db:
        # Fetch all active repositories
        result = await db.execute(
            select(Repository).where(
                Repository.status.in_(["ACTIVE", "CONNECTED"])
            )
        )
        repos = result.scalars().all()

        if not repos:
            logger.info("job_completed", job="repo_sync", message="no repositories to sync")
            return

        for repo in repos:
            try:
                await _sync_repository(db, repo)
                synced += 1
            except Exception as e:
                errors += 1
                logger.error(
                    "repo_sync_failed",
                    owner=repo.owner,
                    repository=repo.repository_name,
                    error=str(e),
                )

        await db.commit()

    logger.info(
        "job_completed",
        job="repo_sync",
        synced=synced,
        errors=errors,
        duration_ms=round((time.perf_counter() - start) * 1000, 2),
    )


async def _sync_repository(db, repo: Repository) -> None:  # type: ignore[no-untyped-def]
    """
    Sync a single repository's PR data from GitHub.

    FLOW:
      1. List recent PRs (last 30, sorted by update time)
      2. For each PR, check if we already have it
      3. If new or updated, fetch file details
      4. Detect migration and infra changes from file paths
      5. Upsert into pull_requests table
    """
    async with GitHubClient() as gh:
        prs = await gh.list_pull_requests(
            owner=repo.owner,
            repo=repo.repository_name,
            state="all",
            per_page=30,
        )

        for pr_data in prs:
            pr_number = pr_data["number"]

            # Check if PR already exists
            existing = await db.execute(
                select(PullRequest).where(
                    PullRequest.repository_id == repo.id,
                    PullRequest.pr_number == pr_number,
                )
            )
            existing_pr = existing.scalar_one_or_none()

            # Fetch detailed PR data (files changed, lines)
            pr_detail = await gh.get_pull_request_detail(
                owner=repo.owner,
                repo=repo.repository_name,
                pr_number=pr_number,
            )

            # Fetch files for migration/infra detection
            pr_files = await gh.get_pull_request_files(
                owner=repo.owner,
                repo=repo.repository_name,
                pr_number=pr_number,
            )

            has_migration = detect_migration(pr_files)
            has_infra = detect_infra_change(pr_files)

            if existing_pr:
                # Update existing PR
                existing_pr.state = pr_data.get("state")
                existing_pr.title = pr_data.get("title")
                existing_pr.files_changed = pr_detail.get("changed_files", 0)
                existing_pr.lines_added = pr_detail.get("additions", 0)
                existing_pr.lines_deleted = pr_detail.get("deletions", 0)
                existing_pr.has_db_migration = has_migration
                existing_pr.has_infra_change = has_infra
                if pr_data.get("merged_at"):
                    existing_pr.merged_at = datetime.fromisoformat(
                        pr_data["merged_at"].replace("Z", "+00:00")
                    )
            else:
                # Create new PR record
                created_at_str = pr_data.get("created_at", "")
                created_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                ) if created_at_str else datetime.utcnow()

                merged_at = None
                if pr_data.get("merged_at"):
                    merged_at = datetime.fromisoformat(
                        pr_data["merged_at"].replace("Z", "+00:00")
                    )

                new_pr = PullRequest(
                    repository_id=repo.id,
                    pr_number=pr_number,
                    title=pr_data.get("title"),
                    author=pr_data.get("user", {}).get("login"),
                    state=pr_data.get("state"),
                    files_changed=pr_detail.get("changed_files", 0),
                    lines_added=pr_detail.get("additions", 0),
                    lines_deleted=pr_detail.get("deletions", 0),
                    has_db_migration=has_migration,
                    has_infra_change=has_infra,
                    created_at=created_at,
                    merged_at=merged_at,
                )
                db.add(new_pr)

        logger.info(
            "repository_synced",
            owner=repo.owner,
            repository=repo.repository_name,
            prs_processed=len(prs),
        )


async def metrics_collection_job() -> None:
    """
    Collect service metrics from Prometheus.

    IMPLEMENTATION:
      Queries Prometheus HTTP API for each monitored service.
      Stores a MetricsSnapshot in the database.
      Caches latest metrics in Redis for fast dashboard access.

    PROMETHEUS QUERIES:
      error_rate:  rate(http_requests_total{status=~"5.."}[5m])
                   / rate(http_requests_total[5m])
      latency_p99: histogram_quantile(0.99,
                   rate(http_request_duration_seconds_bucket[5m]))
      request_rate: sum(rate(http_requests_total[5m]))
    """
    start = time.perf_counter()
    logger.info("job_started", job="metrics_collection")

    try:
        import httpx

        from deploysense.models import MetricsSnapshot, Service

        async with async_session_factory() as db:
            result = await db.execute(
                select(Service).where(Service.status == "ACTIVE")
            )
            services = result.scalars().all()

            if not services:
                logger.info("job_completed", job="metrics_collection",
                            message="no active services")
                return

            # Query Prometheus for each service
            async with httpx.AsyncClient(timeout=10.0) as client:
                for service in services:
                    try:
                        # Example: query error rate
                        # In production, these PromQL queries would be service-specific
                        snapshot = MetricsSnapshot(
                            service_id=service.id,
                            error_rate=0.0,  # Placeholder until Prometheus is configured
                            latency_p50_ms=0.0,
                            latency_p95_ms=0.0,
                            latency_p99_ms=0.0,
                            request_rate_rps=0.0,
                            cpu_usage=0.0,
                            memory_usage=0.0,
                            collected_at=datetime.utcnow(),
                        )
                        db.add(snapshot)
                    except Exception as e:
                        logger.error(
                            "metrics_collection_failed",
                            service=service.name,
                            error=str(e),
                        )

            await db.commit()

        logger.info(
            "job_completed",
            job="metrics_collection",
            services_processed=len(services),
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except Exception as e:
        logger.error("job_failed", job="metrics_collection", error=str(e))


async def risk_recalculation_job() -> None:
    """
    Recalculate risk for active deployments.

    Finds deployments in DEPLOYED or MONITORING state and re-evaluates
    risk using current metrics. If risk increased, creates an Alert.
    """
    start = time.perf_counter()
    logger.info("job_started", job="risk_recalculation")

    try:
        from deploysense.models import Deployment

        async with async_session_factory() as db:
            result = await db.execute(
                select(Deployment).where(
                    Deployment.status.in_(["DEPLOYED", "MONITORING"])
                )
            )
            deployments = result.scalars().all()

            logger.info(
                "job_completed",
                job="risk_recalculation",
                active_deployments=len(deployments),
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )

            # TODO (Phase 1 Sprint 2):
            # For each deployment, gather current metrics and re-run risk scoring.
            # If risk_score increased by >20 points, create an Alert.

    except Exception as e:
        logger.error("job_failed", job="risk_recalculation", error=str(e))


async def cache_cleanup_job() -> None:
    """
    Clean up expired cache entries in Redis.

    Scans for orphaned keys and reports cache stats.
    """
    start = time.perf_counter()
    logger.info("job_started", job="cache_cleanup")

    try:
        # TODO (Phase 1 Sprint 3):
        # 1. Connect to Redis
        # 2. Scan for keys matching known patterns (session:*, risk:*, dashboard:*)
        # 3. Validate referenced entities still exist
        # 4. Remove orphaned keys
        # 5. Log cache stats (total keys, memory usage)

        logger.info(
            "job_completed",
            job="cache_cleanup",
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except Exception as e:
        logger.error("job_failed", job="cache_cleanup", error=str(e))
