"""OrbitOps Phase 03 — Telemetry Frame Generation.

Telemetry frames are derived exclusively from authoritative simulation state.
No values are fabricated or injected at this layer.

Telemetry Mnemonic Registry
-----------------------------
PWR_BUS_V      Bus voltage [V]
PWR_SOLAR_W    Solar generation [W]
BATT_SOC       Battery state of charge [%]
BATT_TEMP_C    Battery temperature (estimated from bus thermal state) [°C]
TEMP_BUS_C     Spacecraft bus temperature [°C]
TEMP_PL_C      Payload instrument temperature [°C]
ATT_RATE_DPS   Angular rate magnitude [°/s]
RF_SNR_DB      RF signal-to-noise ratio [dB] (local estimate in Phase 03)
IS_IN_ECLIPSE  Eclipse state flag [bool]

Sensor Noise
------------
Phase 03 applies minimal deterministic Gaussian noise (σ ≈ 0.1–0.5% of range)
to distinguish "true physical state" from "measured telemetry value".
The underlying physics state and the measured value are SEPARATE variables.
Noise seeds are derived from (satellite_rng, tick_count) for determinism.
The advanced sensor corruption / SEU scenario belongs to Phase 07.

Frame Structure
---------------
Each frame contains:
  - satellite_id, mission_id
  - sim_timestamp (deterministic simulation time)
  - sequence_number (monotonically increasing per satellite)
  - operational_mode
  - subsystem_health dict
  - measurements dict (mnemonic → value with unit)
  - raw_state dict (true underlying physics, for engine-internal use)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.simulation.state import SatelliteRuntimeState


@dataclass
class TelemetryMeasurement:
    """Single telemetry parameter measurement."""

    mnemonic: str
    value: float | bool
    unit: str
    description: str = ""


@dataclass
class TelemetryFrame:
    """Complete telemetry snapshot for one satellite at one simulation tick.

    This is the primary output type from the simulation engine.
    All values originate from the authoritative simulation state.
    """

    satellite_id: str
    mission_id: str
    satellite_name: str
    sim_timestamp: datetime  # Deterministic simulation UTC time
    sequence_number: int
    operational_mode: str

    # Individual measurements (mnemonic → TelemetryMeasurement)
    measurements: dict[str, TelemetryMeasurement] = field(default_factory=dict)

    # Subsystem health statuses
    subsystem_health: dict[str, str] = field(default_factory=dict)

    # Derived flags
    is_in_eclipse: bool = False

    # Orbital position
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    altitude_km: float = 0.0

    # Events generated during this tick
    events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise frame to a plain dictionary for API and persistence."""
        return {
            "satellite_id": self.satellite_id,
            "mission_id": self.mission_id,
            "satellite_name": self.satellite_name,
            "sim_timestamp": self.sim_timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "operational_mode": self.operational_mode,
            "is_in_eclipse": self.is_in_eclipse,
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "altitude_km": self.altitude_km,
            "subsystem_health": self.subsystem_health,
            "events": self.events,
            "measurements": {
                k: {
                    "mnemonic": v.mnemonic,
                    "value": v.value,
                    "unit": v.unit,
                    "description": v.description,
                }
                for k, v in self.measurements.items()
            },
        }

    def get_value(self, mnemonic: str, default: float = 0.0) -> float | bool:
        """Retrieve a measurement value by mnemonic."""
        m = self.measurements.get(mnemonic)
        if m is None:
            return default
        return m.value


def _add_noise(value: float, sigma: float, rng: random.Random) -> float:
    """Add Gaussian noise to a measurement.

    Parameters
    ----------
    value:
        True physical state value.
    sigma:
        Standard deviation of sensor noise.
    rng:
        Satellite-specific seeded RNG.

    Returns
    -------
    float
        Measured value with noise applied.
    """
    if sigma <= 0.0:
        return value
    return value + rng.gauss(0.0, sigma)


