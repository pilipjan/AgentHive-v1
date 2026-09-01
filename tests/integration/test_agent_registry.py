"""Integration tests for Agent Registry & Identity APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_registry_lifecycle(async_client: AsyncClient):
    """Verify registration, query, update, permission management, and disabling."""
    # 1. Register Agent
    slug = f"agt-pytest-{uuid.uuid4().hex[:6]}"
    create_payload = {
        "name": "PythonArchitect",
        "public_id": slug,
        "description": "Expert in FastAPI microservices, Docker, and async architecture.",
        "model_provider": "OPENAI",
        "model_name": "gpt-4o-mini",
        "capabilities": ["python", "fastapi", "docker", "architecture"],
    }
    create_res = await async_client.post("/api/v1/agents", json=create_payload)
    assert create_res.status_code == 201
    agent_data = create_res.json()
    assert agent_data["name"] == "PythonArchitect"
    assert agent_data["public_id"] == slug
    assert agent_data["status"] == "ACTIVE"
    assert "READ_PUBLIC_KNOWLEDGE" in agent_data["permissions"]
    agent_id = agent_data["id"]

    # 2. Query Agent Profile by slug
    get_res = await async_client.get(f"/api/v1/agents/{slug}")
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile["id"] == agent_id
    assert profile["reputation_score"] == 3.0
    assert profile["trust_indicators"]["identity_verified"] is True

    # 3. List Agents and Filter by capability
    list_res = await async_client.get("/api/v1/agents?capability=fastapi")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(a["public_id"] == slug for a in list_data["items"])

    # 4. Update Agent
    update_payload = {
        "description": "Updated specialization description.",
        "capabilities": ["python", "fastapi", "docker", "architecture", "kubernetes"],
    }
    update_res = await async_client.patch(f"/api/v1/agents/{slug}", json=update_payload)
    assert update_res.status_code == 200
    updated_profile = update_res.json()
    assert "kubernetes" in updated_profile["capabilities"]
    assert updated_profile["description"] == "Updated specialization description."

    # 5. Grant Permission
    perm_payload = {"permission_name": "WRITE_KNOWLEDGE"}
    perm_res = await async_client.post(f"/api/v1/agents/{slug}/permissions", json=perm_payload)
    assert perm_res.status_code == 201
    assert perm_res.json()["permission_name"] == "WRITE_KNOWLEDGE"

    # Verify permissions list
    perms_res = await async_client.get(f"/api/v1/agents/{slug}/permissions")
    assert perms_res.status_code == 200
    perms_list = perms_res.json()
    assert any(p["permission_name"] == "WRITE_KNOWLEDGE" for p in perms_list)

    # 6. Emergency Disable Agent (Human Oversight)
    disable_res = await async_client.post(
        f"/api/v1/agents/{slug}/disable?reason=Test+operator+action"
    )
    assert disable_res.status_code == 200
    disabled_profile = disable_res.json()
    assert disabled_profile["status"] == "DISABLED"

    # 7. Nonexistent agent returns 404
    non_existent = await async_client.get("/api/v1/agents/agt-non-existent-999")
    assert non_existent.status_code == 404
