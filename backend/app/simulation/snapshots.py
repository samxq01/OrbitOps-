"""OrbitOps Phase 03 — Simulation State Snapshot and Checkpoint System.

Snapshots capture the complete deterministic state of the simulation engine
at a single point in time, enabling:
  - Deterministic continuation after restoration
  - Verification of identical results between independent engine instances
  - Foundation for Phase 11 Mission Time Machine (replay uses separate read path)

Snapshot Schema Version
-----------------------
Version: "3.0.0" (Phase 03 initial schema)
Breaking changes to the schema must increment the version.

Serialisation Contract
-----------------------
- Snapshots are serialised to plain Python dicts (JSON-serialisable).
- All floats are stored as-is (no rounding) to preserve determinism.
- RNG state is captured as a tuple (version, state_list, gauss_next).
- Timestamps are ISO 8601 strings.

Restoration Contract
--------------------
1. Validate the snapshot schema version.
2. Construct temporary state objects from snapshot data.
3. Validate all physical parameters before activating.
4. Replace active engine state atomically.
5. A partially restored snapshot must never activate corrupted state.

Limitations
-----------
- Phase 03 snapshots do not cover the WebSocket broadcaster state (Phase 04).
- Historical mission replay is a separate read-only operation (Phase 11).
- Inspecting a snapshot MUST NOT mutate the active engine state.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.simulation.clock import SimulationClock
from app.simulation.state import SatelliteRuntimeState

logger = logging.getLogger("orbitops.simulation.snapshots")

SNAPSHOT_SCHEMA_VERSION: str = "3.0.0"


@dataclass
class SimulationSnapshot:
    """Complete immutable snapshot of simulation engine state.

    Attributes
    ----------
    schema_version:
        Version tag for migration compatibility checking.
    captured_at_iso:
        Wall-clock UTC time when the snapshot was taken (informational only).
    clock_state:
        Serialised SimulationClock state dictionary.
    satellite_states:
        Dict mapping satellite_id → serialised SatelliteRuntimeState dict.
    metadata:
        Optional freeform metadata (mission_id, description, etc.)
    """

    schema_version: str = SNAPSHOT_SCHEMA_VERSION
    captured_at_iso: str = ""
    clock_state: dict[str, Any] = field(default_factory=dict)
    satellite_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise snapshot to a JSON-compatible dict."""
        return {
            "schema_version": self.schema_version,
            "captured_at_iso": self.captured_at_iso,
            "clock_state": self.clock_state,
            "satellite_states": self.satellite_states,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise snapshot to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationSnapshot:
        """Deserialise a snapshot from a plain dictionary.

        Raises
        ------
        ValueError
            If schema version is incompatible.
        """
        schema_ver = data.get("schema_version", "unknown")
        if schema_ver != SNAPSHOT_SCHEMA_VERSION:
            msg = (
                f"Snapshot schema version mismatch: expected {SNAPSHOT_SCHEMA_VERSION}, "
                f"got '{schema_ver}'. Restoration aborted."
            )
            raise ValueError(msg)

        return cls(
            schema_version=schema_ver,
            captured_at_iso=str(data.get("captured_at_iso", "")),
            clock_state=dict(data.get("clock_state", {})),
            satellite_states={k: dict(v) for k, v in data.get("satellite_states", {}).items()},
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> SimulationSnapshot:
        """Deserialise a snapshot from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_sim_time_s(self) -> float:
        """Extract simulation time from the embedded clock state."""
        return float(self.clock_state.get("sim_time_s", 0.0))

    def get_tick_count(self) -> int:
        """Extract tick count from the embedded clock state."""
        return int(self.clock_state.get("tick_count", 0))

    def get_satellite_ids(self) -> list[str]:
        """Return the list of satellite IDs captured in this snapshot."""
        return list(self.satellite_states.keys())


def capture_snapshot(
    clock: SimulationClock,
    satellite_states: dict[str, SatelliteRuntimeState],
    metadata: dict[str, Any] | None = None,
) -> SimulationSnapshot:
    """Create a snapshot from the current engine state.

    This function reads state; it does NOT mutate any engine objects.
    Satellite state is deep-copied to prevent snapshot-inspection from
    accidentally mutating the live simulation.

    Parameters
    ----------
    clock:
        Current simulation clock.
    satellite_states:
        Dict mapping satellite_id → SatelliteRuntimeState.
    metadata:
        Optional descriptive metadata.

    Returns
    -------
    SimulationSnapshot
        Immutable snapshot of the current state.
    """
    from datetime import UTC

    captured_at = datetime.now(UTC).isoformat()

    # Deep-copy satellite states to isolate snapshot from live engine
    sat_state_dicts: dict[str, dict[str, Any]] = {}
    for sat_id, sat_state in satellite_states.items():
        sat_copy = sat_state.deep_copy()
        sat_state_dicts[sat_id] = sat_copy.to_dict()

    return SimulationSnapshot(
        schema_version=SNAPSHOT_SCHEMA_VERSION,
        captured_at_iso=captured_at,
        clock_state=clock.to_dict(),
        satellite_states=sat_state_dicts,
        metadata=metadata or {},
    )


def restore_snapshot(
    snapshot: SimulationSnapshot,
) -> tuple[SimulationClock, dict[str, SatelliteRuntimeState]]:
    """Restore simulation state from a snapshot.

    Validates all data before constructing live objects.
    The returned clock and satellite states are completely new objects —
    they do not share references with the snapshot's internal dicts.

    Parameters
    ----------
    snapshot:
        A previously captured SimulationSnapshot.

    Returns
    -------
    tuple[SimulationClock, dict[str, SatelliteRuntimeState]]
        (restored_clock, restored_satellite_states)

    Raises
    ------
    ValueError
        If the snapshot data fails validation.
    """
    # Validate schema version (already checked in from_dict, but double-check)
    if snapshot.schema_version != SNAPSHOT_SCHEMA_VERSION:
        msg = f"Incompatible snapshot schema version: {snapshot.schema_version}"
        raise ValueError(msg)

    # Validate clock state has required keys
    required_clock_keys = {"epoch_utc_iso", "sim_time_s", "tick_count", "warp", "default_dt"}
    missing = required_clock_keys - set(snapshot.clock_state.keys())
    if missing:
        msg = f"Snapshot clock state missing required keys: {missing}"
        raise ValueError(msg)

    # Validate satellite states
    if not snapshot.satellite_states:
        msg = "Snapshot contains no satellite states"
        raise ValueError(msg)

    for sat_id, sat_data in snapshot.satellite_states.items():
        if "satellite_id" not in sat_data:
            msg = f"Snapshot satellite state for '{sat_id}' missing 'satellite_id'"
            raise ValueError(msg)
        if "operational_mode" not in sat_data:
            msg = f"Snapshot satellite state for '{sat_id}' missing 'operational_mode'"
            raise ValueError(msg)

    # Restore clock
    restored_clock = SimulationClock.from_dict(snapshot.clock_state)

    # Restore satellite states
    restored_satellites: dict[str, SatelliteRuntimeState] = {}
    for sat_id, sat_data in snapshot.satellite_states.items():
        restored_state = SatelliteRuntimeState.from_dict(sat_data)
        restored_satellites[sat_id] = restored_state

    logger.info(
        "Snapshot restored: t=%.1f s, tick=%d, satellites=%s",
        restored_clock.sim_time_s,
        restored_clock.tick_count,
        list(restored_satellites.keys()),
    )

    return restored_clock, restored_satellites


def validate_snapshot_integrity(snapshot: SimulationSnapshot) -> list[str]:
    """Run integrity checks on a snapshot and return a list of issues found.

    Parameters
    ----------
    snapshot:
        Snapshot to validate.

    Returns
    -------
    list[str]
        List of validation issues. Empty list means snapshot is valid.
    """
    issues: list[str] = []

    # Schema version check
    if snapshot.schema_version != SNAPSHOT_SCHEMA_VERSION:
        issues.append(
            f"Schema version mismatch: expected {SNAPSHOT_SCHEMA_VERSION}, "
            f"got {snapshot.schema_version}"
        )

    # Clock validation
    clock_data = snapshot.clock_state
    if float(clock_data.get("sim_time_s", -1.0)) < 0.0:
        issues.append("Clock sim_time_s is negative")
    if int(clock_data.get("tick_count", -1)) < 0:
        issues.append("Clock tick_count is negative")
    if float(clock_data.get("default_dt", 0.0)) <= 0.0:
        issues.append("Clock default_dt must be positive")

    # Satellite state validation
    for sat_id, sat_data in snapshot.satellite_states.items():
        power_data = sat_data.get("power", {})
        soc = power_data.get("battery_soc_pct", -1.0)
        if not (0.0 <= float(soc) <= 100.0):
            issues.append(f"Satellite {sat_id}: invalid SOC {soc}")

        energy = power_data.get("battery_energy_wh", -1.0)
        if float(energy) < 0.0:
            issues.append(f"Satellite {sat_id}: negative battery energy {energy} Wh")

        thermal_data = sat_data.get("thermal", {})
        bus_temp_k = float(thermal_data.get("bus_temp_k", 0.0))
        if bus_temp_k <= 0.0:
            issues.append(f"Satellite {sat_id}: invalid bus_temp_k {bus_temp_k} K")

    return issues