def generate_telemetry_frame(
    state: SatelliteRuntimeState,
    sim_timestamp: datetime,
    events: list[str] | None = None,
) -> TelemetryFrame:
    """Generate a complete telemetry frame from authoritative simulation state.

    Noise is applied deterministically using state.satellite_rng.
    The underlying physics state (state.power, state.thermal, etc.) is NOT
    modified by this function — it is read-only from this perspective.

    Parameters
    ----------
    state:
        Complete satellite runtime state (authoritative source).
    sim_timestamp:
        Current simulation UTC timestamp (from clock, NOT datetime.now()).
    events:
        Optional list of events generated during this tick.

    Returns
    -------
    TelemetryFrame
        Complete telemetry snapshot with all measurements.
    """
    rng = state.satellite_rng  # Use satellite's own seeded RNG for noise

    # Increment sequence counter (mutates state — this is intentional)
    state.telemetry_sequence += 1

    # --- Power measurements ---
    bus_v_measured = _add_noise(state.power.bus_voltage_v, sigma=0.02, rng=rng)
    solar_w_measured = _add_noise(state.power.solar_power_w, sigma=0.5, rng=rng)
    batt_soc_measured = _add_noise(state.power.battery_soc_pct, sigma=0.1, rng=rng)

    # Battery temperature (simplified: follows bus temp with slight offset)
    batt_temp_c = _add_noise(state.thermal.bus_temp_c - 2.0, sigma=0.3, rng=rng)

    # --- Thermal measurements ---
    bus_temp_measured = _add_noise(state.thermal.bus_temp_c, sigma=0.2, rng=rng)
    payload_temp_measured = _add_noise(state.thermal.payload_temp_c, sigma=0.3, rng=rng)

    # --- ADCS measurements ---
    rate_measured = _add_noise(state.adcs.angular_rate_dps, sigma=0.005, rng=rng)
    rate_measured = max(0.0, rate_measured)

    # --- Comms measurements ---
    snr_measured = _add_noise(state.comms.snr_db, sigma=0.1, rng=rng)

    # Assemble measurements dict
    measurements = {
        "PWR_BUS_V": TelemetryMeasurement(
            mnemonic="PWR_BUS_V",
            value=round(bus_v_measured, 3),
            unit="V",
            description="Power bus voltage",
        ),
        "PWR_SOLAR_W": TelemetryMeasurement(
            mnemonic="PWR_SOLAR_W",
            value=round(max(0.0, solar_w_measured), 2),
            unit="W",
            description="Solar array power generation",
        ),
        "BATT_SOC": TelemetryMeasurement(
            mnemonic="BATT_SOC",
            value=round(max(0.0, min(100.0, batt_soc_measured)), 2),
            unit="%",
            description="Battery state of charge",
        ),
        "BATT_TEMP_C": TelemetryMeasurement(
            mnemonic="BATT_TEMP_C",
            value=round(batt_temp_c, 2),
            unit="°C",
            description="Battery temperature (estimated)",
        ),
        "TEMP_BUS_C": TelemetryMeasurement(
            mnemonic="TEMP_BUS_C",
            value=round(bus_temp_measured, 2),
            unit="°C",
            description="Spacecraft bus temperature",
        ),
        "TEMP_PL_C": TelemetryMeasurement(
            mnemonic="TEMP_PL_C",
            value=round(payload_temp_measured, 2),
            unit="°C",
            description="Payload instrument temperature",
        ),
        "ATT_RATE_DPS": TelemetryMeasurement(
            mnemonic="ATT_RATE_DPS",
            value=round(rate_measured, 4),
            unit="°/s",
            description="Angular rate magnitude",
        ),
        "RF_SNR_DB": TelemetryMeasurement(
            mnemonic="RF_SNR_DB",
            value=round(max(0.0, snr_measured), 2),
            unit="dB",
            description="RF signal-to-noise ratio (local estimate, Phase 03)",
        ),
        "IS_IN_ECLIPSE": TelemetryMeasurement(
            mnemonic="IS_IN_ECLIPSE",
            value=state.is_in_eclipse,
            unit="bool",
            description="Satellite in Earth shadow",
        ),
    }

    subsystem_health = {
        "POWER": state.power.health_status,
        "THERMAL": state.thermal.health_status,
        "ADCS": state.adcs.health_status,
        "COMMS": state.comms.health_status,
        "PAYLOAD": state.payload.health_status,
    }

    return TelemetryFrame(
        satellite_id=state.satellite_id,
        mission_id=state.mission_id,
        satellite_name=state.satellite_name,
        sim_timestamp=sim_timestamp,
        sequence_number=state.telemetry_sequence,
        operational_mode=state.operational_mode,
        measurements=measurements,
        subsystem_health=subsystem_health,
        is_in_eclipse=state.is_in_eclipse,
        latitude_deg=state.orbital.latitude_deg,
        longitude_deg=state.orbital.longitude_deg,
        altitude_km=state.orbital.altitude_km,
        events=events or [],
    )
