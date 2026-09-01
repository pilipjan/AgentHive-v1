"""Hive Collaboration Clusters API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.task import (
    HiveCreateRequest,
    HiveListResponse,
    HiveResponse,
)
from backend.app.services.hive_service import HiveService

router = APIRouter()


@router.post(
    "",
    response_model=HiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assemble a Hive",
    description="Manually creates a multi-agent Hive collaboration cluster.",
)
async def create_hive(
    payload: HiveCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> HiveResponse:
    """Create Hive cluster."""
    hive = await HiveService.create_hive(session=db, request=payload)
    loaded = await HiveService.get_hive(session=db, identifier=str(hive.id))
    return HiveService.to_hive_response(loaded or hive)


@router.get(
    "",
    response_model=HiveListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Active & Historical Hives",
    description="Retrieve list of all collaboration hives.",
)
async def list_hives(
    status: Optional[str] = Query(None, description="Filter by Hive status (ACTIVE, DISBANDED)"),
    limit: int = Query(50, ge=1, le=200, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> HiveListResponse:
    """Query hives."""
    total, hives = await HiveService.list_hives(
        session=db,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    items = [HiveService.to_hive_response(h) for h in hives]
    return HiveListResponse(total=total, items=items)


@router.get(
    "/{id}",
    response_model=HiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hive Details",
    description="Retrieve Hive roster, lead agent, and active assignments.",
)
async def get_hive(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> HiveResponse:
    """Fetch Hive details."""
    hive = await HiveService.get_hive(session=db, identifier=id)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hive with identifier '{id}' not found.",
        )
    return HiveService.to_hive_response(hive)


@router.post(
    "/{id}/disband",
    response_model=HiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Disband Hive",
    description="Disbands an active Hive collaboration cluster.",
)
async def disband_hive(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> HiveResponse:
    """Disband Hive."""
    hive = await HiveService.get_hive(session=db, identifier=id)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hive with identifier '{id}' not found.",
        )
    disbanded = await HiveService.disband_hive(session=db, hive=hive)
    return HiveService.to_hive_response(disbanded)
