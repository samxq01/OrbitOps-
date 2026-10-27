"""OrbitOps Phase 03 — Attitude Determination and Control Subsystem (ADCS).

Mathematical Model (from simulation-spec.md §4)
------------------------------------------------
Angular rate dynamics (simplified scalar form):

    ω(t + Δt) = ω(t) + (τ_control + τ_disturbance) / I_sat · Δt

where:
    τ_control:     Control torque from reaction wheels [N·m]
    τ_disturbance: Disturbance torque (gravity gradient, drag) [N·m]
    I_sat:         Satellite moment of inertia [kg·m²]
    ω:             Scalar angular rate magnitude [°/s]

Pointing Modes
--------------
NADIR_POINTING:
    - Payload points toward Earth centre.
    - Nominal mode for imaging satellites.
    - Control torque drives ω toward < 0.05°/s.
    - Sun incidence angle depends on orbital geometry (non-zero in general).

SUN_POINTING:
    - Solar arrays oriented perpendicular to sun vector.
    - Maximises solar power during recovery or charging.
    - Sun incidence angle driven toward 0° (cos θ → 1.0, max generation).
    - Control torque drives ω toward nominal.

SAFE_TUMBLE:
    - Uncontrolled rotation induced by fault or actuator failure.
    - Control torque is zero (no active attitude control).
    - Angular rate exceeds 5°/s threshold.
    - Sun incidence angle varies randomly (reduced solar generation effectiveness).
    - Pointing error is unbounded.

Disturbance Model
-----------------
Disturbance torque is modelled as Gaussian white noise with σ = 1×10⁻⁴ N·m.
The disturbance RNG is owned by the SatelliteRuntimeState.satellite_rng
(a seeded Python Random instance), NOT the global random module.
This ensures determinism per satellite.

Units
-----
Angular rate: degrees/second [°/s]
Torque: N·m
Inertia: kg·m²

Fidelity Disclaimer
-------------------
This model does not implement:
- Full quaternion attitude kinematics.
- Flexible body dynamics.
- Reaction wheel momentum management.
- Magnetic torquer modelling.
- Real-time quaternion integration.
These require Phase 03+ extensions and are not claimed here.
"""

from __future__ import annotations

import math
import random

# Physical constants
MAX_CONTROL_TORQUE_NM: float = 0.05  # τ_max [N·m]
DISTURBANCE_SIGMA_NM: float = 1e-4  # σ_disturbance [N·m]

# Nominal angular rate threshold [°/s]
NOMINAL_RATE_THRESHOLD_DPS: float = 0.05

# SAFE_TUMBLE minimum rate [°/s]
SAFE_TUMBLE_MIN_RATE_DPS: float = 5.0

# Convergence gain for proportional rate control
RATE_CONTROL_GAIN: float = 0.1  # Fraction of error corrected per tick


def compute_disturbance_torque(rng: random.Random) -> float:
    """Sample a Gaussian disturbance torque.

    Uses the satellite's own seeded RNG, NOT the global random module.

    Parameters
    ----------
    rng:
        Satellite-specific seeded Random instance.

    Returns
    -------
    float
        Disturbance torque sample [N·m].
    """
    return rng.gauss(0.0, DISTURBANCE_SIGMA_NM)


def compute_control_torque(
    pointing_mode: str,
    angular_rate_dps: float,
    max_torque_nm: float = MAX_CONTROL_TORQUE_NM,
) -> float:
    """Compute the control torque from reaction wheels.

    For NADIR_POINTING and SUN_POINTING:
        Proportional control driving rate toward 0 (NOMINAL_RATE_THRESHOLD_DPS).
        Torque is clamped to [-τ_max, +τ_max].

    For SAFE_TUMBLE:
        No active control (zero torque).

    Parameters
    ----------
    pointing_mode:
        "NADIR_POINTING", "SUN_POINTING", or "SAFE_TUMBLE".
    angular_rate_dps:
        Current angular rate magnitude [°/s].
    max_torque_nm:
        Maximum reaction wheel torque [N·m].

    Returns
    -------
    float
        Control torque [N·m]. Positive = decelerating. Negative = accelerating.
    """
    if pointing_mode == "SAFE_TUMBLE":
        return 0.0  # No active control

    # Proportional control: target rate = NOMINAL_RATE_THRESHOLD_DPS
    rate_error_dps = angular_rate_dps - NOMINAL_RATE_THRESHOLD_DPS
    # Control torque opposes the error (negative feedback)
    # Scaled by some proportional gain; clamped to max torque
    torque_nm = -RATE_CONTROL_GAIN * rate_error_dps
    return max(-max_torque_nm, min(max_torque_nm, torque_nm))


