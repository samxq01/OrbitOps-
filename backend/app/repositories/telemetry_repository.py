"""Telemetry samples persistence repository."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.telemetry import TelemetrySampleModel


class TelemetryRepository:
    """Data access repository for digital twin telemetry records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def insert_sample(self, sample: TelemetrySampleModel) -> TelemetrySampleModel:
        """Insert and flush a single telemetry sample."""
        self.session.add(sample)
        self.session.flush()
        return sample

    def insert_batch(self, samples: list[TelemetrySampleModel]) -> None:
        """Insert a batch of telemetry samples efficiently."""
        self.session.add_all(samples)
        self.session.flush()

    def get_history(
        self,
        satellite_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 300,
    ) -> list[TelemetrySampleModel]:
        """Fetch historical telemetry samples chronologically for a satellite."""
        stmt = (
            select(TelemetrySampleModel)
            .where(TelemetrySampleModel.satellite_id == satellite_id)
            .order_by(TelemetrySampleModel.sim_timestamp.asc())
        )

        if start_time:
            stmt = stmt.where(TelemetrySampleModel.sim_timestamp >= start_time)
        if end_time:
            stmt = stmt.where(TelemetrySampleModel.sim_timestamp <= end_time)

        # Enforce maximum query bound to protect memory
        bounded_limit = min(max(1, limit), 1000)
        stmt = stmt.limit(bounded_limit)

        return list(self.session.scalars(stmt).all())

    def get_latest(self, satellite_id: str) -> TelemetrySampleModel | None:
        """Fetch the most recent telemetry sample for a satellite."""
        stmt = (
            select(TelemetrySampleModel)
            .where(TelemetrySampleModel.satellite_id == satellite_id)
            .order_by(TelemetrySampleModel.sim_timestamp.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).first()

    def count_samples(self, satellite_id: str | None = None) -> int:
        """Count total persisted telemetry samples."""
        stmt = select(func.count(TelemetrySampleModel.sample_id))
        if satellite_id:
            stmt = stmt.where(TelemetrySampleModel.satellite_id == satellite_id)
        count = self.session.scalar(stmt)
        return count or 0
