# DeploySense

**Deployment Intelligence Platform** — predicts deployment risk before production releases and continuously evaluates deployment health after releases.

## What DeploySense Is

DeploySense answers five critical questions:

1. **Should this deployment be released?**
2. **What is the probability of deployment failure?**
3. **What factors contribute to deployment risk?**
4. **Should the deployment be automatically rolled back?**
5. **What are the likely root causes of failures?**

## What DeploySense Is NOT

- ❌ Not a CI/CD platform
- ❌ Not a Jenkins clone
- ❌ Not a deployment dashboard
- ❌ Not a monitoring tool

## Architecture

```
┌─────────────────┐     ┌───────────────┐     ┌────────────────┐
│   API Service   │────▶│  Risk Engine  │     │ Worker Service │
│   (Port 8000)   │     │  (Port 8001)  │     │  (Background)  │
└────────┬────────┘     └───────┬───────┘     └───────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ┌─────▼─────┐          ┌──────▼──────┐
              │ PostgreSQL │          │    Redis    │
              │    (16)    │          │    (7)      │
              └────────────┘          └─────────────┘
```

**3 Services:**
- **API Service** — Authentication, webhooks, deployment CRUD, dashboard APIs
- **Risk Engine** — Risk scoring, failure prediction, deployment evaluation
- **Worker Service** — GitHub sync, metrics collection, scheduled background jobs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Migrations | Alembic |
| Observability | Prometheus + Grafana + OpenTelemetry |
| Container | Docker |
| Orchestration | Kubernetes + Helm |
| GitOps | ArgoCD |
| IaC | Terraform |

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd deploysense

# 2. Start infrastructure
docker compose up -d

# 3. Install Python dependencies
python -m pip install -e ".[dev]"

# 4. Copy environment config
cp .env.example .env

# 5. Run database migrations
make migrate

# 6. Start the API service
make api

# 7. Start the Risk Engine (separate terminal)
make risk-engine

# 8. Open API docs
open http://localhost:8000/docs
```

## Project Structure

```
deploysense/
├── api/                    # Service 1: API Service
│   ├── main.py             # FastAPI application entry point
│   ├── schemas.py          # Pydantic request/response models
│   └── routes/
│       ├── deployments.py  # Deployment CRUD endpoints
│       ├── services.py     # Service management endpoints
│       └── webhooks.py     # GitHub/ArgoCD/Prometheus webhooks
├── risk_engine/            # Service 2: Risk Engine
│   ├── main.py             # FastAPI application (port 8001)
│   ├── scoring.py          # Heuristic risk scoring algorithm
│   └── routes.py           # Internal risk evaluation endpoints
├── worker/                 # Service 3: Worker Service
│   ├── main.py             # APScheduler-based background runner
│   └── jobs.py             # Scheduled job definitions
├── database/               # Shared database layer
│   ├── base.py             # SQLAlchemy base model + mixins
│   └── session.py          # Async engine + session factory
├── core/
│   └── __init__.py         # Application configuration (Pydantic Settings)
├── models.py               # All SQLAlchemy ORM models
├── logging.py              # Structured logging (structlog)
└── config.py               # Config re-exports

tests/
├── test_risk_scoring.py    # Risk engine unit tests
└── test_api.py             # API route tests

architecture/               # 10-step architecture documentation
infra/prometheus/           # Prometheus configuration
```

## Development Commands

```bash
make help           # Show all available commands
make api            # Run API service (port 8000)
make risk-engine    # Run Risk Engine (port 8001)
make worker         # Run Worker service
make test           # Run all tests
make lint           # Run linter (ruff + mypy)
make format         # Auto-format code
make docker-up      # Start Postgres + Redis
make docker-down    # Stop infrastructure
make migrate        # Run database migrations
make migrate-new MSG="description"  # Create new migration
```

## Implementation Roadmap

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Phase 0** | Foundation (infrastructure, project setup) | Weeks 1-2 |
| **Phase 1** | MVP (deployments, risk engine, dashboard) | Weeks 3-6 |
| **Phase 2** | Intelligence (AI analysis, root cause) | Weeks 7-10 |
| **Phase 3** | Scale (HA, performance, security) | Weeks 11-14 |

## License

MIT
