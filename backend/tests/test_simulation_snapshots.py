"""Tests for OrbitOps Phase 03 -- Simulation State Snapshot and Checkpoint System.

Covers:
  - SimulationSnapshot creation and metadata serialization
  - JSON serialization and deserialization round-trip
  - Schema version enforcement and integrity validation
  - Corrupted snapshot rejection (atomic safety: active state remains unmodified)
  - Deterministic continuation (restoration produces identical future states)
  - Snapshot inspection non-mutability
"""

from __future__ import annotations

import pytest

from app.simulation.engine import SimulationEngine
from app.simulation.fleet import build_default_fleet
from app.simulation.snapshots import (
    SNAPSHOT_SCHEMA_VERSION,
    SimulationSnapshot,
    validate_snapshot_integrity,
)


@pytest.fixture
def running_engine() -> SimulationEngine:
    """Provide an engine initialized and advanced by 25 ticks."""
    fleet = build_default_fleet()
    eng = SimulationEngine(fleet_configs=fleet, seed=42)
    eng.start()
    for _ in range(25):
        eng.tick(dt=1.0)
    return eng


# ======================================================================
# 1. Snapshot Capture & Serialization
# ======================================================================


def test_capture_snapshot_structure(running_engine: SimulationEngine):
    """Snapshot contains valid clock, satellite states, and schema version."""
    snapshot = running_engine.capture_snapshot(metadata={"operator": "test", "phase": 3})

    assert snapshot.schema_version == SNAPSHOT_SCHEMA_VERSION
    assert snapshot.get_sim_time_s() == 25.0
    assert snapshot.get_tick_count() == 25
    assert set(snapshot.get_satellite_ids()) == {"SAT-001", "SAT-002", "SAT-003"}
    assert snapshot.metadata == {"operator": "test", "phase": 3}


def test_snapshot_json_roundtrip(running_engine: SimulationEngine):
    """Snapshot survives serialization to JSON and deserialization without data loss."""
    snapshot_orig = running_engine.capture_snapshot(metadata={"run_id": "exp-42"})
    json_str = snapshot_orig.to_json()

    snapshot_restored = SimulationSnapshot.from_json(json_str)

    assert snapshot_restored.schema_version == snapshot_orig.schema_version
    assert snapshot_restored.get_sim_time_s() == snapshot_orig.get_sim_time_s()
    assert snapshot_restored.get_tick_count() == snapshot_orig.get_tick_count()
    assert snapshot_restored.get_satellite_ids() == snapshot_orig.get_satellite_ids()
    assert snapshot_restored.metadata == snapshot_orig.metadata


def test_snapshot_rejects_incompatible_schema_version():
    """Deserializer rejects snapshot with incompatible schema version."""
    invalid_data = {
        "schema_version": "1.0.0-incompatible",
        "captured_at_iso": "2026-10-27T00:00:00Z",
        "clock_state": {},
        "satellite_states": {},
        "metadata": {},
    }
    with pytest.raises(ValueError, match="version mismatch"):
        SimulationSnapshot.from_dict(invalid_data)


# ======================================================================
# 2. Integrity Validation
# ======================================================================


def test_validate_valid_snapshot(running_engine: SimulationEngine):
    """Integrity check returns no issues for a valid snapshot."""
    snapshot = running_engine.capture_snapshot()
    issues = validate_snapshot_integrity(snapshot)
    assert issues == []


def test_validate_corrupted_clock_state(running_engine: SimulationEngine):
    """Integrity check detects invalid/missing clock parameters."""
    snapshot = running_engine.capture_snapshot()
    snapshot.clock_state["sim_time_s"] = -10.0  # Invalid negative sim_time

    issues = validate_snapshot_integrity(snapshot)
    assert any("sim_time_s" in issue for issue in issues)


