"""Tests for OrbitOps Phase 03 — Power Subsystem Model."""

import pytest

from app.simulation.power import (
    BASE_AVIONICS_POWER_W,
    DEFAULT_CHARGE_EFFICIENCY,
    SOLAR_CONSTANT_W_M2,
    compute_bus_voltage,
    compute_solar_power,
    compute_total_load,
    integrate_battery_energy,
)


class TestSolarPowerGeneration:
    def test_maximum_generation_perpendicular(self) -> None:
        """θ=0° (perpendicular) → maximum solar power."""
        power = compute_solar_power(1.2, 0.28, sun_incidence_deg=0.0, is_in_eclipse=False)
        expected = SOLAR_CONSTANT_W_M2 * 1.2 * 0.28
        assert power == pytest.approx(expected, rel=1e-9)

    def test_zero_generation_in_eclipse(self) -> None:
        """Eclipse = True → P_solar = 0."""
        power = compute_solar_power(1.2, 0.28, 0.0, is_in_eclipse=True)
        assert power == 0.0

    def test_zero_generation_at_90deg_incidence(self) -> None:
        """θ=90° → cos(90°) = 0 → P_solar = 0."""
        power = compute_solar_power(1.2, 0.28, sun_incidence_deg=90.0, is_in_eclipse=False)
        assert power == pytest.approx(0.0, abs=1e-9)

    def test_cosine_scaling(self) -> None:
        """Power scales as cos(θ)."""
        p0 = compute_solar_power(1.2, 0.28, 0.0, False)
        p45 = compute_solar_power(1.2, 0.28, 45.0, False)
        import math

        assert p45 == pytest.approx(p0 * math.cos(math.radians(45.0)), rel=1e-9)

    def test_solar_power_never_negative(self) -> None:
        """Power must not be negative for any incidence angle."""
        for angle in [0, 45, 89, 90, 91, 180]:
            power = compute_solar_power(1.2, 0.28, float(angle), False)
            assert power >= 0.0

    def test_invalid_area_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            compute_solar_power(0.0, 0.28, 0.0, False)

    def test_invalid_efficiency_raises(self) -> None:
        with pytest.raises(ValueError, match="\\(0, 1\\]"):
            compute_solar_power(1.2, 0.0, 0.0, False)
        with pytest.raises(ValueError):
            compute_solar_power(1.2, 1.5, 0.0, False)

    def test_different_satellite_areas(self) -> None:
        """Alpha (1.2 m²), Beta (1.8 m²), Gamma (0.8 m²) produce proportional power."""
        p_alpha = compute_solar_power(1.2, 0.28, 0.0, False)
        p_beta = compute_solar_power(1.8, 0.28, 0.0, False)
        p_gamma = compute_solar_power(0.8, 0.28, 0.0, False)
        assert p_beta > p_alpha > p_gamma
        assert p_beta / p_alpha == pytest.approx(1.8 / 1.2, rel=1e-9)


class TestTotalLoad:
    def test_base_load_included(self) -> None:
        """Total load includes base avionics even with all optional loads at zero."""
        load = compute_total_load(0.0, 0.0, 0.0, 0.0)
        assert load == pytest.approx(BASE_AVIONICS_POWER_W)

    def test_payload_increases_load(self) -> None:
        """Activating payload increases total load."""
        load_standby = compute_total_load(15.0, 20.0, 5.0, 0.0)
        load_active = compute_total_load(15.0, 20.0, 180.0, 0.0)
        assert load_active > load_standby

    def test_heater_increases_load(self) -> None:
        """Heater power adds to total load."""
        load_no_heater = compute_total_load(15.0, 20.0, 5.0, 0.0)
        load_with_heater = compute_total_load(15.0, 20.0, 5.0, 40.0)
        assert load_with_heater == pytest.approx(load_no_heater + 40.0)

    def test_negative_power_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            compute_total_load(-1.0, 20.0, 5.0, 0.0)


