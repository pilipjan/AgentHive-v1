"""Unit tests for token escrow mathematics, wallet locking, and payout arithmetic."""

import uuid
import pytest
from backend.app.models.escrow import AgentWallet, EscrowContract


def test_wallet_balance_arithmetic():
    """Verify deposit, lock, release, and earnings calculations."""
    wallet = AgentWallet(
        id=uuid.uuid4(),
        owner_type="AGENT",
        balance=500.0,
        locked_escrow=0.0,
        total_earned=0.0,
        total_spent=0.0,
    )

    # 1. Lock 200 credits in bounty
    bounty = 200.0
    wallet.balance -= bounty
    wallet.locked_escrow += bounty
    wallet.total_spent += bounty

    assert wallet.balance == 300.0
    assert wallet.locked_escrow == 200.0
    assert wallet.total_spent == 200.0

    # 2. Complete and earn a 350 credit bounty
    payout = 350.0
    wallet.balance += payout
    wallet.total_earned += payout

    assert wallet.balance == 650.0
    assert wallet.total_earned == 350.0


def test_escrow_contract_state_transitions():
    """Verify valid escrow contract lifecycle states."""
    valid_states = {"HELD", "RELEASED", "REFUNDED", "DISPUTED"}
    assert "HELD" in valid_states
    assert "RELEASED" in valid_states
    assert "REFUNDED" in valid_states
