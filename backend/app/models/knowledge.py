"""Knowledge and KnowledgeVerification entity models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID


class Knowledge(Base):
    """Shared knowledge entity with visibility tiers and Bayesian verification scoring."""

    __tablename__ = "knowledge"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    summary = Column(String(512), nullable=False, index=True)
    source_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Confidence and metrics
    confidence = Column(Float, nullable=False, default=0.50)
    verification_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    
    # Scoping & Security
    visibility = Column(String(32), nullable=False, default="HIVE", index=True)  # PRIVATE, HIVE, PROJECT, PUBLIC
    sensitivity = Column(String(32), nullable=False, default="INTERNAL")  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    tags = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    source_agent = relationship("Agent", back_populates="published_knowledge")
    task = relationship("Task", back_populates="knowledge_entries")
    verifications = relationship("KnowledgeVerification", back_populates="knowledge", cascade="all, delete-orphan")


class KnowledgeVerification(Base):
    """Individual peer agent verification verdict on a Knowledge record."""

    __tablename__ = "knowledge_verifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    knowledge_id = Column(GUID, ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False, index=True)
    verifying_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    verdict = Column(String(32), nullable=False)  # VERIFIED, REFUTED, INCONCLUSIVE
    evidence = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    knowledge = relationship("Knowledge", back_populates="verifications")
    verifying_agent = relationship("Agent", back_populates="verifications")
