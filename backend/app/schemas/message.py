"""Pydantic schemas for Controlled Agent Messaging APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.permissions.enums import PolicyVerdict, SensitivityTier


class MessageSendRequest(BaseModel):
    """Payload for submitting a message through the controlled messaging hub."""

    sender_agent_id: str = Field(..., description="Public ID or UUID of sender agent")
    recipient_agent_id: Optional[str] = Field(None, description="Public ID or UUID of recipient agent (null for broadcast)")
    task_id: Optional[str] = Field(None, description="Associated Task ID (optional scoping)")
    hive_id: Optional[str] = Field(None, description="Associated Hive ID (optional scoping)")
    message_type: str = Field(default="DIRECT", description="Message type (DIRECT, BROADCAST, SYSTEM, REVIEW)")
    content: str = Field(..., min_length=1, description="Message text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata headers")


class MessageResponse(BaseModel):
    """Controlled message response model."""

    id: str
    message_id: str
    sender_agent_id: str
    sender_agent_name: str
    recipient_agent_id: Optional[str]
    recipient_agent_name: Optional[str]
    task_id: Optional[str]
    hive_id: Optional[str]
    message_type: str
    content: str
    sensitivity: SensitivityTier
    authorization_result: PolicyVerdict
    metadata: Dict[str, Any]
    created_at: datetime


class MessageListResponse(BaseModel):
    """Paginated list of messages."""

    total: int
    items: List[MessageResponse]
