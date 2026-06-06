# Step 2: Service Definition

---

## 2.1 Service Inventory

| # | Service | Language | Primary Responsibility | Scaling Model |
|---|---------|----------|----------------------|---------------|
| 1 | **API Service** | Python (FastAPI) | Authentication, GitHub webhooks, deployment APIs, dashboard APIs | HPA (CPU/RPS) |
| 2 | **Risk Engine Service** | Python (FastAPI) | Risk scoring, deployment evaluation, failure prediction | HPA (CPU) |
| 3 | **Worker Service** | Python | Background jobs, GitHub synchronization, metrics collection, scheduled tasks | HPA (queue depth) |

---

## 2.2 Detailed Service Specifications

### Service 1: API Service

```yaml
Name: api-service
Language: Python 3.13
Framework: FastAPI
Port: 8000
Health: /health
Metrics: /metrics
```

### Responsibilities

- User authentication
- GitHub OAuth integration
- GitHub webhook ingestion
- Deployment CRUD operations
- Team and repository management
- Dashboard APIs
- WebSocket support for real-time updates

### Dependencies

- PostgreSQL
- Redis
- Risk Engine Service
- Worker Service

### Example Endpoints

```http
POST   /api/v1/auth/github
GET    /api/v1/deployments
POST   /api/v1/deployments
GET    /api/v1/deployments/{id}
GET    /api/v1/risk/{deployment_id}
POST   /api/v1/webhooks/github
GET    /ws/deployments
```

---

### Service 2: Risk Engine Service

```yaml
Name: risk-engine
Language: Python 3.13
Framework: FastAPI
Port: 8001
Health: /health
Metrics: /metrics
```

### Responsibilities

- Deployment risk scoring
- Failure probability prediction
- Risk factor analysis
- Deployment evaluation
- Risk history tracking
- Future ML model hosting

### Risk Features

| Feature | Source |
|----------|---------|
| Lines Changed | GitHub |
| Files Changed | GitHub |
| CI Pass Rate | GitHub |
| Previous Rollbacks | Deployment History |
| Deployment Frequency | Deployment History |
| Recent Failures | Deployment History |
| Database Migration Presence | GitHub |
| Infrastructure Changes | GitHub |
| Service Stability | Historical Data |

### Risk Levels

| Score | Level | Action |
|---------|---------|---------|
| 0-25 | Low | Approve |
| 26-50 | Moderate | Approve + Monitor |
| 51-75 | High | Manual Review |
| 76-100 | Critical | Block Deployment |

### Example Endpoints

```http
POST /internal/risk/evaluate
GET  /internal/risk/{deployment_id}
GET  /internal/risk/history/{service}
```

---

### Service 3: Worker Service

```yaml
Name: worker-service
Language: Python 3.13
Framework: Background Workers
Port: Internal
```

### Responsibilities

- GitHub repository synchronization
- Pull request ingestion
- Commit ingestion
- Deployment metrics collection
- Alert processing
- Scheduled jobs
- Cache refresh operations
- Notification processing

### Scheduled Jobs

| Job | Frequency |
|------|------------|
| Repository Sync | Every 15 minutes |
| Metrics Collection | Every 1 minute |
| Risk Recalculation | Every 30 minutes |
| Cache Cleanup | Every 1 hour |

### Dependencies

- PostgreSQL
- Redis
- GitHub API
- Prometheus API

---

## 2.3 Service Dependency Graph

```text
                    ┌─────────────────┐
                    │   API Service   │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼

         ┌───────────────┐      ┌────────────────┐
         │  Risk Engine  │      │ Worker Service │
         └───────┬───────┘      └───────┬────────┘
                 │                      │
                 └──────────┬───────────┘
                            │
                            ▼

                    ┌─────────────┐
                    │ PostgreSQL  │
                    └─────────────┘

                            │

                            ▼

                       ┌────────┐
                       │ Redis  │
                       └────────┘

```

---

## 2.4 Inter-Service Communication Matrix

| From → To | Protocol | Pattern | Purpose |
|------------|------------|----------|---------|
| API Service → Risk Engine | REST | Sync | Risk evaluation |
| API Service → Worker Service | REST | Sync | Trigger jobs |
| Worker Service → GitHub API | HTTP | Sync | Repository data |
| Worker Service → Prometheus | HTTP | Sync | Metrics collection |
| Risk Engine → PostgreSQL | SQL | Sync | Risk history |
| API Service → PostgreSQL | SQL | Sync | Application data |
| Worker Service → PostgreSQL | SQL | Sync | Data ingestion |
| All Services → Redis | TCP | Sync | Cache/session storage |
| API Service → Frontend | HTTP/WebSocket | Sync | Dashboard updates |

---

## 2.5 Future Service Extraction Plan

The following modules remain inside existing services initially and will only become independent services if justified by scale:

### Future AI Analysis Service

Responsibilities:

- Root cause analysis
- PR analysis
- Deployment failure explanation
- Deployment summaries

### Future Notification Service

Responsibilities:

- Slack notifications
- Email notifications
- PagerDuty integration

### Future Policy Engine

Responsibilities:

- Deployment gates
- Approval workflows
- Change freeze enforcement

### Future Event Bus

Kafka will be introduced only when:

- Event volume becomes high
- Replay capability is required
- Multiple services need asynchronous communication
- Background workloads become difficult to manage synchronously