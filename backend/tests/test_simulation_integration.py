"""Integration tests for OrbitOps Phase 03 -- Simulation Engine and Persistence.

Covers:
  - Constellation loading from seeded database (build_fleet_from_db)
  - Full 100-tick constellation execution with all 3 satellites
  - Determinism across repeated independent runs with identical seed
  - Constellation heterogeneity (satellites differ in orbit, mass, power, payload)
  - Cross-satellite state isolation (no contamination between spacecraft states)
  - Telemetry database persistence and repository round-trip
  - Traceability cases:
      TC-04 (FR-004 Simulation tick integration)
      TC-05 (FR-005 Simulation clock controls)
      TC-06 (FR-006 Orbital propagation and eclipse)
      TC-07 (FR-007 Coupled subsystem telemetry generation)
      TC-12 (FR-012 Autonomous emergency safe-mode transition)
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.db.bootstrap import seed_virtual_constellation
from app.repositories.telemetry_repository import TelemetryRepository
from app.simulation.engine import SimulationEngine
from app.simulation.fleet import (
    build_fleet_from_db,
    persist_telemetry_batch,
)


@pytest.fixture
def seeded_db(db_session: Session) -> Session:
    """Provide a seeded test database session."""
    seed_virtual_constellation(db_session)
    return db_session


# ======================================================================
# 1. Database Integration and Fleet Loading
# ======================================================================


def test_build_fleet_from_db(seeded_db: Session):
    """build_fleet_from_db successfully converts Phase 02 seeded models into domain configs."""
    configs = build_fleet_from_db(seeded_db)
    assert len(configs) == 3

    sat_ids = [c.satellite_id for c in configs]
    assert sat_ids == ["SAT-001", "SAT-002", "SAT-003"]

    alpha = next(c for c in configs if c.satellite_id == "SAT-001")
    assert alpha.satellite_name == "ORBITOPS-ALPHA"
    assert alpha.battery_capacity_wh == 320.0
    assert alpha.solar_area_m2 == 1.2
    assert alpha.mass_kg == 180.0

    beta = next(c for c in configs if c.satellite_id == "SAT-002")
    assert beta.satellite_name == "ORBITOPS-BETA"
    assert beta.battery_capacity_wh == 480.0

    gamma = next(c for c in configs if c.satellite_id == "SAT-003")
    assert gamma.satellite_name == "ORBITOPS-GAMMA"
    assert gamma.battery_capacity_wh == 220.0


# ======================================================================
# 2. 100-Tick Execution and Fleet Heterogeneity
# ======================================================================


def test_100_tick_fleet_execution(seeded_db: Session):
    """Execute 100 ticks with all three satellites and verify progression."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    all_frames = []
    for _ in range(100):
        frames = engine.tick(dt=1.0)
        assert len(frames) == 3
        all_frames.append(frames)

    assert engine.clock.tick_count == 100
    assert engine.clock.sim_time_s == 100.0

    # Verify sequence numbers for each satellite strictly monotonically increase 1..100
    for sat_id in ["SAT-001", "SAT-002", "SAT-003"]:
        sat_seqs = [
            next(f.sequence_number for f in frame_batch if f.satellite_id == sat_id)
            for frame_batch in all_frames
        ]
        assert sat_seqs == list(range(1, 101))


