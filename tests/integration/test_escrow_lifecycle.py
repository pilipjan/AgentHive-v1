"""Integration tests for Token Escrow Economics, Wallets, and Bounty Settlement."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_escrow_wallet_lifecycle_and_bounty_settlement(async_client: AsyncClient):
    """Verify operator wallet balance, job bounty escrow locking, and winning agent payout."""
    uid = uuid.uuid4().hex[:6]
    agent_slug = f"agt-escrow-{uid}"

    # 1. Register specialized agent
    reg_res = await async_client.post("/api/v1/agents", json={
        "name": "EscrowSpecialist",
        "public_id": agent_slug,
        "description": "Expert in automated contract execution and token economics.",
        "capabilities": ["escrow", "finance", "contract", "bounties"],
    })
    assert reg_res.status_code == 201

    # 2. Query initial agent wallet
    wallet_res = await async_client.get(f"/api/v1/escrow/wallets/{agent_slug}")
    assert wallet_res.status_code == 200
    agent_wallet = wallet_res.json()
    initial_agent_balance = agent_wallet["balance"]
    assert initial_agent_balance >= 0

    # 3. Query operator/creator wallet
    op_wallet_res = await async_client.get("/api/v1/escrow/wallets/me")
    assert op_wallet_res.status_code == 200
    op_wallet_initial = op_wallet_res.json()
    initial_op_balance = op_wallet_initial["balance"]

    # 4. Post a Job Bounty with 300.0 credit reward (locks funds in escrow)
    bounty_amount = 300.0
    job_res = await async_client.post("/api/v1/marketplace/jobs", json={
        "title": "Implement multi-sig wallet payout verifier",
        "description": "Construct cryptographic proof verifier for bounty settlement.",
        "requirements": ["escrow", "finance"],
        "bounty_reward": bounty_amount,
        "auto_invite_bids": False,
    })
    assert job_res.status_code == 201
    job_data = job_res.json()
    job_id = job_data["job_id"]

    # 5. Agent submits proposal
    prop_res = await async_client.post(f"/api/v1/marketplace/jobs/{job_id}/proposals", json={
        "agent_id": agent_slug,
        "proposed_strategy": "Direct atomic settlement with zero-trust assertion ledger.",
        "estimated_duration_seconds": 15,
    })
    assert prop_res.status_code == 201
    proposal_id = prop_res.json()["proposal_id"]

    # 6. Accept proposal and award bounty (triggers atomic escrow payout)
    award_res = await async_client.post(f"/api/v1/marketplace/jobs/{job_id}/accept-proposal/{proposal_id}")
    assert award_res.status_code == 200
    award_data = award_res.json()
    assert award_data["status"] == "COMPLETED"

    # 7. Verify winning agent wallet received the bounty payout
    updated_wallet_res = await async_client.get(f"/api/v1/escrow/wallets/{agent_slug}")
    assert updated_wallet_res.status_code == 200
    updated_agent_wallet = updated_wallet_res.json()
    assert updated_agent_wallet["balance"] == initial_agent_balance + bounty_amount
    assert updated_agent_wallet["total_earned"] >= bounty_amount

    # 8. Verify deposit endpoint
    deposit_res = await async_client.post("/api/v1/escrow/deposit", json={
        "target_type": "AGENT",
        "target_id": agent_slug,
        "amount": 150.0,
    })
    assert deposit_res.status_code == 200
    assert deposit_res.json()["balance"] == updated_agent_wallet["balance"] + 150.0

    # 9. Query transactions ledger
    tx_res = await async_client.get("/api/v1/escrow/transactions")
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    assert tx_data["total"] >= 1
    assert len(tx_data["items"]) >= 1
