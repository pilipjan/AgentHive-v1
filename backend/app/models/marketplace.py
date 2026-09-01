"""SQLAlchemy 2.0 Models for Agent Marketplace, Task Bounties, and Job Proposals."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class JobPosting(Base, TimestampMixin):
    """A task or bounty posted to the Agent Marketplace for agent bidding."""

    __tablename__ = "job_postings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    creator_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=list, nullable=False)  # List of required capability tags
    bounty_reward = Column(Float, default=100.0, nullable=False)  # Reward points/credits
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, MATCHING, AWARDED, COMPLETED, CANCELLED
    accepted_proposal_id = Column(GUID, nullable=True)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], lazy="selectin")
    proposals = relationship("AgentProposal", back_populates="job", cascade="all, delete-orphan", lazy="selectin")
    task = relationship("Task", foreign_keys=[task_id], lazy="selectin")


class AgentProposal(Base, TimestampMixin):
    """A proposal/bid submitted by an AI agent to compete for an open job."""

    __tablename__ = "agent_proposals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_id = Column(String(64), unique=True, nullable=False, index=True)
    job_id = Column(GUID, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    proposed_strategy = Column(Text, nullable=False)
    estimated_duration_seconds = Column(Integer, default=30, nullable=False)
    bid_score = Column(Float, default=0.0, nullable=False)  # Multi-factor ranking score
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, ACCEPTED, REJECTED, WITHDRAWN

    # Relationships
    job = relationship("JobPosting", back_populates="proposals")
    agent = relationship("Agent", foreign_keys=[agent_id], lazy="selectin")
