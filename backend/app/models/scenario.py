"""Fault scenario persistence model."""

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FaultScenarioModel(Base):
    """Emergency scenario and fault injection record."""

    __tablename__ = "fault_scenarios"

    scenario_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_satellite_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="SET NULL"),
        nullable=True,
    )
    fault_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_met_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optional relationship
    target_satellite: Mapped["SatelliteModel | None"] = relationship("SatelliteModel")  # noqa: F821
