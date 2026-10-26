"""Health response schema."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class HealthResponse(BaseModel):
    """Structured health response for OrbitOps API."""

    service: str = Field(default="orbitops-api", description="Service identifier")
    status: str = Field(default="healthy", description="Operational health status")
    version: str = Field(default="0.1.0", description="API version")
    environment: str = Field(default="development", description="Deployment environment")
    simulation_mode: bool = Field(
        default=True,
        description="Explicitly indicates that all operations and telemetry are simulated",
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Current server UTC timestamp",
    )
