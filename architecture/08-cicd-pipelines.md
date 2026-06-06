# Step 8: CI/CD Pipelines

---

## 8.1 Pipeline Architecture Overview

```text
Developer
    |
    v

GitHub Repository
    |
    v

GitHub Actions

    ├── Lint
    ├── Tests
    ├── Security Scan
    ├── Build Docker Image
    └── Push Image

    |
    v

Container Registry
(GHCR / Docker Hub)

    |
    v

GitOps Repository

    |
    v

ArgoCD

    |
    v

Kubernetes Cluster
```

---

## 8.2 Pull Request Pipeline

### Trigger

```yaml
on:
  pull_request:
    branches:
      - main
```

### Stages

#### 1. Code Quality

```bash
ruff check .
ruff format --check .
mypy .
```

---

#### 2. Unit Tests

```bash
pytest tests/unit
```

Requirements:

- All tests pass
- Minimum 80% coverage

---

#### 3. Integration Tests

Dependencies:

- PostgreSQL
- Redis

```bash
pytest tests/integration
```

---

#### 4. Security Scan

Tools:

```bash
bandit
safety
trivy
```

Requirements:

- No critical vulnerabilities
- No leaked secrets

---

#### 5. Docker Build Validation

```bash
docker build .
```

Purpose:

- Ensure image builds successfully

---

## 8.3 Main Branch Pipeline

### Trigger

```yaml
on:
  push:
    branches:
      - main
```

### Stages

#### 1. Run Tests

```bash
pytest
```

---

#### 2. Build Docker Images

Services:

- api-service
- risk-engine
- worker-service

Example:

```bash
docker build -t api-service .
docker build -t risk-engine .
docker build -t worker-service .
```

---

#### 3. Push Images

Registry:

```text
ghcr.io
```

Tagging:

```text
latest
commit-sha
```

Example:

```text
ghcr.io/deploysense/api-service:latest
ghcr.io/deploysense/api-service:<commit-sha>
```

---

#### 4. Update GitOps Repository

Update:

```yaml
image:
  tag: <commit-sha>
```

Commit:

```text
chore: update deploysense images
```

---

#### 5. ArgoCD Sync

ArgoCD detects:

```text
GitOps repository changes
```

Then:

```text
Deploys updated image
```

to Kubernetes.

---

## 8.4 Release Pipeline

### Trigger

```yaml
on:
  push:
    tags:
      - v*
```

Example:

```text
v1.0.0
v1.1.0
v2.0.0
```

---

### Stages

#### Generate Release Notes

```bash
git log
```

---

#### Create GitHub Release

Artifacts:

- Docker image versions
- Release notes

---

#### Update Production Environment

Update GitOps manifests:

```yaml
image:
  tag: v1.0.0
```

ArgoCD deploys automatically.

---

## 8.5 Docker Standards

### Base Images

API Service

```dockerfile
python:3.13-slim
```

Risk Engine

```dockerfile
python:3.13-slim
```

Worker Service

```dockerfile
python:3.13-slim
```

---

### Requirements

- Multi-stage builds
- Non-root user
- Minimal image size
- Health checks enabled

---

## 8.6 Deployment Strategy

### Kubernetes Rolling Update

```yaml
strategy:
  type: RollingUpdate
```

Configuration:

```yaml
maxSurge: 1
maxUnavailable: 0
```

Benefits:

- Zero downtime
- Safe rollout

---

## 8.7 Rollback Strategy

Rollback performed through:

```text
ArgoCD
```

Rollback Sources:

- Previous Git commit
- Previous image tag

Deployment can be restored by:

```text
Git revert
```

or

```text
ArgoCD rollback
```

---

## 8.8 Quality Gates

| Gate | Requirement |
|--------|-------------|
| Linting | Must Pass |
| Formatting | Must Pass |
| Type Checking | Must Pass |
| Unit Tests | Must Pass |
| Integration Tests | Must Pass |
| Security Scan | Must Pass |
| Docker Build | Must Pass |
| Image Scan | Must Pass |
| Coverage | ≥ 80% |

---

## 8.9 Environment Strategy

### Development

Purpose:

- Local development
- Feature testing

Deployment:

```text
Docker Compose
```

---

### Staging

Purpose:

- Integration testing
- Pre-production validation

Deployment:

```text
Kubernetes
```

---

### Production

Purpose:

- Live deployments

Deployment:

```text
Kubernetes + ArgoCD
```

---

## 8.10 Git Branch Strategy

### Main

```text
main
```

Production-ready code.

---

### Feature Branches

```text
feature/*
```

Examples:

```text
feature/risk-engine
feature/github-integration
feature/alerts
```

---

### Release Tags

```text
v1.0.0
v1.1.0
v2.0.0
```

---

## 8.11 Future Enhancements

Introduced only when scale justifies them:

- Multi-architecture image builds
- Canary deployments
- Blue-Green deployments
- Progressive delivery
- Kafka-based deployment events
- Supply chain signing
- SBOM generation
- Multi-cluster deployments