def test_fleet_heterogeneity(seeded_db: Session):
    """Verify that satellites differ in physical properties and operational outputs."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    frames = engine.tick(dt=1.0)
    f1 = next(f for f in frames if f.satellite_id == "SAT-001")
    f2 = next(f for f in frames if f.satellite_id == "SAT-002")
    f3 = next(f for f in frames if f.satellite_id == "SAT-003")

    # Different altitudes
    assert f1.altitude_km != f2.altitude_km
    assert f2.altitude_km != f3.altitude_km

    # Different solar areas and resulting generation
    assert f1.measurements["PWR_SOLAR_W"].value != f2.measurements["PWR_SOLAR_W"].value


# ======================================================================
# 3. Determinism Across Independent Runs
# ======================================================================


def test_strict_fleet_determinism(seeded_db: Session):
    """Repeated runs with identical seed and inputs produce identical numerical telemetry."""
    configs1 = build_fleet_from_db(seeded_db)
    configs2 = build_fleet_from_db(seeded_db)

    engine1 = SimulationEngine(fleet_configs=configs1, seed=42)
    engine2 = SimulationEngine(fleet_configs=configs2, seed=42)

    engine1.start()
    engine2.start()

    for _ in range(50):
        frames1 = engine1.tick(dt=1.0)
        frames2 = engine2.tick(dt=1.0)

        for f1, f2 in zip(frames1, frames2, strict=True):
            assert f1.satellite_id == f2.satellite_id
            assert f1.latitude_deg == f2.latitude_deg
            assert f1.longitude_deg == f2.longitude_deg
            assert f1.is_in_eclipse == f2.is_in_eclipse
            for m_key in ["PWR_BUS_V", "PWR_SOLAR_W", "BATT_SOC", "TEMP_BUS_C", "ATT_RATE_DPS"]:
                v1 = float(f1.measurements[m_key].value)
                v2 = float(f2.measurements[m_key].value)
                assert abs(v1 - v2) < 1e-10, f"Mismatch in {m_key} for {f1.satellite_id}"


# ======================================================================
# 4. State Isolation Between Satellites
# ======================================================================


def test_no_cross_satellite_contamination(seeded_db: Session):
    """Perturbing state in SAT-001 has zero effect on SAT-002 or SAT-003."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    # Step 10 ticks normally
    for _ in range(10):
        engine.tick(dt=1.0)

    # Force SAT-001 into SAFE_MODE by setting low SOC and reaching persistence threshold
    sat1_state = engine._satellite_states["SAT-001"]
    sat1_state.low_soc_ticks = 59
    sat1_state.power.battery_soc_pct = 15.0
    sat1_state.power.battery_energy_wh = 15.0 / 100.0 * sat1_state.power.battery_capacity_wh

    # Advance 5 more ticks
    frames = []
    for _ in range(5):
        frames = engine.tick(dt=1.0)

    f1 = next(f for f in frames if f.satellite_id == "SAT-001")
    f2 = next(f for f in frames if f.satellite_id == "SAT-002")
    f3 = next(f for f in frames if f.satellite_id == "SAT-003")

    assert f1.operational_mode == "SAFE_MODE"
    assert f2.operational_mode == "NOMINAL"
    assert f3.operational_mode == "NOMINAL"


# ======================================================================
# 5. Telemetry Persistence Integration
# ======================================================================


def test_telemetry_batch_persistence(seeded_db: Session):
    """Telemetry frames generated by the engine persist cleanly into the database."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    # Run 5 ticks and persist all frames
    all_persisted = []
    for _ in range(5):
        frames = engine.tick(dt=1.0)
        samples = persist_telemetry_batch(seeded_db, frames)
        all_persisted.extend(samples)

    assert len(all_persisted) == 15  # 5 ticks * 3 satellites

    # Query through TelemetryRepository
    repo = TelemetryRepository(seeded_db)
    sat1_history = repo.get_history("SAT-001", limit=100)
    assert len(sat1_history) == 5

    # Check values match
    for idx, sample in enumerate(sat1_history):
        assert sample.sequence_number == idx + 1
        assert sample.pwr_bus_v > 20.0
        assert sample.batt_soc > 0.0
        assert "measurements" in sample.metrics_payload


# ======================================================================
# 6. Requirements Traceability Verification Cases
# ======================================================================


def test_tc_04_simulation_tick_integration(seeded_db: Session):
    """TC-04 (FR-004): Deterministic simulation tick advances all subsystems simultaneously."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    initial_time = engine.clock.sim_time_s
    frames = engine.tick(dt=1.0)

    assert engine.clock.sim_time_s == initial_time + 1.0
    assert len(frames) == 3
    for frame in frames:
        # All 5 subsystems must be reflected in health and measurements
        assert set(frame.subsystem_health.keys()) == {
            "POWER",
            "THERMAL",
            "ADCS",
            "COMMS",
            "PAYLOAD",
        }
        assert frame.sequence_number == 1


