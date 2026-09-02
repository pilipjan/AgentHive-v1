"""Pydantic schemas for semantic search requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Semantic search query payload."""
    query: str = Field(..., min_length=2, max_length=1000, description="Natural language search query")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")
    similarity_threshold: float = Field(0.25, ge=0.0, le=1.0, description="Minimum cosine similarity score")
    tag_filter: Optional[str] = Field(None, description="Filter knowledge by tag")
    status_filter: Optional[str] = Field(None, description="Filter agents by status (ACTIVE, DISABLED)")


class KnowledgeSearchResult(BaseModel):
    """A single knowledge entry result with similarity score."""
    id: str
    summary: str
    content: str
    tags: List[str]
    source_agent_id: Optional[str] = None
    similarity: float
    created_at: Optional[str] = None


class AgentSearchResult(BaseModel):
    """A single agent result with similarity score."""
    id: str
    public_id: str
    name: str
    capabilities: List[str]
    reputation_score: float
    status: str
    similarity: float


class KnowledgeSearchResponse(BaseModel):
    """Response for semantic knowledge search."""
    query: str
    total: int
    results: List[KnowledgeSearchResult]


class AgentSearchResponse(BaseModel):
    """Response for semantic agent search."""
    query: str
    total: int
    results: List[AgentSearchResult]


class BackfillResponse(BaseModel):
    """Response for embedding backfill operations."""
    knowledge_embedded: int
    agents_embedded: int
    message: str
