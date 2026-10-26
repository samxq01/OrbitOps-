"""Satellite subsystem persistence repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.exceptions import SubsystemNotFoundError
from app.models.satellite import SatelliteSubsystemModel


class SubsystemRepository:
    """Data access repository for spacecraft subsystem components."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_satellite(self, satellite_id: str) -> list[SatelliteSubsystemModel]:
        """List all subsystems for a given satellite."""
        stmt = select(SatelliteSubsystemModel).where(
            SatelliteSubsystemModel.satellite_id == satellite_id
        )
        return list(self.session.scalars(stmt).all())

    def get_by_type(self, satellite_id: str, subsystem_type: str) -> SatelliteSubsystemModel | None:
        """Retrieve subsystem by satellite ID and subsystem type."""
        stmt = select(SatelliteSubsystemModel).where(
            SatelliteSubsystemModel.satellite_id == satellite_id,
            SatelliteSubsystemModel.subsystem_type == subsystem_type,
        )
        return self.session.scalars(stmt).first()

    def create(self, subsystem: SatelliteSubsystemModel) -> SatelliteSubsystemModel:
        """Persist a new subsystem record."""
        self.session.add(subsystem)
        self.session.flush()
        return subsystem

    def update_health(
        self,
        subsystem_id: str,
        health_status: str,
        power_draw_w: float | None = None,
        temperature_c: float | None = None,
    ) -> SatelliteSubsystemModel:
        """Update subsystem health status and physical operational readings."""
        subsystem = self.session.get(SatelliteSubsystemModel, subsystem_id)
        if not subsystem:
            raise SubsystemNotFoundError(f"Subsystem '{subsystem_id}' not found.")

        subsystem.health_status = health_status
        if power_draw_w is not None:
            subsystem.power_draw_w = power_draw_w
        if temperature_c is not None:
            subsystem.temperature_c = temperature_c

        self.session.flush()
        return subsystem
