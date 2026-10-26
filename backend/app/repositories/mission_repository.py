"""Mission persistence repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mission import MissionModel


class MissionRepository:
    """Data access repository for mission sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, mission_id: str) -> MissionModel | None:
        """Retrieve mission by ID."""
        return self.session.get(MissionModel, mission_id)

    def get_by_name(self, name: str) -> MissionModel | None:
        """Retrieve mission by name."""
        stmt = select(MissionModel).where(MissionModel.name == name)
        return self.session.scalars(stmt).first()

    def create(
        self,
        name: str,
        start_time: datetime | None = None,
        time_warp_factor: float = 1.0,
        is_active: bool = True,
        mission_id: str | None = None,
    ) -> MissionModel:
        """Create and persist a new mission record."""
        mission = MissionModel(
            mission_id=mission_id or str(uuid.uuid4()),
            name=name,
            start_time=start_time or datetime.now(UTC),
            time_warp_factor=time_warp_factor,
            is_active=is_active,
        )
        self.session.add(mission)
        self.session.flush()
        return mission

    def get_or_create_default(self, name: str = "ORBITOPS-MISSION-01") -> MissionModel:
        """Retrieve the default mission or create it if missing."""
        mission = self.get_by_name(name)
        if not mission:
            mission = self.create(name=name)
        return mission

    def list_active(self) -> list[MissionModel]:
        """List all active mission sessions."""
        stmt = select(MissionModel).where(MissionModel.is_active.is_(True))
        return list(self.session.scalars(stmt).all())
