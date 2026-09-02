"""SQLAlchemy Models for HiveStore Agent Blueprints and Clone Tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class AgentBlueprint(Base):
    """A publishable, cloneable agent template that creators share on HiveStore."""

    __tablename__ = "agent_blueprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False, index=True)  # e.g. "stream-ai-dj"
    
    name = Column(String(120), nullable=False)
    tagline = Column(String(200), nullable=True)  # Short one-liner description
    description = Column(Text, nullable=False)  # Full markdown description
    category = Column(String(40), nullable=False, default="general")  # DJ, Scraper, Research, Coding, etc.
    tags = Column(ARRAY(String), nullable=False, default=list)

    # Creator
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    creator_name = Column(String(100), nullable=True)

    # Source & Setup
    repo_url = Column(String(255), nullable=True)  # GitHub / GitLab repo link
    setup_instructions = Column(Text, nullable=True)  # Markdown setup guide
    docker_compose_snippet = Column(Text, nullable=True)  # Docker compose YAML
    env_vars_template = Column(Text, nullable=True)  # .env.example content
    required_models = Column(ARRAY(String), nullable=False, default=list)  # e.g. ["gemma2:2b", "gpt-4o"]
    required_tools = Column(ARRAY(String), nullable=False, default=list)  # e.g. ["ollama", "ffmpeg", "yt-dlp"]

    # Linked live agent (optional — if the creator has a running instance)
    linked_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Stats (denormalized for fast reads)
    clone_count = Column(Integer, nullable=False, default=0)
    review_count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=False, default=0.0)
    active_instances = Column(Integer, nullable=False, default=0)  # How many clones are currently running

    # Status
    status = Column(String(20), nullable=False, default="PUBLISHED")  # DRAFT, PUBLISHED, ARCHIVED
    featured = Column(String(10), nullable=False, default="NO")  # YES / NO

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", backref="blueprints", lazy="joined")
    linked_agent = relationship("Agent", backref="blueprint", lazy="joined")

    __table_args__ = (
        Index("idx_blueprint_category", "category"),
        Index("idx_blueprint_status", "status"),
        Index("idx_blueprint_clone_count", "clone_count"),
        Index("idx_blueprint_avg_rating", "avg_rating"),
        Index("idx_blueprint_creator_id", "creator_id"),
    )


class BlueprintClone(Base):
    """Record of a user cloning (forking) an agent blueprint."""

    __tablename__ = "blueprint_clones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clone_id = Column(String(64), unique=True, nullable=False, index=True)
    
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False)
    cloner_name = Column(String(100), nullable=True)
    cloner_note = Column(Text, nullable=True)  # Optional note like "Running on my Raspberry Pi"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    blueprint = relationship("AgentBlueprint", backref="clones", lazy="joined")

    __table_args__ = (
        Index("idx_clone_blueprint_id", "blueprint_id"),
    )
