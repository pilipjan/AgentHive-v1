"""Token Escrow Economics and Agent Wallets API Endpoints."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.escrow import (
    DepositRequest,
    EscrowContractResponse,
    TransactionListResponse,
    WalletResponse,
)
from backend.app.services.agent_service import AgentService
from backend.app.services.escrow_service import EscrowService

router = APIRouter()


@router.get(
    "/wallets/me",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Operator / Current User Wallet",
    description="Fetch available balance, locked escrow, and lifetime statistics for the operator account.",
)
async def get_operator_wallet(
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Fetch default operator wallet."""
    user = await AgentService.get_or_create_default_user(db)
    wallet = await EscrowService.get_or_create_wallet(db, "USER", user.id)
    return EscrowService.to_wallet_response(wallet)


@router.get(
    "/wallets/{agent_id}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Wallet",
    description="Fetch available balance, locked escrow, and earned bounties for a specific agent.",
)
async def get_agent_wallet(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Fetch agent wallet by slug or UUID."""
    wallet = await EscrowService.get_agent_wallet_by_slug(db, agent_id)
    return EscrowService.to_wallet_response(wallet)


@router.post(
    "/deposit",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Deposit Credits to Wallet",
    description="Add test or purchased credits to an agent or operator wallet.",
)
async def deposit_credits(
    payload: DepositRequest,
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Deposit credits."""
    wallet = await EscrowService.deposit(
        session=db,
        target_type=payload.target_type,
        target_identifier=payload.target_id,
        amount=payload.amount,
    )
    return EscrowService.to_wallet_response(wallet)


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Escrow Transactions",
    description="Query immutable audit ledger of balance transfers, deposits, locks, releases, and refunds.",
)
async def list_transactions(
    wallet_id: Optional[str] = Query(None, description="Filter by wallet UUID"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """Query transactions."""
    w_uuid = None
    if wallet_id:
        try:
            w_uuid = uuid.UUID(wallet_id)
        except ValueError:
            pass

    total, txs = await EscrowService.list_transactions(
        session=db,
        wallet_id=w_uuid,
        limit=limit,
        offset=offset,
    )
    items = [EscrowService.to_transaction_response(t) for t in txs]
    return TransactionListResponse(total=total, items=items)
