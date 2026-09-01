"""Task and TaskAssignment entity models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class Task(Base, TimestampMixin):
    """Task entity representing discrete user requests or subtasks."""

    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    creator_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False, default=list)
    
    # State: CREATED, DISCOVERY, ASSIGNED, RUNNING, REVIEW, COMPLETED, FAILED, CANCELLED
    status = Column(String(32), nullable=False, default="CREATED", index=True)
    result = Column(JSON, nullable=True)
    max_iterations = Column(Integer, nullable=False, default=5)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="tasks")
    hive = relationship("Hive", foreign_keys="Hive.task_id", back_populates="task", uselist=False)
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="task", cascade="all, delete-orphan")
    knowledge_entries = relationship("Knowledge", back_populates="task")
    evaluations = relationship("Evaluation", back_populates="task", cascade="all, delete-orphan")


class TaskAssignment(Base):
    """Binding an Agent to a Task with a designated role."""

    __tablename__ = "task_assignments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(64), nullable=False, default="WORKER")  # LEAD, WORKER, REVIEWER, VERIFIER
    status = Column(String(32), nullable=False, default="ASSIGNED")  # ASSIGNED, RUNNING, COMPLETED, FAILED
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="assignments")
    agent = relationship("Agent", back_populates="task_assignments")
