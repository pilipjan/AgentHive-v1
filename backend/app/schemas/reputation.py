"""Pydantic schemas for Evaluations and Multi-Factor Reputation APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationCreateRequest(BaseModel):
    """Payload for submitting a peer review evaluation."""

    task_id: str = Field(..., description="Scoped Task identifier")
    reviewer_agent_id: str = Field(..., description="Reviewer Agent identifier")
    target_agent_id: str = Field(..., description="Target Agent identifier being reviewed")
    task_success_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Task completion score")
    usefulness_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Collaboration usefulness score")
    accuracy_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Rigor and accuracy score")
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Consistency score")
    safety_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Policy and security compliance score")
    comments: Optional[str] = Field(None, description="Qualitative performance feedback")


class EvaluationResponse(BaseModel):
    """Evaluation record details."""

    id: str
    task_id: str
    reviewer_agent_id: str
    reviewer_agent_name: str
    target_agent_id: str
    target_agent_name: str
    task_success_score: float
    usefulness_score: float
    accuracy_score: float
    reliability_score: float
    safety_score: float
    comments: Optional[str]
    created_at: datetime


class ReputationMetricsResponse(BaseModel):
    """Underlying multi-dimensional telemetry metrics."""

    task_success_rate: float
    reviewer_usefulness_score: float
    verification_accuracy: float
    reliability_score: float
    safety_compliance_rate: float
    security_violations: int
    evaluations_count: int


class ReputationDetailResponse(BaseModel):
    """Comprehensive multi-factor reputation profile."""

    agent_id: str
    agent_name: str
    composite_score: float
    star_rating: float
    total_tasks_completed: int
    successful_tasks: int
    metrics: ReputationMetricsResponse
    weight_formula: Dict[str, float]
    verification_eligible: bool


class ReputationEventItem(BaseModel):
    """Immutable reputation adjustment ledger entry."""

    id: str
    event_type: str
    score_delta: float
    new_score: float
    reference_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime


class ReputationHistoryResponse(BaseModel):
    """Audit ledger of all reputation score adjustments."""

    agent_id: str
    total_events: int
    events: List[ReputationEventItem]
