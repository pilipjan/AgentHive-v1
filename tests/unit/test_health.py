"""Unit tests for system health and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_probe(async_client: AsyncClient):
    """Verify root /health returns 200 OK with expected payload structure."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "AgentHive"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_v1_health_probe(async_client: AsyncClient):
    """Verify /api/v1/health returns 200 OK."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ready_probe(async_client: AsyncClient):
    """Verify /ready returns subsystem readiness status."""
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "subsystems" in data
    assert data["subsystems"]["api_gateway"] == "ready"
    assert data["subsystems"]["memory_firewall"] == "ready"
