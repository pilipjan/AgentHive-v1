"""Message Service Layer for mediated agent-to-agent communication."""

import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Agent, Hive, Message, Task
from backend.app.schemas.message import MessageResponse, MessageSendRequest
from backend.app.services.agent_service import AgentService
from backend.app.core.websocket import event_broadcaster
from security.audit.auditor import AuditService
from security.firewall.pipeline import MemoryFirewall
from security.permissions.enums import PolicyVerdict


class MessageService:
    """Business logic for Controlled Agent Messaging through the Memory Firewall."""

    @classmethod
    async def send_message(
        cls,
        session: AsyncSession,
        request: MessageSendRequest,
    ) -> Message:
        """Process and transmit a message through the Memory Firewall."""
        # 1. Fetch and validate sender
        sender = await AgentService.get_agent_by_id_or_slug(session, request.sender_agent_id)
        if not sender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sender agent '{request.sender_agent_id}' not found.",
            )
        if sender.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sender agent '{sender.public_id}' is {sender.status} and cannot send messages.",
            )

        # 2. Fetch and validate recipient (if direct)
        recipient = None
        if request.recipient_agent_id:
            recipient = await AgentService.get_agent_by_id_or_slug(session, request.recipient_agent_id)
            if not recipient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recipient agent '{request.recipient_agent_id}' not found.",
                )
            if recipient.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Recipient agent '{recipient.public_id}' is {recipient.status}.",
                )

        # 3. Optional task / hive resolution
        task_id_uuid = None
        if request.task_id:
            task_res = await session.execute(
                select(Task).where(or_(Task.task_id == request.task_id, Task.id == request.task_id if cls._is_uuid(request.task_id) else False))
            )
            task = task_res.scalar_one_or_none()
            if task:
                task_id_uuid = task.id

        hive_id_uuid = None
        if request.hive_id:
            hive_res = await session.execute(
                select(Hive).where(or_(Hive.public_id == request.hive_id, Hive.id == request.hive_id if cls._is_uuid(request.hive_id) else False))
            )
            hive = hive_res.scalar_one_or_none()
            if hive:
                hive_id_uuid = hive.id

        # 4. Extract sender permissions
        sender_perms = [p.permission_name for p in (sender.permissions or [])]

        # 5. Process through Memory Firewall
        firewall_res = MemoryFirewall.process_message(
            content=request.content,
            sender_id=sender.public_id,
            sender_permissions=sender_perms,
            is_same_hive=True,
        )

        # 6. If blocked, audit and reject
        if firewall_res.verdict == PolicyVerdict.BLOCKED:
            await AuditService.record_event(
                session=session,
                actor_type="AGENT",
                actor_id=sender.public_id,
                action="MESSAGE_BLOCKED",
                target_type="AGENT",
                target_id=recipient.public_id if recipient else "BROADCAST",
                status="BLOCKED",
                details={
                    "reason": firewall_res.rejection_reason,
                    "detected_secrets": firewall_res.detected_secrets,
                    "detected_pii": firewall_res.detected_pii,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Memory Firewall rejected message: {firewall_res.rejection_reason}",
            )

        # 7. Create and persist sanitized Message
        msg_id_str = f"msg-{uuid.uuid4().hex[:10]}"
        message = Message(
            message_id=msg_id_str,
            sender_agent_id=sender.id,
            recipient_agent_id=recipient.id if recipient else None,
            task_id=task_id_uuid,
            hive_id=hive_id_uuid,
            message_type=request.message_type.upper(),
            content=firewall_res.sanitized_text,
            raw_content_hash=firewall_res.original_text_hash,
            sensitivity=firewall_res.sensitivity.value,
            authorization_result=firewall_res.verdict.value,
            extra_metadata=request.metadata,
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)

        # 8. Record audit log
        await AuditService.record_event(
            session=session,
            actor_type="AGENT",
            actor_id=sender.public_id,
            action="MESSAGE_SENT",
            target_type="MESSAGE",
            target_id=message.message_id,
            status=firewall_res.verdict.value,
            details={
                "recipient": recipient.public_id if recipient else "BROADCAST",
                "sensitivity": firewall_res.sensitivity.value,
                "sanitized": firewall_res.verdict == PolicyVerdict.REDACTED,
            },
        )

        # 9. Broadcast live WebSocket event
        await event_broadcaster.broadcast(
            "AGENT_MESSAGE_SENT",
            {
                "message_id": message.message_id,
                "sender_id": sender.public_id,
                "sender_name": sender.name,
                "recipient_id": recipient.public_id if recipient else None,
                "content_preview": message.content[:120],
                "verdict": firewall_res.verdict.value,
            },
            topic="global",
        )

        return message

    @classmethod
    async def list_messages(
        cls,
        session: AsyncSession,
        task_id: Optional[str] = None,
        hive_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Message]]:
        """Query messages with filtering and pagination."""
        query = (
            select(Message)
            .options(
                selectinload(Message.sender_agent),
                selectinload(Message.recipient_agent),
            )
        )
        count_query = select(func.count()).select_from(Message)

        if task_id:
            task_res = await session.execute(
                select(Task.id).where(or_(Task.task_id == task_id, Task.id == task_id if cls._is_uuid(task_id) else False))
            )
            t_uuid = task_res.scalar_one_or_none()
            if t_uuid:
                query = query.where(Message.task_id == t_uuid)
                count_query = count_query.where(Message.task_id == t_uuid)

        if hive_id:
            hive_res = await session.execute(
                select(Hive.id).where(or_(Hive.public_id == hive_id, Hive.id == hive_id if cls._is_uuid(hive_id) else False))
            )
            h_uuid = hive_res.scalar_one_or_none()
            if h_uuid:
                query = query.where(Message.hive_id == h_uuid)
                count_query = count_query.where(Message.hive_id == h_uuid)

        if agent_id:
            agent_res = await session.execute(
                select(Agent.id).where(or_(Agent.public_id == agent_id, Agent.id == agent_id if cls._is_uuid(agent_id) else False))
            )
            a_uuid = agent_res.scalar_one_or_none()
            if a_uuid:
                cond = or_(Message.sender_agent_id == a_uuid, Message.recipient_agent_id == a_uuid)
                query = query.where(cond)
                count_query = count_query.where(cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(Message.created_at.asc()).limit(limit).offset(offset)
        result = await session.execute(query)
        messages = list(result.scalars().all())

        return total, messages

    @classmethod
    def to_message_response(cls, msg: Message) -> MessageResponse:
        """Format Message entity to MessageResponse."""
        sender_name = msg.sender_agent.name if msg.sender_agent else "Unknown"
        sender_pub = msg.sender_agent.public_id if msg.sender_agent else str(msg.sender_agent_id)
        
        recipient_name = msg.recipient_agent.name if msg.recipient_agent else None
        recipient_pub = msg.recipient_agent.public_id if msg.recipient_agent else (str(msg.recipient_agent_id) if msg.recipient_agent_id else None)

        return MessageResponse(
            id=str(msg.id),
            message_id=msg.message_id,
            sender_agent_id=sender_pub,
            sender_agent_name=sender_name,
            recipient_agent_id=recipient_pub,
            recipient_agent_name=recipient_name,
            task_id=str(msg.task_id) if msg.task_id else None,
            hive_id=str(msg.hive_id) if msg.hive_id else None,
            message_type=msg.message_type,
            content=msg.content,
            sensitivity=msg.sensitivity,
            authorization_result=msg.authorization_result,
            metadata=msg.extra_metadata or {},
            created_at=msg.created_at,
        )

    @staticmethod
    def _is_uuid(val: str) -> bool:
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False
