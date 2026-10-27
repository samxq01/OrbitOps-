"""OrbitOps Phase 03 — Thermal Subsystem Model.

Mathematical Model (from simulation-spec.md §3)
------------------------------------------------
Lumped-capacitance energy balance:

    m · c_p · dT/dt = Q_in − Q_out

where:
    Q_in  = P_dissipated + α_solar · A_proj · G_solar · (1 − δ_eclipse) + Q_albedo
    Q_out = ε · σ · A_radiator · (T⁴ − T_space⁴)

Constants:
    σ = 5.67037 × 10⁻⁸ W/(m²·K⁴)  (Stefan-Boltzmann constant)
    ε = 0.85                         (infrared emissivity)
    α_solar = 0.15                   (solar absorptivity)
    T_space = 3.0 K                  (deep space background)
    m·c_p ≈ 45000 J/K                (lumped bus heat capacity)

Heater Hysteresis Control
--------------------------
Hysteresis prevents rapid toggling near the threshold:
    - Heater turns ON  if T_bus < heater_on_threshold_c  (5°C)
    - Heater turns OFF if T_bus > heater_off_threshold_c (15°C)
    - No change while temperature is between thresholds (hysteresis band)

Temperature Threshold Matrix (gap-free, from simulation-spec.md §3.1 with resolution)
-----------------------------------------------------------------------
Original spec had gaps between: [-5, +5) and [+35, +50) labelled warning,
but [-15, -5) and [+50, +65) were undefined.

Resolved (gap-free) mapping:
    NOMINAL:  +5°C ≤ T ≤ +35°C
    WARNING:  (-15°C ≤ T < +5°C)  OR  (+35°C < T ≤ +65°C)
    CRITICAL: T < -15°C  OR  T > +65°C

Internal Physics Units
----------------------
All radiative calculations use Kelvin to avoid errors in Stefan-Boltzmann T⁴.
The Euler integration step uses Kelvin internally.
Celsius values are only computed at output boundaries.

Numerical Stability
-------------------
For Δt = 1.0 s and m·c_p = 45000 J/K, the temperature increment per step is:
    ΔT = (Q_in − Q_out) / (m·c_p) · Δt
Maximum |Q_net| ≈ 1000 W → ΔT_max ≈ 0.022°C per step
This is well within the stability bound for explicit Euler integration.
"""

from __future__ import annotations

# Stefan-Boltzmann constant [W/(m²·K⁴)]
STEFAN_BOLTZMANN: float = 5.67037e-8

# Deep space background temperature [K]
T_SPACE_K: float = 3.0

# Solar constant [W/m²]
SOLAR_CONSTANT_W_M2: float = 1361.0

# Temperature threshold constants [°C]
TEMP_NOMINAL_LOW_C: float = 5.0  # Below this → WARNING (approaching heater range)
TEMP_NOMINAL_HIGH_C: float = 35.0  # Above this → WARNING
TEMP_CRITICAL_LOW_C: float = -15.0  # Below this → CRITICAL
TEMP_CRITICAL_HIGH_C: float = 65.0  # Above this → CRITICAL

KELVIN_OFFSET: float = 273.15  # 0°C in Kelvin


def celsius_to_kelvin(temp_c: float) -> float:
    """Convert Celsius to Kelvin."""
    return temp_c + KELVIN_OFFSET


def kelvin_to_celsius(temp_k: float) -> float:
    """Convert Kelvin to Celsius."""
    return temp_k - KELVIN_OFFSET


