"""Integration tests for Security and Audit API endpoints."""

import pytest
from httpx import AsyncClient
from backend.app.core.database import AsyncSessionLocal
from security.audit.auditor import AuditService


@pytest.mark.asyncio
async def test_security_inspect_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/security/inspect endpoint."""
    payload = {
        "content": "Server auth token sk-ant-1234567890abcdefghijklmnopqrstuvwx",
        "sender_id": "test-agent-01",
        "permissions": ["MESSAGE_AGENTS"],
        "target_scope": "HIVE",
        "is_same_hive": True,
    }
    response = await async_client.post("/api/v1/security/inspect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "REDACTED"
    assert "ANTHROPIC_API_KEY" in data["detected_secrets"]
    assert "[REDACTED_SECRET:ANTHROPIC_API_KEY]" in data["sanitized_text"]


@pytest.mark.asyncio
async def test_audit_log_query_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/audit endpoint."""
    # Insert test audit log
    async with AsyncSessionLocal() as session:
        await AuditService.record_event(
            session=session,
            actor_type="SYSTEM",
            actor_id="sys-01",
            action="SECURITY_SCAN_COMPLETED",
            status="SUCCESS",
            details={"threats_mitigated": 3},
        )

    response = await async_client.get("/api/v1/audit?action=SECURITY_SCAN_COMPLETED")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["action"] == "SECURITY_SCAN_COMPLETED"
