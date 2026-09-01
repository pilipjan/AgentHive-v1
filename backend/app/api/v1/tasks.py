"""Task & Multi-Agent Orchestration API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
)
from backend.app.services.task_service import TaskService
from orchestration.state_machine import TaskState

router = APIRouter()


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Task & Trigger Orchestration",
    description="Submits a new task, analyzes prerequisites, matches suitable agents, forms a Hive, and executes orchestration.",
)
async def create_task(
    payload: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Submit task and run orchestration."""
    task = await TaskService.create_task(session=db, request=payload)
    loaded = await TaskService.get_task(session=db, task_id=str(task.id))
    return TaskService.to_task_response(loaded or task)


@router.get(
    "",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List & Filter Tasks",
    description="List tasks filtered by lifecycle state or search keywords.",
)
async def list_tasks(
    status: Optional[TaskState] = Query(None, description="Filter by task lifecycle state"),
    search: Optional[str] = Query(None, description="Keyword search in title or description"),
    limit: int = Query(50, ge=1, le=200, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Query tasks."""
    total, tasks = await TaskService.list_tasks(
        session=db,
        status_filter=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    items = [TaskService.to_summary_response(t) for t in tasks]
    return TaskListResponse(total=total, items=items)


@router.get(
    "/{id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Task Details & Execution State",
    description="Retrieve task details, assigned agents, subtask execution outputs, and review evaluations.",
)
async def get_task(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Fetch task details."""
    task = await TaskService.get_task(session=db, task_id=id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with identifier '{id}' not found.",
        )
    return TaskService.to_task_response(task)


@router.post(
    "/{id}/cancel",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Emergency Cancel Task (Human Oversight)",
    description="Instantly cancels an in-flight task.",
)
async def cancel_task(
    id: str,
    reason: str = Query("Operator manual cancellation", description="Reason for cancellation"),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Emergency task cancellation."""
    task = await TaskService.get_task(session=db, task_id=id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with identifier '{id}' not found.",
        )
    cancelled = await TaskService.cancel_task(session=db, task=task, reason=reason)
    return TaskService.to_task_response(cancelled)
