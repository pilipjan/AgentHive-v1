"""Reputation & Evaluation API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.reputation import (
    EvaluationCreateRequest,
    EvaluationResponse,
    ReputationDetailResponse,
    ReputationHistoryResponse,
)
from backend.app.services.reputation_service import ReputationService

router = APIRouter()


@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Peer Review Evaluation",
    description="Submits a multi-dimensional peer review evaluation for a completed task and updates reputation.",
)
async def submit_evaluation(
    payload: EvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Submit evaluation."""
    evaluation = await ReputationService.submit_evaluation(session=db, request=payload)
    return EvaluationResponse(
        id=str(evaluation.id),
        task_id=payload.task_id,
        reviewer_agent_id=payload.reviewer_agent_id,
        reviewer_agent_name=payload.reviewer_agent_id,
        target_agent_id=payload.target_agent_id,
        target_agent_name=payload.target_agent_id,
        task_success_score=evaluation.task_success_score,
        usefulness_score=evaluation.usefulness_score,
        accuracy_score=evaluation.accuracy_score,
        reliability_score=evaluation.reliability_score,
        safety_score=evaluation.safety_score,
        comments=evaluation.comments,
        created_at=evaluation.created_at,
    )


@router.get(
    "/reputation/{agent_id}",
    response_model=ReputationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Multi-Factor Reputation",
    description="Retrieve comprehensive 5-factor reputation breakdown, underlying metric telemetry, and star rating.",
)
async def get_reputation(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReputationDetailResponse:
    """Fetch reputation breakdown."""
    return await ReputationService.get_agent_reputation(session=db, identifier=agent_id)


@router.get(
    "/reputation/{agent_id}/history",
    response_model=ReputationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Reputation Event History",
    description="Retrieve immutable chronological ledger of score adjustments for an agent.",
)
async def get_reputation_history(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max history events"),
    db: AsyncSession = Depends(get_db),
) -> ReputationHistoryResponse:
    """Fetch reputation history events."""
    return await ReputationService.get_reputation_history(session=db, identifier=agent_id, limit=limit)
