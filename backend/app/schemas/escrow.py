"""Pydantic request and response schemas for Token Escrow and Agent Wallets."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    """Agent or User Wallet details."""
    id: str
    owner_type: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    user_id: Optional[str] = None
    balance: float
    locked_escrow: float
    total_earned: float
    total_spent: float
    updated_at: datetime


class DepositRequest(BaseModel):
    """Credit deposit request."""
    target_type: str = Field(..., description="'AGENT' or 'USER'")
    target_id: str = Field(..., description="Agent public_id/UUID or User UUID")
    amount: float = Field(..., gt=0, description="Amount of credits to deposit")


class EscrowContractResponse(BaseModel):
    """Escrow contract detail."""
    id: str
    contract_id: str
    job_id: str
    job_title: Optional[str] = None
    amount: float
    status: str
    funder_wallet_id: str
    recipient_agent_id: Optional[str] = None
    recipient_agent_name: Optional[str] = None
    release_tx_id: Optional[str] = None
    refund_tx_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransactionResponse(BaseModel):
    """Audit transaction record."""
    id: str
    tx_id: str
    tx_type: str
    amount: float
    balance_after: Optional[float] = None
    source_wallet_id: Optional[str] = None
    destination_wallet_id: Optional[str] = None
    contract_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated transactions list."""
    total: int
    items: List[TransactionResponse]
