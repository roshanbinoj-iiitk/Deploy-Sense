# Step 3: API Definitions

---

## 3.1 Public API Surface

Base URL: `https://api.deploysense.io/api/v1`

Authentication: Bearer JWT (GitHub OAuth)

---

## 3.1.1 Deployments API

```http
GET    /deployments
GET    /deployments/{id}
GET    /deployments/{id}/risk
GET    /deployments/{id}/timeline
POST   /deployments
POST   /deployments/{id}/approve
POST   /deployments/{id}/rollback
GET    /deployments/stats
```

### GET /deployments

```json
{
  "data": [
    {
      "id": "dep_123",
      "service": "payments-api",
      "environment": "production",
      "version": "v2.1.0",
      "status": "DEPLOYED",
      "risk_score": 42,
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 120
  }
}
```

### GET /deployments/{id}/risk

```json
{
  "deployment_id": "dep_123",
  "risk_score": 42,
  "risk_level": "MODERATE",
  "failure_probability": 0.21,
  "factors": [
    {
      "name": "database_migration",
      "contribution": 0.25
    },
    {
      "name": "lines_changed",
      "contribution": 0.12
    }
  ],
  "recommendation": "PROCEED"
}
```

---

## 3.1.2 Risk API

```http
POST   /risk/evaluate
GET    /risk/{deployment_id}
GET    /risk/history/{service}
GET    /risk/trends
```

### POST /risk/evaluate

```json
{
  "service": "payments-api",
  "environment": "production",
  "git_sha": "abc123",
  "pull_request": 1423
}
```

Response

```json
{
  "risk_score": 42,
  "risk_level": "MODERATE",
  "failure_probability": 0.21,
  "recommendation": "PROCEED"
}
```

---

## 3.1.3 Services API

```http
GET    /services
GET    /services/{name}
GET    /services/{name}/health
GET    /services/{name}/deployments
```

### GET /services/{name}/health

```json
{
  "service": "payments-api",
  "status": "HEALTHY",
  "stability_score": 92,
  "current_version": "v2.1.0",
  "metrics": {
    "error_rate": 0.002,
    "latency_p99_ms": 220,
    "request_rate_rps": 1500
  }
}
```

---

## 3.1.4 Repository API

```http
GET    /repositories
POST   /repositories
GET    /repositories/{id}
DELETE /repositories/{id}
POST   /repositories/{id}/sync
```

### POST /repositories

```json
{
  "owner": "org",
  "repository": "payments-api"
}
```

Response

```json
{
  "id": "repo_123",
  "owner": "org",
  "repository": "payments-api",
  "status": "CONNECTED"
}
```

---

## 3.1.5 Alerts API

```http
GET    /alerts
GET    /alerts/{id}
POST   /alerts/{id}/acknowledge
POST   /alerts/{id}/resolve
```

### GET /alerts/{id}

```json
{
  "id": "alert_123",
  "severity": "HIGH",
  "service": "payments-api",
  "message": "Error rate exceeded threshold",
  "status": "OPEN"
}
```

---

## 3.1.6 AI Analysis API

```http
POST   /ai/analyze/deployment
POST   /ai/analyze/pull-request
GET    /ai/analyses/{id}
```

### POST /ai/analyze/deployment

```json
{
  "deployment_id": "dep_123"
}
```

Response

```json
{
  "analysis_id": "ai_123",
  "status": "PROCESSING"
}
```

### GET /ai/analyses/{id}

```json
{
  "analysis_id": "ai_123",
  "status": "COMPLETED",
  "summary": "Database migration increased deployment risk.",
  "root_causes": [
    {
      "confidence": 0.88,
      "description": "Schema migration locked a heavily used table."
    }
  ]
}
```

---

## 3.1.7 Webhook Endpoints

```http
POST   /webhooks/github
POST   /webhooks/argocd
POST   /webhooks/prometheus
```

---

## 3.2 Internal Service APIs

DeploySense uses REST between internal services during MVP.

### API Service → Risk Engine

```http
POST /internal/risk/evaluate
```

Request

```json
{
  "deployment_id": "dep_123",
  "service": "payments-api",
  "git_sha": "abc123"
}
```

Response

```json
{
  "risk_score": 42,
  "risk_level": "MODERATE",
  "failure_probability": 0.21
}
```

---

### API Service → Worker Service

```http
POST /internal/jobs/github-sync
POST /internal/jobs/metrics-collection
POST /internal/jobs/recalculate-risk
```

Response

```json
{
  "job_id": "job_123",
  "status": "QUEUED"
}
```

---

## 3.3 WebSocket API

### Connection

```http
GET /ws/deployments
```

### Events

```json
{
  "event": "deployment.updated",
  "deployment_id": "dep_123",
  "status": "DEPLOYED"
}
```

```json
{
  "event": "risk.updated",
  "deployment_id": "dep_123",
  "risk_score": 42
}
```

```json
{
  "event": "alert.created",
  "alert_id": "alert_123",
  "severity": "HIGH"
}
```

---

## 3.4 Standard Error Format

```json
{
  "error": {
    "code": "RISK_EVALUATION_FAILED",
    "message": "Unable to calculate risk score",
    "request_id": "req_123",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Standard HTTP Status Codes

| Code | Usage |
|--------|--------|
| 400 | Validation Error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource Not Found |
| 409 | Conflict |
| 422 | Business Rule Violation |
| 429 | Rate Limit Exceeded |
| 500 | Internal Error |
| 503 | Service Unavailable |