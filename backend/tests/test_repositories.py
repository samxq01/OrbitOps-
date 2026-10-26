"""Tests for repository persistence operations."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import CommandStatus, EvidencePolarity, SatelliteMode, SatelliteType
from app.domain.exceptions import SatelliteNotFoundError
from app.models.command import SatelliteCommandModel
from app.models.incident import IncidentEvidenceModel, IncidentRecordModel
from app.models.satellite import SatelliteModel
from app.models.telemetry import TelemetrySampleModel
from app.repositories import (
    CommandRepository,
    EventRepository,
    IncidentRepository,
    MissionRepository,
    SatelliteRepository,
    TelemetryRepository,
)


def test_mission_and_satellite_repositories(db_session: Session) -> None:
    """Verify Mission and Satellite repository CRUD methods."""
    mission_repo = MissionRepository(db_session)
    sat_repo = SatelliteRepository(db_session)

    mission = mission_repo.create("MISSION-REPO-TEST")
    assert mission.mission_id is not None
    assert mission_repo.get_by_id(mission.mission_id) is not None

    sat = SatelliteModel(
        satellite_id="SAT-REPO-1",
        mission_id=mission.mission_id,
        name="ORBITOPS-REPO-ALPHA",
        norad_id=99201,
        satellite_type=SatelliteType.EARTH_OBSERVATION.value,
        operational_mode=SatelliteMode.NOMINAL.value,
        semi_major_axis_km=6920.0,
        inclination_deg=97.0,
        mass_kg=175.0,
        battery_capacity_wh=310.0,
        solar_area_m2=1.1,
    )
    sat_repo.create(sat)

    assert sat_repo.exists("SAT-REPO-1") is True
    assert sat_repo.exists("SAT-NONEXISTENT") is False

    retrieved = sat_repo.get_by_id("SAT-REPO-1")
    assert retrieved is not None
    assert retrieved.name == "ORBITOPS-REPO-ALPHA"

    # Test update mode
    updated = sat_repo.update_mode("SAT-REPO-1", SatelliteMode.SAFE_MODE.value)
    assert updated.operational_mode == SatelliteMode.SAFE_MODE.value

    # Test nonexistent satellite error
    with pytest.raises(SatelliteNotFoundError):
        sat_repo.update_mode("SAT-UNKNOWN", SatelliteMode.EMERGENCY.value)


def test_telemetry_repository_history_and_limits(db_session: Session) -> None:
    """Verify TelemetryRepository insert, ordering, and bounded limit logic."""
    mission = MissionRepository(db_session).create("MISSION-TELEM-REPO")
    sat = SatelliteRepository(db_session).create(
        SatelliteModel(
            satellite_id="SAT-TELEM-REPO",
            mission_id=mission.mission_id,
            name="ORBITOPS-TELEM-REPO",
            norad_id=99202,
            satellite_type=SatelliteType.COMMUNICATION.value,
            operational_mode=SatelliteMode.NOMINAL.value,
            semi_major_axis_km=7000.0,
            inclination_deg=5.0,
            mass_kg=220.0,
            battery_capacity_wh=450.0,
            solar_area_m2=1.6,
        )
    )

    telem_repo = TelemetryRepository(db_session)

    # Insert 10 chronological samples
    samples = []
    base_time = datetime(2026, 10, 26, 12, 0, 0, tzinfo=UTC)
    for i in range(10):
        t = datetime.fromtimestamp(base_time.timestamp() + (i * 10), tz=UTC)
        sample = TelemetrySampleModel(
            satellite_id=sat.satellite_id,
            sim_timestamp=t,
            sequence_number=i + 1,
            pwr_bus_v=28.0 - (i * 0.1),
            pwr_solar_w=400.0,
            batt_soc=90.0 - (i * 0.5),
            batt_temp_c=20.0 + (i * 0.2),
            temp_bus_c=22.0,
            temp_pl_c=25.0,
            att_rate_dps=0.02,
            rf_snr_db=14.0,
            is_in_eclipse=False,
        )
        samples.append(sample)

    telem_repo.insert_batch(samples)

    # Check total count
    assert telem_repo.count_samples(sat.satellite_id) == 10

    # Retrieve history bounded to 5
    history = telem_repo.get_history(sat.satellite_id, limit=5)
    assert len(history) == 5
    # Verify chronological ascending order
    assert history[0].sim_timestamp < history[1].sim_timestamp

    # Check latest sample
    latest = telem_repo.get_latest(sat.satellite_id)
    assert latest is not None
    assert latest.sequence_number == 10


def test_event_repository_monotonic_sequence(db_session: Session) -> None:
    """Verify EventRepository monotonic sequence numbers and immutability."""
    event_repo = EventRepository(db_session)
    t = datetime(2026, 10, 26, 12, 0, 0, tzinfo=UTC)

    e1 = event_repo.append_event("SIMULATION_STARTED", t, {"sim": "init"})
    e2 = event_repo.append_event("FAULT_INJECTED", t, {"code": "SCN-01"}, satellite_id="SAT-001")
    e3 = event_repo.append_event("MODE_TRANSITION", t, {"to": "SAFE_MODE"}, satellite_id="SAT-001")

    assert e1.sequence_number == 1
    assert e2.sequence_number == 2
    assert e3.sequence_number == 3

    events = event_repo.get_events(satellite_id="SAT-001")
    assert len(events) == 2
    assert events[0].sequence_number == 2
    assert events[1].sequence_number == 3


def test_incident_and_evidence_repository(db_session: Session) -> None:
    """Verify Incident and Evidence repository operations."""
    mission = MissionRepository(db_session).create("MISSION-INC-TEST")
    sat = SatelliteRepository(db_session).create(
        SatelliteModel(
            satellite_id="SAT-INC-TEST",
            mission_id=mission.mission_id,
            name="ORBITOPS-INC-SAT",
            norad_id=99203,
            satellite_type=SatelliteType.RESEARCH.value,
            operational_mode=SatelliteMode.DEGRADED.value,
            semi_major_axis_km=7000.0,
            inclination_deg=45.0,
            mass_kg=100.0,
            battery_capacity_wh=200.0,
            solar_area_m2=0.8,
        )
    )

    inc_repo = IncidentRepository(db_session)
    now = datetime.now(UTC)

    incident = IncidentRecordModel(
        incident_id="INC-TEST-001",
        satellite_id=sat.satellite_id,
        title="High Bus Temperature",
        severity="WARNING",
        detected_at=now,
    )
    inc_repo.create_incident(incident)

    # Add evidence
    evidence = IncidentEvidenceModel(
        incident_id=incident.incident_id,
        telemetry_mnemonic="TEMP_BUS_C",
        observed_value=48.5,
        expected_value=25.0,
        polarity=EvidencePolarity.SUPPORTING.value,
        hypothesis="Radiator Blockage",
        explanation="Bus temperature exceeded warning threshold of 45C",
    )
    inc_repo.add_evidence(evidence)

    # Acknowledge
    inc_repo.acknowledge(incident.incident_id)

    # Update diagnosis
    inc_repo.update_diagnosis(
        incident_id=incident.incident_id,
        confidence_score=0.85,
        primary_cause="Thermal radiator blocked by louver failure",
        recommended_action="CMD_SLEW_TO_COLD_SINK",
    )

    retrieved = inc_repo.get_by_id(incident.incident_id, include_evidence=True)
    assert retrieved is not None
    assert retrieved.acknowledged is True
    assert retrieved.confidence_score == 0.85
    assert len(retrieved.evidence_records) == 1
    assert retrieved.evidence_records[0].telemetry_mnemonic == "TEMP_BUS_C"


def test_command_repository(db_session: Session) -> None:
    """Verify CommandRepository queueing and status transitions."""
    mission = MissionRepository(db_session).create("MISSION-CMD-TEST")
    sat = SatelliteRepository(db_session).create(
        SatelliteModel(
            satellite_id="SAT-CMD-TEST",
            mission_id=mission.mission_id,
            name="ORBITOPS-CMD-SAT",
            norad_id=99204,
            satellite_type=SatelliteType.COMMUNICATION.value,
            operational_mode=SatelliteMode.NOMINAL.value,
            semi_major_axis_km=7000.0,
            inclination_deg=5.0,
            mass_kg=200.0,
            battery_capacity_wh=400.0,
            solar_area_m2=1.5,
        )
    )

    cmd_repo = CommandRepository(db_session)
    cmd = SatelliteCommandModel(
        command_id="CMD-TEST-100",
        satellite_id=sat.satellite_id,
        command_mnemonic="CMD_SHED_PAYLOAD",
        parameters={"load": "OFF"},
        status=CommandStatus.QUEUED.value,
        submitted_by="operator",
    )
    cmd_repo.create(cmd)

    # Advance status
    cmd_repo.update_status(cmd.command_id, CommandStatus.APPROVED.value)
    retrieved = cmd_repo.get_by_id(cmd.command_id)
    assert retrieved is not None
    assert retrieved.status == CommandStatus.APPROVED.value

    # Mark completed
    cmd_repo.update_status(cmd.command_id, CommandStatus.COMPLETED.value)
    completed = cmd_repo.get_by_id(cmd.command_id)
    assert completed is not None
    assert completed.status == CommandStatus.COMPLETED.value
    assert completed.executed_at is not None