def compute_radiative_heat_loss(
    temp_k: float,
    radiator_area_m2: float,
    emissivity: float = 0.85,
    t_space_k: float = T_SPACE_K,
) -> float:
    """Compute radiative heat loss via Stefan-Boltzmann law.

    Q_out = ε · σ · A_radiator · (T⁴ − T_space⁴)

    Parameters
    ----------
    temp_k:
        Spacecraft bus temperature [K]. Must be positive.
    radiator_area_m2:
        Radiator surface area [m²]. Must be positive.
    emissivity:
        IR emissivity of radiator surface [0, 1]. Default: 0.85.
    t_space_k:
        Deep space background temperature [K]. Default: 3.0 K.

    Returns
    -------
    float
        Heat radiated to space [W]. Non-negative.

    Raises
    ------
    ValueError
        If inputs are physically invalid.
    """
    if temp_k <= 0.0:
        msg = f"Temperature must be > 0 K for radiation; got {temp_k} K"
        raise ValueError(msg)
    if radiator_area_m2 <= 0.0:
        msg = f"Radiator area must be positive; got {radiator_area_m2} m²"
        raise ValueError(msg)
    if not (0.0 < emissivity <= 1.0):
        msg = f"Emissivity must be in (0, 1]; got {emissivity}"
        raise ValueError(msg)

    q_out = emissivity * STEFAN_BOLTZMANN * radiator_area_m2 * (temp_k**4 - t_space_k**4)
    return max(0.0, q_out)


def compute_solar_heating(
    solar_absorptivity: float,
    proj_area_m2: float,
    is_in_eclipse: bool,
) -> float:
    """Compute solar heat absorbed by the spacecraft bus.

    Q_solar = α_solar · A_proj · G_solar · (1 − δ_eclipse)

    Parameters
    ----------
    solar_absorptivity:
        Solar absorptivity of bus coating [0, 1]. Default: 0.15.
    proj_area_m2:
        Projected cross-sectional area facing sun [m²].
    is_in_eclipse:
        True if in Earth shadow (zero solar heating).

    Returns
    -------
    float
        Solar heat input [W]. Non-negative.
    """
    if is_in_eclipse:
        return 0.0
    if proj_area_m2 <= 0.0:
        return 0.0
    if solar_absorptivity < 0.0:
        return 0.0
    return solar_absorptivity * proj_area_m2 * SOLAR_CONSTANT_W_M2


def update_heater_state(
    current_heater_active: bool,
    bus_temp_c: float,
    on_threshold_c: float = 5.0,
    off_threshold_c: float = 15.0,
) -> bool:
    """Apply thermostatic heater hysteresis logic.

    The heater turns ON if T_bus < on_threshold_c.
    The heater turns OFF if T_bus > off_threshold_c.
    Between thresholds: no change (hysteresis).

    Parameters
    ----------
    current_heater_active:
        Current heater state (True = ON).
    bus_temp_c:
        Current bus temperature [°C].
    on_threshold_c:
        Temperature below which heater activates [°C]. Default: 5.0.
    off_threshold_c:
        Temperature above which heater deactivates [°C]. Default: 15.0.

    Returns
    -------
    bool
        New heater state (True = ON).
    """
    if off_threshold_c <= on_threshold_c:
        msg = (
            f"off_threshold ({off_threshold_c}°C) must be greater than "
            f"on_threshold ({on_threshold_c}°C) for hysteresis to work."
        )
        raise ValueError(msg)

    if bus_temp_c < on_threshold_c:
        return True  # Turn ON
    if bus_temp_c > off_threshold_c:
        return False  # Turn OFF
    # Inside hysteresis band: maintain current state
    return current_heater_active


