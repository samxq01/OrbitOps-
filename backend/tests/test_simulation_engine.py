"""Tests for OrbitOps Phase 03 -- Simulation Engine Core.

Covers:
  - SimulationEngine initialisation & input validation
  - Simulation clock control (start, pause, resume, reset, warp)
  - Tick and step execution
  - Subsystem coupling (orbit -> eclipse -> ADCS -> power -> thermal -> health)
  - Autonomous mode transitions (safe-mode threshold behavior)
  - State isolation and immutability of returned copies
  - In-memory numerical stability (no NaN/Inf, bounds checks)
"""

from __future__ import annotations

import math

import pytest

from app.simulation.engine import SatelliteConfig, SimulationEngine
from app.simulation.fleet import build_default_fleet


@pytest.fixture
def sample_fleet() -> list[SatelliteConfig]:
    """Provide standard three-satellite fleet configs."""
    return build_default_fleet()


@pytest.fixture
def engine(sample_fleet: list[SatelliteConfig]) -> SimulationEngine:
    """Create a configured engine with default seed."""
    return SimulationEngine(fleet_configs=sample_fleet, seed=42)


# ======================================================================
# 1. Initialisation and Input Validation
# ======================================================================


def test_engine_init_requires_satellites():
    """Engine must reject empty satellite fleet configuration."""
    with pytest.raises(ValueError, match="requires at least one satellite"):
        SimulationEngine(fleet_configs=[], seed=42)


def test_engine_init_populates_satellites(engine: SimulationEngine):
    """Engine properly initialises all satellite IDs and clocks."""
    assert engine.satellite_ids == ["SAT-001", "SAT-002", "SAT-003"]
    assert engine.clock.tick_count == 0
    assert engine.clock.sim_time_s == 0.0
    assert engine.clock.is_running is False


def test_engine_init_rejects_invalid_orbit():
    """Engine must reject configurations with unphysical orbital parameters."""
    bad_config = SatelliteConfig(
        satellite_id="SAT-BAD",
        satellite_name="BAD-SAT",
        mission_id="MIS-001",
        semi_major_axis_km=5000.0,  # Below Earth radius (6378.137 km)
        inclination_deg=51.6,
        mass_kg=100.0,
        battery_capacity_wh=500.0,
        solar_area_m2=2.0,
    )
    with pytest.raises(ValueError, match="[Ss]emi-major axis"):
        SimulationEngine(fleet_configs=[bad_config], seed=42)


# ======================================================================
# 2. Clock Control & Advancement
# ======================================================================


def test_engine_pause_and_step(engine: SimulationEngine):
    """Paused engine produces no frames on tick(), but step() forces advancement."""
    engine.start()
    frames = engine.tick()
    assert len(frames) == 3
    assert engine.clock.tick_count == 1

    engine.pause()
    assert engine.clock.is_paused is True

    # tick() while paused returns empty list and does not advance time
    paused_frames = engine.tick()
    assert paused_frames == []
    assert engine.clock.tick_count == 1

    # step() advances by 1 dt regardless of paused state
    stepped_frames = engine.step()
    assert len(stepped_frames) == 3
    assert engine.clock.tick_count == 2
    assert engine.clock.sim_time_s == 2.0


def test_engine_resume(engine: SimulationEngine):
    """Resuming paused engine allows normal ticking."""
    engine.start()
    engine.tick()
    engine.pause()
    assert engine.tick() == []

    engine.resume()
    frames = engine.tick()
    assert len(frames) == 3
    assert engine.clock.tick_count == 2


def test_engine_reset(engine: SimulationEngine, sample_fleet: list[SatelliteConfig]):
    """Resetting engine returns clock and state to initial conditions."""
    engine.start()
    for _ in range(10):
        engine.tick()
    assert engine.clock.tick_count == 10

    engine.reset(fleet_configs=sample_fleet)
    assert engine.clock.tick_count == 0
    assert engine.clock.sim_time_s == 0.0
    state = engine.get_satellite_state("SAT-001")
    assert state.power.battery_soc_pct == 80.0


def test_engine_tick_n(engine: SimulationEngine):
    """tick_n advances by exactly n steps."""
    engine.start()
    frame_batches = engine.tick_n(15)
    assert len(frame_batches) == 15
    assert engine.clock.tick_count == 15
    assert engine.clock.sim_time_s == 15.0

    with pytest.raises(ValueError, match="positive"):
        engine.tick_n(0)


# ======================================================================
# 3. State Isolation and Immutability
# ======================================================================


def test_get_satellite_state_returns_deep_copy(engine: SimulationEngine):
    """Mutating returned state copy must not affect internal engine state."""
    state1 = engine.get_satellite_state("SAT-001")
    state1.power.battery_soc_pct = 12.34

    state2 = engine.get_satellite_state("SAT-001")
    assert state2.power.battery_soc_pct == 80.0


def test_get_unknown_satellite_raises(engine: SimulationEngine):
    """Querying unknown satellite raises KeyError."""
    with pytest.raises(KeyError, match="SAT-999"):
        engine.get_satellite_state("SAT-999")


