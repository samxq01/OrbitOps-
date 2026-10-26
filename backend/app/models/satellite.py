"""Satellite and subsystem persistence models."""

import uuid
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SatelliteModel(Base):
    """Virtual satellite spacecraft entity."""

    __tablename__ = "satellites"
    __table_args__ = (
        CheckConstraint("mass_kg > 0", name="chk_satellite_mass_pos"),
        CheckConstraint("battery_capacity_wh > 0", name="chk_satellite_battery_pos"),
        CheckConstraint("solar_area_m2 > 0", name="chk_satellite_solar_pos"),
        CheckConstraint(
            "inclination_deg >= 0.0 AND inclination_deg <= 180.0",
            name="chk_satellite_inclination_range",
        ),
    )

    satellite_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("missions.mission_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    norad_id: Mapped[int] = mapped_column(Integer, nullable=False)
    satellite_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operational_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="NOMINAL",
        index=True,
    )
    semi_major_axis_km: Mapped[float] = mapped_column(Float, nullable=False)
    inclination_deg: Mapped[float] = mapped_column(Float, nullable=False)
    mass_kg: Mapped[float] = mapped_column(Float, nullable=False)
    battery_capacity_wh: Mapped[float] = mapped_column(Float, nullable=False)
    solar_area_m2: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    mission: Mapped["MissionModel"] = relationship(  # noqa: F821
        "MissionModel",
        back_populates="satellites",
    )
    subsystems: Mapped[list["SatelliteSubsystemModel"]] = relationship(
        "SatelliteSubsystemModel",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )
    telemetry_samples: Mapped[list["TelemetrySampleModel"]] = relationship(  # noqa: F821
        "TelemetrySampleModel",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["IncidentRecordModel"]] = relationship(  # noqa: F821
        "IncidentRecordModel",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )
    contact_windows: Mapped[list["ContactWindowModel"]] = relationship(  # noqa: F821
        "ContactWindowModel",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )
    commands: Mapped[list["SatelliteCommandModel"]] = relationship(  # noqa: F821
        "SatelliteCommandModel",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )


class SatelliteSubsystemModel(Base):
    """Subsystem record associated with a virtual satellite."""

    __tablename__ = "satellite_subsystems"
    __table_args__ = (
        UniqueConstraint("satellite_id", "subsystem_type", name="uq_sat_subsystem_type"),
        CheckConstraint("power_draw_w >= 0", name="chk_subsystem_power_nonneg"),
    )

    subsystem_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    satellite_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subsystem_type: Mapped[str] = mapped_column(String(30), nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOMINAL")
    power_draw_w: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    satellite: Mapped[SatelliteModel] = relationship(
        "SatelliteModel",
        back_populates="subsystems",
    )
