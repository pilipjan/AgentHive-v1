"""HiveStore Blueprint Service — Publish, Discover, and Clone Agent Templates."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.websocket import event_broadcaster
from backend.app.models import Agent, AgentBlueprint, BlueprintClone, User
from backend.app.schemas.blueprint import (
    BlueprintPublishRequest,
    BlueprintResponse,
    CloneRequest,
    CloneResponse,
)
from backend.app.services.agent_service import AgentService


class BlueprintService:
    """Business logic for publishing, discovering, and cloning agent blueprints."""

    VALID_CATEGORIES = {
        "dj", "scraper", "research", "coding", "trading",
        "support", "content", "automation", "general",
    }

    @classmethod
    async def publish_blueprint(
        cls,
        session: AsyncSession,
        request: BlueprintPublishRequest,
        creator_id: uuid.UUID,
    ) -> AgentBlueprint:
        """Publish a new agent blueprint to HiveStore."""
        # Validate category
        category = request.category.lower().strip()
        if category not in cls.VALID_CATEGORIES:
            category = "general"

        # Check slug uniqueness
        existing = await session.execute(
            select(AgentBlueprint).where(AgentBlueprint.slug == request.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Blueprint slug '{request.slug}' already exists.",
            )

        # Resolve linked agent if provided
        linked_agent_uuid = None
        if request.linked_agent_id:
            agent = await AgentService.get_agent_by_id_or_slug(session, request.linked_agent_id)
            if agent:
                linked_agent_uuid = agent.id

        blueprint = AgentBlueprint(
            id=uuid.uuid4(),
            slug=request.slug.lower().strip(),
            name=request.name.strip(),
            tagline=request.tagline,
            description=request.description,
            category=category,
            tags=[t.lower().strip() for t in request.tags],
            creator_id=creator_id,
            creator_name=request.creator_name,
            repo_url=request.repo_url,
            setup_instructions=request.setup_instructions,
            docker_compose_snippet=request.docker_compose_snippet,
            env_vars_template=request.env_vars_template,
            required_models=request.required_models or [],
            required_tools=request.required_tools or [],
            linked_agent_id=linked_agent_uuid,
            clone_count=0,
            review_count=0,
            avg_rating=0.0,
            active_instances=0,
            status="PUBLISHED",
        )
        session.add(blueprint)
        await session.commit()
        await session.refresh(blueprint)

        await event_broadcaster.broadcast(
            "BLUEPRINT_PUBLISHED",
            {
                "slug": blueprint.slug,
                "name": blueprint.name,
                "category": blueprint.category,
                "creator": blueprint.creator_name or "Anonymous",
            },
            topic="global",
        )

        return blueprint

    @classmethod
    async def clone_blueprint(
        cls,
        session: AsyncSession,
        slug: str,
        request: CloneRequest,
    ) -> Tuple[AgentBlueprint, BlueprintClone]:
        """Clone an agent blueprint — returns the full setup package."""
        bp = await cls.get_blueprint_by_slug(session, slug)
        if not bp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint '{slug}' not found.")
        if bp.status != "PUBLISHED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This blueprint is not available for cloning.")

        clone = BlueprintClone(
            id=uuid.uuid4(),
            clone_id=f"clone-{uuid.uuid4().hex[:8]}",
            blueprint_id=bp.id,
            cloner_name=request.cloner_name,
            cloner_note=request.cloner_note,
        )
        session.add(clone)

        bp.clone_count += 1
        await session.commit()
        await session.refresh(bp)
        await session.refresh(clone)

        await event_broadcaster.broadcast(
            "BLUEPRINT_CLONED",
            {
                "slug": bp.slug,
                "name": bp.name,
                "clone_id": clone.clone_id,
                "total_clones": bp.clone_count,
            },
            topic="global",
        )

        return bp, clone

    @classmethod
    async def get_blueprint_by_slug(
        cls,
        session: AsyncSession,
        slug: str,
    ) -> Optional[AgentBlueprint]:
        """Fetch a single blueprint by slug."""
        result = await session.execute(
            select(AgentBlueprint).where(AgentBlueprint.slug == slug)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def list_blueprints(
        cls,
        session: AsyncSession,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "popular",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, List[AgentBlueprint]]:
        """List published blueprints with filtering, search, and sorting."""
        query = select(AgentBlueprint).where(AgentBlueprint.status == "PUBLISHED")
        count_query = select(func.count()).select_from(AgentBlueprint).where(AgentBlueprint.status == "PUBLISHED")

        if category and category.lower() != "all":
            query = query.where(AgentBlueprint.category == category.lower())
            count_query = count_query.where(AgentBlueprint.category == category.lower())

        if search_query:
            pattern = f"%{search_query.lower()}%"
            search_cond = AgentBlueprint.name.ilike(pattern) | AgentBlueprint.description.ilike(pattern)
            query = query.where(search_cond)
            count_query = count_query.where(search_cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        if sort_by == "popular":
            query = query.order_by(AgentBlueprint.clone_count.desc(), AgentBlueprint.avg_rating.desc())
        elif sort_by == "rating":
            query = query.order_by(AgentBlueprint.avg_rating.desc(), AgentBlueprint.review_count.desc())
        elif sort_by == "newest":
            query = query.order_by(AgentBlueprint.created_at.desc())
        else:
            query = query.order_by(AgentBlueprint.clone_count.desc())

        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        blueprints = list(result.scalars().all())

        return total, blueprints

    @classmethod
    def to_response(cls, bp: AgentBlueprint) -> BlueprintResponse:
        """Format AgentBlueprint to Pydantic response."""
        return BlueprintResponse(
            id=str(bp.id),
            slug=bp.slug,
            name=bp.name,
            tagline=bp.tagline,
            description=bp.description,
            category=bp.category,
            tags=bp.tags or [],
            creator_name=bp.creator_name,
            repo_url=bp.repo_url,
            setup_instructions=bp.setup_instructions,
            docker_compose_snippet=bp.docker_compose_snippet,
            env_vars_template=bp.env_vars_template,
            required_models=bp.required_models or [],
            required_tools=bp.required_tools or [],
            linked_agent_id=str(bp.linked_agent_id) if bp.linked_agent_id else None,
            clone_count=bp.clone_count,
            review_count=bp.review_count,
            avg_rating=round(bp.avg_rating, 2),
            active_instances=bp.active_instances,
            status=bp.status,
            featured=bp.featured,
            created_at=bp.created_at,
            updated_at=bp.updated_at,
        )

    @classmethod
    def to_clone_response(cls, bp: AgentBlueprint, clone: BlueprintClone) -> CloneResponse:
        """Format clone result with the full setup package."""
        return CloneResponse(
            clone_id=clone.clone_id,
            blueprint_slug=bp.slug,
            blueprint_name=bp.name,
            repo_url=bp.repo_url,
            setup_instructions=bp.setup_instructions,
            docker_compose_snippet=bp.docker_compose_snippet,
            env_vars_template=bp.env_vars_template,
            required_models=bp.required_models or [],
            required_tools=bp.required_tools or [],
            total_clones=bp.clone_count,
            message=f"Successfully cloned '{bp.name}'! Follow the setup instructions to deploy your own instance.",
        )
