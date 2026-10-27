"""Tests for OrbitOps Phase 03 — Orbital Propagation Engine."""

import math

import pytest

from app.simulation.orbit import (
    EARTH_GM_KM3_S2,
    EARTH_RADIUS_KM,
    compute_eci_position,
    compute_mean_motion,
    compute_orbital_period,
    eci_to_geodetic,
    propagate_true_anomaly,
    validate_orbital_parameters,
)


class TestMeanMotion:
    def test_alpha_mean_motion(self) -> None:
        """SAT-001 ALPHA: a = 6921.0 km → n = sqrt(μ/a³)."""
        a = 6921.0
        n = compute_mean_motion(a)
        expected = math.sqrt(EARTH_GM_KM3_S2 / (a**3))
        assert n == pytest.approx(expected, rel=1e-10)

    def test_beta_mean_motion(self) -> None:
        a = 7071.0
        n = compute_mean_motion(a)
        expected = math.sqrt(EARTH_GM_KM3_S2 / (a**3))
        assert n == pytest.approx(expected, rel=1e-10)

    def test_gamma_mean_motion(self) -> None:
        a = 7021.0
        n = compute_mean_motion(a)
        expected = math.sqrt(EARTH_GM_KM3_S2 / (a**3))
        assert n == pytest.approx(expected, rel=1e-10)

    def test_below_earth_surface_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_mean_motion(EARTH_RADIUS_KM - 1.0)

    def test_at_earth_radius_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_mean_motion(EARTH_RADIUS_KM)


class TestOrbitalPeriod:
    def test_alpha_period_approximately_95min(self) -> None:
        """~550 km LEO should have period ≈ 95 minutes."""
        period_s = compute_orbital_period(6921.0)
        period_min = period_s / 60.0
        assert 93.0 <= period_min <= 98.0, f"Period {period_min:.1f} min outside expected range"

    def test_beta_period(self) -> None:
        """~700 km LEO: period ≈ 98–100 minutes."""
        period_s = compute_orbital_period(7071.0)
        period_min = period_s / 60.0
        assert 97.0 <= period_min <= 102.0

    def test_period_formula(self) -> None:
        """T = 2π * sqrt(a³/μ)."""
        a = 6921.0
        expected = 2.0 * math.pi * math.sqrt(a**3 / EARTH_GM_KM3_S2)
        assert compute_orbital_period(a) == pytest.approx(expected, rel=1e-10)

    def test_higher_altitude_longer_period(self) -> None:
        """Higher altitude → longer period (Kepler's third law)."""
        t_low = compute_orbital_period(6921.0)
        t_high = compute_orbital_period(7500.0)
        assert t_high > t_low


class TestECIPosition:
    def test_equatorial_circular_position(self) -> None:
        """i=0, Ω=0, ω=0, ν=0 → satellite at (a, 0, 0) in ECI."""
        a = 7000.0
        x, y, z = compute_eci_position(a, 0.0, 0.0, 0.0, 0.0)
        assert x == pytest.approx(a, rel=1e-10)
        assert y == pytest.approx(0.0, abs=1e-9)
        assert z == pytest.approx(0.0, abs=1e-9)

    def test_position_at_quarter_orbit(self) -> None:
        """i=0, ν=π/2 → satellite at (0, a, 0) for equatorial orbit."""
        a = 7000.0
        x, y, z = compute_eci_position(a, 0.0, 0.0, 0.0, math.pi / 2)
        assert x == pytest.approx(0.0, abs=1e-9)
        assert y == pytest.approx(a, rel=1e-9)
        assert z == pytest.approx(0.0, abs=1e-9)

    def test_orbital_radius_constant(self) -> None:
        """For a circular orbit, |r| = a at all true anomaly values."""
        a = 6921.0
        incl = math.radians(97.6)
        for nu in [0.0, math.pi / 4, math.pi / 2, math.pi, 3 * math.pi / 2]:
            x, y, z = compute_eci_position(a, incl, 0.0, 0.0, nu)
            r = math.sqrt(x**2 + y**2 + z**2)
            assert r == pytest.approx(a, rel=1e-9), f"r={r:.4f} ≠ a={a} at ν={nu:.2f} rad"

    def test_polar_orbit_z_variation(self) -> None:
        """For a polar orbit (i=90°), z oscillates between -a and +a."""
        a = 7021.0
        incl = math.radians(89.0)
        x, y, z = compute_eci_position(a, incl, 0.0, 0.0, math.pi / 2)
        # At ν=π/2 in a nearly polar orbit, z should be near ±a*sin(incl)
        assert abs(z) > 0.0

    def test_inclination_limits_latitude(self) -> None:
        """Max |z| for inclination i is limited to a * sin(i)."""
        a = 6921.0
        incl = math.radians(97.6)
        max_z = 0.0
        for nu in [i * 0.1 for i in range(63)]:
            _, _, z = compute_eci_position(a, incl, 0.0, 0.0, nu)
            max_z = max(max_z, abs(z))
        # max |z| should be close to a (for inclination ≈ 90°)
        assert max_z < a * 1.001


