"""Pydantic schemas for Tasks, Multi-Agent Orchestration, and Hives."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestration.state_machine import TaskState


class TaskCreateRequest(BaseModel):
    """Payload for submitting a new Task."""

    title: str = Field(..., min_length=3, max_length=255, description="Task title")
    description: str = Field(..., min_length=10, description="Task objective and detailed instructions")
    requirements: List[str] = Field(default_factory=list, description="Required capability prerequisites (e.g. ['python', 'research'])")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Max execution steps")
    auto_orchestrate: bool = Field(default=True, description="Whether to automatically match agents, form Hive, and execute orchestration")


class TaskAssignmentResponse(BaseModel):
    """Details of an agent assigned to a task."""

    id: str
    agent_id: str
    agent_name: str
    role: str
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Comprehensive task details and execution state."""

    id: str
    task_id: str
    title: str
    description: str
    requirements: List[str]
    status: TaskState
    result: Optional[Dict[str, Any]] = None
    max_iterations: int
    hive_id: Optional[str] = None
    assigned_agents: List[TaskAssignmentResponse] = []
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskSummaryResponse(BaseModel):
    """Concise task metadata for list views."""

    id: str
    task_id: str
    title: str
    status: TaskState
    requirements: List[str]
    assigned_agent_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    total: int
    items: List[TaskSummaryResponse]


# Hive schemas
class HiveMemberResponse(BaseModel):
    """Details of an agent participating in a Hive."""

    agent_id: str
    agent_name: str
    role_in_hive: str
    joined_at: datetime


class HiveResponse(BaseModel):
    """Comprehensive Hive collaboration cluster details."""

    id: str
    public_id: str
    name: str
    description: Optional[str]
    lead_agent_id: Optional[str]
    lead_agent_name: Optional[str]
    task_id: Optional[str]
    status: str
    members: List[HiveMemberResponse]
    created_at: datetime


class HiveCreateRequest(BaseModel):
    """Payload for manually assembling a Hive."""

    name: str = Field(..., min_length=2, max_length=128, description="Hive cluster name")
    description: Optional[str] = Field(None, description="Collaboration charter")
    lead_agent_id: Optional[str] = Field(None, description="Designated lead agent identifier")
    member_agent_ids: List[str] = Field(default_factory=list, description="Roster of initial member agent identifiers")
    task_id: Optional[str] = Field(None, description="Optional associated task ID")


class HiveListResponse(BaseModel):
    """Paginated list of Hives."""

    total: int
    items: List[HiveResponse]
