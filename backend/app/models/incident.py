"""Incident and evidence persistence models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentRecordModel(Base):
    """Incident record created upon telemetry anomaly detection."""

    __tablename__ = "incident_records"
    __table_args__ = (Index("idx_incidents_sat_sev", "satellite_id", "severity", "acknowledged"),)

    incident_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}",
    )
    satellite_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("satellites.satellite_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARNING")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Nullable until Anomaly Investigator evaluates evidence
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_cause: Mapped[str | None] = mapped_column(String(150), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Relationships
    satellite: Mapped["SatelliteModel"] = relationship(  # noqa: F821
        "SatelliteModel",
        back_populates="incidents",
    )
    evidence_records: Mapped[list["IncidentEvidenceModel"]] = relationship(
        "IncidentEvidenceModel",
        back_populates="incident",
        cascade="all, delete-orphan",
    )


class IncidentEvidenceModel(Base):
    """Deterministic telemetry evidence proof correlating hypothesis with observed telemetry."""

    __tablename__ = "incident_evidence"
    __table_args__ = (Index("idx_evidence_incident", "incident_id"),)

    evidence_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_records.incident_id", ondelete="CASCADE"),
        nullable=False,
    )
    telemetry_mnemonic: Mapped[str] = mapped_column(String(50), nullable=False)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    polarity: Mapped[str] = mapped_column(String(20), nullable=False)  # SUPPORTING or CONTRADICTING
    hypothesis: Mapped[str] = mapped_column(String(100), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    incident: Mapped[IncidentRecordModel] = relationship(
        IncidentRecordModel,
        back_populates="evidence_records",
    )
