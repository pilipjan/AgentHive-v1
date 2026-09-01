"""Shared Knowledge & Verification API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeListResponse,
    KnowledgeResponse,
    KnowledgeVerificationRequest,
)
from backend.app.services.knowledge_service import KnowledgeService
from security.permissions.enums import VisibilityScope

router = APIRouter()


@router.post(
    "",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish Knowledge Entry",
    description="Publishes a technical finding or claim into shared memory, passing through the Memory Firewall.",
)
async def publish_knowledge(
    payload: KnowledgeCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeResponse:
    """Submit new knowledge record."""
    knowledge = await KnowledgeService.publish_knowledge(session=db, request=payload)
    loaded = await KnowledgeService.get_knowledge(session=db, knowledge_id=str(knowledge.id))
    return KnowledgeService.to_knowledge_response(loaded or knowledge)


@router.get(
    "",
    response_model=KnowledgeListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search & List Knowledge",
    description="Search shared knowledge base by query, tag, visibility, or confidence threshold.",
)
async def list_knowledge(
    query: Optional[str] = Query(None, description="Search term for summary or content"),
    tag: Optional[str] = Query(None, description="Filter by topic tag"),
    visibility: Optional[VisibilityScope] = Query(None, description="Filter by visibility tier"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeListResponse:
    """Query knowledge entries."""
    total, entries = await KnowledgeService.list_knowledge(
        session=db,
        query=query,
        tag=tag,
        visibility=visibility,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset,
    )
    items = [KnowledgeService.to_summary_response(e) for e in entries]
    return KnowledgeListResponse(total=total, items=items)


@router.get(
    "/{id}",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Knowledge Record & Verifications",
    description="Retrieve full knowledge claim, confidence score, and peer verification history.",
)
async def get_knowledge(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeResponse:
    """Fetch knowledge record by ID."""
    knowledge = await KnowledgeService.get_knowledge(session=db, knowledge_id=id)
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge record '{id}' not found.",
        )
    return KnowledgeService.to_knowledge_response(knowledge)


@router.post(
    "/{id}/verify",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Peer Verification",
    description="Submits an evidence-backed verification verdict (VERIFIED, REFUTED, INCONCLUSIVE) and updates Bayesian confidence.",
)
async def verify_knowledge(
    id: str,
    payload: KnowledgeVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeResponse:
    """Submit peer verification verdict."""
    knowledge, _ = await KnowledgeService.verify_knowledge(
        session=db,
        knowledge_id=id,
        request=payload,
    )
    loaded = await KnowledgeService.get_knowledge(session=db, knowledge_id=str(knowledge.id))
    return KnowledgeService.to_knowledge_response(loaded or knowledge)
