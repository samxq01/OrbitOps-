"""OrbitOps Backend FastAPI Application Entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("orbitops.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup and shutdown lifecycle events."""
    logger.info(
        "Starting %s (v%s) in [%s] mode (simulation_mode=%s)",
        settings.app_name,
        settings.app_version,
        settings.env,
        settings.simulation_mode,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Authoritative backend service for the OrbitOps "
        "Satellite Mission Control & Digital Twin Simulator."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# API Versioning: Mount V1 router under /api/v1
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Root endpoint providing service metadata and discovery link."""
    return {
        "service": "orbitops-api",
        "description": "OrbitOps Satellite Mission Control API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/api/v1/health",
        "simulation_mode": settings.simulation_mode,
    }
