"""Integration tests for Agent Marketplace, Task Bounties, and Bidding APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_marketplace_job_bidding_and_award_lifecycle(async_client: AsyncClient):
    """Verify job publishing, auto-bidding, ranking, and proposal acceptance."""
    # 1. Register 2 Specialized Agents
    uid = uuid.uuid4().hex[:6]
    a1_slug = f"agt-expert-{uid}"
    a2_slug = f"agt-general-{uid}"

    await async_client.post("/api/v1/agents", json={
        "name": "ExpertDeveloper",
        "public_id": a1_slug,
        "capabilities": ["python", "fastapi", "docker"],
    })
    await async_client.post("/api/v1/agents", json={
        "name": "GeneralAssistant",
        "public_id": a2_slug,
        "capabilities": ["research"],
    })

    # 2. Publish Open Job Bounty
    job_payload = {
        "title": "Build high-throughput async webhook distributor",
        "description": "Develop an asynchronous FastAPI webhook engine handling 10k req/sec.",
        "requirements": ["python", "fastapi"],
        "bounty_reward": 500.0,
        "auto_invite_bids": True,
    }
    job_res = await async_client.post("/api/v1/marketplace/jobs", json=job_payload)
    assert job_res.status_code == 201
    job_data = job_res.json()
    job_id = job_data["job_id"]
    assert job_data["bounty_reward"] == 500.0
    assert job_data["proposals_count"] >= 1

    # 3. Submit Manual Proposal from General Assistant
    manual_bid_payload = {
        "agent_id": a2_slug,
        "proposed_strategy": "Will research best webhook dispatch algorithms and write documentation.",
        "estimated_duration_seconds": 45,
    }
    bid_res = await async_client.post(f"/api/v1/marketplace/jobs/{job_id}/proposals", json=manual_bid_payload)
    assert bid_res.status_code == 201
    assert bid_res.json()["agent_id"] == a2_slug

    # 4. Fetch Job with Ranked Proposals
    get_job_res = await async_client.get(f"/api/v1/marketplace/jobs/{job_id}")
    assert get_job_res.status_code == 200
    job_details = get_job_res.json()
    assert len(job_details["proposals"]) >= 2
    # First proposal must be highest score
    proposals = job_details["proposals"]
    assert proposals[0]["bid_score"] >= proposals[1]["bid_score"]
    winning_bid_id = proposals[0]["id"]

    # 5. Accept Winning Proposal & Award Bounty
    accept_res = await async_client.post(f"/api/v1/marketplace/jobs/{job_id}/accept-proposal/{winning_bid_id}")
    assert accept_res.status_code == 200
    awarded_job = accept_res.json()
    assert awarded_job["status"] == "COMPLETED"
    assert awarded_job["task_id"] is not None

    # Verify winning proposal is marked ACCEPTED
    winning_p = [p for p in awarded_job["proposals"] if p["id"] == winning_bid_id][0]
    assert winning_p["status"] == "ACCEPTED"
