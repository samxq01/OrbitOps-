"""Satellite persistence repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.exceptions import SatelliteNotFoundError
from app.models.satellite import SatelliteModel


class SatelliteRepository:
    """Data access repository for virtual satellites."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_satellites(self, mission_id: str | None = None) -> list[SatelliteModel]:
        """List satellites optionally filtered by mission."""
        stmt = select(SatelliteModel).options(selectinload(SatelliteModel.subsystems))
        if mission_id:
            stmt = stmt.where(SatelliteModel.mission_id == mission_id)
        return list(self.session.scalars(stmt).all())

    def get_by_id(
        self, satellite_id: str, include_subsystems: bool = True
    ) -> SatelliteModel | None:
        """Retrieve a satellite by ID."""
        stmt = select(SatelliteModel).where(SatelliteModel.satellite_id == satellite_id)
        if include_subsystems:
            stmt = stmt.options(selectinload(SatelliteModel.subsystems))
        return self.session.scalars(stmt).first()

    def get_by_name(self, name: str) -> SatelliteModel | None:
        """Retrieve a satellite by name."""
        stmt = select(SatelliteModel).where(SatelliteModel.name == name)
        return self.session.scalars(stmt).first()

    def exists(self, satellite_id: str) -> bool:
        """Check whether a satellite ID exists."""
        stmt = select(SatelliteModel.satellite_id).where(
            SatelliteModel.satellite_id == satellite_id
        )
        return self.session.scalars(stmt).first() is not None

    def create(self, satellite: SatelliteModel) -> SatelliteModel:
        """Persist a new satellite entity."""
        self.session.add(satellite)
        self.session.flush()
        return satellite

    def update_mode(self, satellite_id: str, new_mode: str) -> SatelliteModel:
        """Update operational mode of a satellite."""
        satellite = self.get_by_id(satellite_id)
        if not satellite:
            raise SatelliteNotFoundError(satellite_id)
        satellite.operational_mode = new_mode
        self.session.flush()
        return satellite

    def update_config(self, satellite_id: str, updates: dict[str, Any]) -> SatelliteModel:
        """Update configurable physical/orbital parameters."""
        satellite = self.get_by_id(satellite_id)
        if not satellite:
            raise SatelliteNotFoundError(satellite_id)

        for key, value in updates.items():
            if hasattr(satellite, key) and key not in ("satellite_id", "mission_id"):
                setattr(satellite, key, value)

        self.session.flush()
        return satellite
