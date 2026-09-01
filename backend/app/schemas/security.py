"""Pydantic schemas for Security & Audit APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.permissions.enums import PolicyVerdict, SensitivityTier, VisibilityScope


class SecurityInspectRequest(BaseModel):
    """Payload for dry-run Memory Firewall inspection."""

    content: str = Field(..., description="Raw text content to inspect")
    sender_id: str = Field(default="test-agent-01", description="Actor public identifier")
    permissions: List[str] = Field(
        default=["READ_PUBLIC_KNOWLEDGE", "MESSAGE_AGENTS", "WRITE_KNOWLEDGE"],
        description="Declared permissions",
    )
    target_scope: VisibilityScope = Field(
        default=VisibilityScope.HIVE,
        description="Target visibility boundary",
    )
    is_same_hive: bool = Field(default=True, description="Whether target is within the same Hive")


class SecurityInspectResponse(BaseModel):
    """Response returned from Memory Firewall inspection."""

    verdict: PolicyVerdict
    original_text_hash: str
    sanitized_text: str
    sensitivity: SensitivityTier
    detected_secrets: List[str]
    detected_pii: List[str]
    rejection_reason: Optional[str] = None


class AuditLogItem(BaseModel):
    """Sanitized audit log item."""

    id: str
    timestamp: datetime
    actor_type: str
    actor_id: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    status: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None


class AuditLogQueryResponse(BaseModel):
    """Paginated list of audit logs."""

    total: int
    items: List[AuditLogItem]
