"""Tests for OrbitOps Phase 03 — Thermal Subsystem Model."""

import math

import pytest

from app.simulation.thermal import (
    STEFAN_BOLTZMANN,
    T_SPACE_K,
    celsius_to_kelvin,
    compute_radiative_heat_loss,
    compute_solar_heating,
    evaluate_thermal_health,
    integrate_thermal_state,
    kelvin_to_celsius,
    update_heater_state,
)


class TestTemperatureConversions:
    def test_celsius_to_kelvin(self) -> None:
        assert celsius_to_kelvin(0.0) == pytest.approx(273.15)
        assert celsius_to_kelvin(20.0) == pytest.approx(293.15)
        assert celsius_to_kelvin(-15.0) == pytest.approx(258.15)

    def test_kelvin_to_celsius(self) -> None:
        assert kelvin_to_celsius(273.15) == pytest.approx(0.0)
        assert kelvin_to_celsius(293.15) == pytest.approx(20.0)

    def test_round_trip(self) -> None:
        for t in [-20.0, 0.0, 20.0, 65.0]:
            assert kelvin_to_celsius(celsius_to_kelvin(t)) == pytest.approx(t)


class TestRadiativeHeatLoss:
    def test_stefan_boltzmann_formula(self) -> None:
        """Q_out = ε · σ · A · (T⁴ - T_space⁴)."""
        T = 293.15  # 20°C
        A = 0.6
        eps = 0.85
        expected = eps * STEFAN_BOLTZMANN * A * (T**4 - T_SPACE_K**4)
        q_out = compute_radiative_heat_loss(T, A, emissivity=eps)
        assert q_out == pytest.approx(expected, rel=1e-9)

    def test_higher_temp_more_radiation(self) -> None:
        """Hotter spacecraft radiates more heat."""
        q_cold = compute_radiative_heat_loss(200.0, 0.6)
        q_hot = compute_radiative_heat_loss(400.0, 0.6)
        assert q_hot > q_cold

    def test_invalid_temperature_raises(self) -> None:
        with pytest.raises(ValueError, match="0 K"):
            compute_radiative_heat_loss(0.0, 0.6)

    def test_invalid_area_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            compute_radiative_heat_loss(293.15, 0.0)

    def test_invalid_emissivity_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_radiative_heat_loss(293.15, 0.6, emissivity=0.0)
        with pytest.raises(ValueError):
            compute_radiative_heat_loss(293.15, 0.6, emissivity=1.1)

    def test_non_negative_output(self) -> None:
        """Radiative loss is always non-negative."""
        for T in [100.0, 200.0, 300.0, 400.0]:
            q = compute_radiative_heat_loss(T, 0.6)
            assert q >= 0.0


class TestSolarHeating:
    def test_solar_heating_in_sunlight(self) -> None:
        """Q_solar = α · A_proj · G_solar in sunlight."""
        from app.simulation.thermal import SOLAR_CONSTANT_W_M2

        q = compute_solar_heating(0.15, 0.3, is_in_eclipse=False)
        expected = 0.15 * 0.3 * SOLAR_CONSTANT_W_M2
        assert q == pytest.approx(expected)

    def test_no_solar_heating_in_eclipse(self) -> None:
        """Zero solar input during eclipse."""
        q = compute_solar_heating(0.15, 0.3, is_in_eclipse=True)
        assert q == 0.0


class TestHeaterHysteresis:
    def test_heater_turns_on_below_threshold(self) -> None:
        """Heater activates when T < on_threshold (5°C)."""
        new_state = update_heater_state(False, bus_temp_c=3.0)
        assert new_state is True

    def test_heater_turns_off_above_threshold(self) -> None:
        """Heater deactivates when T > off_threshold (15°C)."""
        new_state = update_heater_state(True, bus_temp_c=20.0)
        assert new_state is False

    def test_heater_maintains_state_in_hysteresis_band(self) -> None:
        """No change when temperature is in hysteresis band [5°C, 15°C]."""
        # Heater was ON: stays ON in band
        on_in_band = update_heater_state(True, bus_temp_c=10.0)
        assert on_in_band is True
        # Heater was OFF: stays OFF in band
        off_in_band = update_heater_state(False, bus_temp_c=10.0)
        assert off_in_band is False

    def test_invalid_threshold_raises(self) -> None:
        """off_threshold must be > on_threshold."""
        with pytest.raises(ValueError, match="greater than"):
            update_heater_state(False, 10.0, on_threshold_c=20.0, off_threshold_c=10.0)

    def test_rapid_toggling_prevented(self) -> None:
        """Hysteresis prevents rapid on/off cycling near threshold."""
        # At exactly 10°C, heater state should not toggle
        state = True
        for _ in range(10):
            state = update_heater_state(state, bus_temp_c=10.0)
        assert state is True  # Should remain ON


