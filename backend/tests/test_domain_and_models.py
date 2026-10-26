"""Tests for SQLAlchemy ORM models, relationships, and constraints."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.constants import VIRTUAL_NORAD_ALPHA
from app.domain.enums import SatelliteMode, SatelliteType, SubsystemType
from app.models.mission import MissionModel
from app.models.satellite import SatelliteModel, SatelliteSubsystemModel
from app.models.telemetry import TelemetrySampleModel


def test_foreign_key_violation_rejected(db_session: Session) -> None:
    """Verify that inserting a satellite with nonexistent mission_id raises IntegrityError."""
    fake_mission_id = str(uuid.uuid4())
    sat = SatelliteModel(
        satellite_id="SAT-TEST-99",
        mission_id=fake_mission_id,
        name="ORBITOPS-ORPHAN",
        norad_id=99999,
        satellite_type=SatelliteType.EARTH_OBSERVATION.value,
        operational_mode=SatelliteMode.NOMINAL.value,
        semi_major_axis_km=6900.0,
        inclination_deg=97.0,
        mass_kg=150.0,
        battery_capacity_wh=300.0,
        solar_area_m2=1.0,
    )
    db_session.add(sat)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_satellite_negative_mass_rejected(db_session: Session) -> None:
    """Verify that negative mass violates check constraint."""
    mission = MissionModel(name="TEST-MISSION-1", start_time=datetime.now(UTC))
    db_session.add(mission)
    db_session.flush()

    sat = SatelliteModel(
        satellite_id="SAT-NEG-MASS",
        mission_id=mission.mission_id,
        name="ORBITOPS-INVALID-MASS",
        norad_id=99998,
        satellite_type=SatelliteType.RESEARCH.value,
        operational_mode=SatelliteMode.NOMINAL.value,
        semi_major_axis_km=7000.0,
        inclination_deg=45.0,
        mass_kg=-10.0,  # Invalid
        battery_capacity_wh=200.0,
        solar_area_m2=1.0,
    )
    db_session.add(sat)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_satellite_subsystems_cascade_delete(db_session: Session) -> None:
    """Verify that deleting a satellite cascades to delete its subsystems."""
    mission = MissionModel(name="TEST-CASCADE-MISSION", start_time=datetime.now(UTC))
    db_session.add(mission)
    db_session.flush()

    sat = SatelliteModel(
        satellite_id="SAT-CASCADE-1",
        mission_id=mission.mission_id,
        name="ORBITOPS-CASCADE",
        norad_id=VIRTUAL_NORAD_ALPHA,
        satellite_type=SatelliteType.EARTH_OBSERVATION.value,
        operational_mode=SatelliteMode.NOMINAL.value,
        semi_major_axis_km=6921.0,
        inclination_deg=97.6,
        mass_kg=180.0,
        battery_capacity_wh=320.0,
        solar_area_m2=1.2,
    )
    db_session.add(sat)
    db_session.flush()

    sub = SatelliteSubsystemModel(
        satellite_id=sat.satellite_id,
        subsystem_type=SubsystemType.POWER.value,
        health_status="NOMINAL",
        power_draw_w=25.0,
        temperature_c=20.0,
        configuration={"nominal_bus_v": 28.0},
    )
    db_session.add(sub)
    db_session.flush()

    # Delete satellite
    db_session.delete(sat)
    db_session.flush()

    # Check subsystem is deleted
    assert db_session.get(SatelliteSubsystemModel, sub.subsystem_id) is None


def test_telemetry_soc_out_of_bounds_rejected(db_session: Session) -> None:
    """Verify check constraint rejecting battery SOC > 100% or < 0%."""
    mission = MissionModel(name="TEST-TELEM-MISSION", start_time=datetime.now(UTC))
    db_session.add(mission)
    db_session.flush()

    sat = SatelliteModel(
        satellite_id="SAT-TELEM-TEST",
        mission_id=mission.mission_id,
        name="ORBITOPS-TELEM",
        norad_id=99997,
        satellite_type=SatelliteType.COMMUNICATION.value,
        operational_mode=SatelliteMode.NOMINAL.value,
        semi_major_axis_km=7000.0,
        inclination_deg=5.0,
        mass_kg=200.0,
        battery_capacity_wh=400.0,
        solar_area_m2=1.5,
    )
    db_session.add(sat)
    db_session.flush()

    sample = TelemetrySampleModel(
        satellite_id=sat.satellite_id,
        sim_timestamp=datetime.now(UTC),
        sequence_number=1,
        pwr_bus_v=28.0,
        pwr_solar_w=400.0,
        batt_soc=125.0,  # Invalid: > 100%
        batt_temp_c=20.0,
        temp_bus_c=22.0,
        temp_pl_c=25.0,
        att_rate_dps=0.01,
        rf_snr_db=14.0,
        is_in_eclipse=False,
    )
    db_session.add(sample)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
