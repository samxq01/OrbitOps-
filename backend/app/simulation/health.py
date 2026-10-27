"""OrbitOps Phase 03 — Health Evaluation and Safe-Mode Transition Engine.

This module evaluates subsystem telemetry thresholds and applies autonomous
safe-mode transitions per the SRS requirements.

Threshold Policies (from SRS)
------------------------------
Battery SOC critical threshold:   < 20%
Battery SOC warning threshold:    < 40%
Temperature critical high:        > 65°C
Temperature critical low:         < -15°C
Angular rate critical:            > 5°/s

Autonomous Safe-Mode Transition Rules (FR-012)
----------------------------------------------
The satellite may autonomously enter SAFE_MODE when:

    (A) POWER CRISIS: SOC < 20% for more than `low_soc_persistence_ticks` consecutive ticks.
    (B) THERMAL RUNAWAY: bus_temp_c > 65°C for more than `high_temp_persistence_ticks` ticks.
    (C) SAFE_TUMBLE: Angular rate exceeds 5°/s (immediate).

On safe-mode entry:
- Payload is disabled (handled by payload.py).
- Transmitter is disabled (handled by communications.py).
- ADCS switches to SUN_POINTING to maximise charging.

Mode Transition Limitations (Phase 03 scope)
--------------------------------------------
- This evaluator generates health statuses and autonomous safety events.
- Full operator telecommand validation and execution is Phase 10.
- The anomaly investigator and evidence proof matrix is Phase 08.
- Recovery from SAFE_MODE requires explicit operator commands (Phase 10).

Determinism
-----------
Transition decisions are deterministic — same inputs always produce same output.
No random threshold jitter. Counter values in SatelliteRuntimeState track
consecutive ticks in alarm condition.

Event Flood Prevention
-----------------------
`mode_just_changed` flag prevents repeated event generation on consecutive ticks
for the same mode transition.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("orbitops.simulation.health")

# Battery SOC thresholds [%]
SOC_CRITICAL_PCT: float = 20.0
SOC_WARNING_PCT: float = 40.0

# Temperature thresholds [°C]
TEMP_CRITICAL_HIGH_C: float = 65.0
TEMP_CRITICAL_LOW_C: float = -15.0
TEMP_WARNING_HIGH_C: float = 35.0
TEMP_WARNING_LOW_C: float = 5.0

# Persistence thresholds (consecutive ticks in alarm before mode transition)
# At 1 second per tick: 60 ticks = 60 simulated seconds
LOW_SOC_PERSISTENCE_TICKS: int = 60  # 60 s of critically low SOC → SAFE_MODE
HIGH_TEMP_PERSISTENCE_TICKS: int = 60  # 60 s of critical temp → SAFE_MODE

# Angular rate [°/s] threshold for immediate SAFE_TUMBLE detection
ANGULAR_RATE_CRITICAL_DPS: float = 5.0


def evaluate_power_health(soc_pct: float) -> str:
    """Classify power subsystem health from battery SOC.

    Parameters
    ----------
    soc_pct:
        Battery state of charge [%].

    Returns
    -------
    str
        "NOMINAL", "WARNING", or "CRITICAL".
    """
    if soc_pct < SOC_CRITICAL_PCT:
        return "CRITICAL"
    if soc_pct < SOC_WARNING_PCT:
        return "WARNING"
    return "NOMINAL"


def evaluate_overall_health(
    power_health: str,
    thermal_health: str,
    adcs_health: str,
    comms_health: str,
    payload_health: str,
) -> str:
    """Aggregate subsystem health into overall satellite health status.

    Worst-case aggregation: any CRITICAL subsystem → CRITICAL overall.
    Any WARNING subsystem → WARNING overall.
    All NOMINAL → NOMINAL overall.

    Returns
    -------
    str
        "NOMINAL", "WARNING", or "CRITICAL".
    """
    statuses = [power_health, thermal_health, adcs_health, comms_health, payload_health]
    if "CRITICAL" in statuses:
        return "CRITICAL"
    if "WARNING" in statuses:
        return "WARNING"
    return "NOMINAL"


def update_mode_transitions(
    current_mode: str,
    soc_pct: float,
    bus_temp_c: float,
    angular_rate_dps: float,
    low_soc_ticks: int,
    high_temp_ticks: int,
    mode_just_changed: bool,
) -> tuple[str, int, int, bool, list[str]]:
    """Evaluate and apply autonomous mode transitions.

    Parameters
    ----------
    current_mode:
        Current satellite operational mode.
    soc_pct:
        Battery state of charge [%].
    bus_temp_c:
        Bus temperature [°C].
    angular_rate_dps:
        Angular rate magnitude [°/s].
    low_soc_ticks:
        Consecutive ticks with SOC < 20%.
    high_temp_ticks:
        Consecutive ticks with bus temp > 65°C.
    mode_just_changed:
        True if mode changed on the PREVIOUS tick (prevents repeated events).

    Returns
    -------
    tuple[str, int, int, bool, list[str]]
        (new_mode, new_low_soc_ticks, new_high_temp_ticks, mode_just_changed, events)
        - new_mode: Updated operational mode.
        - new_low_soc_ticks: Updated counter.
        - new_high_temp_ticks: Updated counter.
        - mode_just_changed: True if mode changed THIS tick.
        - events: List of event description strings generated this tick.
    """
    events: list[str] = []
    new_mode = current_mode

    # Cannot automatically transition from OFFLINE mode
    if current_mode == "OFFLINE":
        return current_mode, 0, 0, False, events

    # Reset mode_just_changed at start of each evaluation
    this_tick_changed = False

    # --- Update persistence counters ---
    new_low_soc_ticks = (low_soc_ticks + 1) if soc_pct < SOC_CRITICAL_PCT else 0
    new_high_temp_ticks = (high_temp_ticks + 1) if bus_temp_c > TEMP_CRITICAL_HIGH_C else 0

    # --- Immediate SAFE_TUMBLE detection ---
    # If angular rate is critically high and we're in NOMINAL/DEGRADED, enter SAFE_MODE
    if (
        angular_rate_dps > ANGULAR_RATE_CRITICAL_DPS
        and current_mode in ("NOMINAL", "DEGRADED")
        and not mode_just_changed
    ):
        new_mode = "SAFE_MODE"
        this_tick_changed = True
        events.append(
            f"SAFE_MODE entry: angular rate {angular_rate_dps:.2f}°/s exceeds "
            f"critical threshold {ANGULAR_RATE_CRITICAL_DPS}°/s"
        )
        logger.warning(
            "Satellite entering SAFE_MODE due to excessive angular rate %.2f°/s",
            angular_rate_dps,
        )

    # --- Persistent power crisis ---
    elif (
        new_low_soc_ticks >= LOW_SOC_PERSISTENCE_TICKS
        and current_mode in ("NOMINAL", "DEGRADED")
        and not mode_just_changed
    ):
        new_mode = "SAFE_MODE"
        this_tick_changed = True
        events.append(
            f"SAFE_MODE entry: battery SOC {soc_pct:.1f}% below critical threshold "
            f"{SOC_CRITICAL_PCT}% for {new_low_soc_ticks} consecutive ticks"
        )
        logger.warning(
            "Satellite entering SAFE_MODE due to sustained critical SOC %.1f%%",
            soc_pct,
        )
        new_low_soc_ticks = 0  # Reset counter after transition

    # --- Persistent thermal crisis ---
    elif (
        new_high_temp_ticks >= HIGH_TEMP_PERSISTENCE_TICKS
        and current_mode in ("NOMINAL", "DEGRADED")
        and not mode_just_changed
    ):
        new_mode = "SAFE_MODE"
        this_tick_changed = True
        events.append(
            f"SAFE_MODE entry: bus temperature {bus_temp_c:.1f}°C above critical threshold "
            f"{TEMP_CRITICAL_HIGH_C}°C for {new_high_temp_ticks} consecutive ticks"
        )
        logger.warning(
            "Satellite entering SAFE_MODE due to sustained critical temperature %.1f°C",
            bus_temp_c,
        )
        new_high_temp_ticks = 0  # Reset counter after transition

    # --- DEGRADED mode transition ---
    # Enter DEGRADED if any warning threshold breached in NOMINAL mode
    elif current_mode == "NOMINAL" and not mode_just_changed:
        has_warning = (
            soc_pct < SOC_WARNING_PCT
            or bus_temp_c > TEMP_WARNING_HIGH_C
            or bus_temp_c < TEMP_WARNING_LOW_C
        )
        if has_warning:
            new_mode = "DEGRADED"
            this_tick_changed = True
            events.append(
                f"DEGRADED entry: subsystem warning threshold breached "
                f"(SOC={soc_pct:.1f}%, T={bus_temp_c:.1f}°C)"
            )

    # --- RECOVERY from SAFE_MODE ---
    # If SAFE_MODE conditions are resolved and SOC is recovering, note readiness
    # (Actual RECOVERY command is Phase 10 operator action; we only flag it here)
    elif current_mode == "SAFE_MODE" and not mode_just_changed:
        if soc_pct >= SOC_WARNING_PCT and bus_temp_c < TEMP_CRITICAL_HIGH_C:
            # Conditions improved — log that RECOVERY could be commanded
            # Do not auto-transition to NOMINAL (requires operator command in Phase 10)
            events.append(
                f"SAFE_MODE conditions resolved: SOC={soc_pct:.1f}%, T={bus_temp_c:.1f}°C. "
                "RECOVERY command required for return to NOMINAL."
            )

    return new_mode, new_low_soc_ticks, new_high_temp_ticks, this_tick_changed, events