def integrate_angular_rate(
    angular_rate_dps: float,
    pointing_mode: str,
    inertia_kg_m2: float,
    dt_s: float,
    rng: random.Random,
    max_torque_nm: float = MAX_CONTROL_TORQUE_NM,
) -> float:
    """Integrate angular rate over one timestep.

    ω(t + Δt) = ω(t) + (τ_control + τ_disturbance) / I_sat · Δt

    The torque is in N·m, inertia in kg·m², giving angular acceleration in
    rad/s². Convert to °/s² by multiplying by (180/π):
        Δω [°/s] = (τ [N·m] / I [kg·m²]) · Δt [s] · (180/π)

    Parameters
    ----------
    angular_rate_dps:
        Current angular rate [°/s].
    pointing_mode:
        "NADIR_POINTING", "SUN_POINTING", or "SAFE_TUMBLE".
    inertia_kg_m2:
        Satellite moment of inertia [kg·m²]. Must be positive.
    dt_s:
        Integration timestep [s].
    rng:
        Satellite-specific seeded RNG for disturbance sampling.
    max_torque_nm:
        Maximum control torque [N·m].

    Returns
    -------
    float
        New angular rate [°/s]. Always ≥ 0.

    Raises
    ------
    ValueError
        If inertia or timestep are non-positive.
    """
    if inertia_kg_m2 <= 0.0:
        msg = f"Moment of inertia must be positive; got {inertia_kg_m2} kg·m²"
        raise ValueError(msg)
    if dt_s <= 0.0:
        msg = f"ADCS timestep must be positive; got {dt_s} s"
        raise ValueError(msg)

    tau_control = compute_control_torque(pointing_mode, angular_rate_dps, max_torque_nm)
    tau_disturbance = compute_disturbance_torque(rng)
    tau_net = tau_control + tau_disturbance

    # Angular acceleration [rad/s²] → convert to [°/s²]
    alpha_dps2 = (tau_net / inertia_kg_m2) * math.degrees(1.0)

    new_rate = angular_rate_dps + alpha_dps2 * dt_s

    # Physical floor: rate cannot be negative (it's a scalar magnitude)
    new_rate = max(0.0, new_rate)

    # In SAFE_TUMBLE mode, enforce minimum tumble rate
    if pointing_mode == "SAFE_TUMBLE":
        new_rate = max(SAFE_TUMBLE_MIN_RATE_DPS, new_rate)

    return new_rate


def compute_sun_incidence(
    pointing_mode: str,
    orbital_true_anomaly_rad: float,
    inclination_rad: float,
    rng: random.Random,
) -> float:
    """Estimate sun incidence angle on solar arrays based on pointing mode.

    Simplified geometric model for educational purposes:

    SUN_POINTING:
        Arrays track the sun → incidence angle ≈ 0° (small residual error).
        Small noise added for realism.

    NADIR_POINTING:
        Arrays are not tracking sun. Incidence depends on orbital geometry.
        Simplified: varies sinusoidally with orbital phase.
        Typical average angle ≈ 30–45° for LEO sun-synchronous.

    SAFE_TUMBLE:
        Random orientation: incidence uniformly distributed on [0°, 90°).
        Solar generation severely degraded.

    Parameters
    ----------
    pointing_mode:
        "NADIR_POINTING", "SUN_POINTING", or "SAFE_TUMBLE".
    orbital_true_anomaly_rad:
        Current true anomaly [rad], used for NADIR geometry estimation.
    inclination_rad:
        Orbital inclination [rad].
    rng:
        Satellite-specific seeded RNG.

    Returns
    -------
    float
        Sun incidence angle [°], in [0, 90].
    """
    if pointing_mode == "SUN_POINTING":
        # Tracking arrays: small residual pointing error (1–3° noise)
        return abs(rng.gauss(0.0, 1.5))

    if pointing_mode == "NADIR_POINTING":
        # Simplified: sun angle varies with orbital phase
        # β₀ = 30° baseline + 20° × |sin(inclination)| solar beta angle contribution
        beta_deg = 30.0 + 20.0 * abs(math.sin(inclination_rad))
        # Variation with orbital position (simplified: sinusoidal)
        variation = 15.0 * math.sin(orbital_true_anomaly_rad)
        angle = beta_deg + variation + rng.gauss(0.0, 0.5)
        return max(0.0, min(90.0, angle))

    # SAFE_TUMBLE: random orientation
    return rng.uniform(0.0, 90.0)


def evaluate_adcs_health(
    angular_rate_dps: float,
    pointing_mode: str,
) -> str:
    """Classify ADCS health from angular rate and pointing mode.

    NOMINAL:  rate ≤ 0.5°/s and not in SAFE_TUMBLE
    WARNING:  0.5°/s < rate ≤ 5°/s or unexpected high rate in controlled mode
    CRITICAL: rate > 5°/s or in SAFE_TUMBLE

    Parameters
    ----------
    angular_rate_dps:
        Current angular rate [°/s].
    pointing_mode:
        Current pointing mode.

    Returns
    -------
    str
        Health status: "NOMINAL", "WARNING", or "CRITICAL".
    """
    if pointing_mode == "SAFE_TUMBLE" or angular_rate_dps > 5.0:
        return "CRITICAL"
    if angular_rate_dps > 0.5:
        return "WARNING"
    return "NOMINAL"
