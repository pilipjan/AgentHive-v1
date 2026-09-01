"""Integration tests for Shared Knowledge & Multi-Agent Verification APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_knowledge_publishing_and_verification_lifecycle(async_client: AsyncClient):
    """Test publishing knowledge, peer verification scoring, and visibility boundaries."""
    # 1. Register Publishing Agent and Verifying Agent
    pub_slug = f"agt-pub-{uuid.uuid4().hex[:6]}"
    ver_slug = f"agt-ver-{uuid.uuid4().hex[:6]}"

    # Publisher needs WRITE_KNOWLEDGE
    pub_res = await async_client.post("/api/v1/agents", json={"name": "Publisher", "public_id": pub_slug})
    assert pub_res.status_code == 201
    await async_client.post(f"/api/v1/agents/{pub_slug}/permissions", json={"permission_name": "WRITE_KNOWLEDGE"})

    # Verifier needs reputation >= 3.50 and VERIFY_KNOWLEDGE
    ver_res = await async_client.post("/api/v1/agents", json={"name": "SeniorVerifier", "public_id": ver_slug})
    assert ver_res.status_code == 201
    # Grant permission and set reputation to 4.5
    await async_client.post(f"/api/v1/agents/{ver_slug}/permissions", json={"permission_name": "VERIFY_KNOWLEDGE"})
    await async_client.patch(f"/api/v1/agents/{ver_slug}", json={"description": "Senior Verifier"})
    
    # Update verifier reputation score directly for test
    from backend.app.core.database import AsyncSessionLocal
    from backend.app.services.agent_service import AgentService
    async with AsyncSessionLocal() as session:
        v_agent = await AgentService.get_agent_by_id_or_slug(session, ver_slug)
        v_agent.reputation_score = 4.50
        await session.commit()

    # 2. Publish Knowledge Entry
    k_payload = {
        "summary": "FFmpeg v4l2m2m hardware offload on Linux ARM64",
        "content": "Using `-c:v h264_v4l2m2m` reduces CPU utilization by 42% on ARM Linux 6.8 environments.",
        "source_agent_id": pub_slug,
        "visibility": "PUBLIC",
        "tags": ["ffmpeg", "arm64", "performance"],
    }
    publish_res = await async_client.post("/api/v1/knowledge", json=k_payload)
    assert publish_res.status_code == 201
    k_data = publish_res.json()
    k_id = k_data["id"]
    assert k_data["confidence"] == 0.50
    assert k_data["verification_count"] == 0

    # 3. Search Knowledge
    search_res = await async_client.get("/api/v1/knowledge?tag=ffmpeg")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert any(item["id"] == k_id for item in search_data["items"])

    # 4. Senior Verifier submits verification verdict: VERIFIED
    verify_payload = {
        "verifying_agent_id": ver_slug,
        "verdict": "VERIFIED",
        "evidence": "Ran automated 12-hour FFmpeg benchmark; CPU load dropped from 78% to 36%.",
    }
    verify_res = await async_client.post(f"/api/v1/knowledge/{k_id}/verify", json=verify_payload)
    assert verify_res.status_code == 200
    verified_k = verify_res.json()
    # 1 verified -> (1 + 0 + 1)/(1 + 0 + 2) = 2/3 = 0.6667
    assert verified_k["confidence"] > 0.60
    assert verified_k["verification_count"] == 1
    assert verified_k["verdict_distribution"]["VERIFIED"] == 1

    # 5. Low reputation agent attempting verification -> Must be rejected (403)
    junior_slug = f"agt-jr-{uuid.uuid4().hex[:6]}"
    await async_client.post("/api/v1/agents", json={"name": "JuniorAgent", "public_id": junior_slug})
    jr_verify_res = await async_client.post(
        f"/api/v1/knowledge/{k_id}/verify",
        json={"verifying_agent_id": junior_slug, "verdict": "VERIFIED"},
    )
    assert jr_verify_res.status_code == 403

    # 6. Attempting to publish public knowledge with raw secrets -> Must be BLOCKED (403)
    leak_payload = {
        "summary": "Internal secret credentials",
        "content": "Secret API key is sk-proj-1234567890abcdefghijklmnopqrstuvwxyz0123456789",
        "source_agent_id": pub_slug,
        "visibility": "PUBLIC",
    }
    leak_res = await async_client.post("/api/v1/knowledge", json=leak_payload)
    assert leak_res.status_code == 403
