"""OrbitOps Phase 03 — Simplified Two-Body Circular Orbit Propagator.

Mathematical Model
------------------
Uses the two-body gravitational model for a circular (zero-eccentricity) orbit.

Phase 03 Approximation
----------------------
The true anomaly advances linearly at the mean motion rate, which is the exact
solution for a CIRCULAR orbit (eccentricity = 0). This is documented as the
Phase 03 approximation for all three satellites, including GAMMA (which the
SRS labels as eccentric). The existing Phase 02 database stores only
semi_major_axis_km and inclination_deg (no eccentricity element), so
implementing true eccentric Kepler propagation would require a migration that
is not justified for Phase 03's educational scope.

Documented limitation: Phase 03 models all orbits as circular. Eccentric
propagation (Kepler's equation solver for E from M) is deferred to a future
enhancement and will require schema migration to persist eccentricity, RAAN,
and argument of perigee.

Physical constants
------------------
μ = 398600.4418 km³/s²  (Earth gravitational parameter, EGM2008)
R_E = 6371.0 km          (Mean Earth radius)

Coordinate frames
-----------------
ECI (Earth-Centred Inertial):
  - Origin: Earth centre
  - X: Vernal equinox (J2000.0)
  - Z: Earth north pole
  - Y: Completes right-handed system

ECEF (Earth-Centred Earth-Fixed) conversion:
  The Earth rotates at ω_E = 7.2921150 × 10⁻⁵ rad/s.
  Longitude = true_anomaly_based_angle - Earth_rotation_since_epoch.
  For a simplified educational model, we compute geographical longitude from
  the ECI position by subtracting Earth rotation accumulated since t=0.

Units
-----
All internal distances: km
All internal angles: radians (converted to degrees at output boundary)
All internal times: seconds
"""

from __future__ import annotations

import math

# -----------------------------------------------------------------------
# Physical constants
# -----------------------------------------------------------------------
EARTH_GM_KM3_S2: float = 398_600.4418  # μ [km³/s²]
EARTH_RADIUS_KM: float = 6_371.0  # R_E [km]
EARTH_ROTATION_RAD_S: float = 7.2921150e-5  # ω_E [rad/s] — for ECEF conversion


def compute_mean_motion(semi_major_axis_km: float) -> float:
    """Compute mean orbital motion from semi-major axis.

    n = sqrt(μ / a³)

    Parameters
    ----------
    semi_major_axis_km:
        Semi-major axis [km]. Must be > EARTH_RADIUS_KM.

    Returns
    -------
    float
        Mean motion [rad/s].

    Raises
    ------
    ValueError
        If semi-major axis is physically invalid.
    """
    if semi_major_axis_km <= EARTH_RADIUS_KM:
        msg = (
            f"Semi-major axis {semi_major_axis_km} km is at or below Earth's surface "
            f"({EARTH_RADIUS_KM} km)."
        )
        raise ValueError(msg)
    return math.sqrt(EARTH_GM_KM3_S2 / (semi_major_axis_km**3))


def compute_orbital_period(semi_major_axis_km: float) -> float:
    """Compute orbital period in seconds.

    T = 2π / n = 2π * sqrt(a³ / μ)

    Parameters
    ----------
    semi_major_axis_km:
        Semi-major axis [km].

    Returns
    -------
    float
        Orbital period [s].
    """
    n = compute_mean_motion(semi_major_axis_km)
    return (2.0 * math.pi) / n


def propagate_true_anomaly(
    true_anomaly_rad: float,
    mean_motion_rad_s: float,
    dt_s: float,
) -> float:
    """Advance true anomaly for a circular orbit.

    For a circular orbit, the true anomaly equals the mean anomaly and
    advances linearly at the mean motion rate:

        ν(t + Δt) = ν(t) + n · Δt

    The result is wrapped to [0, 2π).

    Parameters
    ----------
    true_anomaly_rad:
        Current true anomaly [rad].
    mean_motion_rad_s:
        Mean orbital motion [rad/s].
    dt_s:
        Time step [s]. Must be positive.

    Returns
    -------
    float
        Updated true anomaly [rad], in [0, 2π).
    """
    if dt_s <= 0.0:
        msg = f"Propagation timestep must be positive; got {dt_s} s"
        raise ValueError(msg)
    new_nu = true_anomaly_rad + mean_motion_rad_s * dt_s
    return new_nu % (2.0 * math.pi)


