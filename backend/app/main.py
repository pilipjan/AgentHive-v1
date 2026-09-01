"""AgentHive Core Backend Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.health import router as root_health_router
from backend.app.core.config import settings
from backend.app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle context manager."""
    logger.info("Initializing AgentHive Backend v%s in %s mode...", settings.APP_VERSION, settings.ENVIRONMENT)
    # Subsystem startup hooks can be initialized here
    yield
    logger.info("Shutting down AgentHive Backend...")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="AgentHive Core API",
        description="The Collaborative Infrastructure Platform for AI Agents",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root probes for direct load-balancer / orchestrator access
    app.include_router(root_health_router, tags=["System Probes"])

    # API v1 routes
    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
