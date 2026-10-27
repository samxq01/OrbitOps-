"""OrbitOps Phase 03 — Deterministic Simulation Clock.

Manages simulation time independently from wall-clock time.
No datetime.now() usage inside physics calculations.

Clock Contract
--------------
- Simulation time is represented as a float (seconds since epoch).
- The epoch is set at construction and never changes.
- Time warp controls how many simulated seconds pass per real second.
- Warp does NOT change the physics timestep; it changes external advance cadence.
- A paused clock does not advance.
- Manual step() advances by exactly one default_dt regardless of warp.
- advance(dt) advances by the given dt if not paused.
- Tick sequence numbers are monotonically increasing integers.
- The clock does not interact with any subsystem directly.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

logger = logging.getLogger("orbitops.simulation.clock")

# Supported warp multipliers
VALID_WARP_FACTORS: frozenset[float] = frozenset({1.0, 5.0, 10.0, 50.0, 100.0})
DEFAULT_WARP_FACTOR: float = 1.0
DEFAULT_TIMESTEP_S: float = 1.0  # 1 simulated second per tick


class SimulationClock:
    """Deterministic simulation clock decoupled from wall-clock time.

    Attributes
    ----------
    epoch_utc:
        The simulation's fixed reference epoch (UTC datetime).
    _sim_time_s:
        Current simulation time in seconds since epoch.
    _tick_count:
        Number of ticks advanced since last reset.
    _warp:
        Time-warp multiplier (informational; does not change equations).
    _paused:
        If True, advance() and step() have no effect.
    _default_dt:
        Default logical timestep in seconds (default: 1.0 s).
    """

    def __init__(
        self,
        epoch_utc: datetime | None = None,
        default_dt: float = DEFAULT_TIMESTEP_S,
        initial_warp: float = DEFAULT_WARP_FACTOR,
    ) -> None:
        """Initialise a deterministic simulation clock.

        Parameters
        ----------
        epoch_utc:
            The fixed simulation epoch in UTC. Defaults to
            2026-10-26T00:00:00Z (OrbitOps mission epoch).
        default_dt:
            Default logical timestep in seconds. Must be positive.
        initial_warp:
            Initial time-warp multiplier. Must be in VALID_WARP_FACTORS.
        """
        if default_dt <= 0.0:
            msg = f"Clock timestep must be positive; got {default_dt} s"
            raise ValueError(msg)
        if initial_warp not in VALID_WARP_FACTORS:
            msg = (
                f"Warp factor {initial_warp} is not supported. "
                f"Supported values: {sorted(VALID_WARP_FACTORS)}"
            )
            raise ValueError(msg)

        self.epoch_utc: datetime = epoch_utc or datetime(2026, 10, 26, 0, 0, 0, tzinfo=UTC)
        self._default_dt: float = default_dt
        self._warp: float = initial_warp
        self._sim_time_s: float = 0.0
        self._tick_count: int = 0
        self._paused: bool = True  # Starts paused; must call start()
        self._started: bool = False

    # ------------------------------------------------------------------
    # Control API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start or resume the clock."""
        self._paused = False
        self._started = True
        logger.debug("SimulationClock started at t=%.3f s", self._sim_time_s)

    def pause(self) -> None:
        """Pause the clock. A paused clock does not advance."""
        self._paused = True
        logger.debug("SimulationClock paused at t=%.3f s", self._sim_time_s)

    def resume(self) -> None:
        """Resume a paused clock."""
        if not self._started:
            msg = "Cannot resume a clock that has never been started."
            raise RuntimeError(msg)
        self._paused = False
        logger.debug("SimulationClock resumed at t=%.3f s", self._sim_time_s)

    def reset(self, keep_epoch: bool = True) -> None:
        """Reset the clock to t=0 and tick_count=0.

        Parameters
        ----------
        keep_epoch:
            If True (default), preserves the original epoch_utc.
            If False, resets epoch_utc to the current simulation epoch.
        """
        self._sim_time_s = 0.0
        self._tick_count = 0
        self._paused = True
        self._started = False
        if not keep_epoch:
            self.epoch_utc = datetime(2026, 10, 26, 0, 0, 0, tzinfo=UTC)
        logger.debug("SimulationClock reset.")

    def step(self) -> float:
        """Advance the clock by exactly one default_dt, regardless of paused state.

        Returns
        -------
        float
            The dt that was applied (always self._default_dt).
        """
        return self._advance_internal(self._default_dt)

    def advance(self, dt: float | None = None) -> float:
        """Advance the clock by dt if not paused.

        Parameters
        ----------
        dt:
            Time delta in seconds. If None, uses default_dt.

        Returns
        -------
        float
            The dt applied (0.0 if paused).
        """
        if self._paused:
            return 0.0
        return self._advance_internal(dt if dt is not None else self._default_dt)

    def set_time_warp(self, warp: float) -> None:
        """Set the time-warp multiplier.

        Parameters
        ----------
        warp:
            Must be in VALID_WARP_FACTORS.
        """
        if warp not in VALID_WARP_FACTORS:
            msg = (
                f"Warp factor {warp} is not supported. "
                f"Supported values: {sorted(VALID_WARP_FACTORS)}"
            )
            raise ValueError(msg)
        self._warp = warp
        logger.info("SimulationClock warp set to %.1f×", warp)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def sim_time_s(self) -> float:
        """Current simulation time in seconds since epoch."""
        return self._sim_time_s

    @property
    def mission_elapsed_time_s(self) -> float:
        """Alias for sim_time_s; emphasises mission-elapsed framing."""
        return self._sim_time_s

    @property
    def tick_count(self) -> int:
        """Number of ticks executed since last reset."""
        return self._tick_count

    @property
    def warp(self) -> float:
        """Current time-warp multiplier."""
        return self._warp

    @property
    def time_warp(self) -> float:
        """Current time-warp multiplier (alias for warp)."""
        return self._warp

    @property
    def is_paused(self) -> bool:
        """True when the clock is paused."""
        return self._paused

    @property
    def is_running(self) -> bool:
        """True when the clock is running and not paused."""
        return self._started and not self._paused

    @property
    def default_dt(self) -> float:
        """Default logical timestep in seconds."""
        return self._default_dt

    @property
    def sim_timestamp_utc(self) -> datetime:
        """Current simulation time expressed as a UTC datetime object.

        This is the epoch plus accumulated simulation seconds.
        It does NOT call datetime.now(); it is purely derived from the clock state.
        """
        from datetime import timedelta

        return self.epoch_utc + timedelta(seconds=self._sim_time_s)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, object]:
        """Serialise clock state for snapshot persistence."""
        return {
            "epoch_utc_iso": self.epoch_utc.isoformat(),
            "sim_time_s": self._sim_time_s,
            "tick_count": self._tick_count,
            "warp": self._warp,
            "paused": self._paused,
            "started": self._started,
            "default_dt": self._default_dt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> SimulationClock:
        """Restore a clock from a serialised snapshot dictionary."""
        epoch = datetime.fromisoformat(str(data["epoch_utc_iso"]))
        clock = cls(
            epoch_utc=epoch,
            default_dt=float(data["default_dt"]),  # type: ignore[arg-type]
            initial_warp=float(data["warp"]),  # type: ignore[arg-type]
        )
        clock._sim_time_s = float(data["sim_time_s"])  # type: ignore[arg-type]
        clock._tick_count = int(data["tick_count"])  # type: ignore[arg-type]
        clock._paused = bool(data["paused"])
        clock._started = bool(data["started"])
        return clock

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _advance_internal(self, dt: float) -> float:
        """Validate and apply a time delta unconditionally."""
        if dt <= 0.0:
            msg = f"Clock dt must be positive; got {dt} s"
            raise ValueError(msg)
        self._sim_time_s += dt
        self._tick_count += 1
        return dt

    def __repr__(self) -> str:
        state = "RUNNING" if self.is_running else "PAUSED"
        return (
            f"SimulationClock(t={self._sim_time_s:.1f}s, "
            f"tick={self._tick_count}, warp={self._warp}×, {state})"
        )
