"""Incident and evidence persistence repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.exceptions import EntityNotFoundError
from app.models.incident import IncidentEvidenceModel, IncidentRecordModel


class IncidentRepository:
    """Data access repository for anomalies and evidence proofs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_incident(self, incident: IncidentRecordModel) -> IncidentRecordModel:
        """Persist a newly detected anomaly incident."""
        self.session.add(incident)
        self.session.flush()
        return incident

    def get_by_id(
        self, incident_id: str, include_evidence: bool = True
    ) -> IncidentRecordModel | None:
        """Retrieve an incident by ID with optional evidence records."""
        stmt = select(IncidentRecordModel).where(IncidentRecordModel.incident_id == incident_id)
        if include_evidence:
            stmt = stmt.options(selectinload(IncidentRecordModel.evidence_records))
        return self.session.scalars(stmt).first()

    def list_incidents(
        self,
        satellite_id: str | None = None,
        acknowledged: bool | None = None,
    ) -> list[IncidentRecordModel]:
        """List incidents with optional satellite and acknowledgment filters."""
        stmt = select(IncidentRecordModel).options(
            selectinload(IncidentRecordModel.evidence_records)
        )
        if satellite_id:
            stmt = stmt.where(IncidentRecordModel.satellite_id == satellite_id)
        if acknowledged is not None:
            stmt = stmt.where(IncidentRecordModel.acknowledged == acknowledged)
        stmt = stmt.order_by(IncidentRecordModel.detected_at.desc())
        return list(self.session.scalars(stmt).all())

    def acknowledge(self, incident_id: str) -> IncidentRecordModel:
        """Mark an incident as acknowledged by operator."""
        incident = self.get_by_id(incident_id, include_evidence=False)
        if not incident:
            raise EntityNotFoundError(f"Incident '{incident_id}' not found.")
        incident.acknowledged = True
        self.session.flush()
        return incident

    def add_evidence(self, evidence: IncidentEvidenceModel) -> IncidentEvidenceModel:
        """Persist an individual telemetry proof record for an incident."""
        self.session.add(evidence)
        self.session.flush()
        return evidence

    def update_diagnosis(
        self,
        incident_id: str,
        confidence_score: float,
        primary_cause: str,
        recommended_action: str,
    ) -> IncidentRecordModel:
        """Attach calibrated diagnostic conclusions and recommended recovery action."""
        incident = self.get_by_id(incident_id)
        if not incident:
            raise EntityNotFoundError(f"Incident '{incident_id}' not found.")
        incident.confidence_score = confidence_score
        incident.primary_cause = primary_cause
        incident.recommended_action = recommended_action
        self.session.flush()
        return incident

    def resolve_incident(
        self, incident_id: str, resolved_at: datetime | None = None
    ) -> IncidentRecordModel:
        """Mark an incident as resolved."""
        incident = self.get_by_id(incident_id)
        if not incident:
            raise EntityNotFoundError(f"Incident '{incident_id}' not found.")
        incident.resolved_at = resolved_at or datetime.now(UTC)
        self.session.flush()
        return incident