def integrate_thermal_state(
    bus_temp_k: float,
    payload_temp_k: float,
    total_electrical_dissipation_w: float,
    is_in_eclipse: bool,
    heater_active: bool,
    dt_s: float,
    heat_capacity_j_per_k: float = 45_000.0,
    radiator_area_m2: float = 0.6,
    proj_area_m2: float = 0.3,
    solar_absorptivity: float = 0.15,
    ir_emissivity: float = 0.85,
    heater_power_w: float = 40.0,
) -> tuple[float, float, float, float]:
    """Integrate the lumped thermal energy balance over one timestep.

    m · c_p · dT/dt = Q_in − Q_out

    Q_in  = P_dissipated + Q_solar + Q_heater
    Q_out = ε · σ · A_radiator · (T⁴ − T_space⁴)

    Forward Euler integration:
        T(t + Δt) = T(t) + (Q_in − Q_out) / (m·c_p) · Δt

    The payload temperature is modelled as following the bus temperature
    with a simplified lag factor (fraction of full change per tick) since
    the payload is thermally coupled to the bus but has its own heat mass.

    Parameters
    ----------
    bus_temp_k:
        Current spacecraft bus temperature [K].
    payload_temp_k:
        Current payload temperature [K].
    total_electrical_dissipation_w:
        All electrical power dissipated as heat in bus [W].
        (For this lumped model, all electrical load becomes heat.)
    is_in_eclipse:
        True if in Earth shadow.
    heater_active:
        True if survival heaters are powered on.
    dt_s:
        Integration timestep [s].
    heat_capacity_j_per_k:
        m·c_p [J/K] lumped thermal mass. Default: 45000 J/K.
    radiator_area_m2:
        A_radiator [m²]. Default: 0.6 m².
    proj_area_m2:
        A_proj [m²] projected area for solar absorption. Default: 0.3 m².
    solar_absorptivity:
        α_solar. Default: 0.15.
    ir_emissivity:
        ε. Default: 0.85.
    heater_power_w:
        Heater output power [W] when active. Default: 40.0 W.

    Returns
    -------
    tuple[float, float, float, float]
        (new_bus_temp_k, new_payload_temp_k, q_in_w, q_out_w)

    Raises
    ------
    ValueError
        If any physical constraint is violated.
    """
    if dt_s <= 0.0:
        msg = f"Thermal timestep must be positive; got {dt_s} s"
        raise ValueError(msg)
    if heat_capacity_j_per_k <= 0.0:
        msg = f"Heat capacity must be positive; got {heat_capacity_j_per_k} J/K"
        raise ValueError(msg)
    if bus_temp_k <= 0.0:
        msg = f"Bus temperature must be > 0 K; got {bus_temp_k} K"
        raise ValueError(msg)

    # Heater contribution to Q_in
    q_heater = heater_power_w if heater_active else 0.0

    # Solar absorption
    q_solar = compute_solar_heating(solar_absorptivity, proj_area_m2, is_in_eclipse)

    # Total heat input to bus
    q_in = total_electrical_dissipation_w + q_solar + q_heater

    # Radiative heat loss (Stefan-Boltzmann)
    q_out = compute_radiative_heat_loss(bus_temp_k, radiator_area_m2, ir_emissivity)

    # Net heat [W] → temperature change [K/s] → Kelvin after dt
    dT_dt = (q_in - q_out) / heat_capacity_j_per_k
    new_bus_temp_k = bus_temp_k + dT_dt * dt_s

    # Payload temperature: simplified coupling — payload follows bus with 20% lag factor
    # (payload has its own thermal mass, represented by a slower response)
    payload_coupling = 0.05  # fraction of difference resolved per second
    payload_pull_k = (new_bus_temp_k - payload_temp_k) * payload_coupling * dt_s
    new_payload_temp_k = payload_temp_k + payload_pull_k

    # Physical floor: cannot be below absolute zero (should never trigger in practice)
    new_bus_temp_k = max(0.1, new_bus_temp_k)
    new_payload_temp_k = max(0.1, new_payload_temp_k)

    return new_bus_temp_k, new_payload_temp_k, q_in, q_out


def evaluate_thermal_health(bus_temp_c: float) -> str:
    """Classify bus temperature into a health status.

    Gap-free threshold matrix:
        NOMINAL:  +5°C ≤ T ≤ +35°C
        WARNING:  (-15°C ≤ T < +5°C)  OR  (+35°C < T ≤ +65°C)
        CRITICAL: T < -15°C  OR  T > +65°C

    Parameters
    ----------
    bus_temp_c:
        Bus temperature [°C].

    Returns
    -------
    str
        Health status: "NOMINAL", "WARNING", or "CRITICAL".
    """
    if bus_temp_c < TEMP_CRITICAL_LOW_C or bus_temp_c > TEMP_CRITICAL_HIGH_C:
        return "CRITICAL"
    if bus_temp_c < TEMP_NOMINAL_LOW_C or bus_temp_c > TEMP_NOMINAL_HIGH_C:
        return "WARNING"
    return "NOMINAL"