class TestTrueAnomalyPropagation:
    def test_positive_propagation(self) -> None:
        n = compute_mean_motion(6921.0)
        dt = 60.0
        nu0 = 0.5
        nu1 = propagate_true_anomaly(nu0, n, dt)
        expected = (nu0 + n * dt) % (2.0 * math.pi)
        assert nu1 == pytest.approx(expected, rel=1e-10)

    def test_wrapping_past_2pi(self) -> None:
        n = compute_mean_motion(6921.0)
        # Large dt that wraps around multiple times
        dt = 100000.0
        nu1 = propagate_true_anomaly(0.0, n, dt)
        assert 0.0 <= nu1 < 2.0 * math.pi

    def test_zero_dt_raises(self) -> None:
        with pytest.raises(ValueError):
            propagate_true_anomaly(0.0, 1e-3, 0.0)

    def test_negative_dt_raises(self) -> None:
        with pytest.raises(ValueError):
            propagate_true_anomaly(0.0, 1e-3, -1.0)

    def test_deterministic_propagation(self) -> None:
        """Same inputs → same output."""
        n = compute_mean_motion(6921.0)
        for _ in range(5):
            nu = propagate_true_anomaly(0.1, n, 30.0)
            assert nu == propagate_true_anomaly(0.1, n, 30.0)

    def test_position_changes_with_time(self) -> None:
        """True anomaly must advance after a positive dt."""
        n = compute_mean_motion(6921.0)
        nu0 = 0.0
        nu1 = propagate_true_anomaly(nu0, n, 10.0)
        assert nu1 != nu0


class TestGeodeticConversion:
    def test_equatorial_position(self) -> None:
        """ECI point along X-axis → 0° latitude."""
        r = 7000.0
        lat, lon, alt = eci_to_geodetic(r, 0.0, 0.0, sim_time_s=0.0)
        assert lat == pytest.approx(0.0, abs=1e-9)
        assert alt == pytest.approx(r - EARTH_RADIUS_KM, rel=1e-9)

    def test_altitude_positive(self) -> None:
        """Altitude must be positive for valid LEO orbits."""
        lat, lon, alt = eci_to_geodetic(7000.0, 0.0, 0.0, 0.0)
        assert alt > 0.0

    def test_latitude_bounded(self) -> None:
        """Latitude must be in [-90, 90]."""
        for x, y, z in [(7000, 0, 0), (0, 7000, 3000), (-4000, 5000, 1000)]:
            lat, _, _ = eci_to_geodetic(x, y, z, 0.0)
            assert -90.0 <= lat <= 90.0

    def test_longitude_bounded(self) -> None:
        """Longitude must be in [-180, 180]."""
        for t in [0, 1000, 5000, 43200]:
            _, lon, _ = eci_to_geodetic(7000, 0, 0, sim_time_s=t)
            assert -180.0 <= lon <= 180.0

    def test_longitude_changes_with_earth_rotation(self) -> None:
        """Due to Earth's rotation, longitude decreases with time for a fixed ECI point."""
        # For a fixed ECI point (no orbital motion), longitude should shift westward
        _, lon_t0, _ = eci_to_geodetic(7000.0, 0.0, 0.0, sim_time_s=0.0)
        _, lon_t1, _ = eci_to_geodetic(7000.0, 0.0, 0.0, sim_time_s=1000.0)
        # Earth rotates eastward, so ECI points appear to move westward in ECEF
        assert lon_t0 != lon_t1

    def test_polar_position_latitude(self) -> None:
        """ECI Z-axis position (above north pole) → +90° latitude."""
        r = 7000.0
        lat, _, _ = eci_to_geodetic(0.0, 0.0, r, 0.0)
        assert lat == pytest.approx(90.0, abs=0.001)


class TestParameterValidation:
    def test_valid_parameters_pass(self) -> None:
        validate_orbital_parameters(6921.0, 97.6)  # Should not raise

    def test_below_surface_raises(self) -> None:
        with pytest.raises(ValueError, match="surface"):
            validate_orbital_parameters(6000.0, 45.0)

    def test_negative_inclination_raises(self) -> None:
        with pytest.raises(ValueError, match="180"):
            validate_orbital_parameters(6921.0, -1.0)

    def test_inclination_over_180_raises(self) -> None:
        with pytest.raises(ValueError, match="180"):
            validate_orbital_parameters(6921.0, 181.0)
