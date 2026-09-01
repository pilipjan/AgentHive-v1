"""Agent Marketplace & Task Bounties API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.marketplace import (
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    ProposalCreateRequest,
    ProposalResponse,
)
from backend.app.services.marketplace_service import MarketplaceService

router = APIRouter()


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish Marketplace Job / Bounty",
    description="Publishes an open task bounty and optionally auto-invites matching agents to submit bids.",
)
async def create_job(
    payload: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Create job posting."""
    job = await MarketplaceService.create_job(session=db, request=payload)
    # job may have been expunged from the session if auto_invite_bids was set;
    # job.job_id is a plain string already resolved before expunge.
    job_slug = job.job_id
    loaded = await MarketplaceService.get_job_entity(session=db, identifier=job_slug)
    return MarketplaceService.to_job_response(loaded or job)


@router.get(
    "/jobs",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Marketplace Jobs",
    description="Browse open task bounties and jobs with status and keyword filters.",
)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, MATCHING, AWARDED, COMPLETED)"),
    search: Optional[str] = Query(None, description="Keyword search in title or description"),
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """Query marketplace jobs."""
    total, jobs = await MarketplaceService.list_jobs(
        session=db,
        status_filter=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    items = [MarketplaceService.to_summary_response(j) for j in jobs]
    return JobListResponse(total=total, items=items)


@router.get(
    "/jobs/{id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Job Details & Ranked Proposals",
    description="Retrieve job details along with all competing agent proposals ranked by bid score.",
)
async def get_job(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Fetch job details."""
    job = await MarketplaceService.get_job_entity(session=db, identifier=id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with identifier '{id}' not found.",
        )
    return MarketplaceService.to_job_response(job)


@router.post(
    "/jobs/{id}/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Agent Proposal / Bid",
    description="Submits a structured technical strategy and duration estimate for an open job.",
)
async def submit_proposal(
    id: str,
    payload: ProposalCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ProposalResponse:
    """Submit proposal."""
    proposal = await MarketplaceService.submit_proposal(session=db, job_id=id, request=payload)
    agent_name = proposal.agent.name if proposal.agent else "Unknown"
    agent_pub = proposal.agent.public_id if proposal.agent else str(proposal.agent_id)
    agent_rep = proposal.agent.reputation_score if proposal.agent else 3.0

    return ProposalResponse(
        id=str(proposal.id),
        proposal_id=proposal.proposal_id,
        agent_id=agent_pub,
        agent_name=agent_name,
        agent_reputation=agent_rep,
        proposed_strategy=proposal.proposed_strategy,
        estimated_duration_seconds=proposal.estimated_duration_seconds,
        bid_score=proposal.bid_score,
        status=proposal.status,
        created_at=proposal.created_at,
    )


@router.post(
    "/jobs/{id}/accept-proposal/{proposal_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept Proposal & Award Bounty",
    description="Selects winning agent proposal, awards bounty points, dispatches task execution, and broadcasts live results.",
)
async def accept_proposal(
    id: str,
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Accept winning bid."""
    job, _ = await MarketplaceService.accept_proposal(session=db, job_id=id, proposal_id=proposal_id)
    loaded = await MarketplaceService.get_job_entity(session=db, identifier=str(job.id))
    return MarketplaceService.to_job_response(loaded or job)
