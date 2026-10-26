"""Smoke tests for OrbitOps health and foundation endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing an HTTP test client."""
    return TestClient(app)


def test_health_endpoint_success(client: TestClient) -> None:
    """Verify that GET /api/v1/health returns 200 with structured health payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "orbitops-api"
    assert data["status"] == "healthy"
    assert data["version"] == settings.app_version
    assert data["environment"] == settings.env
    assert data["simulation_mode"] is True
    assert "timestamp" in data


def test_root_endpoint_metadata(client: TestClient) -> None:
    """Verify that GET / returns service discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "orbitops-api"
    assert data["health"] == "/api/v1/health"
    assert data["simulation_mode"] is True


def test_cors_headers_allowed_origin(client: TestClient) -> None:
    """Verify CORS preflight / origin headers for allowed client origin."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_not_found_route(client: TestClient) -> None:
    """Verify 404 response on unknown routes."""
    response = client.get("/api/v1/unknown-endpoint-route")
    assert response.status_code == 404
