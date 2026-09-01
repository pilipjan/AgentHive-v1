"""Integration tests for database models, relationships, and constraints."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import AsyncSessionLocal
from backend.app.models import (
    User,
    Agent,
    AgentPermission,
    Task,
    TaskAssignment,
    Hive,
    HiveMember,
    Message,
    Knowledge,
    KnowledgeVerification,
    Evaluation,
    ReputationEvent,
    AuditLog,
)


@pytest.mark.asyncio
async def test_complete_database_lifecycle():
    """Verify complete CRUD lifecycle across all 13 database entities."""
    async with AsyncSessionLocal() as session:
        # 1. Create User
        user = User(
            email=f"operator_{uuid.uuid4().hex[:8]}@agenthive.local",
            username=f"op_{uuid.uuid4().hex[:8]}",
            hashed_password="dummy_argon2_hash",
            role="OPERATOR",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None

        # 2. Create Agent
        agent = Agent(
            public_id=f"agt-py-{uuid.uuid4().hex[:8]}",
            name="PythonForge",
            description="Python & backend agent",
            owner_id=user.id,
            model_provider="OPENAI",
            model_name="gpt-4o-mini",
            capabilities=["python", "fastapi", "docker"],
            reputation_score=4.85,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        assert agent.id is not None
        assert "python" in agent.capabilities

        # 3. Add Agent Permission
        permission = AgentPermission(
            agent_id=agent.id,
            permission_name="READ_PUBLIC_KNOWLEDGE",
            granted_by="SYSTEM",
        )
        session.add(permission)
        await session.commit()

        # 4. Create Task
        task = Task(
            task_id=f"tsk-test-{uuid.uuid4().hex[:8]}",
            creator_id=user.id,
            title="Automate FFmpeg Processing",
            description="Optimize video encoding parameters for ARM Linux",
            requirements=["python", "ffmpeg", "linux"],
            status="CREATED",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        assert task.id is not None

        # 5. Assign Agent to Task
        assignment = TaskAssignment(
            task_id=task.id,
            agent_id=agent.id,
            role="LEAD",
            status="ASSIGNED",
        )
        session.add(assignment)
        await session.commit()

        # 6. Create Hive & Member
        hive = Hive(
            public_id=f"hive-{uuid.uuid4().hex[:8]}",
            name="Video Optimization Team",
            description="Specialized hive for ffmpeg encoding",
            lead_agent_id=agent.id,
            task_id=task.id,
            status="ACTIVE",
        )
        session.add(hive)
        await session.commit()
        await session.refresh(hive)

        hive_member = HiveMember(
            hive_id=hive.id,
            agent_id=agent.id,
            role_in_hive="LEAD",
        )
        session.add(hive_member)
        await session.commit()

        # 7. Create Controlled Message
        message = Message(
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            sender_agent_id=agent.id,
            recipient_agent_id=None,
            task_id=task.id,
            hive_id=hive.id,
            message_type="BROADCAST",
            content="FFmpeg benchmark initialized.",
            raw_content_hash="dummyhash12345",
            sensitivity="INTERNAL",
            authorization_result="ALLOWED",
        )
        session.add(message)
        await session.commit()

        # 8. Create Knowledge Entry
        knowledge = Knowledge(
            summary="V4L2 hardware acceleration benchmark",
            content="Enabled v4l2m2m hardware acceleration on ARM.",
            source_agent_id=agent.id,
            task_id=task.id,
            confidence=0.85,
            visibility="PUBLIC",
            tags=["ffmpeg", "arm64", "gpu"],
        )
        session.add(knowledge)
        await session.commit()
        await session.refresh(knowledge)

        # 9. Create Knowledge Verification
        verification = KnowledgeVerification(
            knowledge_id=knowledge.id,
            verifying_agent_id=agent.id,
            verdict="VERIFIED",
            evidence="Observed 40% CPU drop.",
        )
        session.add(verification)
        await session.commit()

        # 10. Create Evaluation
        evaluation = Evaluation(
            task_id=task.id,
            reviewer_agent_id=agent.id,
            target_agent_id=agent.id,
            task_success_score=0.98,
            usefulness_score=0.95,
            accuracy_score=0.99,
            reliability_score=0.97,
            safety_score=1.0,
            comments="Flawless task execution.",
        )
        session.add(evaluation)
        await session.commit()

        # 11. Create Reputation Event
        rep_event = ReputationEvent(
            agent_id=agent.id,
            event_type="TASK_SUCCESS",
            score_delta=0.05,
            new_score=4.90,
            reference_id=task.task_id,
            details={"task": task.title},
        )
        session.add(rep_event)
        await session.commit()

        # 12. Create Audit Log
        audit = AuditLog(
            actor_type="AGENT",
            actor_id=agent.public_id,
            action="KNOWLEDGE_PUBLISHED",
            target_type="KNOWLEDGE",
            target_id=str(knowledge.id),
            status="SUCCESS",
            details={"summary": knowledge.summary},
        )
        session.add(audit)
        await session.commit()

        # 13. Query and Verify
        result = await session.execute(
            select(Agent)
            .options(
                selectinload(Agent.permissions),
                selectinload(Agent.reputation_events),
            )
            .where(Agent.id == agent.id)
        )
        loaded_agent = result.scalar_one_or_none()
        assert loaded_agent is not None
        assert loaded_agent.name == "PythonForge"
        assert len(loaded_agent.permissions) == 1
        assert len(loaded_agent.reputation_events) == 1
