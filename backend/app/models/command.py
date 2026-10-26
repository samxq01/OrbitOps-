"""Satellite telecommand persistence model."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class SatelliteCommandModel(Base):
    """Operator telecommand submitted to the verification and execution pipeline."""

    __tablename__ = "satellite_commands"
    __table_args__ = (Index("idx_commands_sat_status", "satellite_id", "status"),)

    command_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"CMD-{uuid.uuid4().hex[:8].upper()}",
    )
    satellite_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="CASCADE"),
        nullable=False,
    )
    command_mnemonic: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    rejection_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(50), nullable=False, default="operator")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    satellite: Mapped["SatelliteModel"] = relationship(  # noqa: F821
        "SatelliteModel",
        back_populates="commands",
    )
