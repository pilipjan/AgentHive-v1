"""Escrow Service Layer for Token Economics, Wallet Management, and Atomic Bounty Settlement."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.websocket import event_broadcaster
from backend.app.models import Agent, AgentWallet, EscrowContract, EscrowTransaction, JobPosting, User
from backend.app.schemas.escrow import (
    EscrowContractResponse,
    TransactionResponse,
    WalletResponse,
)
from backend.app.services.agent_service import AgentService
from security.audit.auditor import AuditService


class EscrowService:
    """Business logic for Agent Wallets, Escrow Locking, and Atomic Bounty Settlement."""

    @classmethod
    async def get_or_create_wallet(
        cls,
        session: AsyncSession,
        owner_type: str,
        owner_id: uuid.UUID,
    ) -> AgentWallet:
        """Fetch or automatically initialize a credit balance wallet."""
        owner_type = owner_type.upper()
        if owner_type == "AGENT":
            query = select(AgentWallet).where(AgentWallet.agent_id == owner_id)
        else:
            query = select(AgentWallet).where(AgentWallet.user_id == owner_id)

        result = await session.execute(query)
        wallet = result.scalar_one_or_none()

        if not wallet:
            initial_balance = 2500.0 if owner_type == "USER" else 500.0
            wallet = AgentWallet(
                id=uuid.uuid4(),
                owner_type=owner_type,
                agent_id=owner_id if owner_type == "AGENT" else None,
                user_id=owner_id if owner_type == "USER" else None,
                balance=initial_balance,
                locked_escrow=0.0,
                total_earned=0.0,
                total_spent=0.0,
            )
            session.add(wallet)
            await session.commit()
            await session.refresh(wallet)

            # Record initial credit grant transaction
            tx = EscrowTransaction(
                tx_id=f"tx-grant-{uuid.uuid4().hex[:8]}",
                destination_wallet_id=wallet.id,
                tx_type="INITIAL_GRANT",
                amount=initial_balance,
                balance_after=initial_balance,
                details={"reason": "Platform genesis balance endowment"},
            )
            session.add(tx)
            await session.commit()

        return wallet

    @classmethod
    async def get_agent_wallet_by_slug(
        cls,
        session: AsyncSession,
        identifier: str,
    ) -> AgentWallet:
        """Fetch wallet by Agent public_id slug or UUID."""
        agent = await AgentService.get_agent_by_id_or_slug(session, identifier)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{identifier}' not found.")
        return await cls.get_or_create_wallet(session, "AGENT", agent.id)

    @classmethod
    async def deposit(
        cls,
        session: AsyncSession,
        target_type: str,
        target_identifier: str,
        amount: float,
    ) -> AgentWallet:
        """Deposit credits to an agent or user wallet."""
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than zero.")

        target_type = target_type.upper()
        if target_type == "AGENT":
            agent = await AgentService.get_agent_by_id_or_slug(session, target_identifier)
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{target_identifier}' not found.")
            wallet = await cls.get_or_create_wallet(session, "AGENT", agent.id)
        else:
            try:
                user_uuid = uuid.UUID(target_identifier)
            except ValueError:
                default_user = await AgentService.get_or_create_default_user(session)
                user_uuid = default_user.id
            wallet = await cls.get_or_create_wallet(session, "USER", user_uuid)

        wallet.balance += amount
        tx_id = f"tx-dep-{uuid.uuid4().hex[:8]}"
        tx = EscrowTransaction(
            tx_id=tx_id,
            destination_wallet_id=wallet.id,
            tx_type="DEPOSIT",
            amount=amount,
            balance_after=wallet.balance,
            details={"target": target_identifier},
        )
        session.add(tx)
        await session.commit()
        await session.refresh(wallet)

        await event_broadcaster.broadcast(
            "WALLET_DEPOSIT",
            {"wallet_id": str(wallet.id), "amount": amount, "balance": wallet.balance},
            topic="global",
        )

        return wallet

    @classmethod
    async def lock_bounty_escrow(
        cls,
        session: AsyncSession,
        job: JobPosting,
        funder_user_id: uuid.UUID,
        bounty_amount: float,
    ) -> EscrowContract:
        """Lock funds in escrow when an open task bounty is posted."""
        if bounty_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bounty reward must be positive.")

        funder_wallet = await cls.get_or_create_wallet(session, "USER", funder_user_id)
        if funder_wallet.balance < bounty_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: {funder_wallet.balance:.2f} PTS, Required: {bounty_amount:.2f} PTS.",
            )

        # Atomic lock
        funder_wallet.balance -= bounty_amount
        funder_wallet.locked_escrow += bounty_amount
        funder_wallet.total_spent += bounty_amount

        contract = EscrowContract(
            id=uuid.uuid4(),
            contract_id=f"escrow-{uuid.uuid4().hex[:8]}",
            job_id=job.id,
            funder_wallet_id=funder_wallet.id,
            amount=bounty_amount,
            status="HELD",
        )
        session.add(contract)

        tx_id = f"tx-lock-{uuid.uuid4().hex[:8]}"
        tx = EscrowTransaction(
            tx_id=tx_id,
            source_wallet_id=funder_wallet.id,
            contract_id=contract.id,
            tx_type="ESCROW_LOCK",
            amount=bounty_amount,
            balance_after=funder_wallet.balance,
            details={"job_id": job.job_id, "title": job.title},
        )
        session.add(tx)
        await session.commit()
        await session.refresh(contract)

        await event_broadcaster.broadcast(
            "ESCROW_LOCKED",
            {
                "contract_id": contract.contract_id,
                "job_id": job.job_id,
                "bounty": bounty_amount,
                "status": "HELD",
            },
            topic="global",
        )

        return contract

    @classmethod
    async def release_bounty_payout(
        cls,
        session: AsyncSession,
        job: JobPosting,
        winning_agent_id: uuid.UUID,
    ) -> EscrowContract:
        """Atomically release held bounty credits from escrow to the winning agent."""
        query = select(EscrowContract).where(EscrowContract.job_id == job.id)
        res = await session.execute(query)
        contract = res.scalar_one_or_none()

        if not contract or contract.status != "HELD":
            return contract

        # 1. Fetch wallets
        funder_wallet = await session.get(AgentWallet, contract.funder_wallet_id)
        agent_wallet = await cls.get_or_create_wallet(session, "AGENT", winning_agent_id)

        # 2. Transfer escrow
        bounty = contract.amount
        if funder_wallet:
            funder_wallet.locked_escrow = max(0.0, funder_wallet.locked_escrow - bounty)

        agent_wallet.balance += bounty
        agent_wallet.total_earned += bounty

        # 3. Update contract state
        tx_id = f"tx-rel-{uuid.uuid4().hex[:8]}"
        contract.status = "RELEASED"
        contract.recipient_agent_id = winning_agent_id
        contract.release_tx_id = tx_id

        # 4. Record ledger transaction
        tx = EscrowTransaction(
            tx_id=tx_id,
            source_wallet_id=funder_wallet.id if funder_wallet else None,
            destination_wallet_id=agent_wallet.id,
            contract_id=contract.id,
            tx_type="ESCROW_RELEASE",
            amount=bounty,
            balance_after=agent_wallet.balance,
            details={"job_id": job.job_id, "bounty": bounty},
        )
        session.add(tx)
        await session.commit()
        await session.refresh(contract)

        await event_broadcaster.broadcast(
            "ESCROW_RELEASED",
            {
                "contract_id": contract.contract_id,
                "job_id": job.job_id,
                "bounty_payout": bounty,
                "winner_wallet_balance": agent_wallet.balance,
            },
            topic="global",
        )

        return contract

    @classmethod
    async def refund_bounty_escrow(
        cls,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> EscrowContract:
        """Refund held escrow credits back to the bounty creator if cancelled."""
        query = select(EscrowContract).where(EscrowContract.job_id == job_id)
        res = await session.execute(query)
        contract = res.scalar_one_or_none()

        if not contract or contract.status != "HELD":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No held escrow contract found for this job.")

        funder_wallet = await session.get(AgentWallet, contract.funder_wallet_id)
        bounty = contract.amount

        if funder_wallet:
            funder_wallet.locked_escrow = max(0.0, funder_wallet.locked_escrow - bounty)
            funder_wallet.balance += bounty
            funder_wallet.total_spent = max(0.0, funder_wallet.total_spent - bounty)

        tx_id = f"tx-ref-{uuid.uuid4().hex[:8]}"
        contract.status = "REFUNDED"
        contract.refund_tx_id = tx_id

        tx = EscrowTransaction(
            tx_id=tx_id,
            destination_wallet_id=funder_wallet.id if funder_wallet else None,
            contract_id=contract.id,
            tx_type="ESCROW_REFUND",
            amount=bounty,
            balance_after=funder_wallet.balance if funder_wallet else None,
            details={"contract_id": contract.contract_id},
        )
        session.add(tx)
        await session.commit()
        await session.refresh(contract)

        await event_broadcaster.broadcast(
            "ESCROW_REFUNDED",
            {"contract_id": contract.contract_id, "refund_amount": bounty},
            topic="global",
        )

        return contract

    @classmethod
    async def list_transactions(
        cls,
        session: AsyncSession,
        wallet_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[EscrowTransaction]]:
        """Query immutable escrow transactions ledger."""
        query = select(EscrowTransaction)
        count_query = select(func.count()).select_from(EscrowTransaction)

        if wallet_id:
            cond = or_(
                EscrowTransaction.source_wallet_id == wallet_id,
                EscrowTransaction.destination_wallet_id == wallet_id,
            )
            query = query.where(cond)
            count_query = count_query.where(cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(EscrowTransaction.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        txs = list(result.scalars().all())

        return total, txs

    @classmethod
    def to_wallet_response(cls, wallet: AgentWallet) -> WalletResponse:
        """Format AgentWallet to Pydantic schema."""
        a_id = str(wallet.agent_id) if wallet.agent_id else None
        a_name = wallet.agent.name if wallet.agent else None
        u_id = str(wallet.user_id) if wallet.user_id else None

        return WalletResponse(
            id=str(wallet.id),
            owner_type=wallet.owner_type,
            agent_id=a_id,
            agent_name=a_name,
            user_id=u_id,
            balance=round(wallet.balance, 2),
            locked_escrow=round(wallet.locked_escrow, 2),
            total_earned=round(wallet.total_earned, 2),
            total_spent=round(wallet.total_spent, 2),
            updated_at=wallet.updated_at,
        )

    @classmethod
    def to_contract_response(cls, contract: EscrowContract) -> EscrowContractResponse:
        """Format EscrowContract to Pydantic schema."""
        return EscrowContractResponse(
            id=str(contract.id),
            contract_id=contract.contract_id,
            job_id=contract.job.job_id if contract.job else str(contract.job_id),
            job_title=contract.job.title if contract.job else None,
            amount=round(contract.amount, 2),
            status=contract.status,
            funder_wallet_id=str(contract.funder_wallet_id),
            recipient_agent_id=contract.recipient_agent.public_id if contract.recipient_agent else (str(contract.recipient_agent_id) if contract.recipient_agent_id else None),
            recipient_agent_name=contract.recipient_agent.name if contract.recipient_agent else None,
            release_tx_id=contract.release_tx_id,
            refund_tx_id=contract.refund_tx_id,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
        )

    @classmethod
    def to_transaction_response(cls, tx: EscrowTransaction) -> TransactionResponse:
        """Format EscrowTransaction to Pydantic schema."""
        return TransactionResponse(
            id=str(tx.id),
            tx_id=tx.tx_id,
            tx_type=tx.tx_type,
            amount=round(tx.amount, 2),
            balance_after=round(tx.balance_after, 2) if tx.balance_after is not None else None,
            source_wallet_id=str(tx.source_wallet_id) if tx.source_wallet_id else None,
            destination_wallet_id=str(tx.destination_wallet_id) if tx.destination_wallet_id else None,
            contract_id=str(tx.contract_id) if tx.contract_id else None,
            details=tx.details or {},
            created_at=tx.created_at,
        )
