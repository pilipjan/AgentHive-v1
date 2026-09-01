"""Message entity model for controlled agent-to-agent communication."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID


class Message(Base):
    """Controlled message entity passing through the Memory Firewall."""

    __tablename__ = "messages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    message_id = Column(String(64), unique=True, nullable=False, index=True)
    sender_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_agent_id = Column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    hive_id = Column(GUID, ForeignKey("hives.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Classification & Content
    message_type = Column(String(32), nullable=False, default="DIRECT")  # DIRECT, BROADCAST, SYSTEM, REVIEW
    content = Column(Text, nullable=False)
    raw_content_hash = Column(String(64), nullable=False)
    sensitivity = Column(String(32), nullable=False, default="INTERNAL")  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    authorization_result = Column(String(32), nullable=False, default="ALLOWED")  # ALLOWED, REDACTED, BLOCKED
    extra_metadata = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    sender_agent = relationship("Agent", foreign_keys=[sender_agent_id], back_populates="sent_messages")
    recipient_agent = relationship("Agent", foreign_keys=[recipient_agent_id], back_populates="received_messages")
    task = relationship("Task", back_populates="messages")
    hive = relationship("Hive", back_populates="messages")
