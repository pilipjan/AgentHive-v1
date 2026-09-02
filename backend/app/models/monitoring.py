"""SQLAlchemy Models for HiveStore Live Uptime, Heartbeats, and Reviews."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class AgentHeartbeat(Base):
    """Heartbeat telemetry ping from a running agent instance."""

    __tablename__ = "agent_heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(String(64), nullable=False, index=True)  # Unique ID of the running clone/instance
    
    status = Column(String(20), nullable=False, default="ONLINE")  # ONLINE, DEGRADED, OFFLINE
    uptime_seconds = Column(Integer, nullable=False, default=0)
    response_time_ms = Column(Float, nullable=False, default=0.0)
    version = Column(String(30), nullable=True, default="1.0.0")
    host_info = Column(String(100), nullable=True)  # e.g. "Oracle-ARM64", "Docker-Local"

    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    blueprint = relationship("AgentBlueprint", backref="heartbeats", lazy="joined")

    __table_args__ = (
        Index("idx_heartbeat_blueprint_id", "blueprint_id"),
        Index("idx_heartbeat_recorded_at", "recorded_at"),
    )


class AgentReview(Base):
    """Community star rating and review for an agent blueprint."""

    __tablename__ = "agent_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(64), unique=True, nullable=False, index=True)
    
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5 stars
    title = Column(String(150), nullable=True)
    review_text = Column(Text, nullable=False)
    
    verified_clone = Column(Boolean, nullable=False, default=False)  # True if reviewer cloned this blueprint
    uptime_experienced = Column(String(50), nullable=True)  # e.g. "Running for 3 weeks"
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    blueprint = relationship("AgentBlueprint", backref="reviews", lazy="joined")

    __table_args__ = (
        Index("idx_review_blueprint_id", "blueprint_id"),
        Index("idx_review_rating", "rating"),
    )
