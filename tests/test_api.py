"""
DeploySense — Unit Tests: API Routes

Tests for the FastAPI HTTP endpoints.
Uses FastAPI's TestClient (httpx-based) to make real HTTP calls
against the application without starting a server.

NOTE: These tests use the actual database by default.
For true unit tests, we'd mock the DB session.
For MVP, testing against a real (test) DB catches more bugs.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """
    Create a test client for the API Service.

    NOTE: This imports the app, which initializes the DB engine.
    For unit tests to work without Postgres, we'd need to mock
    the database session dependency. That's a Phase 1 task.
    """
    # Lazy import to avoid DB connection on import
    from deploysense.api.main import app

    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Health check should always return 200."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_service_name(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-service"


class TestRootEndpoint:
    """Root endpoint returns service info."""

    def test_root_returns_service_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "deploysense-api"
        assert "docs" in data


class TestMetricsEndpoint:
    """Prometheus metrics endpoint."""

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestOpenAPIDocs:
    """Verify OpenAPI docs are accessible."""

    def test_docs_endpoint(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "DeploySense"
