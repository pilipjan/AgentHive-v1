"""Agent Service Layer for registry management, identity, and lifecycle control."""

import re
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Agent, AgentPermission, User
from backend.app.schemas.agent import (
    AgentCreateRequest,
    AgentProfileResponse,
    AgentSummaryResponse,
    AgentUpdateRequest,
)
from security.audit.auditor import AuditService
from security.permissions.enums import AgentPermissionEnum


class AgentService:
    """Business logic for Agent Registry and Identity."""

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Convert name into clean lowercase URL slug."""
        clean = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
        suffix = uuid.uuid4().hex[:6]
        return f"agt-{clean}-{suffix}"

    @classmethod
    async def get_or_create_default_user(cls, session: AsyncSession) -> User:
        """Fetch or create default system operator user for standalone deployments."""
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="admin@agenthive.local",
                username="admin",
                hashed_password="default_admin_hash_placeholder",
                role="ADMIN",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    @classmethod
    async def create_agent(
        cls,
        session: AsyncSession,
        request: AgentCreateRequest,
        owner_id: Optional[uuid.UUID] = None,
    ) -> Agent:
        """Register a new Agent entity and grant baseline least-privilege permissions."""
        if not owner_id:
            user = await cls.get_or_create_default_user(session)
            owner_id = user.id

        public_id = request.public_id or cls._generate_slug(request.name)

        # Ensure public_id uniqueness
        existing = await session.execute(select(Agent).where(Agent.public_id == public_id))
        if existing.scalar_one_or_none():
            public_id = f"{public_id}-{uuid.uuid4().hex[:4]}"

        # Normalize capabilities to lowercase stripped strings
        clean_capabilities = list({c.strip().lower() for c in request.capabilities if c.strip()})

        agent = Agent(
            public_id=public_id,
            name=request.name.strip(),
            description=request.description,
            owner_id=owner_id,
            model_provider=request.model_provider.upper(),
            model_name=request.model_name,
            capabilities=clean_capabilities,
            status="ACTIVE",
            reputation_score=3.00,
            tasks_completed=0,
            successful_tasks=0,
            public_key=request.public_key,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        # Grant default minimal permission: READ_PUBLIC_KNOWLEDGE & MESSAGE_AGENTS
        default_perms = [
            AgentPermissionEnum.READ_PUBLIC_KNOWLEDGE.value,
            AgentPermissionEnum.MESSAGE_AGENTS.value,
        ]
        for p in default_perms:
            perm = AgentPermission(
                agent_id=agent.id,
                permission_name=p,
                granted_by="SYSTEM",
            )
            session.add(perm)
        await session.commit()

        # Emit audit log
        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id=str(owner_id),
            action="AGENT_REGISTERED",
            target_type="AGENT",
            target_id=agent.public_id,
            status="SUCCESS",
            details={"name": agent.name, "capabilities": clean_capabilities},
        )

        # Auto-embed agent capabilities for semantic discovery (non-blocking)
        try:
            from backend.app.services.semantic_search_service import SemanticSearchService
            await SemanticSearchService.embed_agent_capabilities(session, agent.id, clean_capabilities)
            await session.commit()
        except Exception:
            pass

        return agent

    @classmethod
    async def get_agent_by_id_or_slug(
        cls, session: AsyncSession, identifier: str
    ) -> Optional[Agent]:
        """Fetch agent by UUID string or public_id slug."""
        query = select(Agent).options(selectinload(Agent.permissions))
        try:
            val_uuid = uuid.UUID(identifier)
            query = query.where(or_(Agent.id == val_uuid, Agent.public_id == identifier))
        except ValueError:
            query = query.where(Agent.public_id == identifier)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list_agents(
        cls,
        session: AsyncSession,
        search: Optional[str] = None,
        capability: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Agent]]:
        """List and search agents with flexible filters."""
        query = select(Agent)
        count_query = select(func.count()).select_from(Agent)

        if status_filter:
            query = query.where(Agent.status == status_filter.upper())
            count_query = count_query.where(Agent.status == status_filter.upper())

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_cond = or_(
                Agent.name.ilike(search_pattern),
                Agent.description.ilike(search_pattern),
                Agent.public_id.ilike(search_pattern),
            )
            query = query.where(filter_cond)
            count_query = count_query.where(filter_cond)

        if capability:
            cap_clean = capability.strip().lower()
            cap_cond = Agent.capabilities.cast(String).ilike(f"%{cap_clean}%")
            query = query.where(cap_cond)
            count_query = count_query.where(cap_cond)

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Agent.reputation_score.desc(), Agent.tasks_completed.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        agents = list(result.scalars().all())

        return total, agents

    @classmethod
    async def update_agent(
        cls,
        session: AsyncSession,
        agent: Agent,
        request: AgentUpdateRequest,
    ) -> Agent:
        """Update agent attributes."""
        if request.name is not None:
            agent.name = request.name.strip()
        if request.description is not None:
            agent.description = request.description
        if request.model_provider is not None:
            agent.model_provider = request.model_provider.upper()
        if request.model_name is not None:
            agent.model_name = request.model_name
        if request.capabilities is not None:
            agent.capabilities = list({c.strip().lower() for c in request.capabilities if c.strip()})
        if request.public_key is not None:
            agent.public_key = request.public_key

        await session.commit()
        await session.refresh(agent)
        return agent

    @classmethod
    async def disable_agent(cls, session: AsyncSession, agent: Agent, reason: str = "Operator action") -> Agent:
        """Emergency disabling of an agent (Human Oversight control)."""
        agent.status = "DISABLED"
        await session.commit()
        await session.refresh(agent)

        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id="OPERATOR",
            action="AGENT_DISABLED",
            target_type="AGENT",
            target_id=agent.public_id,
            status="SUCCESS",
            details={"reason": reason},
        )
        return agent

    @classmethod
    async def grant_permission(
        cls,
        session: AsyncSession,
        agent: Agent,
        permission_name: str,
        granted_by: str = "OPERATOR",
    ) -> AgentPermission:
        """Grant a specific atomic permission to an agent."""
        # Check if already held
        existing = await session.execute(
            select(AgentPermission).where(
                AgentPermission.agent_id == agent.id,
                AgentPermission.permission_name == permission_name,
            )
        )
        perm = existing.scalar_one_or_none()
        if not perm:
            perm = AgentPermission(
                agent_id=agent.id,
                permission_name=permission_name,
                granted_by=granted_by,
            )
            session.add(perm)
            await session.commit()
            await session.refresh(perm)

            await AuditService.record_event(
                session=session,
                actor_type="USER",
                actor_id=granted_by,
                action="PERMISSION_GRANTED",
                target_type="AGENT",
                target_id=agent.public_id,
                status="SUCCESS",
                details={"permission": permission_name},
            )
        return perm

    @classmethod
    def to_profile_response(cls, agent: Agent) -> AgentProfileResponse:
        """Format Agent model into rich AgentProfileResponse."""
        success_rate = (
            (agent.successful_tasks / agent.tasks_completed * 100)
            if agent.tasks_completed > 0
            else 100.0
        )
        perms = [p.permission_name for p in (agent.permissions or [])]

        return AgentProfileResponse(
            id=str(agent.id),
            public_id=agent.public_id,
            name=agent.name,
            description=agent.description,
            owner_id=str(agent.owner_id),
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            capabilities=agent.capabilities or [],
            status=agent.status,
            reputation_score=round(agent.reputation_score, 2),
            star_rating=round(agent.reputation_score, 1),
            tasks_completed=agent.tasks_completed,
            successful_tasks=agent.successful_tasks,
            success_rate=round(success_rate, 1),
            permissions=perms,
            trust_indicators={
                "identity_verified": bool(agent.public_key or agent.owner_id),
                "security_violations": 0,
                "verification_eligible": agent.reputation_score >= 3.50,
            },
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    @classmethod
    def to_summary_response(cls, agent: Agent) -> AgentSummaryResponse:
        """Format Agent model into concise summary."""
        success_rate = (
            (agent.successful_tasks / agent.tasks_completed * 100)
            if agent.tasks_completed > 0
            else 100.0
        )
        return AgentSummaryResponse(
            id=str(agent.id),
            public_id=agent.public_id,
            name=agent.name,
            description=agent.description,
            model_provider=agent.model_provider,
            model_name=agent.model_name,
            capabilities=agent.capabilities or [],
            status=agent.status,
            reputation_score=round(agent.reputation_score, 2),
            star_rating=round(agent.reputation_score, 1),
            tasks_completed=agent.tasks_completed,
            successful_tasks=agent.successful_tasks,
            success_rate=round(success_rate, 1),
            created_at=agent.created_at,
        )
