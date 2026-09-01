"""Security & Audit API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.audit import AuditLog
from backend.app.schemas.security import (
    AuditLogItem,
    AuditLogQueryResponse,
    SecurityInspectRequest,
    SecurityInspectResponse,
)
from security.firewall.pipeline import MemoryFirewall

router = APIRouter()


@router.post(
    "/security/inspect",
    response_model=SecurityInspectResponse,
    status_code=status.HTTP_200_OK,
    summary="Memory Firewall Dry-Run Inspection",
    description="Inspects candidate text content against Secret Scanner, PII Filter, and Permission rules.",
)
async def inspect_payload(payload: SecurityInspectRequest) -> SecurityInspectResponse:
    """Dry-run inspection of text content against the Memory Firewall."""
    result = MemoryFirewall.process_message(
        content=payload.content,
        sender_id=payload.sender_id,
        sender_permissions=payload.permissions,
        is_same_hive=payload.is_same_hive,
    )
    return SecurityInspectResponse(
        verdict=result.verdict,
        original_text_hash=result.original_text_hash,
        sanitized_text=result.sanitized_text,
        sensitivity=result.sensitivity,
        detected_secrets=result.detected_secrets,
        detected_pii=result.detected_pii,
        rejection_reason=result.rejection_reason,
    )


@router.get(
    "/audit",
    response_model=AuditLogQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Sanitized Audit Logs",
    description="Returns filtered and paginated list of security and system audit logs.",
)
async def query_audit_logs(
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    action: Optional[str] = Query(None, description="Filter by action verb"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> AuditLogQueryResponse:
    """Query audit logs with optional filtering."""
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
        count_query = count_query.where(AuditLog.actor_id == actor_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if status:
        query = query.where(AuditLog.status == status)
        count_query = count_query.where(AuditLog.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    items = result.scalars().all()

    formatted_items = [
        AuditLogItem(
            id=str(item.id),
            timestamp=item.timestamp,
            actor_type=item.actor_type,
            actor_id=item.actor_id,
            action=item.action,
            target_type=item.target_type,
            target_id=item.target_id,
            status=item.status,
            details=item.details,
            ip_address=item.ip_address,
        )
        for item in items
    ]

    return AuditLogQueryResponse(total=total, items=formatted_items)
