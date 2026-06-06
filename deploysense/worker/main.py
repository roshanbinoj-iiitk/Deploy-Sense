"""
DeploySense — Worker Service Entry Point

WHY THIS EXISTS (architecture/02-microservices.md, Service 3):
The Worker Service handles all background operations:
  1. GitHub repository synchronization (every 15 minutes)
  2. Metrics collection from Prometheus (every 1 minute)
  3. Risk recalculation for active deployments (every 30 minutes)
  4. Cache cleanup (every 1 hour)

WHY NOT CELERY:
  - Celery requires a message broker (Redis/RabbitMQ).
    We already use Redis, but Celery adds significant complexity.
  - APScheduler is lightweight, runs in-process, and handles
    our scheduling needs for MVP.
  - When we need distributed task execution (Phase 3),
    we'll evaluate Celery vs. Kafka consumers.

WHY NOT FASTAPI:
The worker doesn't serve HTTP traffic. It's a long-running process
that executes jobs on a schedule. No web server needed.

SCALING (Phase 3):
  - For now: single worker process
  - Future: Multiple workers with leader election via Redis lock
    to prevent duplicate job execution.
"""

import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from deploysense.core import get_settings
from deploysense.logging import get_logger, setup_logging
from deploysense.worker.jobs import (
    cache_cleanup_job,
    metrics_collection_job,
    repo_sync_job,
    risk_recalculation_job,
)

logger = get_logger(__name__)


async def main() -> None:
    """
    Worker service main loop.

    Sets up the scheduler with all jobs and runs until terminated.
    Handles SIGINT/SIGTERM for graceful shutdown in containers.
    """
    setup_logging()
    settings = get_settings()

    logger.info(
        "worker_starting",
        environment=settings.environment,
    )

    # ── Create Scheduler ─────────────────────────────────────────────────
    scheduler = AsyncIOScheduler()

    # ── Register Jobs ────────────────────────────────────────────────────
    # Intervals match architecture/02-microservices.md section 2.2
    scheduler.add_job(
        repo_sync_job,
        "interval",
        minutes=15,
        id="repo_sync",
        name="GitHub Repository Sync",
    )
    scheduler.add_job(
        metrics_collection_job,
        "interval",
        minutes=1,
        id="metrics_collection",
        name="Prometheus Metrics Collection",
    )
    scheduler.add_job(
        risk_recalculation_job,
        "interval",
        minutes=30,
        id="risk_recalculation",
        name="Risk Recalculation",
    )
    scheduler.add_job(
        cache_cleanup_job,
        "interval",
        hours=1,
        id="cache_cleanup",
        name="Cache Cleanup",
    )

    scheduler.start()
    logger.info("worker_scheduler_started", job_count=len(scheduler.get_jobs()))

    # ── Graceful Shutdown ────────────────────────────────────────────────
    stop_event = asyncio.Event()

    def _shutdown(sig: signal.Signals) -> None:
        logger.info("worker_shutdown_signal", signal=sig.name)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    logger.info("worker_running")
    await stop_event.wait()

    scheduler.shutdown(wait=True)
    logger.info("worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
