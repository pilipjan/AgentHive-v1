"""SQLAlchemy Models for Token Escrow Economics, Agent Wallets, and Transaction Ledgers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class AgentWallet(Base):
    """Token/Credit balance wallet for an Agent or Operator User."""

    __tablename__ = "agent_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type = Column(String(20), nullable=False, default="AGENT")  # 'AGENT' or 'USER'
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    
    balance = Column(Float, nullable=False, default=1000.0)  # Available spendable credits
    locked_escrow = Column(Float, nullable=False, default=0.0)  # Credits currently locked in active bounties
    total_earned = Column(Float, nullable=False, default=0.0)  # Cumulative lifetime earnings from bounties
    total_spent = Column(Float, nullable=False, default=0.0)  # Cumulative lifetime spent on posted bounties

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    agent = relationship("Agent", backref="wallet", lazy="joined")
    user = relationship("User", backref="wallet", lazy="joined")

    __table_args__ = (
        Index("idx_agent_wallets_agent_id", "agent_id"),
        Index("idx_agent_wallets_user_id", "user_id"),
    )


class EscrowContract(Base):
    """Escrow locking contract for a marketplace job bounty or task contract."""

    __tablename__ = "escrow_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(String(64), unique=True, nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    funder_wallet_id = Column(UUID(as_uuid=True), ForeignKey("agent_wallets.id", ondelete="CASCADE"), nullable=False)
    recipient_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    amount = Column(Float, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="HELD",  # HELD, RELEASED, REFUNDED, DISPUTED
    )
    
    release_tx_id = Column(String(64), nullable=True)
    refund_tx_id = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job = relationship("JobPosting", backref="escrow_contract", lazy="joined")
    funder_wallet = relationship("AgentWallet", foreign_keys=[funder_wallet_id], lazy="joined")
    recipient_agent = relationship("Agent", foreign_keys=[recipient_agent_id], lazy="joined")

    __table_args__ = (
        Index("idx_escrow_contracts_job_id", "job_id"),
        Index("idx_escrow_contracts_status", "status"),
    )


class EscrowTransaction(Base):
    """Immutable audit ledger of token balance movements."""

    __tablename__ = "escrow_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_id = Column(String(64), unique=True, nullable=False, index=True)
    
    source_wallet_id = Column(UUID(as_uuid=True), ForeignKey("agent_wallets.id", ondelete="SET NULL"), nullable=True)
    destination_wallet_id = Column(UUID(as_uuid=True), ForeignKey("agent_wallets.id", ondelete="SET NULL"), nullable=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("escrow_contracts.id", ondelete="SET NULL"), nullable=True)

    tx_type = Column(
        String(30),
        nullable=False,
    )  # 'INITIAL_GRANT', 'DEPOSIT', 'ESCROW_LOCK', 'ESCROW_RELEASE', 'ESCROW_REFUND'
    
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=True)
    details = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    source_wallet = relationship("AgentWallet", foreign_keys=[source_wallet_id], lazy="selectin")
    destination_wallet = relationship("AgentWallet", foreign_keys=[destination_wallet_id], lazy="selectin")
    contract = relationship("EscrowContract", foreign_keys=[contract_id], lazy="selectin")

    __table_args__ = (
        Index("idx_escrow_tx_type", "tx_type"),
        Index("idx_escrow_tx_created_at", "created_at"),
    )
