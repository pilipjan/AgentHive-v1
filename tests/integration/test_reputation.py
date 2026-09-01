"""Integration tests for Multi-Factor Reputation & Evaluation APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reputation_and_evaluation_lifecycle(async_client: AsyncClient):
    """Verify evaluation submission, score recalculation, and event ledger logging."""
    # 1. Register Reviewer and Worker Agents
    rev_slug = f"agt-reviewer-{uuid.uuid4().hex[:6]}"
    worker_slug = f"agt-worker-{uuid.uuid4().hex[:6]}"

    await async_client.post("/api/v1/agents", json={"name": "ReviewerAgent", "public_id": rev_slug})
    await async_client.post("/api/v1/agents", json={"name": "WorkerAgent", "public_id": worker_slug})

    # 2. Create Task for Evaluation context
    task_res = await async_client.post("/api/v1/tasks", json={
        "title": "API optimization task",
        "description": "Task for testing reputation evaluation updates.",
        "auto_orchestrate": False,
    })
    assert task_res.status_code == 201
    task_id = task_res.json()["task_id"]

    # 3. Submit Evaluation for Worker Agent
    eval_payload = {
        "task_id": task_id,
        "reviewer_agent_id": rev_slug,
        "target_agent_id": worker_slug,
        "task_success_score": 0.95,
        "usefulness_score": 0.90,
        "accuracy_score": 0.98,
        "reliability_score": 0.92,
        "safety_score": 1.00,
        "comments": "Great collaboration and clean output.",
    }
    eval_res = await async_client.post("/api/v1/evaluations", json=eval_payload)
    assert eval_res.status_code == 201
    eval_data = eval_res.json()
    assert eval_data["task_success_score"] == 0.95

    # 4. Query Worker Reputation Breakdown
    rep_res = await async_client.get(f"/api/v1/reputation/{worker_slug}")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["agent_id"] == worker_slug
    assert rep_data["composite_score"] > 4.50
    assert rep_data["star_rating"] >= 4.5
    assert rep_data["metrics"]["evaluations_count"] == 1
    assert "task_success" in rep_data["weight_formula"]

    # 5. Query Reputation History Ledger
    hist_res = await async_client.get(f"/api/v1/reputation/{worker_slug}/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_events"] >= 1
    assert any(e["event_type"] == "PEER_REVIEW" for e in hist_data["events"])
