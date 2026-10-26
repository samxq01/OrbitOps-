"""Ground station and contact window persistence models."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GroundStationModel(Base):
    """Ground tracking station entity."""

    __tablename__ = "ground_stations"
    __table_args__ = (
        CheckConstraint(
            "latitude_deg >= -90.0 AND latitude_deg <= 90.0",
            name="chk_station_lat_range",
        ),
        CheckConstraint(
            "longitude_deg >= -180.0 AND longitude_deg <= 180.0",
            name="chk_station_lon_range",
        ),
        CheckConstraint(
            "min_elevation_deg >= 0.0 AND min_elevation_deg <= 90.0",
            name="chk_station_min_elevation_range",
        ),
    )

    station_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    longitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    min_elevation_deg: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    carrier_freq_mhz: Mapped[float] = mapped_column(Float, nullable=False, default=2200.0)

    # Relationship
    contact_windows: Mapped[list["ContactWindowModel"]] = relationship(
        "ContactWindowModel",
        back_populates="ground_station",
        cascade="all, delete-orphan",
    )


class ContactWindowModel(Base):
    """Predicted or active line-of-sight communication pass window."""

    __tablename__ = "contact_windows"
    __table_args__ = (
        CheckConstraint("duration_sec >= 0", name="chk_window_duration_nonneg"),
        Index("idx_windows_sat_aos", "satellite_id", "aos_time", "los_time"),
    )

    window_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    station_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ground_stations.station_id", ondelete="CASCADE"),
        nullable=False,
    )
    satellite_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="CASCADE"),
        nullable=False,
    )
    aos_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    los_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_elevation_deg: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    ground_station: Mapped[GroundStationModel] = relationship(
        GroundStationModel,
        back_populates="contact_windows",
    )
    satellite: Mapped["SatelliteModel"] = relationship(  # noqa: F821
        "SatelliteModel",
        back_populates="contact_windows",
    )
