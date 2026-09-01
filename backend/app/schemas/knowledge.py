"""Pydantic schemas for Shared Knowledge & Verification APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.permissions.enums import SensitivityTier, VisibilityScope


class KnowledgeCreateRequest(BaseModel):
    """Payload for submitting a new knowledge entry."""

    summary: str = Field(..., min_length=3, max_length=512, description="Concise summary of the knowledge claim")
    content: str = Field(..., min_length=5, description="Full technical description / finding")
    source_agent_id: str = Field(..., description="Public ID or UUID of publishing agent")
    task_id: Optional[str] = Field(None, description="Source task identifier")
    visibility: VisibilityScope = Field(default=VisibilityScope.HIVE, description="Target visibility tier")
    tags: List[str] = Field(default_factory=list, description="Topic / domain tags")


class KnowledgeVerificationRequest(BaseModel):
    """Payload for submitting a peer verification verdict."""

    verifying_agent_id: str = Field(..., description="Public ID or UUID of verifying agent")
    verdict: str = Field(..., description="Verdict: VERIFIED, REFUTED, or INCONCLUSIVE")
    evidence: Optional[str] = Field(None, description="Corroborating or counter-evidence")


class VerificationRecordResponse(BaseModel):
    """Verification record details."""

    id: str
    verifying_agent_id: str
    verifying_agent_name: str
    verdict: str
    evidence: Optional[str]
    timestamp: datetime


class KnowledgeResponse(BaseModel):
    """Detailed knowledge record with verification summary."""

    id: str
    summary: str
    content: str
    source_agent_id: str
    source_agent_name: str
    task_id: Optional[str]
    confidence: float
    verification_count: int
    success_count: int
    failure_count: int
    visibility: VisibilityScope
    sensitivity: SensitivityTier
    tags: List[str]
    verdict_distribution: Dict[str, int]
    verifications: List[VerificationRecordResponse]
    created_at: datetime
    last_verified_at: Optional[datetime] = None


class KnowledgeSummaryResponse(BaseModel):
    """Concise knowledge summary for search listings."""

    id: str
    summary: str
    source_agent_id: str
    source_agent_name: str
    confidence: float
    verification_count: int
    visibility: VisibilityScope
    sensitivity: SensitivityTier
    tags: List[str]
    created_at: datetime


class KnowledgeListResponse(BaseModel):
    """Paginated list of knowledge records."""

    total: int
    items: List[KnowledgeSummaryResponse]
