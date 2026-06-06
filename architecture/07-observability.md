# Step 7: Observability Architecture

---

## 7.1 Observability Stack Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                       │
│                                                              │
│  API Service                                                 │
│  Risk Engine                                                 │
│  Worker Service                                              │
│                                                              │
│          │                                                   │
│          ▼                                                   │
│                                                              │
│  OpenTelemetry                                               │
│          │                                                   │
│          ├────────── Metrics ──────────► Prometheus          │
│          │                                   │               │
│          │                                   ▼               │
│          │                               Grafana             │
│          │                                                   │
│          ├────────── Logs ─────────────► Loki                │
│          │                                   │               │
│          │                                   ▼               │
│          │                               Grafana             │
│          │                                                   │
│          └────────── Traces ───────────► OTel Collector      │
│                                              │               │
│                                              ▼               │
│                                           Grafana            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7.2 Metrics Architecture

### Prometheus

Every service exposes:

```text
/metrics
```

Prometheus scrapes metrics from:

- API Service
- Risk Engine
- Worker Service
- PostgreSQL Exporter
- Redis Exporter
- Kubernetes Components

---

## 7.3 Application Metrics

### API Service Metrics

```text
deploysense_http_requests_total

deploysense_http_request_duration_seconds

deploysense_active_websocket_connections

deploysense_github_webhook_events_total

deploysense_auth_requests_total
```

---

### Risk Engine Metrics

```text
deploysense_risk_calculations_total

deploysense_risk_calculation_duration_seconds

deploysense_risk_score_distribution

deploysense_failure_probability_distribution

deploysense_risk_engine_errors_total
```

---

### Worker Service Metrics

```text
deploysense_jobs_processed_total

deploysense_job_duration_seconds

deploysense_github_sync_total

deploysense_metrics_collection_total

deploysense_worker_failures_total
```

---

## 7.4 Deployment Metrics

```text
deploysense_deployments_total

deploysense_active_deployments

deploysense_deployment_duration_seconds

deploysense_rollbacks_total

deploysense_deployment_failures_total
```

---

## 7.5 Infrastructure Metrics

### PostgreSQL

```text
postgres_connections

postgres_transactions_total

postgres_query_duration_seconds

postgres_database_size_bytes
```

### Redis

```text
redis_memory_used_bytes

redis_connected_clients

redis_commands_processed_total
```

### Kubernetes

```text
container_cpu_usage_seconds_total

container_memory_usage_bytes

kube_pod_status_phase

kube_deployment_status_replicas_available
```

---

## 7.6 Alerting Rules

### API Service Down

```yaml
alert: APIServiceDown
expr: up{job="api-service"} == 0
for: 1m
```

---

### Risk Engine Down

```yaml
alert: RiskEngineDown
expr: up{job="risk-engine"} == 0
for: 1m
```

---

### High Error Rate

```yaml
alert: HighErrorRate
expr: rate(deploysense_http_requests_total{status=~"5.."}[5m]) > 5
for: 5m
```

---

### High Deployment Failure Rate

```yaml
alert: HighDeploymentFailureRate
expr: increase(deploysense_deployment_failures_total[1h]) > 5
for: 5m
```

---

### PostgreSQL Unavailable

```yaml
alert: PostgreSQLDown
expr: up{job="postgres"} == 0
for: 1m
```

---

### Redis Unavailable

```yaml
alert: RedisDown
expr: up{job="redis"} == 0
for: 1m
```

---

## 7.7 Logging Architecture

### Loki

All services emit structured JSON logs.

Example:

```json
{
  "timestamp": "2026-01-15T10:37:00Z",
  "level": "ERROR",
  "service": "risk-engine",
  "message": "Risk calculation failed",
  "deployment_id": "dep_123",
  "trace_id": "trace_123"
}
```

---

### Log Labels

```text
service
namespace
pod
environment
```

---

### Log Retention

| Log Type | Retention |
|-----------|-----------|
| ERROR | 90 Days |
| WARN | 30 Days |
| INFO | 14 Days |
| DEBUG | Disabled in Production |

---

## 7.8 Distributed Tracing

### OpenTelemetry

Every request receives:

```text
trace_id
span_id
```

Tracked Flows:

- Deployment Creation
- Risk Evaluation
- GitHub Synchronization
- Metrics Collection
- AI Analysis

---

### Example Trace Flow

```text
User Request
      │
      ▼

API Service
      │
      ▼

Risk Engine
      │
      ▼

PostgreSQL

Trace Visible End-to-End
```

---

## 7.9 Grafana Dashboards

### Dashboard 1 — Platform Overview

Panels:

- Active Deployments
- Deployments Per Day
- Risk Score Distribution
- Deployment Success Rate
- Rollback Count
- Active Alerts

---

### Dashboard 2 — Risk Analysis

Panels:

- Risk Scores By Service
- Failure Probability Trends
- Top Risk Factors
- Risk History
- Risk Engine Performance

---

### Dashboard 3 — Service Health

Panels:

- API Latency
- API Error Rate
- Worker Throughput
- Database Health
- Redis Health
- Pod Health

---

### Dashboard 4 — Infrastructure

Panels:

- CPU Usage
- Memory Usage
- Pod Count
- Node Status
- PostgreSQL Metrics
- Redis Metrics

---

## 7.10 Service Level Objectives (SLOs)

| Service | SLO |
|----------|----------|
| API Service Availability | 99.9% |
| Risk Engine Availability | 99.5% |
| Worker Service Availability | 99.5% |
| Deployment Risk Evaluation Success Rate | 99.5% |
| API Latency (P99) | < 500ms |
| Risk Evaluation Latency (P99) | < 2s |

---

## 7.11 Future Enhancements

Future additions may include:

- Kafka Monitoring
- AI Service Monitoring
- Advanced SLO Burn Rate Alerting
- Long-Term Metrics Storage
- Multi-Cluster Observability
- Synthetic Monitoring