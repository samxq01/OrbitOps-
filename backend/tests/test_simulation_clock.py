"""Tests for OrbitOps Phase 03 — Deterministic Simulation Clock."""

import pytest

from app.simulation.clock import (
    DEFAULT_TIMESTEP_S,
    VALID_WARP_FACTORS,
    SimulationClock,
)


class TestClockInitialisation:
    def test_default_construction(self) -> None:
        clock = SimulationClock()
        assert clock.sim_time_s == 0.0
        assert clock.tick_count == 0
        assert clock.warp == 1.0
        assert clock.is_paused is True
        assert clock.is_running is False
        assert clock.default_dt == DEFAULT_TIMESTEP_S

    def test_invalid_timestep_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SimulationClock(default_dt=0.0)
        with pytest.raises(ValueError, match="positive"):
            SimulationClock(default_dt=-1.0)

    def test_invalid_warp_raises(self) -> None:
        with pytest.raises(ValueError, match="not supported"):
            SimulationClock(initial_warp=3.0)

    def test_valid_warp_factors_accepted(self) -> None:
        for warp in VALID_WARP_FACTORS:
            clock = SimulationClock(initial_warp=warp)
            assert clock.warp == warp


class TestClockStartPauseResume:
    def test_start_makes_running(self) -> None:
        clock = SimulationClock()
        clock.start()
        assert clock.is_running is True
        assert clock.is_paused is False

    def test_pause_stops_advance(self) -> None:
        clock = SimulationClock()
        clock.start()
        clock.pause()
        result = clock.advance()
        assert result == 0.0
        assert clock.sim_time_s == 0.0
        assert clock.tick_count == 0

    def test_resume_after_pause(self) -> None:
        clock = SimulationClock()
        clock.start()
        clock.pause()
        clock.resume()
        assert clock.is_running is True

    def test_resume_without_start_raises(self) -> None:
        clock = SimulationClock()
        with pytest.raises(RuntimeError):
            clock.resume()


class TestClockAdvance:
    def test_advance_increases_time(self) -> None:
        clock = SimulationClock()
        clock.start()
        dt = clock.advance()
        assert dt == DEFAULT_TIMESTEP_S
        assert clock.sim_time_s == pytest.approx(DEFAULT_TIMESTEP_S)
        assert clock.tick_count == 1

    def test_advance_custom_dt(self) -> None:
        clock = SimulationClock()
        clock.start()
        clock.advance(5.0)
        assert clock.sim_time_s == pytest.approx(5.0)

    def test_advance_zero_dt_raises(self) -> None:
        clock = SimulationClock()
        clock.start()
        with pytest.raises(ValueError, match="positive"):
            clock.advance(0.0)

    def test_advance_negative_dt_raises(self) -> None:
        clock = SimulationClock()
        clock.start()
        with pytest.raises(ValueError, match="positive"):
            clock.advance(-1.0)

    def test_advance_while_paused_returns_zero(self) -> None:
        clock = SimulationClock()
        clock.start()
        clock.pause()
        result = clock.advance(10.0)
        assert result == 0.0


class TestClockStep:
    def test_step_advances_one_default_dt(self) -> None:
        clock = SimulationClock()
        dt = clock.step()
        assert dt == DEFAULT_TIMESTEP_S
        assert clock.sim_time_s == pytest.approx(DEFAULT_TIMESTEP_S)
        assert clock.tick_count == 1

    def test_step_works_while_paused(self) -> None:
        """step() advances regardless of paused state."""
        clock = SimulationClock()
        clock.start()
        clock.pause()
        dt = clock.step()
        assert dt == DEFAULT_TIMESTEP_S
        assert clock.sim_time_s == pytest.approx(DEFAULT_TIMESTEP_S)

    def test_step_monotonic(self) -> None:
        clock = SimulationClock()
        prev_time = 0.0
        for _ in range(50):
            clock.step()
            assert clock.sim_time_s > prev_time
            prev_time = clock.sim_time_s


class TestClockReset:
    def test_reset_clears_time_and_ticks(self) -> None:
        clock = SimulationClock()
        clock.start()
        for _ in range(10):
            clock.advance()
        clock.reset()
        assert clock.sim_time_s == 0.0
        assert clock.tick_count == 0
        assert clock.is_paused is True

    def test_reset_then_start_works(self) -> None:
        clock = SimulationClock()
        clock.start()
        clock.advance()
        clock.reset()
        clock.start()
        clock.advance()
        assert clock.sim_time_s == pytest.approx(DEFAULT_TIMESTEP_S)


class TestClockTimestampProperty:
    def test_sim_timestamp_utc_is_deterministic(self) -> None:
        from datetime import UTC, datetime, timedelta

        epoch = datetime(2026, 10, 26, 0, 0, 0, tzinfo=UTC)
        clock = SimulationClock(epoch_utc=epoch)
        clock.start()
        clock.advance(3600.0)  # 1 hour
        expected = epoch + timedelta(seconds=3600.0)
        assert clock.sim_timestamp_utc == expected


class TestClockWarp:
    def test_set_valid_warp(self) -> None:
        clock = SimulationClock()
        clock.set_time_warp(10.0)
        assert clock.warp == 10.0

    def test_set_invalid_warp_raises(self) -> None:
        clock = SimulationClock()
        with pytest.raises(ValueError, match="not supported"):
            clock.set_time_warp(7.0)


class TestClockDeterminism:
    def test_repeated_tick_produces_identical_times(self) -> None:
        """Two clocks advanced the same way must reach the same time."""
        clock_a = SimulationClock()
        clock_b = SimulationClock()
        for clock in (clock_a, clock_b):
            clock.start()
            for _ in range(100):
                clock.advance(1.0)

        assert clock_a.sim_time_s == clock_b.sim_time_s
        assert clock_a.tick_count == clock_b.tick_count


class TestClockSerialisation:
    def test_round_trip(self) -> None:
        clock = SimulationClock()
        clock.start()
        for _ in range(25):
            clock.advance(2.0)

        data = clock.to_dict()
        restored = SimulationClock.from_dict(data)

        assert restored.sim_time_s == clock.sim_time_s
        assert restored.tick_count == clock.tick_count
        assert restored.warp == clock.warp
        assert restored.is_paused == clock.is_paused
        assert restored.default_dt == clock.default_dt
