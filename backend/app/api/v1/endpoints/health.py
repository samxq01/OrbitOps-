"""Health endpoint implementation."""

from fastapi import APIRouter, status

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status, version, and simulation mode of the OrbitOps API.",
)
async def check_health() -> HealthResponse:
    """Retrieve current service health status."""
    return HealthResponse(
        service="orbitops-api",
        status="healthy",
        version=settings.app_version,
        environment=settings.env,
        simulation_mode=settings.simulation_mode,
    )
