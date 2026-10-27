"""OrbitOps Phase 03 — Deterministic Satellite Digital Twin Simulation Engine.

This package implements the pure-domain simulation core. All modules in this
package are independent of FastAPI, HTTP requests, and database sessions.
Physics calculations operate exclusively on simulation domain objects.

Module hierarchy:
    clock       — Deterministic simulation clock with warp and step control
    orbit       — Two-body circular orbit propagator and coordinate conversion
    eclipse     — Cylindrical Earth-shadow detection
    power       — Solar array, battery SOC, and bus voltage model
    thermal     — Lumped thermal energy balance with heater hysteresis
    adcs        — Attitude determination and control subsystem dynamics
    communications — Transmitter state and simplified link quality
    payload     — Instrument power consumption and data accumulation
    health      — Subsystem threshold evaluation and safe-mode transitions
    state       — Runtime satellite state dataclasses
    telemetry   — Telemetry frame generation from authoritative state
    snapshots   — Serialisation and restoration of deterministic simulation state
    engine      — Main simulation engine orchestrating all subsystems
"""

from app.simulation.clock import SimulationClock
from app.simulation.engine import SimulationEngine
from app.simulation.snapshots import SimulationSnapshot
from app.simulation.state import SatelliteRuntimeState

__all__ = [
    "SimulationClock",
    "SimulationEngine",
    "SimulationSnapshot",
    "SatelliteRuntimeState",
]
