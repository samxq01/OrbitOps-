"""Command persistence repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.exceptions import EntityNotFoundError
from app.models.command import SatelliteCommandModel


class CommandRepository:
    """Data access repository for telecommand pipeline records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, command: SatelliteCommandModel) -> SatelliteCommandModel:
        """Persist a newly queued telecommand."""
        self.session.add(command)
        self.session.flush()
        return command

    def get_by_id(self, command_id: str) -> SatelliteCommandModel | None:
        """Retrieve a telecommand by ID."""
        return self.session.get(SatelliteCommandModel, command_id)

    def list_by_satellite(
        self,
        satellite_id: str,
        status: str | None = None,
    ) -> list[SatelliteCommandModel]:
        """List telecommands for a satellite with optional status filter."""
        stmt = select(SatelliteCommandModel).where(
            SatelliteCommandModel.satellite_id == satellite_id
        )
        if status:
            stmt = stmt.where(SatelliteCommandModel.status == status)
        stmt = stmt.order_by(SatelliteCommandModel.submitted_at.desc())
        return list(self.session.scalars(stmt).all())

    def update_status(
        self,
        command_id: str,
        status: str,
        rejection_reason: str | None = None,
        executed_at: datetime | None = None,
    ) -> SatelliteCommandModel:
        """Advance command pipeline status."""
        command = self.get_by_id(command_id)
        if not command:
            raise EntityNotFoundError(f"Command '{command_id}' not found.")

        command.status = status
        if rejection_reason is not None:
            command.rejection_reason = rejection_reason
        if executed_at is not None:
            command.executed_at = executed_at
        elif status == "COMPLETED" and not command.executed_at:
            command.executed_at = datetime.now(UTC)

        self.session.flush()
        return command
