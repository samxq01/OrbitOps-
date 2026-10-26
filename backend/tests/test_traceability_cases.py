"""Formal implementations of Traceability Matrix test cases TC-01, TC-02, TC-03, and TC-09."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.bootstrap import seed_virtual_constellation
from app.domain.constants import VIRTUAL_NORAD_ALPHA, VIRTUAL_NORAD_BETA, VIRTUAL_NORAD_GAMMA
from app.domain.enums import SatelliteMode, SatelliteType
from app.models.mission import MissionModel
from app.models.satellite import SatelliteModel
from app.models.telemetry import TelemetrySampleModel
from app.repositories import SatelliteRepository, TelemetryRepository


def test_tc_01_multi_satellite_registry(db_session: Session) -> None:
    """TC-01 (FR-001): Verify satellite registry initializes 3 distinct virtual satellites."""
    # Seed database
    seed_virtual_constellation(db_session)
    sat_repo = SatelliteRepository(db_session)

    satellites = sat_repo.list_satellites()
    assert len(satellites) == 3, "Registry must contain exactly 3 virtual satellites"

    sat_map = {s.satellite_id: s for s in satellites}
    assert "SAT-001" in sat_map
    assert "SAT-002" in sat_map
    assert "SAT-003" in sat_map

    # Validate distinct configurations
    alpha = sat_map["SAT-001"]
    assert alpha.name == "ORBITOPS-ALPHA"
    assert alpha.satellite_type == SatelliteType.EARTH_OBSERVATION.value
    assert alpha.norad_id == VIRTUAL_NORAD_ALPHA
    assert len(alpha.subsystems) == 5

    beta = sat_map["SAT-002"]
    assert beta.name == "ORBITOPS-BETA"
    assert beta.satellite_type == SatelliteType.COMMUNICATION.value
    assert beta.norad_id == VIRTUAL_NORAD_BETA
    assert len(beta.subsystems) == 5

    gamma = sat_map["SAT-003"]
    assert gamma.name == "ORBITOPS-GAMMA"
    assert gamma.satellite_type == SatelliteType.RESEARCH.value
    assert gamma.norad_id == VIRTUAL_NORAD_GAMMA
    assert len(gamma.subsystems) == 5


def test_tc_02_satellite_operational_mode(db_session: Session) -> None:
    """TC-02 (FR-002): Validate initial satellite operational mode and mode query."""
    seed_virtual_constellation(db_session)
    sat_repo = SatelliteRepository(db_session)

    for sat_id in ("SAT-001", "SAT-002", "SAT-003"):
        sat = sat_repo.get_by_id(sat_id)
        assert sat is not None
        assert sat.operational_mode in [mode.value for mode in SatelliteMode]
        assert sat.operational_mode == SatelliteMode.NOMINAL.value


def test_tc_03_configurable_spacecraft_constants(db_session: Session) -> None:
    """TC-03 (FR-003): Verify spacecraft physical constants can be configured and persisted."""
    mission = MissionModel(name="TC-03-MISSION", start_time=datetime.now(UTC))
    db_session.add(mission)
    db_session.flush()

    sat_repo = SatelliteRepository(db_session)
    sat = sat_repo.create(
        SatelliteModel(
            satellite_id="SAT-CONFIG-TEST",
            mission_id=mission.mission_id,
            name="ORBITOPS-CONFIGURABLE",
            norad_id=99301,
            satellite_type=SatelliteType.RESEARCH.value,
            operational_mode=SatelliteMode.NOMINAL.value,
            semi_major_axis_km=6900.0,
            inclination_deg=45.0,
            mass_kg=100.0,
            battery_capacity_wh=200.0,
            solar_area_m2=1.0,
        )
    )

    # Reconfigure constants
    updated = sat_repo.update_config(
        sat.satellite_id,
        {
            "battery_capacity_wh": 500.0,
            "mass_kg": 125.0,
            "solar_area_m2": 2.2,
        },
    )

    assert updated.battery_capacity_wh == 500.0
    assert updated.mass_kg == 125.0
    assert updated.solar_area_m2 == 2.2

    # Query from fresh query
    persisted = sat_repo.get_by_id(sat.satellite_id)
    assert persisted is not None
    assert persisted.battery_capacity_wh == 500.0


def test_tc_09_telemetry_persistence_and_queries(db_session: Session) -> None:
    """TC-09 (FR-009): Test telemetry sample persistence, indexed retrieval, and ordering."""
    seed_virtual_constellation(db_session)
    telem_repo = TelemetryRepository(db_session)

    # Insert 5 samples for SAT-001
    base_time = datetime(2026, 10, 26, 14, 0, 0, tzinfo=UTC)
    samples = []
    for i in range(5):
        sample = TelemetrySampleModel(
            satellite_id="SAT-001",
            sim_timestamp=datetime.fromtimestamp(base_time.timestamp() + (i * 60), tz=UTC),
            sequence_number=i + 1,
            pwr_bus_v=28.1,
            pwr_solar_w=450.0,
            batt_soc=95.0 - i,
            batt_temp_c=18.0,
            temp_bus_c=22.0,
            temp_pl_c=24.0,
            att_rate_dps=0.01,
            rf_snr_db=14.5,
            is_in_eclipse=False,
            metrics_payload={"step": i},
        )
        samples.append(sample)

    telem_repo.insert_batch(samples)

    # Verify query
    history = telem_repo.get_history("SAT-001", limit=10)
    assert len(history) == 5
    # Order must be chronological
    assert history[0].sequence_number == 1
    assert history[-1].sequence_number == 5
    assert history[0].metrics_payload == {"step": 0}
