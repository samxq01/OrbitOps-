"""Mission persistence model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class MissionModel(Base):
    """Mission operational session."""

    __tablename__ = "missions"

    mission_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    time_warp_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Relationships
    satellites: Mapped[list["SatelliteModel"]] = relationship(  # noqa: F821
        "SatelliteModel",
        back_populates="mission",
        cascade="all, delete-orphan",
    )
    checkpoints: Mapped[list["SimulationCheckpointModel"]] = relationship(  # noqa: F821
        "SimulationCheckpointModel",
        back_populates="mission",
        cascade="all, delete-orphan",
    )
