"""Evaluation entity model for peer agent performance reviews."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID


class Evaluation(Base):
    """Peer agent evaluation submitted upon task or subtask completion."""

    __tablename__ = "evaluations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    target_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 5-dimensional evaluation scores (0.0 to 1.0)
    task_success_score = Column(Float, nullable=False, default=1.0)
    usefulness_score = Column(Float, nullable=False, default=1.0)
    accuracy_score = Column(Float, nullable=False, default=1.0)
    reliability_score = Column(Float, nullable=False, default=1.0)
    safety_score = Column(Float, nullable=False, default=1.0)
    
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    task = relationship("Task", back_populates="evaluations")
    reviewer_agent = relationship("Agent", foreign_keys=[reviewer_agent_id], back_populates="evaluations_given")
    target_agent = relationship("Agent", foreign_keys=[target_agent_id], back_populates="evaluations_received")
