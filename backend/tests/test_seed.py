"""Tests for database bootstrap and idempotent constellation seeding."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.bootstrap import seed_virtual_constellation
from app.domain.constants import VIRTUAL_NORAD_ALPHA, VIRTUAL_NORAD_BETA, VIRTUAL_NORAD_GAMMA
from app.domain.enums import SubsystemType
from app.models.ground_station import GroundStationModel
from app.models.satellite import SatelliteModel, SatelliteSubsystemModel
from app.models.scenario import FaultScenarioModel


def test_seed_creates_expected_entities(db_session: Session) -> None:
    """Verify first run of seed creates 3 satellites, 15 subsystems, 3 stations, 4 scenarios."""
    result = seed_virtual_constellation(db_session)

    assert result["satellites_created"] == 3
    assert result["subsystems_created"] == 15
    assert result["stations_created"] == 3
    assert result["scenarios_created"] == 4

    # Verify satellites
    stmt = select(SatelliteModel).order_by(SatelliteModel.satellite_id)
    satellites = list(db_session.scalars(stmt).all())
    assert len(satellites) == 3

    alpha, beta, gamma = satellites[0], satellites[1], satellites[2]
    assert alpha.satellite_id == "SAT-001"
    assert alpha.name == "ORBITOPS-ALPHA"
    assert alpha.norad_id == VIRTUAL_NORAD_ALPHA
    assert alpha.battery_capacity_wh == 320.0

    assert beta.satellite_id == "SAT-002"
    assert beta.name == "ORBITOPS-BETA"
    assert beta.norad_id == VIRTUAL_NORAD_BETA
    assert beta.battery_capacity_wh == 480.0

    assert gamma.satellite_id == "SAT-003"
    assert gamma.name == "ORBITOPS-GAMMA"
    assert gamma.norad_id == VIRTUAL_NORAD_GAMMA
    assert gamma.battery_capacity_wh == 220.0

    # Verify 5 subsystems per satellite
    for sat in satellites:
        subs = db_session.scalars(
            select(SatelliteSubsystemModel).where(
                SatelliteSubsystemModel.satellite_id == sat.satellite_id
            )
        ).all()
        assert len(subs) == 5
        types = {s.subsystem_type for s in subs}
        expected_types = {st.value for st in SubsystemType}
        assert types == expected_types

    # Verify 3 ground stations
    stations = db_session.scalars(select(GroundStationModel)).all()
    assert len(stations) == 3
    station_ids = {s.station_id for s in stations}
    assert station_ids == {"GS-KOUROU", "GS-SVALBARD", "GS-CANBERRA"}

    # Verify 4 scenarios
    scenarios = db_session.scalars(select(FaultScenarioModel)).all()
    assert len(scenarios) == 4
    scenario_ids = {s.scenario_id for s in scenarios}
    assert scenario_ids == {"SCN-01", "SCN-02", "SCN-03", "SCN-04"}


def test_seed_is_idempotent(db_session: Session) -> None:
    """Verify that re-running seed creates 0 duplicates and does not alter existing records."""
    # First seed
    seed_virtual_constellation(db_session)

    # Second seed
    second_result = seed_virtual_constellation(db_session)
    assert second_result["satellites_created"] == 0
    assert second_result["subsystems_created"] == 0
    assert second_result["stations_created"] == 0
    assert second_result["scenarios_created"] == 0

    # Ensure total counts unchanged
    sat_count = len(list(db_session.scalars(select(SatelliteModel)).all()))
    assert sat_count == 3