class TestBatteryEnergyIntegration:
    def test_charging_in_sunlight(self) -> None:
        """Solar > load → battery energy increases."""
        capacity = 320.0
        initial_energy = 200.0  # SOC = 62.5%
        solar_w = 300.0  # High solar generation
        load_w = 60.0  # Low load

        new_energy, soc, is_charging = integrate_battery_energy(
            initial_energy, capacity, solar_w, load_w, dt_s=60.0
        )
        assert is_charging is True
        assert new_energy > initial_energy
        assert 0.0 <= soc <= 100.0

    def test_discharging_in_eclipse(self) -> None:
        """No solar + load → battery discharges."""
        capacity = 320.0
        initial_energy = 200.0

        new_energy, soc, is_charging = integrate_battery_energy(
            initial_energy, capacity, 0.0, 65.0, dt_s=60.0
        )
        assert is_charging is False
        assert new_energy < initial_energy
        assert soc < (initial_energy / capacity) * 100.0

    def test_no_overcharging(self) -> None:
        """Battery cannot exceed 100% SOC."""
        capacity = 320.0
        initial_energy = capacity  # Already fully charged

        new_energy, soc, _ = integrate_battery_energy(
            initial_energy, capacity, 400.0, 60.0, dt_s=3600.0
        )
        assert new_energy <= capacity
        assert soc <= 100.0

    def test_no_discharge_below_zero(self) -> None:
        """Battery cannot go below 0 Wh."""
        capacity = 320.0
        initial_energy = 1.0  # Nearly empty

        new_energy, soc, _ = integrate_battery_energy(
            initial_energy, capacity, 0.0, 1000.0, dt_s=3600.0
        )
        assert new_energy >= 0.0
        assert soc >= 0.0

    def test_unit_conversion_wh_not_joules(self) -> None:
        """Energy change must use W·s / 3600 → Wh conversion."""
        capacity = 100.0
        initial = 50.0  # 50 Wh
        solar = 100.0  # W
        load = 50.0  # W
        # Net = 50 W over 1 second
        # Expected delta = 50 * 0.92 * 1/3600 Wh
        dt = 1.0
        new_energy, _, _ = integrate_battery_energy(
            initial, capacity, solar, load, dt_s=dt, charge_efficiency=DEFAULT_CHARGE_EFFICIENCY
        )
        expected_delta = (solar - load) * DEFAULT_CHARGE_EFFICIENCY * dt / 3600.0
        assert new_energy == pytest.approx(initial + expected_delta, rel=1e-9)

    def test_charge_efficiency_applied(self) -> None:
        """Charging: delta_energy = net_power * η_charge * dt / 3600."""
        capacity = 320.0
        initial = 100.0
        solar = 200.0
        load = 60.0  # Net = 140 W
        dt = 100.0

        new_energy, _, _ = integrate_battery_energy(
            initial, capacity, solar, load, dt_s=dt, charge_efficiency=0.92
        )
        expected_delta = 140.0 * 0.92 * dt / 3600.0
        assert new_energy == pytest.approx(initial + expected_delta, rel=1e-9)

    def test_discharge_efficiency_applied(self) -> None:
        """Discharging: delta = net_power / η_discharge * dt / 3600."""
        capacity = 320.0
        initial = 200.0
        solar = 0.0
        load = 100.0  # Net = -100 W
        dt = 100.0

        new_energy, _, _ = integrate_battery_energy(
            initial, capacity, solar, load, dt_s=dt, discharge_efficiency=0.96
        )
        expected_delta = (-100.0 / 0.96) * dt / 3600.0
        assert new_energy == pytest.approx(initial + expected_delta, rel=1e-9)

    def test_invalid_capacity_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            integrate_battery_energy(100.0, 0.0, 100.0, 60.0, 1.0)

    def test_negative_energy_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            integrate_battery_energy(-1.0, 320.0, 100.0, 60.0, 1.0)

    def test_different_satellite_capacities(self) -> None:
        """Satellites with different capacities should have different SOC evolutions."""
        # Alpha: 320 Wh, Beta: 480 Wh, Gamma: 220 Wh
        _, soc_alpha, _ = integrate_battery_energy(200.0, 320.0, 0.0, 60.0, 600.0)
        _, soc_beta, _ = integrate_battery_energy(300.0, 480.0, 0.0, 60.0, 600.0)
        _, soc_gamma, _ = integrate_battery_energy(150.0, 220.0, 0.0, 60.0, 600.0)
        # All should be different
        assert soc_alpha != soc_beta
        assert soc_beta != soc_gamma

    def test_power_balance_correctness(self) -> None:
        """P_solar = P_load → no change in battery (minus efficiency effects)."""
        capacity = 320.0
        initial = 160.0
        load = 60.0  # solar exactly matches load
        _, _, is_charging = integrate_battery_energy(initial, capacity, load, load, dt_s=1.0)
        # Net = 0, so result should be charging (P_batt = 0 → charging branch)
        assert is_charging is True


class TestBusVoltage:
    def test_nominal_voltage_at_50pct_soc(self) -> None:
        """At SOC=50%, V_bus ≈ V_nominal (with load correction)."""
        v = compute_bus_voltage(soc_pct=50.0, load_power_w=0.0)
        # V = 28 + 0.05*(50-50) - 0 = 28 V
        assert v == pytest.approx(28.0, rel=1e-9)

    def test_higher_soc_higher_voltage(self) -> None:
        """Higher SOC → higher bus voltage."""
        v_low = compute_bus_voltage(20.0, 60.0)
        v_high = compute_bus_voltage(90.0, 60.0)
        assert v_high > v_low

    def test_voltage_bounded(self) -> None:
        """Voltage always within operational range [22, 30.5] V."""
        for soc in [0, 10, 50, 100]:
            for load in [0, 100, 500]:
                v = compute_bus_voltage(float(soc), float(load))
                assert 22.0 <= v <= 30.5
