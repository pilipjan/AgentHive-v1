"""Integration tests for Task Orchestration, Multi-Agent Hives, and Human Oversight."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_orchestration_and_hive_lifecycle(async_client: AsyncClient):
    """Verify task submission, automatic agent matching, hive assembly, peer review, and completion."""
    # 1. Register 3 specialized agents
    a1_slug = f"agt-coder-{uuid.uuid4().hex[:6]}"
    a2_slug = f"agt-researcher-{uuid.uuid4().hex[:6]}"
    a3_slug = f"agt-reviewer-{uuid.uuid4().hex[:6]}"

    await async_client.post("/api/v1/agents", json={
        "name": "PythonCoder",
        "public_id": a1_slug,
        "capabilities": ["python", "fastapi", "docker"],
    })
    await async_client.post("/api/v1/agents", json={
        "name": "WebResearcher",
        "public_id": a2_slug,
        "capabilities": ["research", "analysis", "tts"],
    })
    await async_client.post("/api/v1/agents", json={
        "name": "QualityReviewer",
        "public_id": a3_slug,
        "capabilities": ["verification", "security", "qa"],
    })

    # 2. Submit Task with Requirements requiring Python & Research
    task_payload = {
        "title": "Evaluate lowest cost TTS API for 12-hour daily livestream",
        "description": "Compare ElevenLabs, Azure, and Kokoro TTS on latency, price, and ARM64 compatibility.",
        "requirements": ["python", "research", "tts"],
        "max_iterations": 5,
        "auto_orchestrate": True,
    }
    task_res = await async_client.post("/api/v1/tasks", json=task_payload)
    assert task_res.status_code == 201
    task_data = task_res.json()
    task_id = task_data["task_id"]

    # Verify task completed through orchestration pipeline
    assert task_data["status"] == "COMPLETED"
    assert task_data["hive_id"] is not None
    assert len(task_data["assigned_agents"]) >= 2
    assert "subtasks" in task_data["result"]
    assert task_data["result"]["confidence"] > 0.90

    # 3. Query Task by ID
    get_task_res = await async_client.get(f"/api/v1/tasks/{task_id}")
    assert get_task_res.status_code == 200
    loaded_task = get_task_res.json()
    assert loaded_task["task_id"] == task_id

    # 4. Query Assembled Hive
    hive_id = task_data["hive_id"]
    hive_res = await async_client.get(f"/api/v1/hives/{hive_id}")
    assert hive_res.status_code == 200
    hive_data = hive_res.json()
    assert hive_data["status"] == "ACTIVE"
    assert len(hive_data["members"]) >= 2

    # 5. Test Human Oversight: Task Cancellation
    cancel_task_payload = {
        "title": "Long running batch processing",
        "description": "A slow task to demonstrate operator cancellation.",
        "requirements": ["python"],
        "auto_orchestrate": False,  # Keeps it in CREATED state
    }
    create_unrun = await async_client.post("/api/v1/tasks", json=cancel_task_payload)
    assert create_unrun.status_code == 201
    unrun_id = create_unrun.json()["task_id"]

    # Operator cancels in-flight task
    cancel_res = await async_client.post(f"/api/v1/tasks/{unrun_id}/cancel?reason=Operator+intervened")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 6. Test Disband Hive
    disband_res = await async_client.post(f"/api/v1/hives/{hive_id}/disband")
    assert disband_res.status_code == 200
    assert disband_res.json()["status"] == "DISBANDED"