def test_validate_corrupted_satellite_state(running_engine: SimulationEngine):
    """Integrity check detects unphysical satellite telemetry parameters."""
    snapshot = running_engine.capture_snapshot()
    snapshot.satellite_states["SAT-001"]["power"]["battery_soc_pct"] = 150.0  # Unphysical SOC

    issues = validate_snapshot_integrity(snapshot)
    assert any("SOC" in issue for issue in issues)


def test_engine_restore_corrupted_fails_atomically(running_engine: SimulationEngine):
    """Restoring an invalid snapshot raises ValueError and preserves original engine state."""
    orig_time = running_engine.clock.sim_time_s
    corrupted_snapshot = running_engine.capture_snapshot()
    corrupted_snapshot.clock_state["sim_time_s"] = -5.0

    with pytest.raises(ValueError, match="integrity validation failed"):
        running_engine.restore_from_snapshot(corrupted_snapshot)

    # Active engine state must be unchanged
    assert running_engine.clock.sim_time_s == orig_time


# ======================================================================
# 3. Deterministic Continuation
# ======================================================================


def test_deterministic_continuation():
    """Restoring a snapshot into independent engine produces identical state trajectory."""
    # Engine 1: Continuous execution to 60 ticks
    fleet1 = build_default_fleet()
    engine_continuous = SimulationEngine(fleet_configs=fleet1, seed=42)
    engine_continuous.start()

    # Run for 30 ticks
    for _ in range(30):
        engine_continuous.tick(dt=1.0)

    # Capture snapshot at tick 30
    snapshot_at_30 = engine_continuous.capture_snapshot()

    # Advance continuous engine for 30 more ticks (total 60 ticks)
    for _ in range(30):
        engine_continuous.tick(dt=1.0)

    # Engine 2: Restore from snapshot at tick 30 and advance 30 ticks
    fleet2 = build_default_fleet()
    engine_restored = SimulationEngine(fleet_configs=fleet2, seed=42)
    engine_restored.restore_from_snapshot(snapshot_at_30)
    engine_restored.start()

    for _ in range(30):
        engine_restored.tick(dt=1.0)

    # Compare all satellites at tick 60
    assert engine_restored.clock.tick_count == engine_continuous.clock.tick_count
    assert engine_restored.clock.sim_time_s == engine_continuous.clock.sim_time_s

    for sat_id in ["SAT-001", "SAT-002", "SAT-003"]:
        state_cont = engine_continuous.get_satellite_state(sat_id)
        state_rest = engine_restored.get_satellite_state(sat_id)

        # Orbit match
        assert abs(state_cont.orbital.true_anomaly_rad - state_rest.orbital.true_anomaly_rad) < 1e-9
        assert abs(state_cont.orbital.latitude_deg - state_rest.orbital.latitude_deg) < 1e-9

        # Power match
        assert abs(state_cont.power.battery_soc_pct - state_rest.power.battery_soc_pct) < 1e-9
        assert abs(state_cont.power.solar_power_w - state_rest.power.solar_power_w) < 1e-9

        # Thermal match
        assert abs(state_cont.thermal.bus_temp_k - state_rest.thermal.bus_temp_k) < 1e-9

        # ADCS match
        assert abs(state_cont.adcs.angular_rate_dps - state_rest.adcs.angular_rate_dps) < 1e-9
        assert state_cont.adcs.pointing_mode == state_rest.adcs.pointing_mode


def test_snapshot_inspection_does_not_mutate_engine(running_engine: SimulationEngine):
    """Inspecting snapshot attributes or modifying snapshot dictionary has zero effect on engine."""
    snapshot = running_engine.capture_snapshot()
    snapshot_dict = snapshot.to_dict()

    snapshot_dict["clock_state"]["sim_time_s"] = 9999.0
    snapshot_dict["satellite_states"]["SAT-001"]["power"]["battery_soc_pct"] = 0.0

    state = running_engine.get_satellite_state("SAT-001")
    assert state.power.battery_soc_pct != 0.0
    assert running_engine.clock.sim_time_s == 25.0
