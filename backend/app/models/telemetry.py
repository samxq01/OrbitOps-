"""Telemetry sample persistence model."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class TelemetrySampleModel(Base):
    """Telemetry sample snapshot recorded from digital twin."""

    __tablename__ = "telemetry_samples"
    __table_args__ = (
        CheckConstraint(
            "batt_soc >= 0.0 AND batt_soc <= 100.0",
            name="chk_telem_batt_soc_range",
        ),
        Index("idx_telem_sat_simtime", "satellite_id", "sim_timestamp"),
        Index("idx_telem_seq", "sequence_number"),
    )

    sample_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    satellite_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="CASCADE"),
        nullable=False,
    )
    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False)

    pwr_bus_v: Mapped[float] = mapped_column(Float, nullable=False)
    pwr_solar_w: Mapped[float] = mapped_column(Float, nullable=False)
    batt_soc: Mapped[float] = mapped_column(Float, nullable=False)
    batt_temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_bus_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_pl_c: Mapped[float] = mapped_column(Float, nullable=False)
    att_rate_dps: Mapped[float] = mapped_column(Float, nullable=False)
    rf_snr_db: Mapped[float] = mapped_column(Float, nullable=False)
    is_in_eclipse: Mapped[bool] = mapped_column(Boolean, nullable=False)
    metrics_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationship
    satellite: Mapped["SatelliteModel"] = relationship(  # noqa: F821
        "SatelliteModel",
        back_populates="telemetry_samples",
    )
