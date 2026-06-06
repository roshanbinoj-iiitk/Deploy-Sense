# Step 4: Event Architecture

---

## 4.1 Event Strategy

DeploySense does not require Kafka in the MVP.

The system initially operates using:

- REST APIs
- PostgreSQL
- Redis
- Background Workers

Kafka will be introduced only when:

- Event throughput grows significantly
- Multiple consumers need the same events
- Replayability becomes important
- Service decoupling becomes necessary
- Asynchronous workflows become a bottleneck

---

## 4.2 Future Topic Inventory

| Topic | Purpose | Producer | Consumers |
|---------|---------|---------|---------|
| deployment.created | New deployment registered | API Service | Risk Engine, Worker |
| deployment.updated | Deployment state changed | API Service | Worker |
| risk.calculated | Risk assessment completed | Risk Engine | API Service |
| metrics.collected | Metrics ingestion completed | Worker | Risk Engine |
| alert.created | Alert generated | Worker | API Service |
| ai.analysis.requested | AI analysis requested | API Service | AI Service |
| ai.analysis.completed | AI analysis completed | AI Service | API Service |

---

## 4.3 Partitioning Strategy

| Topic Type | Partition Key |
|------------|--------------|
| deployment.* | deployment_id |
| risk.* | deployment_id |
| metrics.* | service_name |
| alert.* | service_name |
| ai.* | deployment_id |

---

## 4.4 Common Event Envelope

```json
{
  "event_id": "evt_123",
  "event_type": "deployment.created",
  "event_version": "1.0",
  "timestamp": "2026-01-15T10:30:00Z",
  "source": "api-service",
  "correlation_id": "corr_123",
  "data": {}
}
```

---

## 4.5 deployment.created

```json
{
  "event_id": "evt_123",
  "event_type": "deployment.created",
  "data": {
    "deployment_id": "dep_123",
    "service": "payments-api",
    "environment": "production",
    "version": "v2.1.0",
    "git_sha": "abc123",
    "created_by": "johndoe"
  }
}
```

---

## 4.6 deployment.updated

```json
{
  "event_id": "evt_124",
  "event_type": "deployment.updated",
  "data": {
    "deployment_id": "dep_123",
    "previous_status": "PENDING",
    "current_status": "DEPLOYED",
    "updated_at": "2026-01-15T10:35:00Z"
  }
}
```

---

## 4.7 risk.calculated

```json
{
  "event_id": "evt_125",
  "event_type": "risk.calculated",
  "data": {
    "deployment_id": "dep_123",
    "risk_score": 42,
    "risk_level": "MODERATE",
    "failure_probability": 0.21,
    "recommendation": "PROCEED"
  }
}
```

---

## 4.8 metrics.collected

```json
{
  "event_id": "evt_126",
  "event_type": "metrics.collected",
  "data": {
    "service": "payments-api",
    "error_rate": 0.002,
    "latency_p99_ms": 220,
    "request_rate_rps": 1500,
    "collected_at": "2026-01-15T10:36:00Z"
  }
}
```

---

## 4.9 alert.created

```json
{
  "event_id": "evt_127",
  "event_type": "alert.created",
  "data": {
    "alert_id": "alert_123",
    "deployment_id": "dep_123",
    "service": "payments-api",
    "severity": "HIGH",
    "message": "Error rate exceeded threshold"
  }
}
```

---

## 4.10 ai.analysis.requested

```json
{
  "event_id": "evt_128",
  "event_type": "ai.analysis.requested",
  "data": {
    "analysis_id": "ai_123",
    "deployment_id": "dep_123",
    "analysis_type": "ROOT_CAUSE"
  }
}
```

---

## 4.11 ai.analysis.completed

```json
{
  "event_id": "evt_129",
  "event_type": "ai.analysis.completed",
  "data": {
    "analysis_id": "ai_123",
    "deployment_id": "dep_123",
    "summary": "Database migration increased deployment risk.",
    "confidence": 0.88
  }
}
```

---

## 4.12 Kafka Adoption Criteria

Kafka should be introduced when at least one of the following becomes true:

- More than 10,000 deployment-related events per day
- Multiple services need to independently consume the same events
- Event replay becomes a business requirement
- AI analysis becomes fully asynchronous
- Alert processing becomes distributed
- Risk calculations become event-driven

Until then, REST APIs and background workers remain the preferred architecture.

---

## 4.13 Future Consumer Groups

| Consumer Group | Purpose |
|---------------|---------|
| risk-engine | Risk calculations |
| metrics-processor | Metrics ingestion |
| ai-analysis | AI processing |
| alert-processor | Alert handling |
| dashboard-updater | Dashboard cache refresh |

---

## 4.14 Event Design Principles

| Principle | Description |
|------------|------------|
| Idempotent Consumers | Events can be processed multiple times safely |
| Backward Compatibility | New fields must be optional |
| Immutable Events | Events are never modified after publication |
| Correlation IDs | Every workflow is traceable end-to-end |
| Schema Versioning | Every event contains a version |
| Event Replay Safety | Consumers must tolerate replayed events |