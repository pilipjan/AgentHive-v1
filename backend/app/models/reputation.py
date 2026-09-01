"""ReputationEvent entity model for immutable reputation tracking."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID


class ReputationEvent(Base):
    """Immutable record of any event modifying an Agent's reputation score."""

    __tablename__ = "reputation_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event type: TASK_SUCCESS, TASK_FAILURE, VERIFICATION_VERIFIED, VERIFICATION_REFUTED, SECURITY_VIOLATION, PEER_REVIEW
    event_type = Column(String(64), nullable=False, index=True)
    score_delta = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    reference_id = Column(String(64), nullable=True)  # Task ID, Knowledge ID, or Evaluation ID
    details = Column(JSON, nullable=False, default=dict)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    agent = relationship("Agent", back_populates="reputation_events")
