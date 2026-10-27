"""OrbitOps Phase 03 — Deterministic Satellite Digital Twin Engine.

This is the main simulation orchestrator. It owns the simulation clock and
all satellite runtime states. It advances all subsystem models in a
documented, deterministic order.

Simulation Tick Update Order
-----------------------------
For each satellite, within each tick:
  1.  Propagate orbital position (beginning-of-tick orbital elements → new position)
  2.  Compute eclipse state (using new ECI position from step 1)
  3.  Update ADCS sun incidence angle (uses new orbital position and pointing mode)
  4.  Update ADCS angular rate (uses current pointing mode; disturbance from RNG)
  5.  Update payload state (mode-dependent; determines current power draw)
  6.  Update communications state (mode-dependent; determines current power draw)
  7.  Update heater state (uses PREVIOUS thermal state to avoid circularity)
  8.  Compute solar power (uses ADCS sun incidence from step 3 and eclipse from step 2)
  9.  Compute total load (uses ADCS, comms, payload, heater power from steps 4–7)
  10. Integrate battery energy (uses solar power from step 8 and total load from step 9)
  11. Compute bus voltage (uses new SOC from step 10)
  12. Integrate thermal state (uses total load as heat dissipation, eclipse state,
      heater state from step 7)
  13. Evaluate power health (uses new SOC from step 10)
  14. Evaluate thermal health (uses new thermal state from step 12)
  15. Evaluate ADCS health (uses new angular rate from step 4)
  16. Evaluate comms health (uses new comms state from step 6)
  17. Evaluate payload health (uses new payload state from step 5)
  18. Evaluate autonomous mode transitions (uses aggregated health, new SOC, new temp)
  19. Generate telemetry frame (uses all updated state from steps 1–18)

State Isolation
---------------
SAT-001, SAT-002, SAT-003 each have completely independent SatelliteRuntimeState
objects. They share no mutable state. This is enforced by the engine's dict
structure (separate keys) and the deep-copy initialisation.

Architectural Boundaries
------------------------
- The engine does NOT depend on FastAPI.
- The engine does NOT hold open SQLAlchemy sessions.
- Database integration is provided by a separate FleetAdapter class.
- REST endpoint exposure is Phase 04.
- WebSocket broadcasting is Phase 04.

Usage Example (standalone Python)
----------------------------------
    from app.simulation.engine import SimulationEngine
    from app.simulation.fleet import build_fleet_from_config

    configs = build_fleet_from_config(session)
    engine = SimulationEngine(fleet_configs=configs, seed=42)
    engine.start()
    for _ in range(100):
        frames = engine.tick()
    snapshot = engine.capture_snapshot()
    engine.pause()
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.simulation.adcs import (
    compute_sun_incidence,
    evaluate_adcs_health,
    integrate_angular_rate,
)
from app.simulation.clock import SimulationClock
from app.simulation.communications import evaluate_comms_health, update_comms_state
from app.simulation.eclipse import is_in_eclipse
from app.simulation.health import (
    evaluate_power_health,
    update_mode_transitions,
)
from app.simulation.orbit import (
    compute_eci_position,
    compute_mean_motion,
    compute_orbital_period,
    eci_to_geodetic,
    propagate_true_anomaly,
    validate_orbital_parameters,
)
from app.simulation.payload import evaluate_payload_health, update_payload_state
from app.simulation.power import (
    compute_bus_voltage,
    compute_solar_power,
    compute_total_load,
    integrate_battery_energy,
)
from app.simulation.snapshots import (
    SimulationSnapshot,
    capture_snapshot,
    restore_snapshot,
    validate_snapshot_integrity,
)
from app.simulation.state import (
    ADCSState,
    CommunicationsState,
    OrbitalState,
    PayloadState,
    PowerState,
    SatelliteRuntimeState,
    ThermalState,
)
from app.simulation.telemetry import TelemetryFrame, generate_telemetry_frame
from app.simulation.thermal import (
    evaluate_thermal_health,
    integrate_thermal_state,
    update_heater_state,
)

logger = logging.getLogger("orbitops.simulation.engine")

# Default simulation global seed
DEFAULT_SEED: int = 42


@dataclass
class SatelliteConfig:
    """Flat configuration record loaded from the Phase 02 database.

    This is the adapter DTO that bridges SQLAlchemy ORM data and the
    pure domain simulation engine.
    """

    satellite_id: str
    satellite_name: str
    mission_id: str
    semi_major_axis_km: float
    inclination_deg: float
    mass_kg: float
    battery_capacity_wh: float
    solar_area_m2: float
    initial_mode: str = "NOMINAL"

    # Subsystem initial conditions (from seed data)
    initial_battery_soc_pct: float = 80.0
    initial_bus_temp_c: float = 20.0
    initial_payload_temp_c: float = 18.0
    initial_adcs_mode: str = "NADIR_POINTING"
    initial_angular_rate_dps: float = 0.02
    initial_true_anomaly_deg: float = 0.0

    # Payload configuration
    payload_active_power_w: float = 180.0
    payload_standby_power_w: float = 5.0
    payload_data_rate_mbps: float = 0.05
    payload_initially_active: bool = False

    # Comms configuration
    comms_tx_enabled: bool = True
    comms_initially_transmitting: bool = False

    # Satellite-specific ADCS inertia
    adcs_inertia_kg_m2: float = 25.0

    # RAAN for initial orbit diversity (different initial orbital planes)
    initial_raan_deg: float = 0.0


def _build_runtime_state(
    config: SatelliteConfig,
    satellite_index: int,
    global_seed: int,
) -> SatelliteRuntimeState:
    """Construct a SatelliteRuntimeState from a SatelliteConfig.

    Parameters
    ----------
    config:
        Satellite configuration from Phase 02 database.
    satellite_index:
        0-based index within the constellation (used for RNG seed diversity).
    global_seed:
        Engine-wide seed. Satellite RNG is seeded from (global_seed XOR index).

    Returns
    -------
    SatelliteRuntimeState
        Fully initialised runtime state ready for simulation.
    """
    validate_orbital_parameters(config.semi_major_axis_km, config.inclination_deg)

    # --- Orbital state ---
    inclination_rad = math.radians(config.inclination_deg)
    raan_rad = math.radians(config.initial_raan_deg)
    true_anomaly_rad = math.radians(config.initial_true_anomaly_deg)
    mean_motion = compute_mean_motion(config.semi_major_axis_km)
    period_s = compute_orbital_period(config.semi_major_axis_km)

    pos_x, pos_y, pos_z = compute_eci_position(
        config.semi_major_axis_km,
        inclination_rad,
        raan_rad,
        0.0,  # arg_perigee = 0 for circular
        true_anomaly_rad,
    )
    lat, lon, alt = eci_to_geodetic(pos_x, pos_y, pos_z, sim_time_s=0.0)

    orbital = OrbitalState(
        semi_major_axis_km=config.semi_major_axis_km,
        inclination_rad=inclination_rad,
        raan_rad=raan_rad,
        arg_perigee_rad=0.0,
        true_anomaly_rad=true_anomaly_rad,
        pos_x_km=pos_x,
        pos_y_km=pos_y,
        pos_z_km=pos_z,
        latitude_deg=lat,
        longitude_deg=lon,
        altitude_km=alt,
        mean_motion_rad_s=mean_motion,
        orbital_period_s=period_s,
        orbital_radius_km=config.semi_major_axis_km,  # Circular: r = a
    )

    # --- Power state ---
    initial_energy_wh = (config.initial_battery_soc_pct / 100.0) * config.battery_capacity_wh
    power = PowerState(
        battery_energy_wh=initial_energy_wh,
        battery_capacity_wh=config.battery_capacity_wh,
        solar_area_m2=config.solar_area_m2,
        solar_cell_efficiency=0.28,
        battery_soc_pct=config.initial_battery_soc_pct,
    )

    # --- Thermal state ---
    KELVIN_OFFSET = 273.15
    thermal = ThermalState(
        bus_temp_k=config.initial_bus_temp_c + KELVIN_OFFSET,
        payload_temp_k=config.initial_payload_temp_c + KELVIN_OFFSET,
    )

    # --- ADCS state ---
    adcs = ADCSState(
        pointing_mode=config.initial_adcs_mode,
        angular_rate_dps=config.initial_angular_rate_dps,
        inertia_kg_m2=config.adcs_inertia_kg_m2,
    )

    # --- Comms state ---
    comms = CommunicationsState(
        tx_enabled=config.comms_tx_enabled,
        comms_power_w=20.0 if config.comms_tx_enabled else 0.0,
        is_transmitting=config.comms_initially_transmitting,
    )

    # --- Payload state ---
    payload = PayloadState(
        is_active=config.payload_initially_active,
        active_power_w=config.payload_active_power_w,
        standby_power_w=config.payload_standby_power_w,
        current_power_w=(
            config.payload_active_power_w
            if config.payload_initially_active
            else config.payload_standby_power_w
        ),
        data_rate_mbps=config.payload_data_rate_mbps,
    )

    # --- Seeded RNG for this satellite ---
    sat_rng = random.Random(global_seed ^ satellite_index)

    state = SatelliteRuntimeState(
        satellite_id=config.satellite_id,
        satellite_name=config.satellite_name,
        mission_id=config.mission_id,
        operational_mode=config.initial_mode,
        orbital=orbital,
        power=power,
        thermal=thermal,
        adcs=adcs,
        comms=comms,
        payload=payload,
        satellite_rng=sat_rng,
    )

    return state


class SimulationEngine:
    """Deterministic satellite digital twin simulation engine.

    Owns the simulation clock and all satellite runtime states.
    Provides a clean Python API for external control (CLI, tests, Phase 04 API).

    Thread Safety
    -------------
    This engine is NOT thread-safe. External callers must serialize access.
    Phase 04 will add a thread-safe wrapper for the FastAPI event loop.
    """

    def __init__(
        self,
        fleet_configs: list[SatelliteConfig],
        seed: int = DEFAULT_SEED,
        epoch_utc: datetime | None = None,
        default_dt: float = 1.0,
        initial_warp: float = 1.0,
    ) -> None:
        """Initialise the simulation engine.

        Parameters
        ----------
        fleet_configs:
            List of satellite configurations (loaded from Phase 02 database).
        seed:
            Global deterministic seed. Default: 42.
        epoch_utc:
            Simulation epoch. Default: 2026-10-26T00:00:00Z.
        default_dt:
            Default simulation timestep [s]. Default: 1.0 s.
        initial_warp:
            Initial time-warp factor. Default: 1.0×.
        """
        if not fleet_configs:
            msg = "SimulationEngine requires at least one satellite configuration."
            raise ValueError(msg)

        self._seed = seed
        self._clock = SimulationClock(
            epoch_utc=epoch_utc,
            default_dt=default_dt,
            initial_warp=initial_warp,
        )

        # Build independent runtime state for each satellite
        self._satellite_states: dict[str, SatelliteRuntimeState] = {}
        for index, config in enumerate(fleet_configs):
            state = _build_runtime_state(config, satellite_index=index, global_seed=seed)
            self._satellite_states[config.satellite_id] = state
            logger.info(
                "Initialised satellite %s (%s): a=%.1f km, i=%.1f°, SOC=%.1f%%",
                config.satellite_id,
                config.satellite_name,
                config.semi_major_axis_km,
                config.inclination_deg,
                config.initial_battery_soc_pct,
            )

        logger.info(
            "SimulationEngine initialised: %d satellites, seed=%d, dt=%.1f s",
            len(self._satellite_states),
            seed,
            default_dt,
        )

    # ------------------------------------------------------------------
    # Control API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the simulation clock."""
        self._clock.start()

    def pause(self) -> None:
        """Pause the simulation clock."""
        self._clock.pause()

    def resume(self) -> None:
        """Resume a paused simulation clock."""
        self._clock.resume()

    def reset(self, fleet_configs: list[SatelliteConfig] | None = None) -> None:
        """Reset the engine to initial state.

        Parameters
        ----------
        fleet_configs:
            If provided, reinitialises satellites from these configs.
            If None, resets clock only (satellites retain current state).
        """
        self._clock.reset()
        if fleet_configs is not None:
            self._satellite_states = {}
            for index, config in enumerate(fleet_configs):
                state = _build_runtime_state(config, index, self._seed)
                self._satellite_states[config.satellite_id] = state

    def set_time_warp(self, warp: float) -> None:
        """Set the time-warp multiplier."""
        self._clock.set_time_warp(warp)

    # ------------------------------------------------------------------
    # Simulation advancement
    # ------------------------------------------------------------------

    def tick(self, dt: float | None = None) -> list[TelemetryFrame]:
        """Advance the simulation by one timestep and return telemetry frames.

        This is the primary simulation advancement API. If the clock is
        paused, call start() or step() instead.

        Parameters
        ----------
        dt:
            Optional override timestep [s]. If None, uses clock's default_dt.

        Returns
        -------
        list[TelemetryFrame]
            One frame per satellite, all updated for this tick.
        """
        applied_dt = self._clock.advance(dt)
        if applied_dt == 0.0:
            # Clock is paused; return empty frames
            return []
        return self._advance_all_satellites(applied_dt)

    def step(self) -> list[TelemetryFrame]:
        """Advance by exactly one default timestep, regardless of paused state.

        Returns
        -------
        list[TelemetryFrame]
            One frame per satellite.
        """
        applied_dt = self._clock.step()
        return self._advance_all_satellites(applied_dt)

    def tick_n(self, n: int, dt: float | None = None) -> list[list[TelemetryFrame]]:
        """Advance n ticks and return all telemetry frames.

        Parameters
        ----------
        n:
            Number of ticks to advance. Must be positive.
        dt:
            Optional override timestep.

        Returns
        -------
        list[list[TelemetryFrame]]
            List of n frame lists, one per tick.
        """
        if n <= 0:
            msg = f"n must be positive; got {n}"
            raise ValueError(msg)
        results = []
        for _ in range(n):
            frames = self.tick(dt)
            if frames:
                results.append(frames)
        return results

    # ------------------------------------------------------------------
    # Inspection API
    # ------------------------------------------------------------------

    @property
    def clock(self) -> SimulationClock:
        """Read-only access to the simulation clock."""
        return self._clock

    @property
    def satellite_ids(self) -> list[str]:
        """List of satellite IDs managed by this engine."""
        return list(self._satellite_states.keys())

    def get_satellite_state(self, satellite_id: str) -> SatelliteRuntimeState:
        """Return a deep copy of the satellite's current runtime state.

        Returns a copy to prevent external code from mutating engine state.
        """
        state = self._satellite_states.get(satellite_id)
        if state is None:
            msg = f"No satellite with ID '{satellite_id}' found in engine."
            raise KeyError(msg)
        return state.deep_copy()

    def get_all_states(self) -> dict[str, SatelliteRuntimeState]:
        """Return deep copies of all satellite runtime states."""
        return {sat_id: state.deep_copy() for sat_id, state in self._satellite_states.items()}

    # ------------------------------------------------------------------
    # Snapshot API
    # ------------------------------------------------------------------

    def capture_snapshot(self, metadata: dict[str, Any] | None = None) -> SimulationSnapshot:
        """Capture a complete deterministic snapshot of engine state.

        This does not mutate any engine state.
        """
        return capture_snapshot(self._clock, self._satellite_states, metadata=metadata)

    def restore_from_snapshot(self, snapshot: SimulationSnapshot) -> None:
        """Restore engine state from a previously captured snapshot.

        Validates snapshot integrity before restoring. The restoration is
        atomic — if validation fails, the active engine state is unchanged.

        Raises
        ------
        ValueError
            If snapshot validation fails.
        """
        issues = validate_snapshot_integrity(snapshot)
        if issues:
            msg = f"Snapshot integrity validation failed: {'; '.join(issues)}"
            raise ValueError(msg)

        # Restore to temporary objects first, then swap atomically
        restored_clock, restored_satellites = restore_snapshot(snapshot)

        # Atomic state replacement
        self._clock = restored_clock
        self._satellite_states = restored_satellites

        logger.info(
            "Engine restored from snapshot: t=%.1f s, tick=%d",
            self._clock.sim_time_s,
            self._clock.tick_count,
        )

    # ------------------------------------------------------------------
    # Private: tick computation
    # ------------------------------------------------------------------

    def _advance_all_satellites(self, dt: float) -> list[TelemetryFrame]:
        """Advance all satellites by dt and return their telemetry frames.

        Each satellite is advanced independently. State from SAT-001 does NOT
        affect SAT-002 or SAT-003. This is enforced by processing each satellite
        entirely before moving to the next.
        """
        sim_timestamp = self._clock.sim_timestamp_utc
        sim_time_s = self._clock.sim_time_s
        frames: list[TelemetryFrame] = []

        for sat_id, state in self._satellite_states.items():
            try:
                tick_events = self._advance_satellite(state, dt, sim_time_s)
                frame = generate_telemetry_frame(state, sim_timestamp, events=tick_events)
                frames.append(frame)
            except Exception:
                logger.exception("Error advancing satellite %s; skipping this tick", sat_id)

        return frames

    def _advance_satellite(
        self,
        state: SatelliteRuntimeState,
        dt: float,
        sim_time_s: float,
    ) -> list[str]:
        """Advance one satellite through the full subsystem update pipeline.

        Returns a list of event strings generated during this tick.

        Update order (beginning-of-tick → end-of-tick):
        See module docstring for the authoritative order description.
        """
        events: list[str] = []

        # STEP 1: Propagate orbital position
        new_true_anomaly = propagate_true_anomaly(
            state.orbital.true_anomaly_rad,
            state.orbital.mean_motion_rad_s,
            dt,
        )
        state.orbital.true_anomaly_rad = new_true_anomaly

        pos_x, pos_y, pos_z = compute_eci_position(
            state.orbital.semi_major_axis_km,
            state.orbital.inclination_rad,
            state.orbital.raan_rad,
            state.orbital.arg_perigee_rad,
            new_true_anomaly,
        )
        state.orbital.pos_x_km = pos_x
        state.orbital.pos_y_km = pos_y
        state.orbital.pos_z_km = pos_z

        lat, lon, alt = eci_to_geodetic(pos_x, pos_y, pos_z, sim_time_s)
        state.orbital.latitude_deg = lat
        state.orbital.longitude_deg = lon
        state.orbital.altitude_km = alt

        # STEP 2: Eclipse state
        state.is_in_eclipse = is_in_eclipse(pos_x, pos_y, pos_z)

        # STEP 3: ADCS sun incidence angle
        sun_incidence = compute_sun_incidence(
            state.adcs.pointing_mode,
            new_true_anomaly,
            state.orbital.inclination_rad,
            state.satellite_rng,
        )
        state.adcs.sun_incidence_deg = sun_incidence

        # STEP 4: ADCS angular rate integration
        new_rate = integrate_angular_rate(
            state.adcs.angular_rate_dps,
            state.adcs.pointing_mode,
            state.adcs.inertia_kg_m2,
            dt,
            state.satellite_rng,
        )
        state.adcs.angular_rate_dps = new_rate

        # Safe-tumble mode detection
        if state.adcs.pointing_mode != "SAFE_TUMBLE" and new_rate > 5.0:
            state.adcs.pointing_mode = "SAFE_TUMBLE"
            state.adcs.is_detumbling = False
            events.append(f"ADCS entered SAFE_TUMBLE: rate {new_rate:.2f}°/s")

        # STEP 5: Payload state
        (
            new_payload_active,
            new_payload_power,
            new_data_mb,
            effective_payload_power,
        ) = update_payload_state(
            state.payload.is_active,
            state.payload.active_power_w,
            state.payload.standby_power_w,
            state.payload.data_storage_mb,
            state.payload.data_rate_mbps,
            state.operational_mode,
            dt,
        )
        state.payload.is_active = new_payload_active
        state.payload.current_power_w = new_payload_power
        state.payload.data_storage_mb = new_data_mb

        # STEP 6: Communications state
        (
            new_tx_enabled,
            new_is_transmitting,
            new_snr_db,
            new_comms_power,
        ) = update_comms_state(
            state.comms.tx_enabled,
            state.comms.is_transmitting,
            state.operational_mode,
        )
        state.comms.tx_enabled = new_tx_enabled
        state.comms.is_transmitting = new_is_transmitting
        state.comms.snr_db = new_snr_db
        state.comms.comms_power_w = new_comms_power

        # STEP 7: Heater state (uses PREVIOUS bus temperature for hysteresis decision)
        new_heater_active = update_heater_state(
            state.thermal.heater_active,
            state.thermal.bus_temp_c,
            on_threshold_c=state.thermal.heater_on_threshold_c,
            off_threshold_c=state.thermal.heater_off_threshold_c,
        )
        state.thermal.heater_active = new_heater_active
        heater_power = state.thermal.heater_power_w if new_heater_active else 0.0

        # STEP 8: Solar power generation
        adcs_power_w = 15.0  # Nominal ADCS draw
        if state.adcs.pointing_mode == "SAFE_TUMBLE":
            adcs_power_w = 5.0  # Reduced in tumble (no active wheels)

        solar_power = compute_solar_power(
            state.power.solar_area_m2,
            state.power.solar_cell_efficiency,
            state.adcs.sun_incidence_deg,
            state.is_in_eclipse,
        )
        state.power.solar_power_w = solar_power

        # STEP 9: Total electrical load
        total_load = compute_total_load(
            adcs_power_w=adcs_power_w,
            comms_power_w=new_comms_power,
            payload_power_w=state.payload.current_power_w,
            heater_power_w=heater_power,
        )
        state.power.total_load_w = total_load
        state.power.net_power_w = solar_power - total_load

        # STEP 10: Battery energy integration
        new_energy, new_soc, is_charging = integrate_battery_energy(
            state.power.battery_energy_wh,
            state.power.battery_capacity_wh,
            solar_power,
            total_load,
            dt,
            state.power.charge_efficiency,
            state.power.discharge_efficiency,
        )
        state.power.battery_energy_wh = new_energy
        state.power.battery_soc_pct = new_soc
        state.power.is_charging = is_charging

        # STEP 11: Bus voltage
        state.power.bus_voltage_v = compute_bus_voltage(new_soc, total_load)

        # STEP 12: Thermal integration
        # All electrical load is treated as heat dissipation in lumped model
        # (In reality not all load becomes heat in bus, but this is a simplification)
        electrical_dissipation = total_load * 0.6  # ~60% of electrical power becomes heat
        (
            new_bus_temp_k,
            new_payload_temp_k,
            q_in,
            q_out,
        ) = integrate_thermal_state(
            state.thermal.bus_temp_k,
            state.thermal.payload_temp_k,
            electrical_dissipation,
            state.is_in_eclipse,
            new_heater_active,
            dt,
            heat_capacity_j_per_k=state.thermal.heat_capacity_j_per_k,
            radiator_area_m2=state.thermal.radiator_area_m2,
            proj_area_m2=state.thermal.proj_area_m2,
            solar_absorptivity=state.thermal.solar_absorptivity,
            ir_emissivity=state.thermal.ir_emissivity,
            heater_power_w=state.thermal.heater_power_w,
        )
        state.thermal.bus_temp_k = new_bus_temp_k
        state.thermal.payload_temp_k = new_payload_temp_k
        state.thermal.q_in_w = q_in
        state.thermal.q_out_w = q_out

        # STEPS 13–17: Health evaluation
        power_health = evaluate_power_health(new_soc)
        thermal_health = evaluate_thermal_health(state.thermal.bus_temp_c)
        adcs_health = evaluate_adcs_health(new_rate, state.adcs.pointing_mode)
        comms_health = evaluate_comms_health(new_tx_enabled, new_snr_db)
        payload_health = evaluate_payload_health(
            new_payload_active, state.payload.current_power_w, state.payload.active_power_w
        )

        state.power.health_status = power_health
        state.thermal.health_status = thermal_health
        state.adcs.health_status = adcs_health
        state.comms.health_status = comms_health
        state.payload.health_status = payload_health

        # STEP 18: Autonomous mode transitions
        (
            new_mode,
            state.low_soc_ticks,
            state.high_temp_ticks,
            state.mode_just_changed,
            mode_events,
        ) = update_mode_transitions(
            state.operational_mode,
            new_soc,
            state.thermal.bus_temp_c,
            new_rate,
            state.low_soc_ticks,
            state.high_temp_ticks,
            state.mode_just_changed,
        )

        if new_mode != state.operational_mode:
            events.append(f"Mode transition: {state.operational_mode} → {new_mode}")
        state.operational_mode = new_mode
        events.extend(mode_events)

        # If SAFE_MODE entered, switch ADCS to SUN_POINTING for battery recovery
        if new_mode == "SAFE_MODE" and state.adcs.pointing_mode == "NADIR_POINTING":
            state.adcs.pointing_mode = "SUN_POINTING"
            events.append("ADCS switched to SUN_POINTING for SAFE_MODE recovery")

        return events

    def __repr__(self) -> str:
        return f"SimulationEngine(satellites={self.satellite_ids}, clock={self._clock!r})"
