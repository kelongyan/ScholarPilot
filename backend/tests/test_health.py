"""Tests for the health check endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    """``GET /health`` returns 200 with ``{"status": "ok"}``."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_service_info() -> None:
    """``GET /`` returns the service name and version."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "ScholarPilot"
    assert "version" in body
    assert body["docs"] == "/docs"
