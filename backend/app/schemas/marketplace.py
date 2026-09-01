"""Pydantic schemas for Agent Marketplace, Task Bounties, and Job Bidding APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    """Payload for publishing a new job or task bounty."""

    title: str = Field(..., min_length=3, max_length=255, description="Job / task title")
    description: str = Field(..., min_length=10, description="Job scope, objectives, and deliverables")
    requirements: List[str] = Field(default_factory=list, description="Required capability prerequisites (e.g. ['python', 'linux'])")
    bounty_reward: float = Field(default=100.0, ge=1.0, description="Reward points / credits for completion")
    auto_invite_bids: bool = Field(default=True, description="Whether to automatically invite matching registered agents to bid")


class ProposalCreateRequest(BaseModel):
    """Payload for an agent submitting a manual proposal/bid."""

    agent_id: str = Field(..., description="Public handle or UUID of bidding agent")
    proposed_strategy: str = Field(..., min_length=10, description="Technical approach and execution plan")
    estimated_duration_seconds: int = Field(default=30, ge=5, le=3600, description="Estimated execution time in seconds")


class ProposalResponse(BaseModel):
    """Details of an agent proposal."""

    id: str
    proposal_id: str
    agent_id: str
    agent_name: str
    agent_reputation: float
    proposed_strategy: str
    estimated_duration_seconds: int
    bid_score: float
    status: str
    created_at: datetime


class JobResponse(BaseModel):
    """Comprehensive details of a job posting and its competing proposals."""

    id: str
    job_id: str
    title: str
    description: str
    requirements: List[str]
    bounty_reward: float
    status: str
    creator_id: str
    task_id: Optional[str] = None
    accepted_proposal_id: Optional[str] = None
    proposals_count: int
    proposals: List[ProposalResponse] = []
    created_at: datetime
    updated_at: datetime


class JobSummaryResponse(BaseModel):
    """Concise job metadata for marketplace browsing."""

    id: str
    job_id: str
    title: str
    requirements: List[str]
    bounty_reward: float
    status: str
    proposals_count: int
    created_at: datetime


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    total: int
    items: List[JobSummaryResponse]
