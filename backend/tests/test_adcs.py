"""Tests for OrbitOps Phase 03 — ADCS Subsystem Model."""

import math
import random

import pytest

from app.simulation.adcs import (
    MAX_CONTROL_TORQUE_NM,
    SAFE_TUMBLE_MIN_RATE_DPS,
    compute_control_torque,
    compute_disturbance_torque,
    compute_sun_incidence,
    evaluate_adcs_health,
    integrate_angular_rate,
)


class TestDisturbanceTorque:
    def test_torque_is_deterministic_for_seeded_rng(self) -> None:
        """Same seeded RNG → same torque sequence."""
        rng_a = random.Random(42)
        rng_b = random.Random(42)
        for _ in range(100):
            tau_a = compute_disturbance_torque(rng_a)
            tau_b = compute_disturbance_torque(rng_b)
            assert tau_a == tau_b

    def test_torque_small_magnitude(self) -> None:
        """Disturbance torque should be small (σ ≈ 1e-4 N·m)."""
        rng = random.Random(42)
        torques = [abs(compute_disturbance_torque(rng)) for _ in range(1000)]
        avg = sum(torques) / len(torques)
        # Expected |torque| ≈ σ * sqrt(2/π) ≈ 8e-5 N·m
        assert avg < 1e-3  # Should be << 1e-3


class TestControlTorque:
    def test_safe_tumble_zero_control(self) -> None:
        """SAFE_TUMBLE: no active control → zero torque."""
        tau = compute_control_torque("SAFE_TUMBLE", angular_rate_dps=10.0)
        assert tau == 0.0

    def test_nadir_pointing_reduces_high_rate(self) -> None:
        """NADIR_POINTING: high angular rate → negative control torque (decelerating)."""
        tau = compute_control_torque("NADIR_POINTING", angular_rate_dps=5.0)
        assert tau < 0.0  # Negative = opposing rate increase

    def test_control_torque_clamped(self) -> None:
        """Control torque must be clamped to ±τ_max."""
        tau = compute_control_torque("NADIR_POINTING", angular_rate_dps=1000.0)
        assert abs(tau) <= MAX_CONTROL_TORQUE_NM

    def test_sun_pointing_also_has_control(self) -> None:
        """SUN_POINTING also applies control torque."""
        tau = compute_control_torque("SUN_POINTING", angular_rate_dps=5.0)
        assert tau != 0.0


class TestAngularRateIntegration:
    def test_zero_disturbance_nadir_converges(self) -> None:
        """In NADIR_POINTING, angular rate should converge toward nominal over time."""
        rng = random.Random(0)  # Seeded but not contributing to perfect convergence
        rate = 1.0  # Starting at 1°/s
        inertia = 25.0
        for _ in range(1000):
            rate = integrate_angular_rate(rate, "NADIR_POINTING", inertia, dt_s=1.0, rng=rng)
        # Rate should be reduced (though not to exactly 0 due to disturbance noise)
        assert rate < 0.5  # Should have converged

    def test_safe_tumble_rate_bounded_above_minimum(self) -> None:
        """SAFE_TUMBLE rate must be at least SAFE_TUMBLE_MIN_RATE_DPS."""
        rng = random.Random(42)
        rate = 0.1  # Start below tumble rate
        rate = integrate_angular_rate(rate, "SAFE_TUMBLE", 25.0, 1.0, rng)
        assert rate >= SAFE_TUMBLE_MIN_RATE_DPS

    def test_rate_never_negative(self) -> None:
        """Angular rate is a scalar magnitude; must be ≥ 0."""
        rng = random.Random(42)
        rate = 0.01  # Very low rate
        for _ in range(100):
            rate = integrate_angular_rate(rate, "NADIR_POINTING", 25.0, 1.0, rng)
        assert rate >= 0.0

    def test_invalid_inertia_raises(self) -> None:
        rng = random.Random(42)
        with pytest.raises(ValueError, match="positive"):
            integrate_angular_rate(0.1, "NADIR_POINTING", 0.0, 1.0, rng)

    def test_invalid_timestep_raises(self) -> None:
        rng = random.Random(42)
        with pytest.raises(ValueError, match="positive"):
            integrate_angular_rate(0.1, "NADIR_POINTING", 25.0, 0.0, rng)

    def test_determinism_across_same_seed(self) -> None:
        """Same seed and initial conditions → identical rate sequence."""
        rate_a = rate_b = 0.5
        rng_a = random.Random(7)
        rng_b = random.Random(7)
        for _ in range(100):
            rate_a = integrate_angular_rate(rate_a, "NADIR_POINTING", 25.0, 1.0, rng_a)
            rate_b = integrate_angular_rate(rate_b, "NADIR_POINTING", 25.0, 1.0, rng_b)
        assert rate_a == pytest.approx(rate_b, rel=1e-12)


class TestSunIncidence:
    def test_sun_pointing_near_zero(self) -> None:
        """SUN_POINTING should produce small incidence angles."""
        rng = random.Random(42)
        angles = [
            compute_sun_incidence("SUN_POINTING", 0.0, math.radians(97.6), rng) for _ in range(100)
        ]
        avg = sum(angles) / len(angles)
        assert avg < 5.0  # Average should be very small

    def test_nadir_pointing_angle_in_range(self) -> None:
        """NADIR_POINTING sun incidence must be in [0, 90]."""
        rng = random.Random(42)
        for nu in [0.0, math.pi / 4, math.pi / 2, math.pi]:
            angle = compute_sun_incidence("NADIR_POINTING", nu, math.radians(97.6), rng)
            assert 0.0 <= angle <= 90.0

    def test_safe_tumble_varies_widely(self) -> None:
        """SAFE_TUMBLE produces widely varying incidence angles."""
        rng = random.Random(42)
        angles = [
            compute_sun_incidence("SAFE_TUMBLE", 0.0, math.radians(45.0), rng) for _ in range(200)
        ]
        # Should have both small and large angles
        assert min(angles) < 30.0
        assert max(angles) > 60.0


class TestADCSHealth:
    def test_nominal_low_rate_nadir(self) -> None:
        assert evaluate_adcs_health(0.02, "NADIR_POINTING") == "NOMINAL"

    def test_warning_moderate_rate(self) -> None:
        assert evaluate_adcs_health(1.0, "NADIR_POINTING") == "WARNING"

    def test_critical_safe_tumble(self) -> None:
        assert evaluate_adcs_health(0.02, "SAFE_TUMBLE") == "CRITICAL"

    def test_critical_high_rate(self) -> None:
        assert evaluate_adcs_health(10.0, "NADIR_POINTING") == "CRITICAL"
