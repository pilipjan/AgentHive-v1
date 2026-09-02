"""Semantic Search API Endpoints — pgvector-powered ANN search across knowledge and agents."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.search import (
    AgentSearchResponse,
    AgentSearchResult,
    BackfillResponse,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    SemanticSearchRequest,
)
from backend.app.services.semantic_search_service import SemanticSearchService

router = APIRouter()


@router.post(
    "/knowledge",
    response_model=KnowledgeSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Knowledge Search",
    description="Find knowledge entries by meaning using natural language. Uses pgvector HNSW cosine similarity.",
)
async def search_knowledge(
    payload: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSearchResponse:
    """Search knowledge base using semantic similarity."""
    results = await SemanticSearchService.search_knowledge(
        session=db,
        query=payload.query,
        limit=payload.limit,
        similarity_threshold=payload.similarity_threshold,
        tag_filter=payload.tag_filter,
    )
    return KnowledgeSearchResponse(
        query=payload.query,
        total=len(results),
        results=[KnowledgeSearchResult(**r) for r in results],
    )


@router.post(
    "/agents",
    response_model=AgentSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Agent Discovery",
    description="Find agents whose capabilities semantically match a natural language query.",
)
async def search_agents(
    payload: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentSearchResponse:
    """Search agents using semantic capability matching."""
    results = await SemanticSearchService.search_agents(
        session=db,
        query=payload.query,
        limit=payload.limit,
        similarity_threshold=payload.similarity_threshold or 0.20,
        status_filter=payload.status_filter or "ACTIVE",
    )
    return AgentSearchResponse(
        query=payload.query,
        total=len(results),
        results=[AgentSearchResult(**r) for r in results],
    )


@router.post(
    "/backfill",
    response_model=BackfillResponse,
    status_code=status.HTTP_200_OK,
    summary="Backfill Embeddings",
    description="Generate embeddings for all knowledge entries and agents that are missing them.",
)
async def backfill_embeddings(
    db: AsyncSession = Depends(get_db),
) -> BackfillResponse:
    """Trigger embedding backfill for records missing vectors."""
    k_count = await SemanticSearchService.backfill_knowledge_embeddings(db)
    a_count = await SemanticSearchService.backfill_agent_embeddings(db)
    return BackfillResponse(
        knowledge_embedded=k_count,
        agents_embedded=a_count,
        message=f"Backfill complete. Embedded {k_count} knowledge entries and {a_count} agents.",
    )
