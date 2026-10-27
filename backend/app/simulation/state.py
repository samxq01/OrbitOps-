"""OrbitOps Phase 03 — Runtime Satellite State Dataclasses.

These dataclasses represent the mutable in-memory runtime state of each
virtual satellite during simulation. They are completely separate from the
SQLAlchemy ORM models which represent persisted configuration.

Design decisions
----------------
- Dataclasses are used for clarity and easy deep-copying.
- No SQLAlchemy dependency in this module.
- Fields match the SRS simulation specification parameters.
- All angular values use radians internally; converted to degrees at boundary.
- Temperatures use Kelvin internally for radiative equations; Celsius at output.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrbitalState:
    """Two-body circular orbit state in Earth-Centred Inertial (ECI) frame.

    Reference frame
    ---------------
    ECI (Earth-Centred Inertial):
      - Origin: Earth's centre.
      - X-axis: Vernal equinox direction (fixed in inertial space).
      - Z-axis: Earth's north pole.
      - Right-handed coordinate system.

    For a circular orbit, the true anomaly advances at the mean motion rate.
    Eccentricity is held at 0.0 (circular approximation for Phase 03).
    GAMMA is documented as having a higher-altitude eccentric orbit, but the
    Phase 02 database stores only semi_major_axis_km and inclination_deg.
    Phase 03 uses a documented CIRCULAR approximation for all three satellites
    and defers full Kepler equation for eccentric orbits to a future phase.
    """

    # Keplerian elements (circular approximation)
    semi_major_axis_km: float  # a [km]
    inclination_rad: float  # i [rad]
    raan_rad: float = 0.0  # Right Ascension of Ascending Node [rad]
    arg_perigee_rad: float = 0.0  # Argument of perigee [rad] (0 for circular)
    true_anomaly_rad: float = 0.0  # ν [rad] — advances linearly for circular orbit

    # Derived position in ECI [km]
    pos_x_km: float = 0.0
    pos_y_km: float = 0.0
    pos_z_km: float = 0.0

    # Derived geodetic coordinates (Earth-fixed, WGS-84 approximation)
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    altitude_km: float = 0.0

    # Computed orbital parameters
    mean_motion_rad_s: float = 0.0  # n [rad/s]
    orbital_period_s: float = 0.0  # T [s]
    orbital_radius_km: float = 0.0  # |r| [km]


@dataclass
class PowerState:
    """Power subsystem runtime state.

    Units
    -----
    - Power: Watts [W]
    - Energy: Watt-hours [Wh]
    - Voltage: Volts [V]
    - State of Charge: Percent [%]
    """

    battery_energy_wh: float = 0.0  # Current stored energy [Wh]
    battery_capacity_wh: float = 320.0  # Total capacity [Wh]
    solar_area_m2: float = 1.2  # Effective array area [m²]
    solar_cell_efficiency: float = 0.28  # η_cell [dimensionless]

    # Calculated per tick
    solar_power_w: float = 0.0  # P_solar [W]
    total_load_w: float = 0.0  # P_load [W]
    net_power_w: float = 0.0  # P_batt = P_solar - P_load [W]
    bus_voltage_v: float = 28.0  # V_bus [V]
    battery_soc_pct: float = 100.0  # SOC [%]
    is_charging: bool = False

    # Efficiencies (from simulation spec)
    charge_efficiency: float = 0.92
    discharge_efficiency: float = 0.96

    # Bus model constants
    nominal_bus_v: float = 28.0  # V_nominal [V]
    k_curve: float = 0.05  # SOC-to-voltage slope coefficient
    r_internal_ohm: float = 0.08  # R_internal [Ω]

    # Health tracking
    health_status: str = "NOMINAL"

    def soc_from_energy(self) -> float:
        """Compute SOC as percentage from current stored energy."""
        if self.battery_capacity_wh <= 0.0:
            return 0.0
        return max(0.0, min(100.0, (self.battery_energy_wh / self.battery_capacity_wh) * 100.0))


@dataclass
class ThermalState:
    """Thermal subsystem runtime state.

    Implementation note
    -------------------
    Stefan-Boltzmann radiative equations require temperature in Kelvin.
    The internal physics state uses Kelvin. Celsius values are computed
    only at output boundaries (telemetry generation, threshold evaluation).

    Threshold matrix (resolving gaps in original spec):
    - NOMINAL:  +5°C ≤ T ≤ +35°C
    - WARNING:  (-15°C ≤ T < +5°C) OR (+35°C < T ≤ +65°C)
    - CRITICAL: T < -15°C OR T > +65°C
    The [-5, +5] and [+35, +50] bands referenced in the SRS are superseded
    by this contiguous, gap-free mapping.
    """

    CELSIUS_TO_KELVIN: float = 273.15

    # Internal physics state
    bus_temp_k: float = 293.15  # T_bus [K] (= 20°C initial)
    payload_temp_k: float = 291.15  # T_payload [K] (= 18°C initial)

    # Configuration
    heat_capacity_j_per_k: float = 45_000.0  # m·cp [J/K] lumped bus
    radiator_area_m2: float = 0.6  # A_radiator [m²]
    solar_absorptivity: float = 0.15  # α_solar [dimensionless]
    ir_emissivity: float = 0.85  # ε [dimensionless]
    proj_area_m2: float = 0.3  # A_proj [m²] — projected cross-section for solar absorption
    t_space_k: float = 3.0  # T_space [K] (deep-space background)

    # Heater control (hysteresis loop)
    heater_on_threshold_c: float = 5.0  # Turn ON below this temperature
    heater_off_threshold_c: float = 15.0  # Turn OFF above this temperature
    heater_power_w: float = 40.0  # P_heater [W] when active
    heater_active: bool = False

    # Computed per tick
    q_in_w: float = 0.0  # Total heat input [W]
    q_out_w: float = 0.0  # Radiative heat output [W]
    health_status: str = "NOMINAL"

    @property
    def bus_temp_c(self) -> float:
        """Bus temperature in Celsius (display/threshold use only)."""
        return self.bus_temp_k - self.CELSIUS_TO_KELVIN

    @property
    def payload_temp_c(self) -> float:
        """Payload temperature in Celsius (display/threshold use only)."""
        return self.payload_temp_k - self.CELSIUS_TO_KELVIN


@dataclass
class ADCSState:
    """Attitude Determination and Control System runtime state.

    Pointing modes
    --------------
    NADIR_POINTING  : Payload points toward Earth centre (nominal for imaging).
    SUN_POINTING    : Arrays align with solar vector (max power; used in recovery).
    SAFE_TUMBLE     : Uncontrolled slow rotation induced by fault or actuator failure.

    Angular rate units: degrees/second [°/s]
    Torque units: N·m
    Inertia units: kg·m²

    Random disturbances use the engine's seeded RNG, not the global random module.
    """

    pointing_mode: str = "NADIR_POINTING"  # NADIR_POINTING | SUN_POINTING | SAFE_TUMBLE
    angular_rate_dps: float = 0.02  # |ω| [°/s] scalar rate magnitude
    inertia_kg_m2: float = 25.0  # I_sat [kg·m²] (simplified scalar)
    max_control_torque_nm: float = 0.05  # τ_max [N·m]
    disturbance_sigma_nm: float = 1e-4  # σ_disturbance [N·m]

    # Sun incidence angle (degrees from array normal; 0° = perpendicular = max power)
    # In SUN_POINTING mode, this is driven toward 0. In NADIR_POINTING, it's derived
    # from orbital geometry and is non-zero in general.
    sun_incidence_deg: float = 0.0

    # Pointing health
    pointing_error_deg: float = 0.0  # Estimated pointing error
    health_status: str = "NOMINAL"

    # Flag: detumbling convergence
    is_detumbling: bool = False


@dataclass
class CommunicationsState:
    """Communications subsystem runtime state (Phase 03 scope).

    Scope limitation
    ----------------
    Phase 03 models local transmitter state only. Ground station visibility,
    Doppler calculations, and contact window scheduling belong to Phase 09.
    The 'contact_established' flag is intentionally always False here;
    it is not a verified ground link — it is a local transmitter-enabled state.
    """

    tx_enabled: bool = True  # Transmitter powered on/off
    comms_power_w: float = 20.0  # Current power draw [W] (standby or active)
    standby_power_w: float = 20.0  # P_comms standby [W]
    active_power_w: float = 80.0  # P_comms active downlink [W]
    is_transmitting: bool = False  # True when actively downlinking
    snr_db: float = 15.0  # Simplified local SNR estimate [dB]
    health_status: str = "NOMINAL"

    # Phase 09 will populate real contact windows
    contact_established: bool = False  # NOT a verified ground link in Phase 03


@dataclass
class PayloadState:
    """Payload subsystem runtime state.

    Payload power consumption affects the Power subsystem.
    Payload heat dissipation affects the Thermal subsystem.
    """

    is_active: bool = False  # Payload powered on
    active_power_w: float = 180.0  # P_payload when active [W]
    standby_power_w: float = 5.0  # P_payload when standby [W]
    current_power_w: float = 5.0  # Current draw [W]
    data_storage_mb: float = 0.0  # Accumulated science data [MB]
    data_rate_mbps: float = 0.0  # Current data accumulation rate [Mb/s]
    health_status: str = "NOMINAL"


@dataclass
class SatelliteRuntimeState:
    """Complete runtime state for one virtual satellite.

    Ownership
    ---------
    This object is exclusively owned and mutated by the SimulationEngine.
    External code must not mutate it directly. Snapshots return copies.

    Isolation
    ---------
    Each satellite has its own independent RNG seeded at construction.
    Disturbance torques and minor noise use satellite_rng, never the global random.
    """

    satellite_id: str
    satellite_name: str
    mission_id: str
    operational_mode: str = "NOMINAL"

    # Subsystem states
    orbital: OrbitalState = field(default_factory=lambda: OrbitalState(6921.0, 0.0))
    power: PowerState = field(default_factory=PowerState)
    thermal: ThermalState = field(default_factory=ThermalState)
    adcs: ADCSState = field(default_factory=ADCSState)
    comms: CommunicationsState = field(default_factory=CommunicationsState)
    payload: PayloadState = field(default_factory=PayloadState)

    # Eclipse state
    is_in_eclipse: bool = False

    # Autonomous transition tracking
    low_soc_ticks: int = 0  # Consecutive ticks with SOC below critical threshold
    high_temp_ticks: int = 0  # Consecutive ticks with temp above critical threshold
    mode_just_changed: bool = False  # Prevents repeated events on same tick

    # Satellite-specific deterministic RNG (not the global random module)
    # Seeded from (global_seed XOR satellite_index) for independence
    satellite_rng: random.Random = field(default_factory=random.Random)

    # Per-satellite telemetry sequence counter
    telemetry_sequence: int = 0

    def deep_copy(self) -> SatelliteRuntimeState:
        """Return a deep copy of this state for snapshot isolation."""
        new_state = copy.deepcopy(self)
        # Restore RNG state properly (deepcopy handles this correctly for Random)
        return new_state

    def to_dict(self) -> dict[str, Any]:
        """Serialise state to a dictionary for snapshot persistence."""
        rng_state = self.satellite_rng.getstate()
        return {
            "satellite_id": self.satellite_id,
            "satellite_name": self.satellite_name,
            "mission_id": self.mission_id,
            "operational_mode": self.operational_mode,
            "is_in_eclipse": self.is_in_eclipse,
            "low_soc_ticks": self.low_soc_ticks,
            "high_temp_ticks": self.high_temp_ticks,
            "telemetry_sequence": self.telemetry_sequence,
            "rng_state": list(rng_state[1]) if rng_state else None,
            "rng_internalstate": rng_state[0] if rng_state else None,
            "rng_gauss_next": rng_state[2] if rng_state else None,
            "orbital": {
                "semi_major_axis_km": self.orbital.semi_major_axis_km,
                "inclination_rad": self.orbital.inclination_rad,
                "raan_rad": self.orbital.raan_rad,
                "arg_perigee_rad": self.orbital.arg_perigee_rad,
                "true_anomaly_rad": self.orbital.true_anomaly_rad,
                "pos_x_km": self.orbital.pos_x_km,
                "pos_y_km": self.orbital.pos_y_km,
                "pos_z_km": self.orbital.pos_z_km,
                "latitude_deg": self.orbital.latitude_deg,
                "longitude_deg": self.orbital.longitude_deg,
                "altitude_km": self.orbital.altitude_km,
                "mean_motion_rad_s": self.orbital.mean_motion_rad_s,
                "orbital_period_s": self.orbital.orbital_period_s,
                "orbital_radius_km": self.orbital.orbital_radius_km,
            },
            "power": {
                "battery_energy_wh": self.power.battery_energy_wh,
                "battery_capacity_wh": self.power.battery_capacity_wh,
                "solar_area_m2": self.power.solar_area_m2,
                "solar_cell_efficiency": self.power.solar_cell_efficiency,
                "solar_power_w": self.power.solar_power_w,
                "total_load_w": self.power.total_load_w,
                "net_power_w": self.power.net_power_w,
                "bus_voltage_v": self.power.bus_voltage_v,
                "battery_soc_pct": self.power.battery_soc_pct,
                "is_charging": self.power.is_charging,
                "health_status": self.power.health_status,
            },
            "thermal": {
                "bus_temp_k": self.thermal.bus_temp_k,
                "payload_temp_k": self.thermal.payload_temp_k,
                "heater_active": self.thermal.heater_active,
                "heat_capacity_j_per_k": self.thermal.heat_capacity_j_per_k,
                "radiator_area_m2": self.thermal.radiator_area_m2,
                "solar_absorptivity": self.thermal.solar_absorptivity,
                "ir_emissivity": self.thermal.ir_emissivity,
                "proj_area_m2": self.thermal.proj_area_m2,
                "heater_power_w": self.thermal.heater_power_w,
                "heater_on_threshold_c": self.thermal.heater_on_threshold_c,
                "heater_off_threshold_c": self.thermal.heater_off_threshold_c,
                "q_in_w": self.thermal.q_in_w,
                "q_out_w": self.thermal.q_out_w,
                "health_status": self.thermal.health_status,
            },
            "adcs": {
                "pointing_mode": self.adcs.pointing_mode,
                "angular_rate_dps": self.adcs.angular_rate_dps,
                "inertia_kg_m2": self.adcs.inertia_kg_m2,
                "max_control_torque_nm": self.adcs.max_control_torque_nm,
                "disturbance_sigma_nm": self.adcs.disturbance_sigma_nm,
                "sun_incidence_deg": self.adcs.sun_incidence_deg,
                "pointing_error_deg": self.adcs.pointing_error_deg,
                "health_status": self.adcs.health_status,
                "is_detumbling": self.adcs.is_detumbling,
            },
            "comms": {
                "tx_enabled": self.comms.tx_enabled,
                "comms_power_w": self.comms.comms_power_w,
                "is_transmitting": self.comms.is_transmitting,
                "snr_db": self.comms.snr_db,
                "health_status": self.comms.health_status,
            },
            "payload": {
                "is_active": self.payload.is_active,
                "active_power_w": self.payload.active_power_w,
                "standby_power_w": self.payload.standby_power_w,
                "current_power_w": self.payload.current_power_w,
                "data_storage_mb": self.payload.data_storage_mb,
                "data_rate_mbps": self.payload.data_rate_mbps,
                "health_status": self.payload.health_status,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SatelliteRuntimeState:
        """Restore state from a snapshot dictionary."""
        state = cls(
            satellite_id=data["satellite_id"],
            satellite_name=data["satellite_name"],
            mission_id=data["mission_id"],
        )
        state.operational_mode = data["operational_mode"]
        state.is_in_eclipse = data["is_in_eclipse"]
        state.low_soc_ticks = data["low_soc_ticks"]
        state.high_temp_ticks = data["high_temp_ticks"]
        state.telemetry_sequence = data["telemetry_sequence"]

        # Restore orbital state
        orb = data["orbital"]
        state.orbital = OrbitalState(
            semi_major_axis_km=orb["semi_major_axis_km"],
            inclination_rad=orb["inclination_rad"],
            raan_rad=orb["raan_rad"],
            arg_perigee_rad=orb["arg_perigee_rad"],
            true_anomaly_rad=orb["true_anomaly_rad"],
            pos_x_km=orb["pos_x_km"],
            pos_y_km=orb["pos_y_km"],
            pos_z_km=orb["pos_z_km"],
            latitude_deg=orb["latitude_deg"],
            longitude_deg=orb["longitude_deg"],
            altitude_km=orb["altitude_km"],
            mean_motion_rad_s=orb["mean_motion_rad_s"],
            orbital_period_s=orb["orbital_period_s"],
            orbital_radius_km=orb["orbital_radius_km"],
        )

        # Restore power state
        pw = data["power"]
        state.power = PowerState(
            battery_energy_wh=pw["battery_energy_wh"],
            battery_capacity_wh=pw["battery_capacity_wh"],
            solar_area_m2=pw["solar_area_m2"],
            solar_cell_efficiency=pw["solar_cell_efficiency"],
            solar_power_w=pw["solar_power_w"],
            total_load_w=pw["total_load_w"],
            net_power_w=pw["net_power_w"],
            bus_voltage_v=pw["bus_voltage_v"],
            battery_soc_pct=pw["battery_soc_pct"],
            is_charging=pw["is_charging"],
            health_status=pw["health_status"],
        )

        # Restore thermal state
        th = data["thermal"]
        state.thermal = ThermalState(
            bus_temp_k=th["bus_temp_k"],
            payload_temp_k=th["payload_temp_k"],
            heater_active=th["heater_active"],
            heat_capacity_j_per_k=th.get("heat_capacity_j_per_k", 45_000.0),
            radiator_area_m2=th.get("radiator_area_m2", 0.6),
            solar_absorptivity=th.get("solar_absorptivity", 0.15),
            ir_emissivity=th.get("ir_emissivity", 0.85),
            proj_area_m2=th.get("proj_area_m2", 0.3),
            heater_power_w=th.get("heater_power_w", 40.0),
            heater_on_threshold_c=th.get("heater_on_threshold_c", 5.0),
            heater_off_threshold_c=th.get("heater_off_threshold_c", 15.0),
            q_in_w=th["q_in_w"],
            q_out_w=th["q_out_w"],
            health_status=th["health_status"],
        )

        # Restore ADCS state
        ad = data["adcs"]
        state.adcs = ADCSState(
            pointing_mode=ad["pointing_mode"],
            angular_rate_dps=ad["angular_rate_dps"],
            inertia_kg_m2=ad.get("inertia_kg_m2", 25.0),
            max_control_torque_nm=ad.get("max_control_torque_nm", 0.05),
            disturbance_sigma_nm=ad.get("disturbance_sigma_nm", 1e-4),
            sun_incidence_deg=ad["sun_incidence_deg"],
            pointing_error_deg=ad["pointing_error_deg"],
            health_status=ad["health_status"],
            is_detumbling=ad["is_detumbling"],
        )

        # Restore comms state
        co = data["comms"]
        state.comms = CommunicationsState(
            tx_enabled=co["tx_enabled"],
            comms_power_w=co["comms_power_w"],
            is_transmitting=co["is_transmitting"],
            snr_db=co["snr_db"],
            health_status=co["health_status"],
        )

        # Restore payload state
        pl = data["payload"]
        state.payload = PayloadState(
            is_active=pl["is_active"],
            active_power_w=pl["active_power_w"],
            standby_power_w=pl["standby_power_w"],
            current_power_w=pl["current_power_w"],
            data_storage_mb=pl["data_storage_mb"],
            data_rate_mbps=pl["data_rate_mbps"],
            health_status=pl["health_status"],
        )

        # Restore RNG state
        rng_internalstate = data.get("rng_internalstate")
        rng_list = data.get("rng_state")
        rng_gauss = data.get("rng_gauss_next")
        if rng_internalstate is not None and rng_list is not None:
            rng_tuple = (rng_internalstate, tuple(rng_list), rng_gauss)
            state.satellite_rng.setstate(rng_tuple)  # type: ignore[arg-type]

        return state


def _wrap_longitude(lon_deg: float) -> float:
    """Wrap longitude to [-180, 180] degrees."""
    lon = lon_deg % 360.0
    if lon > 180.0:
        lon -= 360.0
    return lon


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))
