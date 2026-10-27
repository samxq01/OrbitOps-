"""OrbitOps Phase 03 — Communications Subsystem Model.

Phase 03 Scope
--------------
This module models LOCAL transmitter state only. Ground station visibility,
Doppler frequency shift calculations, and contact window scheduling are
Phase 09 features. They are NOT implemented or claimed here.

The `contact_established` field in CommunicationsState is ALWAYS False
in Phase 03. It represents a local decision, not a verified two-way link.

Modelled behaviours
-------------------
- Transmitter power state (enabled / disabled)
- Power consumption in standby vs. active downlink mode
- Simplified signal quality indicator (local SNR estimation)
- Safe mode interaction: disable transmitter to reduce load

Future (Phase 09)
-----------------
- Ground station elevation angle calculation
- Contact window AOS/LOS timestamps
- Doppler frequency shift (Δf = -v_rel/c · f₀)
- Verified carrier lock status
"""

from __future__ import annotations

# Phase 03 SNR parameters (simplified local estimate, NOT a real link budget)
# Range 12–18 dB when transmitter active; 0 when disabled.
SNR_NOMINAL_DB: float = 15.0
SNR_DISABLED_DB: float = 0.0

# Power constants
COMMS_STANDBY_W: float = 20.0  # P_comms standby [W]
COMMS_ACTIVE_W: float = 80.0  # P_comms active downlink [W]


def compute_comms_power(
    tx_enabled: bool,
    is_transmitting: bool,
) -> float:
    """Compute communications subsystem power draw.

    Parameters
    ----------
    tx_enabled:
        True if the transmitter is powered on.
    is_transmitting:
        True if actively downlinking (higher power state).

    Returns
    -------
    float
        Power draw [W].
    """
    if not tx_enabled:
        return 0.0
    return COMMS_ACTIVE_W if is_transmitting else COMMS_STANDBY_W


def update_comms_state(
    tx_enabled: bool,
    is_transmitting: bool,
    satellite_mode: str,
) -> tuple[bool, bool, float, float]:
    """Update communications subsystem state for one simulation tick.

    In SAFE_MODE or EMERGENCY: transmitter is powered down to reduce load.
    (Full commandable control is a Phase 10 feature.)

    Parameters
    ----------
    tx_enabled:
        Current transmitter state.
    is_transmitting:
        Whether actively downlinking.
    satellite_mode:
        Current satellite operational mode.

    Returns
    -------
    tuple[bool, bool, float, float]
        (new_tx_enabled, new_is_transmitting, new_snr_db, new_power_w)
    """
    # In SAFE_MODE or EMERGENCY, disable transmitter to conserve power
    if satellite_mode in ("SAFE_MODE", "EMERGENCY"):
        return False, False, SNR_DISABLED_DB, 0.0

    new_power_w = compute_comms_power(tx_enabled, is_transmitting)
    new_snr_db = SNR_NOMINAL_DB if tx_enabled else SNR_DISABLED_DB

    return tx_enabled, is_transmitting, new_snr_db, new_power_w


def evaluate_comms_health(tx_enabled: bool, snr_db: float) -> str:
    """Classify communications health.

    Parameters
    ----------
    tx_enabled:
        Transmitter powered state.
    snr_db:
        Signal-to-noise ratio [dB].

    Returns
    -------
    str
        Health status: "NOMINAL", "WARNING", or "CRITICAL".
    """
    if not tx_enabled:
        return "WARNING"  # Transmitter off is abnormal but not critical
    if snr_db < 3.0:
        return "CRITICAL"
    if snr_db < 10.0:
        return "WARNING"
    return "NOMINAL"
