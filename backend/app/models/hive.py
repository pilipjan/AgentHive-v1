"""Hive and HiveMember entity models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class Hive(Base, TimestampMixin):
    """A collaboration cluster / team of agents working together."""

    __tablename__ = "hives"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    public_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    lead_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default="FORMING")  # FORMING, ACTIVE, DISBANDED, ARCHIVED

    # Relationships
    lead_agent = relationship("Agent", foreign_keys=[lead_agent_id])
    task = relationship("Task", foreign_keys=[task_id], back_populates="hive")
    members = relationship("HiveMember", back_populates="hive", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="hive", cascade="all, delete-orphan")


class HiveMember(Base):
    """Membership mapping of agents within a Hive."""

    __tablename__ = "hive_members"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    hive_id = Column(GUID, ForeignKey("hives.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_hive = Column(String(64), nullable=False, default="MEMBER")  # LEAD, WORKER, REVIEWER, VERIFIER
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("hive_id", "agent_id", name="uq_hive_agent"),
    )

    # Relationships
    hive = relationship("Hive", back_populates="members")
    agent = relationship("Agent", back_populates="hive_memberships")
