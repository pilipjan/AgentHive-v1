"""HiveStore REST API Endpoints — Blueprint Publishing, Discovery, and Cloning."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.blueprint import (
    BlueprintListResponse,
    BlueprintPublishRequest,
    BlueprintResponse,
    CloneRequest,
    CloneResponse,
)
from backend.app.schemas.monitoring import (
    HeartbeatPingRequest,
    HeartbeatResponse,
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewResponse,
    UptimeStatsResponse,
)
from backend.app.services.agent_service import AgentService
from backend.app.services.blueprint_service import BlueprintService
from backend.app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get(
    "/blueprints",
    response_model=BlueprintListResponse,
    status_code=status.HTTP_200_OK,
    summary="Browse Agent Blueprints",
    description="Discover published agent templates. Filter by category, search by name, sort by popularity or rating.",
)
async def list_blueprints(
    category: Optional[str] = Query(None, description="Filter by category (dj, scraper, research, coding, etc.)"),
    q: Optional[str] = Query(None, description="Search by name or description"),
    sort: str = Query("popular", description="Sort: popular, rating, newest"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> BlueprintListResponse:
    total, blueprints = await BlueprintService.list_blueprints(
        session=db,
        category=category,
        search_query=q,
        sort_by=sort,
        limit=limit,
        offset=offset,
    )
    return BlueprintListResponse(
        total=total,
        items=[BlueprintService.to_response(bp) for bp in blueprints],
    )


@router.get(
    "/blueprints/{slug}",
    response_model=BlueprintResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Blueprint Detail",
    description="Fetch full details of a single agent blueprint including setup instructions and clone stats.",
)
async def get_blueprint(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> BlueprintResponse:
    bp = await BlueprintService.get_blueprint_by_slug(db, slug)
    if not bp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Blueprint '{slug}' not found.")
    return BlueprintService.to_response(bp)


@router.post(
    "/blueprints",
    response_model=BlueprintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish Agent Blueprint",
    description="Publish a new agent template to HiveStore so others can discover and clone it.",
)
async def publish_blueprint(
    payload: BlueprintPublishRequest,
    db: AsyncSession = Depends(get_db),
) -> BlueprintResponse:
    user = await AgentService.get_or_create_default_user(db)
    bp = await BlueprintService.publish_blueprint(
        session=db,
        request=payload,
        creator_id=user.id,
    )
    return BlueprintService.to_response(bp)


@router.post(
    "/blueprints/{slug}/clone",
    response_model=CloneResponse,
    status_code=status.HTTP_200_OK,
    summary="Clone Agent Blueprint",
    description="Clone an agent blueprint to get the full setup package (repo, docker compose, env template, setup guide).",
)
async def clone_blueprint(
    slug: str,
    payload: CloneRequest = CloneRequest(),
    db: AsyncSession = Depends(get_db),
) -> CloneResponse:
    bp, clone = await BlueprintService.clone_blueprint(
        session=db,
        slug=slug,
        request=payload,
    )
    return BlueprintService.to_clone_response(bp, clone)


# --- Live Uptime & Monitoring ---

@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    status_code=status.HTTP_200_OK,
    summary="Record Agent Heartbeat",
    description="Running agent instances send periodic pings to prove uptime, latency, and operational health.",
)
async def record_heartbeat(
    payload: HeartbeatPingRequest,
    db: AsyncSession = Depends(get_db),
) -> HeartbeatResponse:
    return await MonitoringService.record_heartbeat(session=db, payload=payload)


@router.get(
    "/blueprints/{slug}/uptime",
    response_model=UptimeStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Uptime & Reliability",
    description="View public uptime percentage, max running time, and active instances for a blueprint.",
)
async def get_uptime_stats(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> UptimeStatsResponse:
    return await MonitoringService.get_uptime_stats(session=db, slug=slug)


# --- Community Reviews & Star Ratings ---

@router.post(
    "/blueprints/{slug}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Community Review",
    description="Leave a 1-5 star review and feedback for an agent blueprint you deployed or tested.",
)
async def submit_review(
    slug: str,
    payload: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    review = await MonitoringService.add_review(session=db, slug=slug, payload=payload)
    return MonitoringService.to_review_response(review)


@router.get(
    "/blueprints/{slug}/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Community Reviews",
    description="Read user reviews, star ratings, and verified clone testimonials for an agent blueprint.",
)
async def list_reviews(
    slug: str,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    total, avg_rating, verified_count, reviews = await MonitoringService.list_reviews(
        session=db,
        slug=slug,
        limit=limit,
        offset=offset,
    )
    return ReviewListResponse(
        total=total,
        avg_rating=round(avg_rating, 2),
        verified_clone_count=verified_count,
        items=[MonitoringService.to_review_response(r) for r in reviews],
    )