def test_satellite_states_are_independent(engine: SimulationEngine):
    """State evolution of SAT-001 does not mutate or affect SAT-002."""
    engine.start()
    frames = engine.tick()
    f1 = next(f for f in frames if f.satellite_id == "SAT-001")
    f2 = next(f for f in frames if f.satellite_id == "SAT-002")

    # SAT-001 is sunlit, SAT-002 is in eclipse
    assert f1.is_in_eclipse != f2.is_in_eclipse
    assert f1.measurements["PWR_SOLAR_W"].value > 200.0
    assert f2.measurements["PWR_SOLAR_W"].value < 5.0


# ======================================================================
# 4. Subsystem Coupling & Health Progression
# ======================================================================


def test_subsystem_coupling_in_tick(engine: SimulationEngine):
    """Verify that a tick updates all subsystem properties and generates telemetry."""
    engine.start()
    frames = engine.tick(dt=1.0)
    assert len(frames) == 3

    for frame in frames:
        m = frame.measurements
        assert "PWR_BUS_V" in m
        assert "BATT_SOC" in m
        assert "PWR_SOLAR_W" in m
        assert "TEMP_BUS_C" in m
        assert "TEMP_PL_C" in m
        assert "ATT_RATE_DPS" in m
        assert "RF_SNR_DB" in m

        # Check telemetry limits
        assert 20.0 <= m["PWR_BUS_V"].value <= 35.0
        assert 0.0 <= m["BATT_SOC"].value <= 100.0
        assert frame.subsystem_health["POWER"] in {"NOMINAL", "WARNING", "CRITICAL"}


def test_autonomous_safemode_on_low_battery():
    """Engine autonomously transitions to SAFE_MODE when battery SOC sustains critical level."""
    fleet = [
        SatelliteConfig(
            satellite_id="SAT-LOW-BATT",
            satellite_name="LOW-BATT-SAT",
            mission_id="MIS-001",
            semi_major_axis_km=6928.137,
            inclination_deg=51.6,
            mass_kg=100.0,
            battery_capacity_wh=100.0,
            solar_area_m2=1.0,
            initial_mode="NOMINAL",
            initial_battery_soc_pct=19.0,
        )
    ]
    eng = SimulationEngine(fleet_configs=fleet, seed=42)
    eng.start()

    # Pre-set low_soc_ticks near persistence threshold (60 ticks)
    eng._satellite_states["SAT-LOW-BATT"].low_soc_ticks = 59
    eng._satellite_states["SAT-LOW-BATT"].power.battery_soc_pct = 19.0

    frames = eng.tick(dt=1.0)
    assert frames[0].operational_mode == "SAFE_MODE"


def test_adcs_switches_to_sun_pointing_in_safe_mode():
    """When satellite enters SAFE_MODE from NADIR_POINTING, ADCS switches to SUN_POINTING."""
    fleet = [
        SatelliteConfig(
            satellite_id="SAT-ADCS-REC",
            satellite_name="ADCS-REC-SAT",
            mission_id="MIS-001",
            semi_major_axis_km=6928.137,
            inclination_deg=51.6,
            mass_kg=100.0,
            battery_capacity_wh=50.0,
            solar_area_m2=1.0,
            initial_mode="NOMINAL",
            initial_battery_soc_pct=19.0,
            initial_adcs_mode="NADIR_POINTING",
        )
    ]
    eng = SimulationEngine(fleet_configs=fleet, seed=42)
    eng.start()

    # Pre-set low_soc_ticks to trigger safe mode on tick
    eng._satellite_states["SAT-ADCS-REC"].low_soc_ticks = 59
    eng._satellite_states["SAT-ADCS-REC"].power.battery_soc_pct = 19.0

    eng.tick(dt=1.0)
    state = eng.get_satellite_state("SAT-ADCS-REC")
    assert state.operational_mode == "SAFE_MODE"
    assert state.adcs.pointing_mode == "SUN_POINTING"


# ======================================================================
# 5. Stability & Extended Run
# ======================================================================


def test_extended_stability_200_ticks(engine: SimulationEngine):
    """Run 200 ticks and verify absence of NaN, Inf, and bounds violations."""
    engine.start()
    for tick_idx in range(200):
        frames = engine.tick(dt=1.0)
        assert len(frames) == 3
        for frame in frames:
            for mnemonic, param in frame.measurements.items():
                val = float(param.value)
                assert not math.isnan(val), (
                    f"NaN in {frame.satellite_id} {mnemonic} at tick {tick_idx}"
                )
                assert not math.isinf(val), (
                    f"Inf in {frame.satellite_id} {mnemonic} at tick {tick_idx}"
                )

            soc = frame.measurements["BATT_SOC"].value
            assert 0.0 <= soc <= 100.0, f"SOC {soc} out of range in tick {tick_idx}"

            bus_v = frame.measurements["PWR_BUS_V"].value
            assert 20.0 <= bus_v <= 35.0, f"Bus voltage {bus_v} unphysical in tick {tick_idx}"
