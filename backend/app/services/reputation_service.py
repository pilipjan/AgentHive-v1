"""Reputation Service Layer for evaluations, mathematical scoring, and event ledgers."""

import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models import Agent, Evaluation, ReputationEvent, Task
from backend.app.schemas.reputation import (
    EvaluationCreateRequest,
    EvaluationResponse,
    ReputationDetailResponse,
    ReputationEventItem,
    ReputationHistoryResponse,
    ReputationMetricsResponse,
)
from backend.app.services.agent_service import AgentService
from reputation.engine import ReputationEngine
from reputation.metrics import AgentPerformanceMetrics, ReputationWeights
from security.audit.auditor import AuditService


class ReputationService:
    """Business logic for peer evaluations and reputation scoring."""

    @classmethod
    async def submit_evaluation(
        cls,
        session: AsyncSession,
        request: EvaluationCreateRequest,
    ) -> Evaluation:
        """Submit a peer agent evaluation, recompute reputation, and record an immutable event."""
        # 1. Resolve task
        task_res = await session.execute(
            select(Task).where(or_(Task.task_id == request.task_id, Task.id == request.task_id if cls._is_uuid(request.task_id) else False))
        )
        task = task_res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{request.task_id}' not found.")

        # 2. Resolve Reviewer
        reviewer = await AgentService.get_agent_by_id_or_slug(session, request.reviewer_agent_id)
        if not reviewer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reviewer agent '{request.reviewer_agent_id}' not found.")
        if reviewer.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Reviewer agent '{reviewer.public_id}' is {reviewer.status}.")

        # 3. Resolve Target Agent
        target = await AgentService.get_agent_by_id_or_slug(session, request.target_agent_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target agent '{request.target_agent_id}' not found.")

        # 4. Create Evaluation Record
        evaluation = Evaluation(
            task_id=task.id,
            reviewer_agent_id=reviewer.id,
            target_agent_id=target.id,
            task_success_score=request.task_success_score,
            usefulness_score=request.usefulness_score,
            accuracy_score=request.accuracy_score,
            reliability_score=request.reliability_score,
            safety_score=request.safety_score,
            comments=request.comments,
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)

        # 5. Re-compute target agent's composite metrics
        all_evals_res = await session.execute(
            select(Evaluation).where(Evaluation.target_agent_id == target.id)
        )
        evals = list(all_evals_res.scalars().all())

        count = len(evals)
        avg_success = sum(e.task_success_score for e in evals) / count if count else 1.0
        avg_usefulness = sum(e.usefulness_score for e in evals) / count if count else 1.0
        avg_accuracy = sum(e.accuracy_score for e in evals) / count if count else 1.0
        avg_reliability = sum(e.reliability_score for e in evals) / count if count else 1.0
        avg_safety = sum(e.safety_score for e in evals) / count if count else 1.0

        metrics = AgentPerformanceMetrics(
            task_success_rate=avg_success,
            reviewer_usefulness_score=avg_usefulness,
            verification_accuracy_score=avg_accuracy,
            reliability_score=avg_reliability,
            safety_compliance_score=avg_safety,
            total_evaluations_count=count,
            security_violations_count=0,
        )

        _, new_scale_5_score = ReputationEngine.calculate_reputation(metrics)
        old_score = target.reputation_score
        score_delta = round(new_scale_5_score - old_score, 2)

        target.reputation_score = new_scale_5_score
        await session.commit()

        # 6. Record Immutable Reputation Event
        event = ReputationEvent(
            agent_id=target.id,
            event_type="PEER_REVIEW",
            score_delta=score_delta,
            new_score=new_scale_5_score,
            reference_id=task.task_id,
            details={
                "reviewer": reviewer.public_id,
                "task": task.title,
                "task_success_score": request.task_success_score,
            },
        )
        session.add(event)
        await session.commit()

        # 7. Record Audit Log
        await AuditService.record_event(
            session=session,
            actor_type="AGENT",
            actor_id=reviewer.public_id,
            action="EVALUATION_SUBMITTED",
            target_type="AGENT",
            target_id=target.public_id,
            status="SUCCESS",
            details={"score_delta": score_delta, "new_score": new_scale_5_score},
        )

        return evaluation

    @classmethod
    async def get_agent_reputation(
        cls,
        session: AsyncSession,
        identifier: str,
    ) -> ReputationDetailResponse:
        """Fetch full reputation breakdown for an agent."""
        agent = await AgentService.get_agent_by_id_or_slug(session, identifier)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{identifier}' not found.")

        # Aggregate evaluations
        evals_res = await session.execute(
            select(Evaluation).where(Evaluation.target_agent_id == agent.id)
        )
        evals = list(evals_res.scalars().all())
        count = len(evals)

        task_success = (
            (agent.successful_tasks / agent.tasks_completed)
            if agent.tasks_completed > 0
            else 1.0
        )
        avg_usefulness = sum(e.usefulness_score for e in evals) / count if count else 1.0
        avg_accuracy = sum(e.accuracy_score for e in evals) / count if count else 1.0
        avg_reliability = sum(e.reliability_score for e in evals) / count if count else 1.0
        avg_safety = sum(e.safety_score for e in evals) / count if count else 1.0

        metrics_resp = ReputationMetricsResponse(
            task_success_rate=round(task_success, 3),
            reviewer_usefulness_score=round(avg_usefulness, 3),
            verification_accuracy=round(avg_accuracy, 3),
            reliability_score=round(avg_reliability, 3),
            safety_compliance_rate=round(avg_safety, 3),
            security_violations=0,
            evaluations_count=count,
        )

        return ReputationDetailResponse(
            agent_id=agent.public_id,
            agent_name=agent.name,
            composite_score=round(agent.reputation_score, 2),
            star_rating=ReputationEngine.compute_star_rating(agent.reputation_score),
            total_tasks_completed=agent.tasks_completed,
            successful_tasks=agent.successful_tasks,
            metrics=metrics_resp,
            weight_formula=ReputationEngine.DEFAULT_WEIGHTS.to_dict(),
            verification_eligible=agent.reputation_score >= 3.50,
        )

    @classmethod
    async def get_reputation_history(
        cls,
        session: AsyncSession,
        identifier: str,
        limit: int = 50,
    ) -> ReputationHistoryResponse:
        """Fetch chronological reputation events for an agent."""
        agent = await AgentService.get_agent_by_id_or_slug(session, identifier)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{identifier}' not found.")

        res = await session.execute(
            select(ReputationEvent)
            .where(ReputationEvent.agent_id == agent.id)
            .order_by(ReputationEvent.timestamp.desc())
            .limit(limit)
        )
        events = list(res.scalars().all())

        items = [
            ReputationEventItem(
                id=str(e.id),
                event_type=e.event_type,
                score_delta=e.score_delta,
                new_score=e.new_score,
                reference_id=e.reference_id,
                details=e.details or {},
                timestamp=e.timestamp,
            )
            for e in events
        ]

        return ReputationHistoryResponse(
            agent_id=agent.public_id,
            total_events=len(items),
            events=items,
        )

    @staticmethod
    def _is_uuid(val: str) -> bool:
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False
