"""Integration tests for HiveStore Heartbeat telemetry, Uptime stats, and Community Reviews."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_monitoring_heartbeats_and_reviews_lifecycle(async_client: AsyncClient):
    """Verify heartbeat recording, uptime calculation, review submissions, and star rating recalculation."""
    uid = uuid.uuid4().hex[:6]
    slug = f"monitored-agent-{uid}"

    # 1. Publish Blueprint
    await async_client.post("/api/v1/store/blueprints", json={
        "slug": slug,
        "name": "Monitored Research Bot",
        "description": "Continuous market analysis agent.",
        "category": "research",
        "tags": ["research", "finance"],
    })

    # 2. Record 2 Heartbeat Pings (proving 30 days of running uptime)
    uptime_30_days = 30 * 86400  # 2,592,000 seconds
    hb_res1 = await async_client.post("/api/v1/store/heartbeat", json={
        "blueprint_slug": slug,
        "instance_id": "inst-vps-01",
        "status": "ONLINE",
        "uptime_seconds": uptime_30_days,
        "response_time_ms": 120.5,
        "host_info": "Oracle-ARM64",
    })
    assert hb_res1.status_code == 200
    assert "mo" in hb_res1.json()["uptime_human"] or "d" in hb_res1.json()["uptime_human"]

    # 3. Query Uptime & Reliability Stats
    uptime_res = await async_client.get(f"/api/v1/store/blueprints/{slug}/uptime")
    assert uptime_res.status_code == 200
    uptime_data = uptime_res.json()
    assert uptime_data["status"] == "ONLINE"
    assert uptime_data["max_uptime_seconds"] == uptime_30_days
    assert uptime_data["total_heartbeats"] == 1
    assert uptime_data["active_instances"] >= 1

    # 4. Submit 5-Star Review
    rev_res1 = await async_client.post(f"/api/v1/store/blueprints/{slug}/reviews", json={
        "reviewer_name": "DevAlice",
        "rating": 5,
        "title": "Running in production for 1 month without a single crash!",
        "review_text": "Cloned this template on my Ubuntu server and it has been analyzing news non-stop.",
        "verified_clone": True,
        "uptime_experienced": "1 month",
    })
    assert rev_res1.status_code == 201
    assert rev_res1.json()["rating"] == 5
    assert rev_res1.json()["verified_clone"] is True

    # 5. Submit 4-Star Review
    rev_res2 = await async_client.post(f"/api/v1/store/blueprints/{slug}/reviews", json={
        "reviewer_name": "DevBob",
        "rating": 4,
        "title": "Great agent, easy setup",
        "review_text": "Works as advertised. Setup took only 5 minutes with Docker Compose.",
        "verified_clone": False,
    })
    assert rev_res2.status_code == 201

    # 6. List Reviews and Verify Average Rating
    list_rev = await async_client.get(f"/api/v1/store/blueprints/{slug}/reviews")
    assert list_rev.status_code == 200
    rev_data = list_rev.json()
    assert rev_data["total"] == 2
    assert rev_data["avg_rating"] == 4.5  # (5 + 4) / 2
    assert rev_data["verified_clone_count"] == 1
    assert len(rev_data["items"]) == 2

    # 7. Verify Blueprint Detail reflects updated rating & review count
    bp_detail = await async_client.get(f"/api/v1/store/blueprints/{slug}")
    assert bp_detail.status_code == 200
    assert bp_detail.json()["review_count"] == 2
    assert bp_detail.json()["avg_rating"] == 4.5
