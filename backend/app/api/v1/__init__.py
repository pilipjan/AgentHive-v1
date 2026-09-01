"""AgentHive API v1 Router Configuration."""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Register subrouters
api_v1_router.include_router(health_router, tags=["System Health"])
