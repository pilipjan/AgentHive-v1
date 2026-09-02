"""Pydantic schemas for HiveStore Uptime Heartbeats and Community Reviews."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class HeartbeatPingRequest(BaseModel):
    """Heartbeat telemetry ping sent by a running agent clone."""
    blueprint_slug: str = Field(..., description="Blueprint slug this instance belongs to")
    instance_id: str = Field(..., description="Unique ID for this running instance")
    status: str = Field("ONLINE", description="'ONLINE', 'DEGRADED', or 'OFFLINE'")
    uptime_seconds: int = Field(0, ge=0, description="Total running seconds")
    response_time_ms: float = Field(0.0, ge=0, description="Inference / task response latency")
    version: Optional[str] = Field("1.0.0", description="Agent version string")
    host_info: Optional[str] = Field(None, description="Host environment e.g. Oracle-ARM64")


class HeartbeatResponse(BaseModel):
    """Heartbeat acknowledgement."""
    instance_id: str
    blueprint_slug: str
    status: str
    uptime_human: str
    recorded_at: datetime


class UptimeStatsResponse(BaseModel):
    """Aggregated uptime and health metrics for an agent blueprint."""
    blueprint_slug: str
    blueprint_name: str
    status: str  # ONLINE, DEGRADED, OFFLINE
    active_instances: int
    total_heartbeats: int
    max_uptime_seconds: int
    max_uptime_human: str
    avg_response_time_ms: float
    last_heartbeat_at: Optional[datetime] = None
    uptime_percentage_30d: float


class ReviewCreateRequest(BaseModel):
    """User review and star rating submission."""
    reviewer_name: str = Field(..., min_length=2, max_length=100, description="Reviewer display name")
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    title: Optional[str] = Field(None, max_length=150, description="Short review headline")
    review_text: str = Field(..., min_length=5, description="Detailed review feedback")
    verified_clone: bool = Field(False, description="Did the reviewer clone and run this agent?")
    uptime_experienced: Optional[str] = Field(None, description="e.g. 'Running for 2 months'")


class ReviewResponse(BaseModel):
    """Public review item."""
    id: str
    review_id: str
    blueprint_id: str
    reviewer_name: str
    rating: int
    title: Optional[str] = None
    review_text: str
    verified_clone: bool
    uptime_experienced: Optional[str] = None
    created_at: datetime


class ReviewListResponse(BaseModel):
    """Paginated reviews list."""
    total: int
    avg_rating: float
    verified_clone_count: int
    items: List[ReviewResponse]