class TestThermalIntegration:
    def test_temperature_increases_with_heat_input(self) -> None:
        """High electrical dissipation → temperature rises."""
        T_initial_k = celsius_to_kelvin(20.0)
        new_bus_k, _, _, _ = integrate_thermal_state(
            bus_temp_k=T_initial_k,
            payload_temp_k=T_initial_k,
            total_electrical_dissipation_w=500.0,
            is_in_eclipse=True,  # No solar
            heater_active=False,
            dt_s=60.0,
        )
        assert new_bus_k > T_initial_k

    def test_temperature_decreases_with_zero_heat(self) -> None:
        """Zero internal heat source → temperature decreases due to radiation."""
        T_initial_k = celsius_to_kelvin(30.0)  # Warm to start
        new_bus_k, _, _, _ = integrate_thermal_state(
            bus_temp_k=T_initial_k,
            payload_temp_k=T_initial_k,
            total_electrical_dissipation_w=0.0,
            is_in_eclipse=True,
            heater_active=False,
            dt_s=60.0,
        )
        assert new_bus_k < T_initial_k

    def test_eclipse_reduces_solar_input(self) -> None:
        """In eclipse, Q_in excludes solar heating."""
        T = celsius_to_kelvin(15.0)
        _, _, q_in_eclipse, _ = integrate_thermal_state(
            T, T, 100.0, is_in_eclipse=True, heater_active=False, dt_s=1.0
        )
        _, _, q_in_sunlit, _ = integrate_thermal_state(
            T, T, 100.0, is_in_eclipse=False, heater_active=False, dt_s=1.0
        )
        assert q_in_sunlit > q_in_eclipse

    def test_heater_increases_temperature(self) -> None:
        """Active heater adds heat to the spacecraft."""
        T = celsius_to_kelvin(0.0)  # Cold spacecraft
        _, _, q_no_heater, _ = integrate_thermal_state(
            T, T, 0.0, True, heater_active=False, dt_s=1.0
        )
        _, _, q_with_heater, _ = integrate_thermal_state(
            T, T, 0.0, True, heater_active=True, dt_s=1.0
        )
        assert q_with_heater > q_no_heater

    def test_invalid_timestep_raises(self) -> None:
        T = celsius_to_kelvin(20.0)
        with pytest.raises(ValueError, match="positive"):
            integrate_thermal_state(T, T, 100.0, False, False, dt_s=0.0)

    def test_invalid_temperature_raises(self) -> None:
        with pytest.raises(ValueError, match="0 K"):
            integrate_thermal_state(0.0, 293.0, 0.0, False, False, 1.0)

    def test_temperature_never_absolute_zero(self) -> None:
        """Temperature cannot reach absolute zero in stable simulation."""
        T = celsius_to_kelvin(20.0)
        for _ in range(100):
            T, _, _, _ = integrate_thermal_state(T, T, 0.0, True, False, 1.0)
        assert T > 0.0

    def test_numerical_stability_1000_ticks(self) -> None:
        """Thermal model remains stable over 1000 ticks."""
        bus_k = celsius_to_kelvin(20.0)
        pl_k = celsius_to_kelvin(18.0)
        for tick in range(1000):
            bus_k, pl_k, _, _ = integrate_thermal_state(
                bus_k, pl_k, 65.0, tick % 2 == 0, False, 1.0
            )
        assert not math.isnan(bus_k)
        assert not math.isinf(bus_k)
        assert bus_k > 0.0


class TestThermalHealthClassification:
    def test_nominal_range(self) -> None:
        assert evaluate_thermal_health(20.0) == "NOMINAL"
        assert evaluate_thermal_health(5.0) == "NOMINAL"
        assert evaluate_thermal_health(35.0) == "NOMINAL"

    def test_warning_range_low(self) -> None:
        assert evaluate_thermal_health(-5.0) == "WARNING"
        assert evaluate_thermal_health(0.0) == "WARNING"

    def test_warning_range_high(self) -> None:
        assert evaluate_thermal_health(40.0) == "WARNING"
        assert evaluate_thermal_health(60.0) == "WARNING"

    def test_critical_range_low(self) -> None:
        assert evaluate_thermal_health(-15.0) == "WARNING"  # exactly at boundary → WARNING
        assert evaluate_thermal_health(-16.0) == "CRITICAL"
        assert evaluate_thermal_health(-100.0) == "CRITICAL"

    def test_critical_range_high(self) -> None:
        assert evaluate_thermal_health(65.0) == "WARNING"  # at boundary → WARNING
        assert evaluate_thermal_health(66.0) == "CRITICAL"
        assert evaluate_thermal_health(120.0) == "CRITICAL"

    def test_all_temperatures_classified(self) -> None:
        """Every temperature must be classified (no gaps)."""
        valid_statuses = {"NOMINAL", "WARNING", "CRITICAL"}
        for temp in range(-50, 150):
            status = evaluate_thermal_health(float(temp))
            assert status in valid_statuses, f"No classification for {temp}°C"
