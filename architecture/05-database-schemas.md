# Step 5: Database Schema

---

## 5.1 Database Topology

| Database | Engine | Purpose |
|-----------|---------|----------|
| deploysense | PostgreSQL 16 | Primary application database |
| cache | Redis 7 | Caching, sessions, temporary state |

---

## 5.2 PostgreSQL Schema

### organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    github_username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'engineer',
    avatar_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_users_org_id ON users(organization_id);
CREATE INDEX idx_users_github_username ON users(github_username);
```

---

### repositories

```sql
CREATE TABLE repositories (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    owner VARCHAR(255) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    default_branch VARCHAR(255) DEFAULT 'main',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_repositories_org_id ON repositories(organization_id);
```

---

### services

```sql
CREATE TABLE services (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES repositories(id),
    name VARCHAR(255) NOT NULL,
    environment VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    stability_score INTEGER DEFAULT 100,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_services_repository_id ON services(repository_id);
```

---

### pull_requests

```sql
CREATE TABLE pull_requests (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES repositories(id),
    pr_number INTEGER NOT NULL,
    title TEXT,
    author VARCHAR(255),
    state VARCHAR(50),
    files_changed INTEGER,
    lines_added INTEGER,
    lines_deleted INTEGER,
    has_db_migration BOOLEAN DEFAULT FALSE,
    has_infra_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    merged_at TIMESTAMP
);
```

Indexes

```sql
CREATE INDEX idx_pull_requests_repository_id ON pull_requests(repository_id);
CREATE INDEX idx_pull_requests_pr_number ON pull_requests(pr_number);
```

---

### deployments

```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY,
    service_id UUID REFERENCES services(id),

    environment VARCHAR(100) NOT NULL,

    version VARCHAR(255),
    git_sha VARCHAR(255) NOT NULL,

    status VARCHAR(50) NOT NULL,

    risk_score INTEGER,
    risk_level VARCHAR(50),
    failure_probability NUMERIC(5,4),

    deployed_by VARCHAR(255),

    initiated_at TIMESTAMP,
    deployed_at TIMESTAMP,
    completed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_deployments_service_id ON deployments(service_id);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_created_at ON deployments(created_at DESC);
```

---

### deployment_events

```sql
CREATE TABLE deployment_events (
    id UUID PRIMARY KEY,
    deployment_id UUID REFERENCES deployments(id),

    event_type VARCHAR(100) NOT NULL,
    previous_state VARCHAR(50),
    current_state VARCHAR(50),

    message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_deployment_events_deployment_id
ON deployment_events(deployment_id);
```

---

### risk_assessments

```sql
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY,

    deployment_id UUID REFERENCES deployments(id),

    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(50) NOT NULL,

    failure_probability NUMERIC(5,4),

    recommendation VARCHAR(100),

    feature_snapshot JSONB,
    factors JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Indexes

```sql
CREATE INDEX idx_risk_assessments_deployment_id
ON risk_assessments(deployment_id);
```

---

### metrics_snapshots

```sql
CREATE TABLE metrics_snapshots (
    id UUID PRIMARY KEY,

    service_id UUID REFERENCES services(id),

    error_rate NUMERIC(10,6),
    latency_p50_ms NUMERIC(10,2),
    latency_p95_ms NUMERIC(10,2),
    latency_p99_ms NUMERIC(10,2),

    request_rate_rps NUMERIC(10,2),

    cpu_usage NUMERIC(10,2),
    memory_usage NUMERIC(10,2),

    collected_at TIMESTAMP NOT NULL
);
```

Indexes

```sql
CREATE INDEX idx_metrics_service_time
ON metrics_snapshots(service_id, collected_at DESC);
```

---

### alerts

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,

    service_id UUID REFERENCES services(id),
    deployment_id UUID REFERENCES deployments(id),

    severity VARCHAR(50),

    title VARCHAR(255),
    description TEXT,

    status VARCHAR(50) DEFAULT 'OPEN',

    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP
);
```

Indexes

```sql
CREATE INDEX idx_alerts_service_id ON alerts(service_id);
CREATE INDEX idx_alerts_status ON alerts(status);
```

---

### ai_analyses

```sql
CREATE TABLE ai_analyses (
    id UUID PRIMARY KEY,

    deployment_id UUID REFERENCES deployments(id),

    analysis_type VARCHAR(100),

    status VARCHAR(50),

    summary TEXT,

    result JSONB,

    model VARCHAR(255),

    requested_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);
```

Indexes

```sql
CREATE INDEX idx_ai_analyses_deployment_id
ON ai_analyses(deployment_id);

CREATE INDEX idx_ai_analyses_status
ON ai_analyses(status);
```

---

## 5.3 Redis Structure

| Key | Purpose | TTL |
|-------|----------|------|
| session:{id} | User session | 1 hour |
| github:webhook:{event_id} | Webhook deduplication | 24 hours |
| risk:{deployment_id} | Cached risk result | 1 hour |
| dashboard:{org_id} | Dashboard cache | 30 seconds |
| metrics:{service_id} | Latest metrics cache | 1 minute |
| ai:{analysis_id} | Analysis cache | 1 hour |

---

## 5.4 Migration Strategy

### Tool

Alembic

### Rules

- Every schema change must have a migration.
- Migrations are version-controlled.
- Every migration must be reversible.
- CI executes migrations against a temporary PostgreSQL instance before merge.
- Production changes should be backward compatible whenever possible.

---

## 5.5 Future Database Enhancements

These are intentionally excluded from the MVP and may be introduced later if justified:

- Kafka Event Store
- TimescaleDB
- ClickHouse
- Read Replicas
- Partitioned Tables
- Multi-Region Replication
- Data Warehouse