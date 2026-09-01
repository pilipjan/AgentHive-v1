"""Audit Service for recording sanitized, immutable platform events."""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditLog
from backend.app.core.logging import logger
from security.scanners.secret_scanner import SecretScanner


class AuditService:
    """Emits structured, sanitized audit log entries to the database."""

    @classmethod
    async def record_event(
        cls,
        session: AsyncSession,
        actor_type: str,
        actor_id: str,
        action: str,
        status: str = "SUCCESS",
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist an audit log entry, guaranteeing no raw secrets are stored."""
        clean_details = details or {}
        
        # Defense-in-depth: scrub any string values inside details dict
        sanitized_details = {}
        for k, v in clean_details.items():
            if isinstance(v, str):
                sanitized_details[k] = SecretScanner.sanitize(v)
            else:
                sanitized_details[k] = v

        audit_entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            status=status,
            details=sanitized_details,
            ip_address=ip_address,
        )

        session.add(audit_entry)
        await session.commit()
        await session.refresh(audit_entry)

        logger.info(
            "AUDIT | actor=%s:%s action=%s target=%s:%s status=%s",
            actor_type,
            actor_id,
            action,
            target_type,
            target_id,
            status,
        )

        return audit_entry
