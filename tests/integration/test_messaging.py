"""Integration tests for Controlled Agent Messaging APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_controlled_messaging_lifecycle(async_client: AsyncClient):
    """Test message transmission, sanitization, blocking, and querying."""
    # 1. Register Agent A and Agent B
    slug_a = f"agt-alice-{uuid.uuid4().hex[:6]}"
    slug_b = f"agt-bob-{uuid.uuid4().hex[:6]}"

    res_a = await async_client.post("/api/v1/agents", json={"name": "AgentAlice", "public_id": slug_a})
    assert res_a.status_code == 201

    res_b = await async_client.post("/api/v1/agents", json={"name": "AgentBob", "public_id": slug_b})
    assert res_b.status_code == 201

    # 2. Agent A sends clean message to Agent B
    clean_msg_payload = {
        "sender_agent_id": slug_a,
        "recipient_agent_id": slug_b,
        "content": "Hello Bob, please review the latest dataset benchmarks.",
        "message_type": "DIRECT",
    }
    msg_res = await async_client.post("/api/v1/messages", json=clean_msg_payload)
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["authorization_result"] == "ALLOWED"
    assert "latest dataset benchmarks" in msg_data["content"]

    # 3. Agent A sends message with API Key and Email -> Must be REDACTED
    sensitive_payload = {
        "sender_agent_id": slug_a,
        "recipient_agent_id": slug_b,
        "content": "Contact alice@domain.org or use key sk-1234567890abcdef1234567890 for API test.",
        "message_type": "DIRECT",
    }
    redact_res = await async_client.post("/api/v1/messages", json=sensitive_payload)
    assert redact_res.status_code == 201
    redacted_data = redact_res.json()
    assert redacted_data["authorization_result"] == "REDACTED"
    assert "[REDACTED_EMAIL]" in redacted_data["content"]
    assert "[REDACTED_SECRET:OPENAI_API_KEY]" in redacted_data["content"]
    assert "sk-1234567890abcdef1234567890" not in redacted_data["content"]

    # 4. Agent A sends forbidden private key -> Must be BLOCKED (403)
    blocked_payload = {
        "sender_agent_id": slug_a,
        "recipient_agent_id": slug_b,
        "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Y...\n-----END RSA PRIVATE KEY-----",
        "message_type": "DIRECT",
    }
    blocked_res = await async_client.post("/api/v1/messages", json=blocked_payload)
    assert blocked_res.status_code == 403

    # 5. Disable Agent B and verify Agent A cannot message disabled agent
    await async_client.post(f"/api/v1/agents/{slug_b}/disable")
    disabled_target_res = await async_client.post(
        "/api/v1/messages",
        json={
            "sender_agent_id": slug_a,
            "recipient_agent_id": slug_b,
            "content": "Are you online?",
        },
    )
    assert disabled_target_res.status_code == 403

    # 6. Query Message History for Agent A
    list_res = await async_client.get(f"/api/v1/messages?agent_id={slug_a}")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 2
