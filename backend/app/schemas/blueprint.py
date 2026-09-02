"""Pydantic schemas for HiveStore Agent Blueprints and Clone operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BlueprintPublishRequest(BaseModel):
    """Request to publish a new agent blueprint to HiveStore."""
    slug: str = Field(..., min_length=3, max_length=64, description="Unique URL-friendly identifier")
    name: str = Field(..., min_length=2, max_length=120, description="Agent blueprint display name")
    tagline: Optional[str] = Field(None, max_length=200, description="Short one-liner description")
    description: str = Field(..., min_length=10, description="Full markdown description of the agent")
    category: str = Field("general", description="Category: dj, scraper, research, coding, trading, support, content, automation, general")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    creator_name: Optional[str] = Field(None, description="Display name of the creator")
    repo_url: Optional[str] = Field(None, description="GitHub / GitLab repository URL")
    setup_instructions: Optional[str] = Field(None, description="Markdown setup guide")
    docker_compose_snippet: Optional[str] = Field(None, description="Docker Compose YAML snippet")
    env_vars_template: Optional[str] = Field(None, description=".env.example template content")
    required_models: List[str] = Field(default_factory=list, description="Required LLM models e.g. ['gemma2:2b']")
    required_tools: List[str] = Field(default_factory=list, description="Required system tools e.g. ['ollama', 'ffmpeg']")
    linked_agent_id: Optional[str] = Field(None, description="Link to a running agent in the registry")


class BlueprintResponse(BaseModel):
    """Public blueprint detail."""
    id: str
    slug: str
    name: str
    tagline: Optional[str] = None
    description: str
    category: str
    tags: List[str]
    creator_name: Optional[str] = None
    repo_url: Optional[str] = None
    setup_instructions: Optional[str] = None
    docker_compose_snippet: Optional[str] = None
    env_vars_template: Optional[str] = None
    required_models: List[str]
    required_tools: List[str]
    linked_agent_id: Optional[str] = None
    clone_count: int
    review_count: int
    avg_rating: float
    active_instances: int
    status: str
    featured: str
    created_at: datetime
    updated_at: datetime


class BlueprintListResponse(BaseModel):
    """Paginated list of blueprints."""
    total: int
    items: List[BlueprintResponse]


class CloneRequest(BaseModel):
    """Request to clone an agent blueprint."""
    cloner_name: Optional[str] = Field(None, description="Name of the person cloning")
    cloner_note: Optional[str] = Field(None, description="Optional note about the clone deployment")


class CloneResponse(BaseModel):
    """Response after cloning a blueprint — includes the full setup package."""
    clone_id: str
    blueprint_slug: str
    blueprint_name: str
    repo_url: Optional[str] = None
    setup_instructions: Optional[str] = None
    docker_compose_snippet: Optional[str] = None
    env_vars_template: Optional[str] = None
    required_models: List[str]
    required_tools: List[str]
    total_clones: int
    message: str
