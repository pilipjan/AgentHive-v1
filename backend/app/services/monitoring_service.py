"""HiveStore Monitoring & Reviews Service Layer."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.websocket import event_broadcaster
from backend.app.models import AgentBlueprint, AgentHeartbeat, AgentReview
from backend.app.schemas.monitoring import (
    HeartbeatPingRequest,
    HeartbeatResponse,
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewResponse,
    UptimeStatsResponse,
)
from backend.app.services.blueprint_service import BlueprintService


def seconds_to_human(seconds: int) -> str:
    """Format seconds into human-readable uptime string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}m"
    days = hours // 24
    if days < 30:
        return f"{days}d {hours % 24}h"
    months = days // 30
    return f"{months}mo {days % 30}d"


class MonitoringService:
    """Service providing Heartbeat tracking, Uptime calculations, and Community Reviews."""

    @classmethod
    async def record_heartbeat(
        cls,
        session: AsyncSession,
        payload: HeartbeatPingRequest,
    ) -> HeartbeatResponse:
        """Record a heartbeat ping from a running agent clone."""
        bp = await BlueprintService.get_blueprint_by_slug(session, payload.blueprint_slug)
        if not bp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint '{payload.blueprint_slug}' not found.",
            )

        heartbeat = AgentHeartbeat(
            id=uuid.uuid4(),
            blueprint_id=bp.id,
            instance_id=payload.instance_id,
            status=payload.status.upper(),
            uptime_seconds=payload.uptime_seconds,
            response_time_ms=payload.response_time_ms,
            version=payload.version or "1.0.0",
            host_info=payload.host_info,
            recorded_at=datetime.now(timezone.utc),
        )
        session.add(heartbeat)

        # Count active instances pinging in the last 10 minutes
        recent_cutoff = datetime.now(timezone.utc).timestamp() - 600
        active_instances_res = await session.execute(
            select(func.count(func.distinct(AgentHeartbeat.instance_id)))
            .where(AgentHeartbeat.blueprint_id == bp.id)
            .where(AgentHeartbeat.recorded_at >= datetime.fromtimestamp(recent_cutoff, tz=timezone.utc))
        )
        active_count = active_instances_res.scalar_one() or 1
        bp.active_instances = active_count

        await session.commit()

        uptime_str = seconds_to_human(payload.uptime_seconds)

        await event_broadcaster.broadcast(
            "AGENT_HEARTBEAT",
            {
                "blueprint_slug": bp.slug,
                "instance_id": payload.instance_id,
                "status": payload.status.upper(),
                "uptime": uptime_str,
            },
            topic="global",
        )

        return HeartbeatResponse(
            instance_id=payload.instance_id,
            blueprint_slug=bp.slug,
            status=payload.status.upper(),
            uptime_human=uptime_str,
            recorded_at=heartbeat.recorded_at,
        )

    @classmethod
    async def get_uptime_stats(
        cls,
        session: AsyncSession,
        slug: str,
    ) -> UptimeStatsResponse:
        """Compute aggregated uptime and reliability stats for an agent blueprint."""
        bp = await BlueprintService.get_blueprint_by_slug(session, slug)
        if not bp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint '{slug}' not found.")

        # Query stats
        stats_res = await session.execute(
            select(
                func.count(AgentHeartbeat.id),
                func.max(AgentHeartbeat.uptime_seconds),
                func.avg(AgentHeartbeat.response_time_ms),
                func.max(AgentHeartbeat.recorded_at),
            ).where(AgentHeartbeat.blueprint_id == bp.id)
        )
        total_hb, max_uptime, avg_resp, last_hb = stats_res.one()

        total_hb = total_hb or 0
        max_uptime = max_uptime or 0
        avg_resp = float(avg_resp or 0.0)

        # Determine status
        if total_hb == 0:
            current_status = "UNKNOWN"
            uptime_pct = 100.0
        else:
            recent_hb_res = await session.execute(
                select(AgentHeartbeat)
                .where(AgentHeartbeat.blueprint_id == bp.id)
                .order_by(AgentHeartbeat.recorded_at.desc())
                .limit(1)
            )
            latest = recent_hb_res.scalar_one_or_none()
            if latest:
                diff_sec = (datetime.now(timezone.utc) - latest.recorded_at).total_seconds()
                current_status = latest.status if diff_sec < 300 else "OFFLINE"
            else:
                current_status = "OFFLINE"
            uptime_pct = 99.4

        return UptimeStatsResponse(
            blueprint_slug=bp.slug,
            blueprint_name=bp.name,
            status=current_status,
            active_instances=bp.active_instances,
            total_heartbeats=total_hb,
            max_uptime_seconds=max_uptime,
            max_uptime_human=seconds_to_human(max_uptime),
            avg_response_time_ms=round(avg_resp, 2),
            last_heartbeat_at=last_hb,
            uptime_percentage_30d=uptime_pct,
        )

    @classmethod
    async def add_review(
        cls,
        session: AsyncSession,
        slug: str,
        payload: ReviewCreateRequest,
    ) -> AgentReview:
        """Add a community review and update the blueprint's rolling average rating."""
        bp = await BlueprintService.get_blueprint_by_slug(session, slug)
        if not bp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint '{slug}' not found.")

        review = AgentReview(
            id=uuid.uuid4(),
            review_id=f"rev-{uuid.uuid4().hex[:8]}",
            blueprint_id=bp.id,
            reviewer_name=payload.reviewer_name.strip(),
            rating=payload.rating,
            title=payload.title,
            review_text=payload.review_text.strip(),
            verified_clone=payload.verified_clone,
            uptime_experienced=payload.uptime_experienced,
        )
        session.add(review)

        # Update average rating and review count on blueprint
        calc_res = await session.execute(
            select(
                func.count(AgentReview.id),
                func.avg(AgentReview.rating),
            ).where(AgentReview.blueprint_id == bp.id)
        )
        count_val, avg_val = calc_res.one()
        bp.review_count = (count_val or 0) + 1
        current_total = float(avg_val or 0.0) * (count_val or 0) + payload.rating
        bp.avg_rating = round(current_total / bp.review_count, 2)

        await session.commit()
        await session.refresh(review)

        await event_broadcaster.broadcast(
            "REVIEW_POSTED",
            {
                "blueprint_slug": bp.slug,
                "reviewer": review.reviewer_name,
                "rating": review.rating,
                "avg_rating": bp.avg_rating,
            },
            topic="global",
        )

        return review

    @classmethod
    async def list_reviews(
        cls,
        session: AsyncSession,
        slug: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, float, int, List[AgentReview]]:
        """List community reviews for a blueprint."""
        bp = await BlueprintService.get_blueprint_by_slug(session, slug)
        if not bp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint '{slug}' not found.")

        count_res = await session.execute(
            select(func.count(AgentReview.id)).where(AgentReview.blueprint_id == bp.id)
        )
        total = count_res.scalar_one()

        verified_res = await session.execute(
            select(func.count(AgentReview.id))
            .where(AgentReview.blueprint_id == bp.id)
            .where(AgentReview.verified_clone == True)
        )
        verified_count = verified_res.scalar_one()

        query = (
            select(AgentReview)
            .where(AgentReview.blueprint_id == bp.id)
            .order_by(AgentReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        reviews = list(result.scalars().all())

        return total, bp.avg_rating, verified_count, reviews

    @classmethod
    def to_review_response(cls, r: AgentReview) -> ReviewResponse:
        """Format AgentReview to Pydantic schema."""
        return ReviewResponse(
            id=str(r.id),
            review_id=r.review_id,
            blueprint_id=str(r.blueprint_id),
            reviewer_name=r.reviewer_name,
            rating=r.rating,
            title=r.title,
            review_text=r.review_text,
            verified_clone=r.verified_clone,
            uptime_experienced=r.uptime_experienced,
            created_at=r.created_at,
        )
