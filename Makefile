# DeploySense — Root Makefile
# Usage: make <target>
#
# This is the single entry point for all development operations.
# Engineers should never need to remember per-service commands.

.PHONY: help install dev test lint format docker-up docker-down migrate clean

# ─── Help ────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ───────────────────────────────────────────────────────────────────

install: ## Install all dependencies
	python -m pip install -e ".[dev]"
	pre-commit install || true

# ─── Run Services ────────────────────────────────────────────────────────────

api: ## Run API service (port 8000)
	uvicorn deploysense.api.main:app --reload --host 0.0.0.0 --port 8000

risk-engine: ## Run Risk Engine service (port 8001)
	uvicorn deploysense.risk_engine.main:app --reload --host 0.0.0.0 --port 8001

worker: ## Run Worker service
	python -m deploysense.worker.main

dev: ## Run all services (requires honcho or similar)
	@echo "Starting all services..."
	@echo "  API:         http://localhost:8000"
	@echo "  Risk Engine: http://localhost:8001"
	@echo "  Docs:        http://localhost:8000/docs"

# ─── Test ────────────────────────────────────────────────────────────────────

test: ## Run all tests
	pytest --cov=deploysense --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest -m unit --cov=deploysense

test-integration: ## Run integration tests (requires docker-compose)
	pytest -m integration

test-e2e: ## Run end-to-end tests
	pytest -m e2e

# ─── Code Quality ────────────────────────────────────────────────────────────

lint: ## Run linter
	ruff check .
	mypy deploysense/

format: ## Auto-format code
	ruff format .
	ruff check --fix .

check: ## Run all checks (lint + test)
	ruff check .
	ruff format --check .
	mypy deploysense/
	pytest --cov=deploysense

# ─── Docker ──────────────────────────────────────────────────────────────────

docker-up: ## Start local infrastructure (Postgres, Redis)
	docker compose up -d

docker-down: ## Stop local infrastructure
	docker compose down

docker-clean: ## Stop and remove volumes
	docker compose down -v

docker-build: ## Build all service images
	docker compose -f docker-compose.yml -f docker-compose.services.yml build

# ─── Database ────────────────────────────────────────────────────────────────

migrate: ## Run database migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add users table")
	alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	alembic history --verbose

# ─── Clean ───────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage htmlcov/