def compute_eci_position(
    semi_major_axis_km: float,
    inclination_rad: float,
    raan_rad: float,
    arg_perigee_rad: float,
    true_anomaly_rad: float,
) -> tuple[float, float, float]:
    """Convert Keplerian elements to ECI Cartesian position.

    For a circular orbit (e=0), the perifocal distance r = a.

    The orbital-plane unit vectors in ECI are:
        P̂ = rotation matrix columns from (Ω, i, ω) Euler angles
        Q̂ = perpendicular in-plane unit vector

    Position in ECI:
        r⃗ = r * (cos ν * P̂ + sin ν * Q̂)

    Parameters
    ----------
    semi_major_axis_km, inclination_rad, raan_rad, arg_perigee_rad, true_anomaly_rad:
        Classical Keplerian orbital elements.

    Returns
    -------
    tuple[float, float, float]
        (X, Y, Z) position in ECI frame [km].
    """
    r = semi_major_axis_km  # For circular orbit e=0, r = a at all points

    # Perifocal frame to ECI rotation
    # Using standard orbital mechanics rotation matrices R3(-Ω) · R1(-i) · R3(-ω)
    cos_om = math.cos(raan_rad)
    sin_om = math.sin(raan_rad)
    cos_i = math.cos(inclination_rad)
    sin_i = math.sin(inclination_rad)
    cos_w = math.cos(arg_perigee_rad)
    sin_w = math.sin(arg_perigee_rad)
    cos_nu = math.cos(true_anomaly_rad)
    sin_nu = math.sin(true_anomaly_rad)

    # P̂ components in ECI (first column of rotation matrix)
    px = cos_om * cos_w - sin_om * sin_w * cos_i
    py = sin_om * cos_w + cos_om * sin_w * cos_i
    pz = sin_w * sin_i

    # Q̂ components in ECI (second column of rotation matrix)
    qx = -cos_om * sin_w - sin_om * cos_w * cos_i
    qy = -sin_om * sin_w + cos_om * cos_w * cos_i
    qz = cos_w * sin_i

    x_km = r * (cos_nu * px + sin_nu * qx)
    y_km = r * (cos_nu * py + sin_nu * qy)
    z_km = r * (cos_nu * pz + sin_nu * qz)

    return x_km, y_km, z_km


def eci_to_geodetic(
    x_km: float,
    y_km: float,
    z_km: float,
    sim_time_s: float,
) -> tuple[float, float, float]:
    """Convert ECI Cartesian position to approximate geodetic coordinates.

    Approximation: spherical Earth (not ellipsoidal WGS-84). Suitable for
    educational purposes with errors < 0.3% in altitude.

    Longitude accounts for Earth's sidereal rotation from t=0:
        λ = atan2(y, x) − ω_E · t

    Parameters
    ----------
    x_km, y_km, z_km:
        ECI position [km].
    sim_time_s:
        Simulation time since epoch [s], used to compute Earth rotation.

    Returns
    -------
    tuple[float, float, float]
        (latitude_deg, longitude_deg, altitude_km).
        Latitude in [-90, 90], longitude in [-180, 180].
    """
    r_km = math.sqrt(x_km**2 + y_km**2 + z_km**2)
    if r_km < 1.0:
        # Guard against degenerate zero vector
        return 0.0, 0.0, 0.0

    # Latitude (geocentric; spherical Earth approximation)
    lat_rad = math.asin(z_km / r_km)

    # Inertial longitude (ECI frame)
    lon_inertial_rad = math.atan2(y_km, x_km)

    # Earth has rotated by ω_E · t since epoch — subtract to get Earth-fixed longitude
    lon_ecef_rad = lon_inertial_rad - EARTH_ROTATION_RAD_S * sim_time_s

    # Normalise longitude to [-π, π]
    lon_ecef_rad = (lon_ecef_rad + math.pi) % (2.0 * math.pi) - math.pi

    altitude_km = r_km - EARTH_RADIUS_KM

    return math.degrees(lat_rad), math.degrees(lon_ecef_rad), altitude_km


def validate_orbital_parameters(
    semi_major_axis_km: float,
    inclination_deg: float,
) -> None:
    """Validate orbital parameters against physical constraints.

    Parameters
    ----------
    semi_major_axis_km:
        Must be > EARTH_RADIUS_KM (orbit above Earth's surface).
    inclination_deg:
        Must be in [0, 180] degrees.

    Raises
    ------
    ValueError
        If any parameter is physically invalid.
    """
    if semi_major_axis_km <= EARTH_RADIUS_KM:
        msg = (
            f"Semi-major axis {semi_major_axis_km:.1f} km is ≤ Earth radius "
            f"{EARTH_RADIUS_KM:.1f} km (orbit below surface)."
        )
        raise ValueError(msg)
    if not (0.0 <= inclination_deg <= 180.0):
        msg = f"Inclination {inclination_deg}° must be in [0, 180] degrees."
        raise ValueError(msg)
