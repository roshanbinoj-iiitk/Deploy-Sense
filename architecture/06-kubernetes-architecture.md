# Step 6: Kubernetes Architecture

---

## 6.1 Cluster Topology

```text
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                      │
│                                                            │
│  Node Pool: System                                         │
│  • Ingress Controller                                      │
│  • ArgoCD                                                  │
│  • Monitoring Stack                                        │
│                                                            │
│  Node Pool: Application                                    │
│  • API Service                                             │
│  • Risk Engine                                             │
│  • Worker Service                                          │
│                                                            │
│  Data Layer                                                │
│  • PostgreSQL                                              │
│  • Redis                                                   │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.2 Namespace Design

| Namespace | Purpose |
|------------|------------|
| deploysense | Core application services |
| deploysense-data | PostgreSQL and Redis |
| deploysense-observability | Monitoring and logging |
| argocd | GitOps platform |
| ingress-nginx | Ingress controller |

---

## 6.3 Application Workloads

### API Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: deploysense
spec:
  replicas: 2
```

Responsibilities:

- Authentication
- GitHub Webhooks
- Dashboard APIs
- Deployment APIs
- WebSocket connections

Resources:

```yaml
requests:
  cpu: 250m
  memory: 256Mi

limits:
  cpu: 1000m
  memory: 512Mi
```

---

### Risk Engine

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: risk-engine
  namespace: deploysense
spec:
  replicas: 2
```

Responsibilities:

- Risk Scoring
- Failure Prediction
- Deployment Analysis

Resources:

```yaml
requests:
  cpu: 500m
  memory: 512Mi

limits:
  cpu: 2000m
  memory: 2Gi
```

---

### Worker Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-service
  namespace: deploysense
spec:
  replicas: 2
```

Responsibilities:

- GitHub Synchronization
- Metrics Collection
- Scheduled Jobs
- Alert Processing

Resources:

```yaml
requests:
  cpu: 250m
  memory: 256Mi

limits:
  cpu: 1000m
  memory: 1Gi
```

---

## 6.4 Data Layer

### PostgreSQL

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: deploysense-data
spec:
  replicas: 1
```

Storage:

```yaml
storage: 20Gi
```

Purpose:

- Primary application database

---

### Redis

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: deploysense-data
spec:
  replicas: 1
```

Purpose:

- Caching
- Session Storage
- Temporary State

---

## 6.5 Horizontal Pod Autoscaling

### API Service

```yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

### Risk Engine

```yaml
minReplicas: 2
maxReplicas: 6
targetCPUUtilizationPercentage: 70
```

### Worker Service

```yaml
minReplicas: 2
maxReplicas: 6
targetCPUUtilizationPercentage: 70
```

---

## 6.6 Network Policies

### External Access

Allowed:

- Ingress Controller → API Service

Blocked:

- Direct Internet → Internal Services

### Internal Access

Allowed:

- API Service → Risk Engine
- API Service → Worker Service
- API Service → PostgreSQL
- Risk Engine → PostgreSQL
- Worker Service → PostgreSQL
- All Services → Redis

---

## 6.7 Ingress Architecture

```text
Internet
    |
    v

NGINX Ingress
    |
    v

API Service
    |
    +------------------+
    |                  |
    v                  v

Risk Engine      Worker Service
```

Ingress Hosts:

```yaml
api.deploysense.io
app.deploysense.io
```

TLS:

```yaml
cert-manager
Let's Encrypt
```

---

## 6.8 Observability Stack

### Prometheus

Purpose:

- Metrics Collection

### Grafana

Purpose:

- Dashboards

### Loki

Purpose:

- Centralized Logging

### OpenTelemetry Collector

Purpose:

- Distributed Tracing

---

## 6.9 GitOps Architecture

### ArgoCD

Responsibilities:

- Kubernetes Deployments
- Application Synchronization
- Rollback Support
- Environment Promotion

Deployment Flow:

```text
Git Push
    |
    v

GitHub Actions
    |
    v

Docker Image Build
    |
    v

Container Registry
    |
    v

GitOps Manifest Update
    |
    v

ArgoCD Sync
    |
    v

Kubernetes Deployment
```

---

## 6.10 Resource Summary

| Workload | Replicas | CPU Request | Memory Request |
|-----------|-----------|-------------|----------------|
| API Service | 2-10 | 250m | 256Mi |
| Risk Engine | 2-6 | 500m | 512Mi |
| Worker Service | 2-6 | 250m | 256Mi |
| PostgreSQL | 1 | 500m | 1Gi |
| Redis | 1 | 250m | 256Mi |
| Prometheus | 1 | 500m | 1Gi |
| Grafana | 1 | 250m | 512Mi |
| Loki | 1 | 500m | 1Gi |
| ArgoCD | 1 | 500m | 512Mi |

---

## 6.11 Future Kubernetes Enhancements

These are intentionally deferred until scale justifies them:

- Kafka Cluster
- PostgreSQL High Availability
- Redis Sentinel
- Service Mesh (Istio)
- Multi-Region Deployment
- GPU Workloads
- Dedicated AI Service
- Separate Notification Service
- Separate Policy Engine