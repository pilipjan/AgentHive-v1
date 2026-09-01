"""AgentHive API v1 Router Configuration."""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.security import router as security_router
from backend.app.api.v1.agents import router as agents_router

api_v1_router = APIRouter()

# Register subrouters
api_v1_router.include_router(health_router, tags=["System Health"])
api_v1_router.include_router(security_router, tags=["Security & Audit"])
api_v1_router.include_router(agents_router, prefix="/agents", tags=["Agent Registry"])
