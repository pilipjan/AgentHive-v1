"""Task Service Layer for Task lifecycle, queries, and Human Oversight controls."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Task, TaskAssignment, User
from backend.app.schemas.task import (
    TaskAssignmentResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
)
from backend.app.services.agent_service import AgentService
from orchestration.coordinator import OrchestrationCoordinator
from orchestration.state_machine import TaskState, TaskStateMachine
from security.audit.auditor import AuditService


class TaskService:
    """Business logic for Task lifecycle management and Human Oversight."""

    @classmethod
    async def create_task(
        cls,
        session: AsyncSession,
        request: TaskCreateRequest,
        creator_id: Optional[uuid.UUID] = None,
    ) -> Task:
        """Create a new Task and optionally trigger orchestration immediately."""
        if not creator_id:
            user = await AgentService.get_or_create_default_user(session)
            creator_id = user.id

        task_id = f"tsk-{uuid.uuid4().hex[:8]}"
        clean_reqs = list({r.strip().lower() for r in request.requirements if r.strip()})

        task = Task(
            task_id=task_id,
            creator_id=creator_id,
            title=request.title.strip(),
            description=request.description.strip(),
            requirements=clean_reqs,
            status=TaskState.CREATED.value,
            max_iterations=request.max_iterations,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        # Audit task creation
        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id=str(creator_id),
            action="TASK_CREATED",
            target_type="TASK",
            target_id=task.task_id,
            status="SUCCESS",
            details={"title": task.title, "requirements": clean_reqs},
        )

        # If auto_orchestrate enabled, run multi-agent coordinator
        if request.auto_orchestrate:
            task = await OrchestrationCoordinator.orchestrate_task(session, task)

        return task

    @classmethod
    async def get_task(cls, session: AsyncSession, task_id: str) -> Optional[Task]:
        """Fetch task by UUID or public task_id slug with eager loaded assignments."""
        query = (
            select(Task)
            .options(
                selectinload(Task.assignments).selectinload(TaskAssignment.agent),
                selectinload(Task.hive),
            )
        )
        try:
            val_uuid = uuid.UUID(task_id)
            query = query.where(or_(Task.id == val_uuid, Task.task_id == task_id))
        except ValueError:
            query = query.where(Task.task_id == task_id)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def list_tasks(
        cls,
        session: AsyncSession,
        status_filter: Optional[TaskState] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Task]]:
        """List tasks with status and keyword filters."""
        query = select(Task).options(selectinload(Task.assignments))
        count_query = select(func.count()).select_from(Task)

        if status_filter:
            query = query.where(Task.status == status_filter.value)
            count_query = count_query.where(Task.status == status_filter.value)

        if search:
            pat = f"%{search.strip()}%"
            cond = or_(Task.title.ilike(pat), Task.description.ilike(pat), Task.task_id.ilike(pat))
            query = query.where(cond)
            count_query = count_query.where(cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        tasks = list(result.scalars().all())

        return total, tasks

    @classmethod
    async def cancel_task(
        cls,
        session: AsyncSession,
        task: Task,
        reason: str = "Operator manual cancellation",
    ) -> Task:
        """Human Oversight: Instantly abort/cancel an in-flight task."""
        current = TaskState(task.status)
        if current in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task is already in terminal state '{task.status}' and cannot be cancelled.",
            )

        task.status = TaskState.CANCELLED.value
        task.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(task)

        await AuditService.record_event(
            session=session,
            actor_type="USER",
            actor_id="OPERATOR",
            action="TASK_CANCELLED",
            target_type="TASK",
            target_id=task.task_id,
            status="SUCCESS",
            details={"reason": reason},
        )
        return task

    @classmethod
    def to_task_response(cls, task: Task) -> TaskResponse:
        """Format Task entity to TaskResponse."""
        assigned = []
        for a in (task.assignments or []):
            agent_name = a.agent.name if a.agent else "Unknown"
            agent_pub = a.agent.public_id if a.agent else str(a.agent_id)
            assigned.append(
                TaskAssignmentResponse(
                    id=str(a.id),
                    agent_id=agent_pub,
                    agent_name=agent_name,
                    role=a.role,
                    status=a.status,
                    assigned_at=a.assigned_at,
                    completed_at=a.completed_at,
                )
            )

        hive_pub = task.hive.public_id if task.hive else None

        return TaskResponse(
            id=str(task.id),
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            requirements=task.requirements or [],
            status=TaskState(task.status),
            result=task.result,
            max_iterations=task.max_iterations,
            hive_id=hive_pub,
            assigned_agents=assigned,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

    @classmethod
    def to_summary_response(cls, task: Task) -> TaskSummaryResponse:
        """Format Task entity to TaskSummaryResponse."""
        return TaskSummaryResponse(
            id=str(task.id),
            task_id=task.task_id,
            title=task.title,
            status=TaskState(task.status),
            requirements=task.requirements or [],
            assigned_agent_count=len(task.assignments or []),
            created_at=task.created_at,
            completed_at=task.completed_at,
        )
