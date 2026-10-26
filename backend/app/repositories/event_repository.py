"""Mission event log persistence repository."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import MissionEventModel


class EventRepository:
    """Data access repository for the immutable append-only mission event store."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_next_sequence_number(self) -> int:
        """Allocate next strictly monotonic sequence number."""
        stmt = select(func.max(MissionEventModel.sequence_number))
        max_seq = self.session.scalar(stmt)
        return (max_seq or 0) + 1

    def append_event(
        self,
        event_type: str,
        sim_timestamp: datetime,
        payload: dict[str, Any] | None = None,
        satellite_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> MissionEventModel:
        """Append an immutable event to the mission event log."""
        seq_num = self.get_next_sequence_number()
        event = MissionEventModel(
            event_id=str(uuid.uuid4()),
            sequence_number=seq_num,
            event_type=event_type,
            satellite_id=satellite_id,
            sim_timestamp=sim_timestamp,
            recorded_at=recorded_at or datetime.now(UTC),
            payload=payload or {},
        )
        self.session.add(event)
        self.session.flush()
        return event

    def get_events(
        self,
        satellite_id: str | None = None,
        event_type: str | None = None,
        since_sequence: int | None = None,
        limit: int = 100,
    ) -> list[MissionEventModel]:
        """Fetch chronologically ordered mission events."""
        stmt = select(MissionEventModel).order_by(MissionEventModel.sequence_number.asc())

        if satellite_id:
            stmt = stmt.where(MissionEventModel.satellite_id == satellite_id)
        if event_type:
            stmt = stmt.where(MissionEventModel.event_type == event_type)
        if since_sequence is not None:
            stmt = stmt.where(MissionEventModel.sequence_number > since_sequence)

        bounded_limit = min(max(1, limit), 1000)
        stmt = stmt.limit(bounded_limit)

        return list(self.session.scalars(stmt).all())
