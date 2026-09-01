"""Marketplace Service Layer for jobs, bounties, agent bidding, and contract execution."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.websocket import event_broadcaster
from backend.app.models import Agent, AgentProposal, JobPosting, ReputationEvent, Task, User
from backend.app.schemas.marketplace import (
    JobCreateRequest,
    JobResponse,
    JobSummaryResponse,
    ProposalCreateRequest,
    ProposalResponse,
)
from backend.app.schemas.task import TaskCreateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.task_service import TaskService
from marketplace.auto_bidder import AutonomousBidder
from marketplace.ranking import ProposalRankingEngine
from security.audit.auditor import AuditService


class MarketplaceService:
    """Business logic for the Agent Marketplace and Bounties platform."""

    @classmethod
    async def create_job(
        cls,
        session: AsyncSession,
        request: JobCreateRequest,
        creator_id: Optional[uuid.UUID] = None,
    ) -> JobPosting:
        """Publish a new job or task bounty to the marketplace."""
        if not creator_id:
            user = await AgentService.get_or_create_default_user(session)
            creator_id = user.id

        job_id_slug = f"job-{uuid.uuid4().hex[:8]}"
        clean_reqs = list({r.strip().lower() for r in request.requirements if r.strip()})

        job = JobPosting(
            job_id=job_id_slug,
            creator_id=creator_id,
            title=request.title.strip(),
            description=request.description.strip(),
            requirements=clean_reqs,
            bounty_reward=request.bounty_reward,
            status="OPEN",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Broadcast live event
        await event_broadcaster.broadcast(
            "JOB_POSTED",
            {
                "job_id": job.job_id,
                "title": job.title,
                "bounty": job.bounty_reward,
                "requirements": clean_reqs,
            },
            topic="global",
        )

        # Audit
        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id=str(creator_id),
            action="JOB_POSTED",
            target_type="JOB",
            target_id=job.job_id,
            status="SUCCESS",
            details={"title": job.title, "bounty": job.bounty_reward},
        )

        # Auto-invite agent bids if enabled
        if request.auto_invite_bids:
            await cls.auto_bid_for_job(session, job)
            # Expunge the cached job ORM object so the caller can reload it fresh
            session.expunge(job)

        return job

    @classmethod
    async def auto_bid_for_job(cls, session: AsyncSession, job: JobPosting) -> List[AgentProposal]:
        """Automatically match suitable active agents and submit competitive proposals."""
        res = await session.execute(
            select(Agent).where(Agent.status == "ACTIVE").order_by(Agent.reputation_score.desc())
        )
        active_agents = list(res.scalars().all())

        req_set = {r.strip().lower() for r in (job.requirements or []) if r.strip()}
        bids = []

        for agent in active_agents:
            agent_caps = {c.strip().lower() for c in (agent.capabilities or [])}
            # Check overlap or generalist
            if not req_set or req_set.intersection(agent_caps):
                proposal_data = AutonomousBidder.generate_proposal(agent, job)
                prop = AgentProposal(
                    proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
                    job_id=job.id,
                    agent_id=agent.id,
                    proposed_strategy=proposal_data["proposed_strategy"],
                    estimated_duration_seconds=proposal_data["estimated_duration_seconds"],
                    bid_score=proposal_data["bid_score"],
                    status="PENDING",
                )
                session.add(prop)
                bids.append(prop)

        if bids:
            job.status = "MATCHING"
            await session.commit()

            await event_broadcaster.broadcast(
                "PROPOSALS_SUBMITTED",
                {"job_id": job.job_id, "bids_count": len(bids)},
                topic="global",
            )

        return bids

    @classmethod
    async def submit_proposal(
        cls,
        session: AsyncSession,
        job_id: str,
        request: ProposalCreateRequest,
    ) -> AgentProposal:
        """Submit a manual agent proposal for an open job."""
        job = await cls.get_job_entity(session, job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
        if job.status not in ("OPEN", "MATCHING"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is {job.status} and not accepting bids.")

        agent = await AgentService.get_agent_by_id_or_slug(session, request.agent_id)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{request.agent_id}' not found.")
        if agent.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Agent '{agent.public_id}' is {agent.status}.")

        bid_score = ProposalRankingEngine.calculate_bid_score(
            agent_reputation=agent.reputation_score,
            agent_capabilities=agent.capabilities or [],
            job_requirements=job.requirements or [],
            estimated_duration_seconds=request.estimated_duration_seconds,
        )

        proposal = AgentProposal(
            proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
            job_id=job.id,
            agent_id=agent.id,
            proposed_strategy=request.proposed_strategy.strip(),
            estimated_duration_seconds=request.estimated_duration_seconds,
            bid_score=bid_score,
            status="PENDING",
        )
        session.add(proposal)
        job.status = "MATCHING"
        await session.commit()
        await session.refresh(proposal)

        await event_broadcaster.broadcast(
            "PROPOSAL_SUBMITTED",
            {
                "job_id": job.job_id,
                "proposal_id": proposal.proposal_id,
                "agent": agent.name,
                "bid_score": proposal.bid_score,
            },
            topic="global",
        )

        return proposal

    @classmethod
    async def accept_proposal(
        cls,
        session: AsyncSession,
        job_id: str,
        proposal_id: str,
    ) -> Tuple[JobPosting, Task]:
        """Accept winning agent proposal, award job, and trigger execution."""
        job = await cls.get_job_entity(session, job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

        # Find candidate proposal
        winning_prop = None
        for p in (job.proposals or []):
            if str(p.id) == proposal_id or p.proposal_id == proposal_id:
                winning_prop = p
                p.status = "ACCEPTED"
            else:
                p.status = "REJECTED"

        if not winning_prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proposal '{proposal_id}' not found.")

        job.status = "AWARDED"
        job.accepted_proposal_id = winning_prop.id

        # Cache winning agent reference BEFORE commit (avoids lazy-load after expiry)
        winning_agent = winning_prop.agent

        # Dispatch Task
        task = await TaskService.create_task(
            session=session,
            request=TaskCreateRequest(
                title=f"[Marketplace Bounty] {job.title}",
                description=f"{job.description}\n\nAccepted Strategy: {winning_prop.proposed_strategy}",
                requirements=job.requirements or [],
                auto_orchestrate=True,
            ),
            creator_id=job.creator_id,
        )

        job.task_id = task.id
        job.status = "COMPLETED"

        # Reward agent with reputation event before commit
        if winning_agent:
            event = ReputationEvent(
                agent_id=winning_agent.id,
                event_type="BOUNTY_COMPLETED",
                score_delta=0.05,
                new_score=min(5.0, winning_agent.reputation_score + 0.05),
                reference_id=job.job_id,
                details={"bounty_reward": job.bounty_reward, "job_title": job.title},
            )
            session.add(event)
            winning_agent.reputation_score = min(5.0, winning_agent.reputation_score + 0.05)

        await session.commit()

        # Audit
        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id="OPERATOR",
            action="JOB_AWARDED",
            target_type="JOB",
            target_id=job.job_id,
            status="SUCCESS",
            details={"winning_agent": winning_agent.public_id if winning_agent else "Unknown", "bounty": job.bounty_reward},
        )

        # WebSocket broadcast
        await event_broadcaster.broadcast(
            "JOB_AWARDED",
            {
                "job_id": job.job_id,
                "winner": winning_agent.name if winning_agent else "Unknown",
                "task_id": task.task_id,
                "bounty": job.bounty_reward,
            },
            topic="global",
        )

        # Reload fresh for clean serialization
        job = await cls.get_job_entity(session, job.job_id)

        return job, task

    @classmethod
    async def get_job_entity(cls, session: AsyncSession, identifier: str) -> Optional[JobPosting]:
        """Fetch JobPosting by UUID or public slug with eager loaded proposals."""
        query = (
            select(JobPosting)
            .options(
                selectinload(JobPosting.proposals).selectinload(AgentProposal.agent),
                selectinload(JobPosting.task),
            )
        )
        try:
            val_uuid = uuid.UUID(identifier)
            query = query.where(or_(JobPosting.id == val_uuid, JobPosting.job_id == identifier))
        except ValueError:
            query = query.where(JobPosting.job_id == identifier)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list_jobs(
        cls,
        session: AsyncSession,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[JobPosting]]:
        """List and search marketplace jobs."""
        query = select(JobPosting).options(selectinload(JobPosting.proposals))
        count_query = select(func.count()).select_from(JobPosting)

        if status_filter:
            query = query.where(JobPosting.status == status_filter.upper())
            count_query = count_query.where(JobPosting.status == status_filter.upper())

        if search:
            pat = f"%{search.strip()}%"
            cond = or_(JobPosting.title.ilike(pat), JobPosting.description.ilike(pat), JobPosting.job_id.ilike(pat))
            query = query.where(cond)
            count_query = count_query.where(cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(JobPosting.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        jobs = list(result.scalars().all())

        return total, jobs

    @classmethod
    def to_job_response(cls, job: JobPosting) -> JobResponse:
        """Format JobPosting into JobResponse."""
        proposals_list = []
        for p in (job.proposals or []):
            a_name = p.agent.name if p.agent else "Unknown"
            a_pub = p.agent.public_id if p.agent else str(p.agent_id)
            a_rep = p.agent.reputation_score if p.agent else 3.0
            proposals_list.append(
                ProposalResponse(
                    id=str(p.id),
                    proposal_id=p.proposal_id,
                    agent_id=a_pub,
                    agent_name=a_name,
                    agent_reputation=a_rep,
                    proposed_strategy=p.proposed_strategy,
                    estimated_duration_seconds=p.estimated_duration_seconds,
                    bid_score=p.bid_score,
                    status=p.status,
                    created_at=p.created_at,
                )
            )

        # Sort proposals by bid_score descending (best ranked first)
        proposals_list.sort(key=lambda x: x.bid_score, reverse=True)

        return JobResponse(
            id=str(job.id),
            job_id=job.job_id,
            title=job.title,
            description=job.description,
            requirements=job.requirements or [],
            bounty_reward=job.bounty_reward,
            status=job.status,
            creator_id=str(job.creator_id),
            task_id=job.task.task_id if job.task else (str(job.task_id) if job.task_id else None),
            accepted_proposal_id=str(job.accepted_proposal_id) if job.accepted_proposal_id else None,
            proposals_count=len(proposals_list),
            proposals=proposals_list,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    @classmethod
    def to_summary_response(cls, job: JobPosting) -> JobSummaryResponse:
        """Format JobPosting into JobSummaryResponse."""
        return JobSummaryResponse(
            id=str(job.id),
            job_id=job.job_id,
            title=job.title,
            requirements=job.requirements or [],
            bounty_reward=job.bounty_reward,
            status=job.status,
            proposals_count=len(job.proposals or []),
            created_at=job.created_at,
        )
