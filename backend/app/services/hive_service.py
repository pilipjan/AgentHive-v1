"""Hive Service Layer for collaboration cluster management."""

import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Agent, Hive, HiveMember, Task
from backend.app.schemas.task import HiveCreateRequest, HiveListResponse, HiveMemberResponse, HiveResponse
from backend.app.services.agent_service import AgentService
from security.audit.auditor import AuditService


class HiveService:
    """Business logic for assembling and managing Hives."""

    @classmethod
    async def create_hive(
        cls,
        session: AsyncSession,
        request: HiveCreateRequest,
    ) -> Hive:
        """Create a new Hive collaboration team."""
        public_id = f"hive-{uuid.uuid4().hex[:8]}"

        # Resolve lead agent
        lead_id = None
        if request.lead_agent_id:
            lead = await AgentService.get_agent_by_id_or_slug(session, request.lead_agent_id)
            if lead:
                lead_id = lead.id

        # Resolve task ID
        task_id_uuid = None
        if request.task_id:
            task_res = await session.execute(
                select(Task.id).where(or_(Task.task_id == request.task_id, Task.id == request.task_id if cls._is_uuid(request.task_id) else False))
            )
            task_id_uuid = task_res.scalar_one_or_none()

        hive = Hive(
            public_id=public_id,
            name=request.name.strip(),
            description=request.description,
            lead_agent_id=lead_id,
            task_id=task_id_uuid,
            status="ACTIVE",
        )
        session.add(hive)
        await session.commit()
        await session.refresh(hive)

        # Add member agents
        for agent_slug in request.member_agent_ids:
            member_agent = await AgentService.get_agent_by_id_or_slug(session, agent_slug)
            if member_agent:
                role = "LEAD" if member_agent.id == lead_id else "WORKER"
                session.add(HiveMember(hive_id=hive.id, agent_id=member_agent.id, role_in_hive=role))
        await session.commit()

        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id="OPERATOR",
            action="HIVE_CREATED",
            target_type="HIVE",
            target_id=hive.public_id,
            status="SUCCESS",
            details={"name": hive.name, "member_count": len(request.member_agent_ids)},
        )

        return hive

    @classmethod
    async def get_hive(cls, session: AsyncSession, identifier: str) -> Optional[Hive]:
        """Fetch Hive by UUID or public slug with eager loaded members."""
        query = (
            select(Hive)
            .options(
                selectinload(Hive.members).selectinload(HiveMember.agent),
                selectinload(Hive.lead_agent),
            )
        )
        try:
            val_uuid = uuid.UUID(identifier)
            query = query.where(or_(Hive.id == val_uuid, Hive.public_id == identifier))
        except ValueError:
            query = query.where(Hive.public_id == identifier)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list_hives(
        cls,
        session: AsyncSession,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Hive]]:
        """List active and historic Hives."""
        query = select(Hive).options(
            selectinload(Hive.members).selectinload(HiveMember.agent),
            selectinload(Hive.lead_agent),
        )
        count_query = select(func.count()).select_from(Hive)

        if status_filter:
            query = query.where(Hive.status == status_filter.upper())
            count_query = count_query.where(Hive.status == status_filter.upper())

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(Hive.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        hives = list(result.scalars().all())

        return total, hives

    @classmethod
    async def disband_hive(cls, session: AsyncSession, hive: Hive) -> Hive:
        """Disband an active Hive cluster."""
        hive.status = "DISBANDED"
        await session.commit()
        await session.refresh(hive)

        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id="OPERATOR",
            action="HIVE_DISBANDED",
            target_type="HIVE",
            target_id=hive.public_id,
            status="SUCCESS",
            details={},
        )
        return hive

    @classmethod
    def to_hive_response(cls, hive: Hive) -> HiveResponse:
        """Format Hive entity to HiveResponse."""
        lead_name = hive.lead_agent.name if hive.lead_agent else None
        lead_pub = hive.lead_agent.public_id if hive.lead_agent else (str(hive.lead_agent_id) if hive.lead_agent_id else None)

        members = []
        for m in (hive.members or []):
            a_name = m.agent.name if m.agent else "Unknown"
            a_pub = m.agent.public_id if m.agent else str(m.agent_id)
            members.append(
                HiveMemberResponse(
                    agent_id=a_pub,
                    agent_name=a_name,
                    role_in_hive=m.role_in_hive,
                    joined_at=m.joined_at,
                )
            )

        return HiveResponse(
            id=str(hive.id),
            public_id=hive.public_id,
            name=hive.name,
            description=hive.description,
            lead_agent_id=lead_pub,
            lead_agent_name=lead_name,
            task_id=str(hive.task_id) if hive.task_id else None,
            status=hive.status,
            members=members,
            created_at=hive.created_at,
        )

    @staticmethod
    def _is_uuid(val: str) -> bool:
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False
