"""Seed test data for testing."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from deploysense.database import async_session_factory
from deploysense.models import (
    Alert,
    Deployment,
    DeploymentEvent,
    PullRequest,
    Repository,
    RiskAssessment,
    Service,
)


async def seed_data():
    async with async_session_factory() as db:
        # Check if repo exists
        result = await db.execute(select(Repository).where(Repository.owner == "test-org"))
        repo = result.scalar_one_or_none()

        if not repo:
            # Create repository
            repo = Repository(
                id=uuid.uuid4(),
                owner="test-org",
                repository_name="test-repo",
                default_branch="main",
                status="ACTIVE",
            )
            db.add(repo)
            await db.flush()
            print(f"Created repository: {repo.owner}/{repo.repository_name}")
        else:
            print(f"Repository exists: {repo.owner}/{repo.repository_name}")

        # Create service linked to repo
        result = await db.execute(select(Service).where(Service.name == "test-service"))
        service = result.scalar_one_or_none()

        if not service:
            service = Service(
                id=uuid.uuid4(),
                name="test-service",
                repository_id=repo.id,
                environment="production",
            )
            db.add(service)
            await db.flush()
            print(f"Created service: {service.name}")
        else:
            print(f"Service exists: {service.name}")

        # Create a PR for testing
        result = await db.execute(
            select(PullRequest).where(
                PullRequest.repository_id == repo.id,
                PullRequest.pr_number == 123,
            )
        )
        pr = result.scalar_one_or_none()

        if not pr:
            pr = PullRequest(
                repository_id=repo.id,
                pr_number=123,
                title="Add new feature with DB migration",
                author="testuser",
                state="open",
                files_changed=15,
                lines_added=250,
                lines_deleted=50,
                has_db_migration=True,
                has_infra_change=True,
                created_at=datetime.utcnow(),
            )
            db.add(pr)
            print("Created PR #123")
        else:
            print("PR #123 already exists")

        result = await db.execute(
            select(Deployment).where(Deployment.git_sha == "a1b2c3d4e5f6demo")
        )
        deployment = result.scalar_one_or_none()
        if not deployment:
            now = datetime.utcnow()
            deployment = Deployment(
                service=service,
                environment="production",
                version="v2.4.0",
                git_sha="a1b2c3d4e5f6demo",
                status="STABLE",
                risk_score=62,
                risk_level="HIGH",
                failure_probability=0.198,
                deployed_by="testuser",
                initiated_at=now - timedelta(minutes=18),
                deployed_at=now - timedelta(minutes=12),
                completed_at=now - timedelta(minutes=4),
            )
            db.add(deployment)
            await db.flush()
            db.add_all(
                [
                    DeploymentEvent(
                        deployment_id=deployment.id,
                        event_type="deployment.created",
                        current_state="PENDING",
                        message="Production deployment registered from GitHub Actions",
                    ),
                    DeploymentEvent(
                        deployment_id=deployment.id,
                        event_type="risk.evaluated",
                        previous_state="PENDING",
                        current_state="RISK_ASSESSED",
                        message="High risk detected: migration and infrastructure changes",
                    ),
                    DeploymentEvent(
                        deployment_id=deployment.id,
                        event_type="deployment.stable",
                        previous_state="MONITORING",
                        current_state="STABLE",
                        message="Health checks remained within the observation window",
                    ),
                    RiskAssessment(
                        deployment_id=deployment.id,
                        risk_score=62,
                        risk_level="HIGH",
                        failure_probability=0.198,
                        recommendation="REQUIRE_MANUAL_APPROVAL",
                        feature_snapshot={
                            "has_db_migration": True,
                            "has_infra_change": True,
                            "files_changed": 15,
                        },
                        factors={
                            "factors": [
                                {
                                    "name": "database_migration",
                                    "contribution": 0.2,
                                    "description": "Includes a database schema migration",
                                },
                                {
                                    "name": "infrastructure_change",
                                    "contribution": 0.15,
                                    "description": "Includes infrastructure changes",
                                },
                            ]
                        },
                    ),
                    Alert(
                        service_id=service.id,
                        deployment_id=deployment.id,
                        severity="HIGH",
                        title="Elevated deployment risk",
                        description="Manual approval required before production release.",
                        status="ACKNOWLEDGED",
                        triggered_at=now - timedelta(minutes=16),
                    ),
                ]
            )
            print("Created deployment, timeline, risk assessment, and alert")
        else:
            print("Demo deployment already exists")

        await db.commit()
        print("\nSeed data complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
