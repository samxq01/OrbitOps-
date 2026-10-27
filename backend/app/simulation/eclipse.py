"""OrbitOps Phase 03 — Cylindrical Earth Shadow (Eclipse) Detection.

Mathematical Model
------------------
A satellite at ECI position vector r⃗ is in Earth's shadow when:

    (1) r⃗ · ŝ < 0          (satellite is on the anti-sun side)
    (2) |r⃗ - (r⃗ · ŝ)ŝ| < R_E   (satellite is within Earth's cylindrical shadow)

where:
    ŝ  = unit vector pointing toward the Sun (from Earth)
    R_E = 6371.0 km (mean Earth radius)

This is the cylindrical shadow model, which neglects penumbra (partial shadow).
For educational purposes this is appropriate and produces an eclipse duration
consistent with the SRS target of ~35 min per ~95 min LEO orbit.

Sun Direction Assumption
------------------------
The Sun direction vector is held constant in the ECI frame for Phase 03.
The ecliptic precession rate is ~360°/year ≈ 0.986°/day, which is small over
the simulation time scales used in this educational context.

Default sun direction: along the +X ECI axis (equinox reference direction).
This simplification is documented and produces deterministic eclipse transitions.

Reference: Vallado, "Fundamentals of Astrodynamics and Applications" §5.3.
"""

from __future__ import annotations

import math

from app.simulation.orbit import EARTH_RADIUS_KM

# Sun direction in ECI frame. Default: +X axis (vernal equinox direction).
# This is a fixed unit vector for Phase 03 (no solar precession modeled).
DEFAULT_SUN_DIRECTION_ECI: tuple[float, float, float] = (1.0, 0.0, 0.0)


def is_in_eclipse(
    pos_x_km: float,
    pos_y_km: float,
    pos_z_km: float,
    sun_direction: tuple[float, float, float] = DEFAULT_SUN_DIRECTION_ECI,
) -> bool:
    """Determine whether a satellite is in Earth's cylindrical shadow.

    Eclipse condition (both must hold):
        (A) r⃗ · ŝ < 0        (on the anti-sun side of Earth)
        (B) |r⃗ − (r⃗·ŝ)ŝ| < R_E  (within Earth's cylindrical projection)

    Parameters
    ----------
    pos_x_km, pos_y_km, pos_z_km:
        Satellite position in ECI frame [km].
    sun_direction:
        Unit vector pointing from Earth toward the Sun in ECI frame.
        Defaults to +X axis (Phase 03 fixed-sun assumption).

    Returns
    -------
    bool
        True if satellite is in eclipse (Earth shadow), False if sunlit.
    """
    sx, sy, sz = sun_direction
    # Ensure sun vector is a unit vector (normalise defensively)
    s_mag = math.sqrt(sx**2 + sy**2 + sz**2)
    if s_mag < 1e-10:
        # Degenerate sun vector: assume no eclipse
        return False
    sx, sy, sz = sx / s_mag, sy / s_mag, sz / s_mag

    # (A) Dot product r⃗ · ŝ
    r_dot_s = pos_x_km * sx + pos_y_km * sy + pos_z_km * sz

    if r_dot_s >= 0.0:
        # Satellite is on the sun side — cannot be in Earth shadow
        return False

    # (B) Perpendicular distance from satellite to the Earth-Sun line
    # Projection of r⃗ onto ŝ
    proj_x = r_dot_s * sx
    proj_y = r_dot_s * sy
    proj_z = r_dot_s * sz

    # Perpendicular component
    perp_x = pos_x_km - proj_x
    perp_y = pos_y_km - proj_y
    perp_z = pos_z_km - proj_z
    perp_dist_km = math.sqrt(perp_x**2 + perp_y**2 + perp_z**2)

    return perp_dist_km < EARTH_RADIUS_KM


def compute_eclipse_fraction(
    semi_major_axis_km: float,
    inclination_rad: float = 0.0,
) -> float:
    """Estimate fractional eclipse time for a circular orbit.

    Uses the simple geometric formula for the cylindrical shadow model:
        f_eclipse ≈ arcsin(R_E / a) / π

    This is the fraction of the orbit spent in Earth's shadow for
    an orbit with zero inclination relative to the ecliptic plane.
    For higher inclinations, eclipse fraction decreases (polar orbits can
    have sun-synchronous geometry with reduced or zero eclipse).

    Parameters
    ----------
    semi_major_axis_km:
        Semi-major axis [km].
    inclination_rad:
        Orbital inclination [rad] (unused in this simplified formula,
        included for future enhancement).

    Returns
    -------
    float
        Estimated eclipse fraction [0, 1].
    """
    if semi_major_axis_km <= EARTH_RADIUS_KM:
        return 0.0
    ratio = EARTH_RADIUS_KM / semi_major_axis_km
    if ratio >= 1.0:
        return 1.0
    return math.asin(ratio) / math.pi
