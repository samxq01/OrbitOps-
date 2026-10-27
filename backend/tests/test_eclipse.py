"""Tests for OrbitOps Phase 03 — Eclipse Detection."""

from app.simulation.eclipse import (
    compute_eclipse_fraction,
    is_in_eclipse,
)
from app.simulation.orbit import EARTH_RADIUS_KM


class TestEclipseGeometry:
    """Test cylindrical shadow model geometry."""

    def test_satellite_directly_sunlit(self) -> None:
        """Satellite on the sun side → NOT in eclipse."""
        # Sun is at +X. Satellite at +X direction → facing sun.
        r = 7000.0
        in_shadow = is_in_eclipse(r, 0.0, 0.0)
        assert in_shadow is False

    def test_satellite_on_anti_sun_side_within_shadow(self) -> None:
        """Satellite on anti-sun side AND within Earth's cylindrical shadow → ECLIPSE."""
        # Sun at +X. Satellite at -X, just outside Earth radius (in cylinder)
        r = 7000.0
        in_shadow = is_in_eclipse(-r, 0.0, 0.0)
        assert in_shadow is True

    def test_satellite_behind_earth_outside_shadow_cylinder(self) -> None:
        """Satellite on anti-sun side but far off the shadow cylinder axis → NOT in eclipse."""
        # Anti-sun side (r·s < 0) but perpendicular distance >> R_Earth
        # Position: x = -7000 (anti-sun), y = 20000 (far from cylinder axis)
        in_shadow = is_in_eclipse(-7000.0, 20_000.0, 0.0)
        assert in_shadow is False

    def test_satellite_at_exact_earth_radius_boundary(self) -> None:
        """Satellite at exact Earth radius on anti-sun side → in eclipse."""
        in_shadow = is_in_eclipse(
            -EARTH_RADIUS_KM * 1.5,  # behind Earth
            EARTH_RADIUS_KM * 0.99,  # just inside shadow cylinder
            0.0,
        )
        assert in_shadow is True

    def test_satellite_outside_shadow_cylinder(self) -> None:
        """Satellite behind Earth but outside the shadow cylinder → NOT in eclipse."""
        in_shadow = is_in_eclipse(
            -EARTH_RADIUS_KM * 1.5,
            EARTH_RADIUS_KM * 1.01,  # just outside shadow cylinder
            0.0,
        )
        assert in_shadow is False

    def test_eclipse_with_custom_sun_direction(self) -> None:
        """Eclipse detection works for non-default sun direction."""
        # Sun in +Y direction. Satellite at -Y should be in shadow.
        in_shadow = is_in_eclipse(0.0, -7000.0, 0.0, sun_direction=(0.0, 1.0, 0.0))
        assert in_shadow is True

    def test_degenerate_zero_sun_vector_no_eclipse(self) -> None:
        """Degenerate zero sun vector → no eclipse (safe fallback)."""
        in_shadow = is_in_eclipse(7000.0, 0.0, 0.0, sun_direction=(0.0, 0.0, 0.0))
        assert in_shadow is False

    def test_polar_position_can_escape_shadow(self) -> None:
        """A high-inclination satellite at the pole is outside Earth's cylindrical shadow."""
        # Satellite directly above north pole (Z-axis) → outside cylindrical shadow along X
        in_shadow = is_in_eclipse(0.0, 0.0, 7000.0)
        # r·s = 0 (z doesn't contribute to x direction) → not on anti-sun side
        assert in_shadow is False


class TestEclipseRepeatability:
    def test_eclipse_is_deterministic(self) -> None:
        """Same inputs → same output every time."""
        for _ in range(10):
            assert is_in_eclipse(-7000.0, 0.0, 0.0) is True
            assert is_in_eclipse(7000.0, 0.0, 0.0) is False

    def test_eclipse_transition_at_earth_radius(self) -> None:
        """Transition from sunlit to eclipse as perpendicular distance crosses R_E."""
        # Just inside shadow cylinder
        in_shadow_inside = is_in_eclipse(-7000.0, EARTH_RADIUS_KM - 1.0, 0.0)
        # Just outside shadow cylinder
        in_shadow_outside = is_in_eclipse(-7000.0, EARTH_RADIUS_KM + 1.0, 0.0)
        assert in_shadow_inside is True
        assert in_shadow_outside is False


class TestEclipseFraction:
    def test_low_orbit_eclipse_fraction(self) -> None:
        """~550 km LEO should have eclipse fraction ≈ 0.35 (35%)."""
        f = compute_eclipse_fraction(6921.0)
        # arcsin(6371/6921) / π ≈ 0.304
        assert 0.25 <= f <= 0.40, f"Eclipse fraction {f:.3f} outside expected range"

    def test_higher_orbit_smaller_fraction(self) -> None:
        """Higher orbit → smaller eclipse fraction (Earth subtends smaller angle)."""
        f_low = compute_eclipse_fraction(6921.0)
        f_high = compute_eclipse_fraction(42_164.0)  # GEO
        assert f_high < f_low

    def test_below_earth_radius_zero_fraction(self) -> None:
        f = compute_eclipse_fraction(EARTH_RADIUS_KM - 1.0)
        assert f == 0.0


class TestEclipsePowerCoupling:
    def test_eclipse_suppresses_solar_power(self) -> None:
        """Solar power must be zero when in eclipse."""
        from app.simulation.power import compute_solar_power

        power_sunlit = compute_solar_power(1.2, 0.28, 0.0, is_in_eclipse=False)
        power_eclipse = compute_solar_power(1.2, 0.28, 0.0, is_in_eclipse=True)
        assert power_sunlit > 0.0
        assert power_eclipse == 0.0