def test_tc_05_simulation_clock_controls(seeded_db: Session):
    """TC-05 (FR-005): Clock controls (start, pause, resume, step, warp)."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)

    # 1. Initially stopped
    assert engine.clock.is_running is False
    assert engine.tick() == []

    # 2. Start
    engine.start()
    assert engine.clock.is_running is True
    frames = engine.tick(dt=1.0)
    assert len(frames) == 3
    assert engine.clock.sim_time_s == 1.0

    # 3. Pause
    engine.pause()
    assert engine.clock.is_paused is True
    assert engine.tick(dt=1.0) == []
    assert engine.clock.sim_time_s == 1.0

    # 4. Step while paused
    stepped = engine.step()
    assert len(stepped) == 3
    assert engine.clock.sim_time_s == 2.0

    # 5. Time warp
    engine.resume()
    engine.set_time_warp(10.0)
    assert engine.clock.time_warp == 10.0
    engine.tick()  # advances by default_dt (1.0 s)
    assert engine.clock.sim_time_s == 3.0


def test_tc_06_orbital_propagation_and_eclipse(seeded_db: Session):
    """TC-06 (FR-006): Orbit propagation accurately transitions between light and eclipse."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    # Step through ~5000 seconds (roughly one complete LEO orbit: ~5700 s)
    eclipse_transitions = 0
    prev_eclipse = None

    for _ in range(120):
        frames = engine.tick(dt=50.0)
        f1 = next(f for f in frames if f.satellite_id == "SAT-001")
        if prev_eclipse is not None and f1.is_in_eclipse != prev_eclipse:
            eclipse_transitions += 1
        prev_eclipse = f1.is_in_eclipse

    # In a full orbit, a satellite must cross into shadow and back out (at least 2 transitions)
    assert eclipse_transitions >= 2


def test_tc_07_coupled_subsystem_telemetry(seeded_db: Session):
    """TC-07 (FR-007): Coupled subsystem dynamics (sunlight -> solar -> batt -> thermal)."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    # Find a tick in sunlight and a tick in eclipse for SAT-001
    sunlight_solar = None
    eclipse_solar = None

    for _ in range(120):
        frames = engine.tick(dt=50.0)
        f = next(fr for fr in frames if fr.satellite_id == "SAT-001")
        solar = f.measurements["PWR_SOLAR_W"].value
        if not f.is_in_eclipse and sunlight_solar is None:
            sunlight_solar = solar
        elif f.is_in_eclipse and eclipse_solar is None:
            eclipse_solar = solar

        if sunlight_solar is not None and eclipse_solar is not None:
            break

    assert sunlight_solar is not None and sunlight_solar > 200.0
    assert eclipse_solar is not None and eclipse_solar < 5.0


def test_tc_12_autonomous_safe_mode_transition(seeded_db: Session):
    """TC-12 (FR-012): Autonomous emergency safe-mode transition on threshold violation."""
    configs = build_fleet_from_db(seeded_db)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()

    # Force low SOC on SAT-003 and reach persistence threshold (60 ticks)
    sat3_state = engine._satellite_states["SAT-003"]
    sat3_state.low_soc_ticks = 59
    sat3_state.power.battery_soc_pct = 19.5  # Critical threshold is < 20%
    sat3_state.power.battery_energy_wh = 19.5 / 100.0 * sat3_state.power.battery_capacity_wh

    frames = engine.tick(dt=1.0)
    f3 = next(f for f in frames if f.satellite_id == "SAT-003")

    assert f3.operational_mode == "SAFE_MODE"
    assert f3.subsystem_health["POWER"] == "CRITICAL"
