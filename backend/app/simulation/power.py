"""OrbitOps Phase 03 — Power Subsystem Model.

Mathematical Model (from simulation-spec.md §2)
------------------------------------------------

1. Solar Array Generation:
   P_solar(t) = G_solar · A_array · η_cell · cos(θ_sun) · (1 − δ_eclipse)

   - G_solar = 1361.0 W/m² (solar constant at 1 AU)
   - A_array: effective solar array area [m²]
   - η_cell = 0.28 (28% multi-junction GaInP/GaAs efficiency)
   - θ_sun: sun incidence angle [deg] relative to array surface normal
   - δ_eclipse ∈ {0, 1}: binary eclipse indicator

2. Total Spacecraft Electrical Load:
   P_load(t) = P_bus_base + P_adcs + P_comms + P_payload + P_heaters

3. Net Battery Power:
   P_batt(t) = P_solar(t) − P_load(t)

4. Battery Energy Storage Dynamics:
   dE_batt/dt = P_batt · η_charge    if P_batt ≥ 0  (charging)
   dE_batt/dt = P_batt / η_discharge  if P_batt < 0  (discharging)

   **Unit conversion required**: Power [W] × time [s] → energy [J].
   Convert to Wh: delta_energy_wh = power_w × dt_s / 3600

5. State of Charge:
   SOC(t) = (E_batt(t) / E_capacity) × 100%
   Clamped to [0.0%, 100.0%].

6. Bus Voltage:
   V_bus(t) = V_nominal + k_curve · (SOC − 50) − I_load · R_internal

Physical Constraints
--------------------
- Battery energy ≥ 0 (never negative).
- SOC ∈ [0%, 100%] (clamped).
- Solar power ≥ 0 (cannot be negative).
- Battery capacity must be positive.
- Solar generation = 0 during eclipse (δ_eclipse = 1).
- Payload activation increases load.
- Heater activation increases load.

Units
-----
Power: Watts [W]
Energy: Watt-hours [Wh]  (NOT joules — the model uses Wh for consistency)
Voltage: Volts [V]
"""

from __future__ import annotations

import math

# Solar constant at 1 AU [W/m²]
SOLAR_CONSTANT_W_M2: float = 1361.0

# Nominal base avionics load [W]
BASE_AVIONICS_POWER_W: float = 25.0

# Default cell efficiency (28% multi-junction GaInP/GaAs)
DEFAULT_CELL_EFFICIENCY: float = 0.28

# Default charging efficiency
DEFAULT_CHARGE_EFFICIENCY: float = 0.92

# DEFAULT discharging efficiency
DEFAULT_DISCHARGE_EFFICIENCY: float = 0.96

# Bus voltage model constants
NOMINAL_BUS_VOLTAGE_V: float = 28.0
BUS_VOLTAGE_K_CURVE: float = 0.05  # V/% SOC deviation from 50%
BUS_R_INTERNAL_OHM: float = 0.08  # Internal resistance [Ω]


def compute_solar_power(
    solar_area_m2: float,
    cell_efficiency: float,
    sun_incidence_deg: float,
    is_in_eclipse: bool,
) -> float:
    """Compute instantaneous solar array power generation.

    P_solar = G_solar · A_array · η_cell · cos(θ_sun) · (1 − δ_eclipse)

    Parameters
    ----------
    solar_area_m2:
        Effective solar array area [m²]. Must be positive.
    cell_efficiency:
        Solar cell efficiency [0, 1]. Typical: 0.28.
    sun_incidence_deg:
        Angle between sun vector and array normal [degrees].
        0° = perpendicular (maximum generation).
        90° = parallel (zero generation from geometric projection).
    is_in_eclipse:
        True if satellite is in Earth shadow. Suppresses all solar generation.

    Returns
    -------
    float
        Solar power generated [W]. Always ≥ 0.

    Raises
    ------
    ValueError
        If solar_area_m2 ≤ 0 or cell_efficiency is outside (0, 1].
    """
    if solar_area_m2 <= 0.0:
        msg = f"Solar array area must be positive; got {solar_area_m2} m²"
        raise ValueError(msg)
    if not (0.0 < cell_efficiency <= 1.0):
        msg = f"Cell efficiency must be in (0, 1]; got {cell_efficiency}"
        raise ValueError(msg)

    if is_in_eclipse:
        return 0.0

    # cos factor: clamp at 0 to avoid negative generation at angles > 90°
    cos_theta = max(0.0, math.cos(math.radians(sun_incidence_deg)))
    power_w = SOLAR_CONSTANT_W_M2 * solar_area_m2 * cell_efficiency * cos_theta
    return max(0.0, power_w)


def compute_total_load(
    adcs_power_w: float,
    comms_power_w: float,
    payload_power_w: float,
    heater_power_w: float,
) -> float:
    """Compute total spacecraft electrical load.

    P_load = P_bus_base + P_adcs + P_comms + P_payload + P_heaters

    All inputs must be non-negative.

    Parameters
    ----------
    adcs_power_w:
        ADCS subsystem power draw [W].
    comms_power_w:
        Communications subsystem power draw [W].
    payload_power_w:
        Payload instrument power draw [W].
    heater_power_w:
        Active heater power draw [W] (0 if heaters off).

    Returns
    -------
    float
        Total electrical load [W].
    """
    for label, val in [
        ("ADCS power", adcs_power_w),
        ("comms power", comms_power_w),
        ("payload power", payload_power_w),
        ("heater power", heater_power_w),
    ]:
        if val < 0.0:
            msg = f"{label} must be non-negative; got {val} W"
            raise ValueError(msg)

    return BASE_AVIONICS_POWER_W + adcs_power_w + comms_power_w + payload_power_w + heater_power_w


