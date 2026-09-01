"""Knowledge Service Layer for shared memory, visibility isolation, and Bayesian peer verification."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Agent, Knowledge, KnowledgeVerification, Task
from backend.app.schemas.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeResponse,
    KnowledgeSummaryResponse,
    KnowledgeVerificationRequest,
    VerificationRecordResponse,
)
from backend.app.services.agent_service import AgentService
from backend.app.core.websocket import event_broadcaster
from security.audit.auditor import AuditService
from security.firewall.pipeline import MemoryFirewall
from security.permissions.authorizer import PermissionAuthorizer
from security.permissions.enums import PolicyVerdict, VisibilityScope


class KnowledgeService:
    """Business logic for the permission-controlled Knowledge system and peer verification ledger."""

    @classmethod
    async def publish_knowledge(
        cls,
        session: AsyncSession,
        request: KnowledgeCreateRequest,
    ) -> Knowledge:
        """Process candidate knowledge through Memory Firewall and store in target visibility tier."""
        # 1. Fetch source agent
        agent = await AgentService.get_agent_by_id_or_slug(session, request.source_agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source agent '{request.source_agent_id}' not found.",
            )
        if agent.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Agent '{agent.public_id}' is {agent.status} and cannot publish knowledge.",
            )

        # 2. Extract agent permissions
        agent_perms = [p.permission_name for p in (agent.permissions or [])]

        # 3. Process via Memory Firewall
        firewall_res = MemoryFirewall.process_knowledge(
            content=request.content,
            summary=request.summary,
            source_agent_id=agent.public_id,
            source_permissions=agent_perms,
            target_visibility=request.visibility,
        )

        if firewall_res.verdict == PolicyVerdict.BLOCKED:
            await AuditService.record_event(
                session=session,
                actor_type="AGENT",
                actor_id=agent.public_id,
                action="KNOWLEDGE_BLOCKED",
                target_type="KNOWLEDGE",
                target_id="PROPOSED_ENTRY",
                status="BLOCKED",
                details={"reason": firewall_res.rejection_reason},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Memory Firewall rejected knowledge: {firewall_res.rejection_reason}",
            )

        # 4. Resolve optional task ID
        task_id_uuid = None
        if request.task_id:
            task_res = await session.execute(
                select(Task.id).where(or_(Task.task_id == request.task_id, Task.id == request.task_id if cls._is_uuid(request.task_id) else False))
            )
            task_id_uuid = task_res.scalar_one_or_none()

        # 5. Clean tags
        clean_tags = list({t.strip().lower() for t in request.tags if t.strip()})

        # 6. Create Knowledge entry
        knowledge = Knowledge(
            summary=request.summary.strip(),
            content=firewall_res.sanitized_text,
            source_agent_id=agent.id,
            task_id=task_id_uuid,
            confidence=0.50,
            verification_count=0,
            success_count=0,
            failure_count=0,
            visibility=request.visibility.value,
            sensitivity=firewall_res.sensitivity.value,
            tags=clean_tags,
        )
        session.add(knowledge)
        await session.commit()
        await session.refresh(knowledge)

        # 7. Record Audit Log
        await AuditService.record_event(
            session=session,
            actor_type="AGENT",
            actor_id=agent.public_id,
            action="KNOWLEDGE_PUBLISHED",
            target_type="KNOWLEDGE",
            target_id=str(knowledge.id),
            status=firewall_res.verdict.value,
            details={
                "summary": knowledge.summary,
                "visibility": knowledge.visibility,
                "sanitized": firewall_res.verdict == PolicyVerdict.REDACTED,
            },
        )

        # 8. Broadcast live event
        await event_broadcaster.broadcast(
            "KNOWLEDGE_PUBLISHED",
            {
                "knowledge_id": str(knowledge.id),
                "summary": knowledge.summary,
                "author": agent.name,
                "visibility": knowledge.visibility,
                "confidence": knowledge.confidence,
            },
            topic="global",
        )

        return knowledge

    @classmethod
    async def verify_knowledge(
        cls,
        session: AsyncSession,
        knowledge_id: str,
        request: KnowledgeVerificationRequest,
    ) -> Tuple[Knowledge, KnowledgeVerification]:
        """Submit an evidence-backed verification verdict and update Bayesian confidence score."""
        # 1. Fetch Knowledge entry
        k_uuid = uuid.UUID(knowledge_id) if cls._is_uuid(knowledge_id) else None
        if not k_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid knowledge UUID format.")

        result = await session.execute(
            select(Knowledge)
            .options(
                selectinload(Knowledge.verifications).selectinload(KnowledgeVerification.verifying_agent),
                selectinload(Knowledge.source_agent),
            )
            .where(Knowledge.id == k_uuid)
        )
        knowledge = result.scalar_one_or_none()
        if not knowledge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Knowledge record '{knowledge_id}' not found.")

        # 2. Fetch and check Verifying Agent
        verifier = await AgentService.get_agent_by_id_or_slug(session, request.verifying_agent_id)
        if not verifier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Verifying agent '{request.verifying_agent_id}' not found.")
        if verifier.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Verifier agent '{verifier.public_id}' is {verifier.status}.")

        # 3. Check authorization & minimum reputation threshold (3.50)
        verifier_perms = [p.permission_name for p in (verifier.permissions or [])]
        if not PermissionAuthorizer.can_verify_knowledge(verifier_perms, verifier.reputation_score):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Agent '{verifier.public_id}' lacks verification permission or minimum reputation threshold (3.50).",
            )

        # 4. Normalize verdict
        verdict_clean = request.verdict.strip().upper()
        if verdict_clean not in ("VERIFIED", "REFUTED", "INCONCLUSIVE"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Verdict must be 'VERIFIED', 'REFUTED', or 'INCONCLUSIVE'.",
            )

        # 5. Create Verification record
        verification = KnowledgeVerification(
            knowledge_id=knowledge.id,
            verifying_agent_id=verifier.id,
            verdict=verdict_clean,
            evidence=request.evidence,
        )
        session.add(verification)
        await session.commit()
        await session.refresh(verification)

        # 6. Re-query all verifications and re-compute dynamic Bayesian confidence
        all_verifs = await session.execute(
            select(KnowledgeVerification).where(KnowledgeVerification.knowledge_id == knowledge.id)
        )
        verif_list = list(all_verifs.scalars().all())

        n_v = sum(1 for v in verif_list if v.verdict == "VERIFIED")
        n_r = sum(1 for v in verif_list if v.verdict == "REFUTED")
        n_inc = sum(1 for v in verif_list if v.verdict == "INCONCLUSIVE")

        # Bayesian confidence formula with Laplace prior (alpha=1, beta=1 -> prior 0.50)
        new_confidence = (n_v + 0.5 * n_inc + 1.0) / (n_v + n_r + n_inc + 2.0)

        knowledge.confidence = round(new_confidence, 4)
        knowledge.verification_count = len(verif_list)
        knowledge.last_verified_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(knowledge)

        # 7. Audit Log
        await AuditService.record_event(
            session=session,
            actor_type="AGENT",
            actor_id=verifier.public_id,
            action="KNOWLEDGE_VERIFIED",
            target_type="KNOWLEDGE",
            target_id=str(knowledge.id),
            status="SUCCESS",
            details={"verdict": verdict_clean, "new_confidence": knowledge.confidence},
        )

        # 8. Broadcast live event
        await event_broadcaster.broadcast(
            "KNOWLEDGE_VERIFIED",
            {
                "knowledge_id": str(knowledge.id),
                "summary": knowledge.summary,
                "verifier": verifier.name,
                "verdict": verdict_clean,
                "new_confidence": knowledge.confidence,
            },
            topic="global",
        )

        return knowledge, verification

    @classmethod
    async def get_knowledge(cls, session: AsyncSession, knowledge_id: str) -> Optional[Knowledge]:
        """Fetch knowledge record with verifications loaded."""
        if not cls._is_uuid(knowledge_id):
            return None

        result = await session.execute(
            select(Knowledge)
            .options(
                selectinload(Knowledge.source_agent),
                selectinload(Knowledge.verifications).selectinload(KnowledgeVerification.verifying_agent),
            )
            .where(Knowledge.id == uuid.UUID(knowledge_id))
        )
        return result.scalar_one_or_none()

    @classmethod
    async def list_knowledge(
        cls,
        session: AsyncSession,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        visibility: Optional[VisibilityScope] = None,
        min_confidence: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Knowledge]]:
        """Search and list knowledge entries."""
        db_query = select(Knowledge).options(selectinload(Knowledge.source_agent))
        count_query = select(func.count()).select_from(Knowledge)

        if visibility:
            db_query = db_query.where(Knowledge.visibility == visibility.value)
            count_query = count_query.where(Knowledge.visibility == visibility.value)

        if min_confidence is not None:
            db_query = db_query.where(Knowledge.confidence >= min_confidence)
            count_query = count_query.where(Knowledge.confidence >= min_confidence)

        if query:
            pattern = f"%{query.strip()}%"
            cond = or_(Knowledge.summary.ilike(pattern), Knowledge.content.ilike(pattern))
            db_query = db_query.where(cond)
            count_query = count_query.where(cond)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one()

        db_query = db_query.order_by(Knowledge.confidence.desc(), Knowledge.verification_count.desc()).limit(limit).offset(offset)
        result = await session.execute(db_query)
        entries = list(result.scalars().all())

        if tag:
            clean_tag = tag.strip().lower()
            entries = [e for e in entries if clean_tag in [t.lower() for t in (e.tags or [])]]
            total = len(entries)

        return total, entries

    @classmethod
    def to_knowledge_response(cls, k: Knowledge) -> KnowledgeResponse:
        """Format Knowledge entity into rich KnowledgeResponse."""
        source_name = k.source_agent.name if k.source_agent else "Unknown"
        source_pub = k.source_agent.public_id if k.source_agent else str(k.source_agent_id)

        verif_records: List[VerificationRecordResponse] = []
        distribution: Dict[str, int] = {"VERIFIED": 0, "REFUTED": 0, "INCONCLUSIVE": 0}

        for v in (k.verifications or []):
            v_agent_name = v.verifying_agent.name if v.verifying_agent else "Unknown"
            v_agent_pub = v.verifying_agent.public_id if v.verifying_agent else str(v.verifying_agent_id)
            if v.verdict in distribution:
                distribution[v.verdict] += 1
            verif_records.append(
                VerificationRecordResponse(
                    id=str(v.id),
                    verifying_agent_id=v_agent_pub,
                    verifying_agent_name=v_agent_name,
                    verdict=v.verdict,
                    evidence=v.evidence,
                    timestamp=v.timestamp,
                )
            )

        return KnowledgeResponse(
            id=str(k.id),
            summary=k.summary,
            content=k.content,
            source_agent_id=source_pub,
            source_agent_name=source_name,
            task_id=str(k.task_id) if k.task_id else None,
            confidence=k.confidence,
            verification_count=k.verification_count,
            success_count=k.success_count,
            failure_count=k.failure_count,
            visibility=VisibilityScope(k.visibility),
            sensitivity=k.sensitivity,
            tags=k.tags or [],
            verdict_distribution=distribution,
            verifications=verif_records,
            created_at=k.created_at,
            last_verified_at=k.last_verified_at,
        )

    @classmethod
    def to_summary_response(cls, k: Knowledge) -> KnowledgeSummaryResponse:
        """Format Knowledge entity into concise summary."""
        source_name = k.source_agent.name if k.source_agent else "Unknown"
        source_pub = k.source_agent.public_id if k.source_agent else str(k.source_agent_id)

        return KnowledgeSummaryResponse(
            id=str(k.id),
            summary=k.summary,
            source_agent_id=source_pub,
            source_agent_name=source_name,
            confidence=k.confidence,
            verification_count=k.verification_count,
            visibility=VisibilityScope(k.visibility),
            sensitivity=k.sensitivity,
            tags=k.tags or [],
            created_at=k.created_at,
        )

    @staticmethod
    def _is_uuid(val: str) -> bool:
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False
