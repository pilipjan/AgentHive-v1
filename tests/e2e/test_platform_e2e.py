"""Complete End-to-End scenario test for AgentHive V1 Platform."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_platform_scenario(async_client: AsyncClient):
    """End-to-End test covering the complete lifecycle:

    1. Health and subsystem readiness.
    2. Agent registration and capability stamping.
    3. Atomic permission assignment.
    4. Controlled messaging with real-time Memory Firewall redaction.
    5. Shared knowledge publishing and Bayesian peer verification.
    6. Task orchestration, Hive formation, and review synthesis.
    7. Peer evaluation and multi-factor reputation calculation.
    8. Sanitized audit logging verification.
    """
    # Step 1: Health & Readiness
    health_res = await async_client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"].upper() == "HEALTHY"

    ready_res = await async_client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"].upper() == "READY"

    # Step 2: Register 3 Specialized Agents
    uid = uuid.uuid4().hex[:6]
    a1_slug = f"agt-extractor-{uid}"
    a2_slug = f"agt-coder-{uid}"
    a3_slug = f"agt-verifier-{uid}"

    # Agent 1: DataExtractor
    r1 = await async_client.post("/api/v1/agents", json={
        "name": "DataExtractor",
        "public_id": a1_slug,
        "description": "Scrapes and parses structured technical specifications.",
        "capabilities": ["data_extraction", "parsing", "http"],
    })
    assert r1.status_code == 201

    # Agent 2: CodeSynthesizer
    r2 = await async_client.post("/api/v1/agents", json={
        "name": "CodeSynthesizer",
        "public_id": a2_slug,
        "description": "Writes production-ready Python and Docker definitions.",
        "capabilities": ["python", "docker", "fastapi"],
    })
    assert r2.status_code == 201

    # Agent 3: Senior Verifier (with high reputation)
    r3 = await async_client.post("/api/v1/agents", json={
        "name": "AuditVerifier",
        "public_id": a3_slug,
        "description": "Evaluates code quality, security posture, and benchmarks.",
        "capabilities": ["verification", "security", "qa"],
    })
    assert r3.status_code == 201

    # Step 3: Grant Atomic Permissions
    await async_client.post(f"/api/v1/agents/{a1_slug}/permissions", json={"permission_name": "SEND_MESSAGE"})
    await async_client.post(f"/api/v1/agents/{a2_slug}/permissions", json={"permission_name": "WRITE_KNOWLEDGE"})
    await async_client.post(f"/api/v1/agents/{a3_slug}/permissions", json={"permission_name": "VERIFY_KNOWLEDGE"})

    # Elevate verifier reputation for verification eligibility
    from backend.app.core.database import AsyncSessionLocal
    from backend.app.services.agent_service import AgentService
    async with AsyncSessionLocal() as session:
        v_agent = await AgentService.get_agent_by_id_or_slug(session, a3_slug)
        v_agent.reputation_score = 4.60
        await session.commit()

    # Step 4: Controlled Messaging through Memory Firewall
    msg_res = await async_client.post("/api/v1/messages", json={
        "sender_agent_id": a1_slug,
        "recipient_agent_id": a2_slug,
        "content": "Sending API dataset sk-proj-999888777666555444333222111000aaaabbbbccccdddd and email alice@team.org",
        "message_type": "DIRECT",
    })
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["authorization_result"] == "REDACTED"
    assert "[REDACTED_SECRET:OPENAI_API_KEY]" in msg_data["content"]
    assert "[REDACTED_EMAIL]" in msg_data["content"]
    assert "sk-proj-999888777666555444333222111000aaaabbbbccccdddd" not in msg_data["content"]

    # Step 5: Shared Knowledge Base & Peer Verification
    k_res = await async_client.post("/api/v1/knowledge", json={
        "summary": "ARM64 v4l2m2m hardware video encoding optimization",
        "content": "Using `-c:v h264_v4l2m2m` drops CPU utilization to 34% on Linux ARM64.",
        "source_agent_id": a2_slug,
        "visibility": "PUBLIC",
        "tags": ["arm64", "ffmpeg", "performance"],
    })
    assert k_res.status_code == 201
    k_id = k_res.json()["id"]

    # Peer Verification by Senior Verifier
    verif_res = await async_client.post(f"/api/v1/knowledge/{k_id}/verify", json={
        "verifying_agent_id": a3_slug,
        "verdict": "VERIFIED",
        "evidence": "Benchmark tested with 1080p stream over 6 hours.",
    })
    assert verif_res.status_code == 200
    assert verif_res.json()["confidence"] > 0.60
    assert verif_res.json()["verification_count"] == 1

    # Step 6: Multi-Agent Task Orchestration & Hive Formation
    task_res = await async_client.post("/api/v1/tasks", json={
        "title": "Architect scalable multi-agent microservice on ARM64",
        "description": "Decompose requirements, match specialized agents, and assemble a temporary Hive.",
        "requirements": ["python", "verification"],
        "max_iterations": 5,
        "auto_orchestrate": True,
    })
    assert task_res.status_code == 201
    task_data = task_res.json()
    assert task_data["status"] == "COMPLETED"
    assert task_data["hive_id"] is not None
    assert len(task_data["assigned_agents"]) >= 2
    assert "subtasks" in task_data["result"]
    assert task_data["result"]["confidence"] > 0.90

    # Step 7: Peer Review Evaluation & Reputation Recalculation
    eval_res = await async_client.post("/api/v1/evaluations", json={
        "task_id": task_data["task_id"],
        "reviewer_agent_id": a3_slug,
        "target_agent_id": a2_slug,
        "task_success_score": 0.98,
        "usefulness_score": 0.95,
        "accuracy_score": 0.97,
        "reliability_score": 0.96,
        "safety_score": 1.00,
        "comments": "Exceptional execution quality and full security compliance.",
    })
    assert eval_res.status_code == 201

    rep_res = await async_client.get(f"/api/v1/reputation/{a2_slug}")
    assert rep_res.status_code == 200
    rep_profile = rep_res.json()
    assert rep_profile["composite_score"] > 4.70
    assert rep_profile["star_rating"] >= 4.7

    # Step 8: Audit Log Verification
    audit_res = await async_client.get("/api/v1/audit?limit=10")
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["items"]
    assert len(audit_items) > 0
