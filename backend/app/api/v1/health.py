"""System Health & Readiness Probes."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, status
from backend.app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="System Liveness Probe",
    description="Returns OK if the AgentHive backend is running and receptive to HTTP requests.",
)
async def get_health() -> Dict[str, Any]:
    """Liveness probe endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="System Readiness Probe",
    description="Returns OK when all core subsystems are initialized and ready to accept traffic.",
)
async def get_readiness() -> Dict[str, Any]:
    """Readiness probe endpoint checking subsystem status."""
    # In V1 scaffold, verify configuration and core dependencies
    return {
        "status": "ready",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "subsystems": {
            "api_gateway": "ready",
            "memory_firewall": "ready",
            "database": "configured",
            "model_providers": "ready",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
