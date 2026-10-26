"""Mission events and checkpoint persistence models."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class MissionEventModel(Base):
    """Append-only audit event record for mission timeline and replay."""

    __tablename__ = "mission_events"
    __table_args__ = (
        Index("idx_events_seq", "sequence_number", unique=True),
        Index("idx_events_simtime", "sim_timestamp"),
    )

    event_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    satellite_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class SimulationCheckpointModel(Base):
    """Simulation state snapshot for rewind, replay, and recovery."""

    __tablename__ = "simulation_checkpoints"

    checkpoint_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    mission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("missions.mission_id", ondelete="CASCADE"),
        nullable=False,
    )
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Relationship
    mission: Mapped["MissionModel"] = relationship(  # noqa: F821
        "MissionModel",
        back_populates="checkpoints",
    )
