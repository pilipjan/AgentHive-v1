"""Agent and AgentPermission entity models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class Agent(Base, TimestampMixin):
    """Core Agent entity within the AgentHive platform."""

    __tablename__ = "agents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    public_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Model configuration
    model_provider = Column(String(32), nullable=False, default="OPENAI")
    model_name = Column(String(64), nullable=False, default="gpt-4o-mini")
    
    # Structured capabilities (declared metadata)
    capabilities = Column(JSON, nullable=False, default=list)
    
    # Lifecycle & Reputation
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)  # ACTIVE, BUSY, DISABLED, QUARANTINED
    reputation_score = Column(Float, nullable=False, default=3.00)
    tasks_completed = Column(Integer, nullable=False, default=0)
    successful_tasks = Column(Integer, nullable=False, default=0)
    
    # Cryptographic identity placeholder
    public_key = Column(Text, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="agents")
    permissions = relationship("AgentPermission", back_populates="agent", cascade="all, delete-orphan")
    task_assignments = relationship("TaskAssignment", back_populates="agent", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_agent_id", back_populates="sender_agent")
    received_messages = relationship("Message", foreign_keys="Message.recipient_agent_id", back_populates="recipient_agent")
    published_knowledge = relationship("Knowledge", back_populates="source_agent")
    verifications = relationship("KnowledgeVerification", back_populates="verifying_agent")
    evaluations_received = relationship("Evaluation", foreign_keys="Evaluation.target_agent_id", back_populates="target_agent")
    evaluations_given = relationship("Evaluation", foreign_keys="Evaluation.reviewer_agent_id", back_populates="reviewer_agent")
    reputation_events = relationship("ReputationEvent", back_populates="agent", cascade="all, delete-orphan")
    hive_memberships = relationship("HiveMember", back_populates="agent", cascade="all, delete-orphan")


class AgentPermission(Base):
    """Explicitly granted atomic permission for an agent."""

    __tablename__ = "agent_permissions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_name = Column(String(64), nullable=False, index=True)
    granted_by = Column(String(64), nullable=False, default="SYSTEM")
    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="permissions")
