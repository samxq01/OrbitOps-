"""OrbitOps Phase 03 — Payload Subsystem Model.

The payload subsystem models science instrument power consumption and data
accumulation. It provides causal inputs to the Power and Thermal subsystems.

Cross-subsystem causality
-------------------------
Payload activated   → current_power_w rises to active_power_w
                    → Power subsystem sees higher load (battery discharges faster)
                    → Thermal subsystem receives more internal heat dissipation

Payload in standby  → current_power_w = standby_power_w (reduced load)

SAFE_MODE behaviour
-------------------
In SAFE_MODE or EMERGENCY, the payload is automatically disabled to reduce
electrical load and allow battery recovery. This is an autonomous protection
behaviour (the full operator telecommand system is Phase 10).

Data accumulation
-----------------
When active, data accumulates at a constant rate per second (instrument-specific).
Data storage is capped at 1024 MB (onboard memory limit for Phase 03 model).
"""

from __future__ import annotations

# Maximum onboard data storage [MB]
MAX_DATA_STORAGE_MB: float = 1024.0

# Default data rates by instrument type [MB/s]
DATA_RATE_IMAGER_MBS: float = 0.5  # ALPHA multispectral imager
DATA_RATE_RELAY_MBS: float = 0.1  # BETA tactical transponder
DATA_RATE_PROBE_MBS: float = 0.05  # GAMMA plasma probe / magnetometer


def update_payload_state(
    is_active: bool,
    active_power_w: float,
    standby_power_w: float,
    data_storage_mb: float,
    data_rate_mbps: float,
    satellite_mode: str,
    dt_s: float,
) -> tuple[bool, float, float, float]:
    """Update payload state for one simulation tick.

    Parameters
    ----------
    is_active:
        Whether the payload instrument is powered on.
    active_power_w:
        Power draw when instrument is active [W].
    standby_power_w:
        Power draw in standby [W].
    data_storage_mb:
        Current accumulated data [MB].
    data_rate_mbps:
        Data accumulation rate when active [MB/s].
    satellite_mode:
        Current satellite operational mode.
    dt_s:
        Timestep [s].

    Returns
    -------
    tuple[bool, float, float, float]
        (new_is_active, new_current_power_w, new_data_storage_mb, effective_power_w)
    """
    # Autonomous protection: disable payload in SAFE_MODE / EMERGENCY
    if satellite_mode in ("SAFE_MODE", "EMERGENCY"):
        return False, standby_power_w, data_storage_mb, standby_power_w

    current_power_w = active_power_w if is_active else standby_power_w

    # Data accumulation
    new_data_mb = data_storage_mb
    if is_active and data_rate_mbps > 0.0:
        delta_mb = data_rate_mbps * dt_s
        new_data_mb = min(MAX_DATA_STORAGE_MB, data_storage_mb + delta_mb)

    return is_active, current_power_w, new_data_mb, current_power_w


def evaluate_payload_health(
    is_active: bool,
    current_power_w: float,
    active_power_w: float,
) -> str:
    """Classify payload health.

    Returns
    -------
    str
        Health status: "NOMINAL", "WARNING", or "CRITICAL".
    """
    if not is_active:
        return "NOMINAL"  # Standby is expected, not a health issue
    # Check for power anomaly: drawing significantly more than expected
    if current_power_w > active_power_w * 1.2:
        return "CRITICAL"
    if current_power_w > active_power_w * 1.05:
        return "WARNING"
    return "NOMINAL"