def integrate_battery_energy(
    battery_energy_wh: float,
    battery_capacity_wh: float,
    solar_power_w: float,
    load_power_w: float,
    dt_s: float,
    charge_efficiency: float = DEFAULT_CHARGE_EFFICIENCY,
    discharge_efficiency: float = DEFAULT_DISCHARGE_EFFICIENCY,
) -> tuple[float, float, bool]:
    """Integrate battery state of charge over one timestep.

    dE_batt/dt = P_batt · η_charge       if P_batt ≥ 0 (charging)
    dE_batt/dt = P_batt / η_discharge    if P_batt < 0 (discharging)

    Unit conversion: [W] × [s] / 3600 → [Wh]

    Parameters
    ----------
    battery_energy_wh:
        Current battery stored energy [Wh]. Must be ≥ 0.
    battery_capacity_wh:
        Battery total capacity [Wh]. Must be > 0.
    solar_power_w:
        Solar generation [W]. Must be ≥ 0.
    load_power_w:
        Total electrical load [W]. Must be > 0.
    dt_s:
        Timestep [s]. Must be positive.
    charge_efficiency:
        η_charge [0, 1]. Default: 0.92.
    discharge_efficiency:
        η_discharge [0, 1]. Default: 0.96.

    Returns
    -------
    tuple[float, float, bool]
        (new_battery_energy_wh, new_soc_pct, is_charging)
        - new_battery_energy_wh: Updated stored energy, clamped to [0, capacity].
        - new_soc_pct: State of charge [%], clamped to [0, 100].
        - is_charging: True if net power balance is positive (battery gaining charge).

    Raises
    ------
    ValueError
        If any physical constraint is violated.
    """
    if battery_capacity_wh <= 0.0:
        msg = f"Battery capacity must be positive; got {battery_capacity_wh} Wh"
        raise ValueError(msg)
    if battery_energy_wh < 0.0:
        msg = f"Battery energy must be non-negative; got {battery_energy_wh} Wh"
        raise ValueError(msg)
    if solar_power_w < 0.0:
        msg = f"Solar power must be non-negative; got {solar_power_w} W"
        raise ValueError(msg)
    if dt_s <= 0.0:
        msg = f"Timestep must be positive; got {dt_s} s"
        raise ValueError(msg)
    if not (0.0 < charge_efficiency <= 1.0):
        msg = f"Charge efficiency must be in (0, 1]; got {charge_efficiency}"
        raise ValueError(msg)
    if not (0.0 < discharge_efficiency <= 1.0):
        msg = f"Discharge efficiency must be in (0, 1]; got {discharge_efficiency}"
        raise ValueError(msg)

    net_power_w = solar_power_w - load_power_w
    is_charging = net_power_w >= 0.0

    # Energy change in Wh (convert W·s → Wh by dividing by 3600)
    if is_charging:
        delta_energy_wh = net_power_w * charge_efficiency * dt_s / 3600.0
    else:
        # Discharging: actual energy withdrawn from battery is larger than net demand
        delta_energy_wh = (net_power_w / discharge_efficiency) * dt_s / 3600.0

    new_energy_wh = battery_energy_wh + delta_energy_wh
    # Clamp to physical bounds
    new_energy_wh = max(0.0, min(battery_capacity_wh, new_energy_wh))

    new_soc_pct = (new_energy_wh / battery_capacity_wh) * 100.0
    new_soc_pct = max(0.0, min(100.0, new_soc_pct))

    return new_energy_wh, new_soc_pct, is_charging


def compute_bus_voltage(
    soc_pct: float,
    load_power_w: float,
    nominal_v: float = NOMINAL_BUS_VOLTAGE_V,
    k_curve: float = BUS_VOLTAGE_K_CURVE,
    r_internal_ohm: float = BUS_R_INTERNAL_OHM,
) -> float:
    """Compute unregulated bus voltage from SOC and load.

    V_bus = V_nominal + k_curve · (SOC − 50) − I_load · R_internal

    where I_load = P_load / V_nominal (simplified; assumes V ≈ V_nominal for I calc)

    Parameters
    ----------
    soc_pct:
        Battery state of charge [%], in [0, 100].
    load_power_w:
        Total electrical load [W].
    nominal_v:
        Nominal bus voltage [V]. Default: 28.0 V.
    k_curve:
        Voltage–SOC slope [V/%]. Default: 0.05 V/%.
    r_internal_ohm:
        Internal resistance [Ω]. Default: 0.08 Ω.

    Returns
    -------
    float
        Estimated bus voltage [V].
    """
    i_load_a = load_power_w / nominal_v if nominal_v > 0.0 else 0.0
    v_bus = nominal_v + k_curve * (soc_pct - 50.0) - i_load_a * r_internal_ohm
    # Clamp to physical operational range
    return max(22.0, min(30.5, v_bus))
