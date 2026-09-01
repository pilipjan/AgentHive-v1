"""Agent Registry API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.agent import (
    AgentCreateRequest,
    AgentListResponse,
    AgentPermissionGrantRequest,
    AgentPermissionResponse,
    AgentProfileResponse,
    AgentSummaryResponse,
    AgentUpdateRequest,
)
from backend.app.services.agent_service import AgentService

router = APIRouter()


@router.post(
    "",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a New Agent",
    description="Registers an agent with structured capabilities, model configs, and initial baseline permissions.",
)
async def register_agent(
    payload: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Create and register a new agent."""
    agent = await AgentService.create_agent(session=db, request=payload)
    loaded = await AgentService.get_agent_by_id_or_slug(session=db, identifier=str(agent.id))
    return AgentService.to_profile_response(loaded or agent)


@router.get(
    "",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List & Search Agents",
    description="Filter, search, and list registered agents by capabilities, status, or keyword.",
)
async def list_agents(
    search: Optional[str] = Query(None, description="Search term for name/description"),
    capability: Optional[str] = Query(None, description="Filter by declared capability"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, DISABLED)"),
    limit: int = Query(50, ge=1, le=200, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> AgentListResponse:
    """Query agents with filtering and search."""
    total, agents = await AgentService.list_agents(
        session=db,
        search=search,
        capability=capability,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    items = [AgentService.to_summary_response(a) for a in agents]
    return AgentListResponse(total=total, items=items)


@router.get(
    "/{id}",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Profile",
    description="Retrieve comprehensive agent profile with reputation breakdown and trust indicators.",
)
async def get_agent(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Fetch agent profile by UUID or public slug."""
    agent = await AgentService.get_agent_by_id_or_slug(session=db, identifier=id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{id}' not found.",
        )
    return AgentService.to_profile_response(agent)


@router.patch(
    "/{id}",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Agent",
    description="Update metadata, declared capabilities, or model parameters of an agent.",
)
async def update_agent(
    id: str,
    payload: AgentUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Update agent details."""
    agent = await AgentService.get_agent_by_id_or_slug(session=db, identifier=id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{id}' not found.",
        )
    updated = await AgentService.update_agent(session=db, agent=agent, request=payload)
    return AgentService.to_profile_response(updated)


@router.post(
    "/{id}/disable",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Emergency Disable Agent",
    description="Instantly disables an agent, aborting active assignments and preventing further communication.",
)
async def disable_agent(
    id: str,
    reason: str = Query("Operator manual disable", description="Reason for disabling"),
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Emergency disable of an agent."""
    agent = await AgentService.get_agent_by_id_or_slug(session=db, identifier=id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{id}' not found.",
        )
    disabled = await AgentService.disable_agent(session=db, agent=agent, reason=reason)
    return AgentService.to_profile_response(disabled)


@router.get(
    "/{id}/permissions",
    response_model=List[AgentPermissionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agent Permissions",
    description="Retrieve all atomic permissions granted to the agent.",
)
async def get_agent_permissions(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> List[AgentPermissionResponse]:
    """List granted permissions."""
    agent = await AgentService.get_agent_by_id_or_slug(session=db, identifier=id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{id}' not found.",
        )
    return [
        AgentPermissionResponse(
            id=str(p.id),
            permission_name=p.permission_name,
            granted_by=p.granted_by,
            granted_at=p.granted_at,
            expires_at=p.expires_at,
        )
        for p in (agent.permissions or [])
    ]


@router.post(
    "/{id}/permissions",
    response_model=AgentPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant Agent Permission",
    description="Explicitly grant an atomic permission to an agent.",
)
async def grant_agent_permission(
    id: str,
    payload: AgentPermissionGrantRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentPermissionResponse:
    """Grant an atomic permission."""
    agent = await AgentService.get_agent_by_id_or_slug(session=db, identifier=id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{id}' not found.",
        )
    perm = await AgentService.grant_permission(
        session=db,
        agent=agent,
        permission_name=payload.permission_name.value,
    )
    return AgentPermissionResponse(
        id=str(perm.id),
        permission_name=perm.permission_name,
        granted_by=perm.granted_by,
        granted_at=perm.granted_at,
        expires_at=perm.expires_at,
    )
