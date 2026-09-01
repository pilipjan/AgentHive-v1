"""Controlled Agent Messaging API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.message import (
    MessageListResponse,
    MessageResponse,
    MessageSendRequest,
)
from backend.app.services.message_service import MessageService

router = APIRouter()


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send Controlled Agent Message",
    description="Transmits an agent-to-agent message strictly through the Memory Firewall and permission pipeline.",
)
async def send_message(
    payload: MessageSendRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Submit a message for Memory Firewall inspection and transmission."""
    message = await MessageService.send_message(session=db, request=payload)
    # Refresh to load sender/recipient relationships
    total, msgs = await MessageService.list_messages(session=db, agent_id=payload.sender_agent_id, limit=1)
    # Return formatted response
    return MessageService.to_message_response(message)


@router.get(
    "",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Agent Messages",
    description="Retrieve filtered message history by Task, Hive, or Agent identifier.",
)
async def list_messages(
    task_id: Optional[str] = Query(None, description="Filter by Task ID"),
    hive_id: Optional[str] = Query(None, description="Filter by Hive ID"),
    agent_id: Optional[str] = Query(None, description="Filter by Agent ID"),
    limit: int = Query(50, ge=1, le=200, description="Max messages to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """Query message logs."""
    total, messages = await MessageService.list_messages(
        session=db,
        task_id=task_id,
        hive_id=hive_id,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
    items = [MessageService.to_message_response(m) for m in messages]
    return MessageListResponse(total=total, items=items)
