"""User entity model."""

import uuid
from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class User(Base, TimestampMixin):
    """User account entity for platform operators and creators."""

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="OPERATOR")
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="creator", cascade="all, delete-orphan")
