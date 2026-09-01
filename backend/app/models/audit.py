"""AuditLog entity model for platform-wide security auditing."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, JSON, String
from backend.app.core.database import Base
from backend.app.models.base import GUID


class AuditLog(Base):
    """Append-only audit log capturing security, administrative, and runtime actions."""

    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    actor_type = Column(String(32), nullable=False, index=True)  # USER, AGENT, SYSTEM
    actor_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # e.g., AGENT_CREATED, SECRET_BLOCKED, PERMISSION_DENIED
    
    target_type = Column(String(32), nullable=True, index=True)  # AGENT, TASK, MESSAGE, KNOWLEDGE, HIVE
    target_id = Column(String(64), nullable=True, index=True)
    
    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, DENIED, REDACTED, BLOCKED, ERROR
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)
