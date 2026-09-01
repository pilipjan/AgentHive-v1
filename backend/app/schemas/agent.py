"""Pydantic schemas for Agent Registry & Identity APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.permissions.enums import AgentPermissionEnum


class AgentCreateRequest(BaseModel):
    """Payload for registering a new agent."""

    name: str = Field(..., min_length=2, max_length=128, description="Display name of the agent")
    public_id: Optional[str] = Field(None, max_length=64, description="Custom unique handle/slug")
    description: Optional[str] = Field(None, description="Detailed agent specialization description")
    model_provider: str = Field(default="OPENAI", description="Provider (OPENAI, ANTHROPIC, GEMINI, OLLAMA, MOCK)")
    model_name: str = Field(default="gpt-4o-mini", description="Model identifier tag")
    capabilities: List[str] = Field(default_factory=list, description="Declared capability tags")
    public_key: Optional[str] = Field(None, description="Optional public key for future cryptographic identity")


class AgentUpdateRequest(BaseModel):
    """Payload for updating an existing agent."""

    name: Optional[str] = Field(None, min_length=2, max_length=128)
    description: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    capabilities: Optional[List[str]] = None
    public_key: Optional[str] = None


class AgentPermissionGrantRequest(BaseModel):
    """Payload for granting an atomic permission to an agent."""

    permission_name: AgentPermissionEnum = Field(..., description="Atomic permission to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration timestamp")


class AgentPermissionResponse(BaseModel):
    """Permission detail response."""

    id: str
    permission_name: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None


class AgentSummaryResponse(BaseModel):
    """Concise agent metadata for directory listings."""

    id: str
    public_id: str
    name: str
    description: Optional[str]
    model_provider: str
    model_name: str
    capabilities: List[str]
    status: str
    reputation_score: float
    star_rating: float
    tasks_completed: int
    successful_tasks: int
    success_rate: float
    created_at: datetime


class AgentProfileResponse(BaseModel):
    """Full comprehensive agent profile with trust metrics and permissions."""

    id: str
    public_id: str
    name: str
    description: Optional[str]
    owner_id: str
    model_provider: str
    model_name: str
    capabilities: List[str]
    status: str
    reputation_score: float
    star_rating: float
    tasks_completed: int
    successful_tasks: int
    success_rate: float
    permissions: List[str]
    trust_indicators: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    """Paginated list of agents."""

    total: int
    items: List[AgentSummaryResponse]
