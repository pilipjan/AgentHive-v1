"""AgentHive API v1 Router Configuration."""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.security import router as security_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.messages import router as messages_router
from backend.app.api.v1.knowledge import router as knowledge_router
from backend.app.api.v1.tasks import router as tasks_router
from backend.app.api.v1.hives import router as hives_router
from backend.app.api.v1.reputation import router as reputation_router
from backend.app.api.v1.websocket import router as websocket_router
from backend.app.api.v1.marketplace import router as marketplace_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.escrow import router as escrow_router
from backend.app.api.v1.mesh import router as mesh_router

api_v1_router = APIRouter()

# Register subrouters
api_v1_router.include_router(health_router, tags=["System Health"])
api_v1_router.include_router(security_router, tags=["Security & Audit"])
api_v1_router.include_router(agents_router, prefix="/agents", tags=["Agent Registry"])
api_v1_router.include_router(messages_router, prefix="/messages", tags=["Controlled Messaging"])
api_v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["Shared Knowledge"])
api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Task Orchestration"])
api_v1_router.include_router(hives_router, prefix="/hives", tags=["Hive Collaboration"])
api_v1_router.include_router(reputation_router, tags=["Multi-Factor Reputation & Reviews"])
api_v1_router.include_router(websocket_router, tags=["Real-Time WebSockets"])
api_v1_router.include_router(marketplace_router, prefix="/marketplace", tags=["Agent Marketplace & Bounties"])
api_v1_router.include_router(search_router, prefix="/search", tags=["Semantic Search"])
api_v1_router.include_router(escrow_router, prefix="/escrow", tags=["Token Escrow Economics"])
api_v1_router.include_router(mesh_router, prefix="/mesh", tags=["Autonomous Peer Discovery Mesh"])
