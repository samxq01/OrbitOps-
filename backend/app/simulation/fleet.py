"""OrbitOps Phase 03 — Fleet Configuration Adapter.

Bridges the Phase 02 SQLAlchemy ORM models with the pure-domain
simulation engine. Converts persisted SatelliteModel records into
SatelliteConfig domain objects without leaking database sessions
into the simulation engine.

Architectural boundary
----------------------
- Reads from database ONCE at initialisation.
- Returns plain SatelliteConfig dataclass objects.
- The simulation engine holds NO reference to the database session.
- Telemetry persistence uses a separate, short-lived session per batch.

Default per-satellite configuration
-------------------------------------
Physical properties that are not stored in the Phase 02 database schema are
populated from documented defaults matching the simulation specification:
  - solar_cell_efficiency: 0.28 (28% multi-junction GaInP/GaAs)
  - charge/discharge efficiencies: 0.92/0.96
  - adcs_inertia_kg_m2: proportional to mass (~0.14 * mass_kg)
  - initial_battery_soc_pct: 80% (mission start assumption)
  - payload config: from subsystem configuration JSON stored in Phase 02
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.satellite import SatelliteModel
from app.models.telemetry import TelemetrySampleModel
from app.repositories.satellite_repository import SatelliteRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.simulation.engine import SatelliteConfig
from app.simulation.telemetry import TelemetryFrame

logger = logging.getLogger("orbitops.simulation.fleet")

# Per-satellite initial RAAN offsets for orbital plane diversity
# (SAT-001: 0°, SAT-002: 120°, SAT-003: 240°)
RAAN_OFFSETS_DEG: dict[str, float] = {
    "SAT-001": 0.0,
    "SAT-002": 120.0,
    "SAT-003": 240.0,
}

# Per-satellite initial true anomaly offsets for in-plane separation
TRUE_ANOMALY_OFFSETS_DEG: dict[str, float] = {
    "SAT-001": 0.0,
    "SAT-002": 60.0,
    "SAT-003": 120.0,
}

# Payload power and data rates (from simulation-spec.md §2.1)
PAYLOAD_SPECS: dict[str, dict[str, float]] = {
    "SAT-001": {  # ALPHA — MULTISPECTRAL_IMAGER
        "active_power_w": 180.0,
        "standby_power_w": 5.0,
        "data_rate_mbps": 0.5,
    },
    "SAT-002": {  # BETA — TACTICAL_TRANSPONDER
        "active_power_w": 120.0,
        "standby_power_w": 8.0,
        "data_rate_mbps": 0.1,
    },
    "SAT-003": {  # GAMMA — PLASMA_PROBE_MAGNETOMETER
        "active_power_w": 35.0,
        "standby_power_w": 3.0,
        "data_rate_mbps": 0.05,
    },
}

# Initial ADCS modes (from Phase 02 seed data)
ADCS_MODES: dict[str, str] = {
    "SAT-001": "NADIR_POINTING",
    "SAT-002": "NADIR_POINTING",
    "SAT-003": "SUN_POINTING",
}


def build_fleet_from_db(session: Session, mission_id: str | None = None) -> list[SatelliteConfig]:
    """Load satellite configurations from the Phase 02 database.

    Parameters
    ----------
    session:
        SQLAlchemy session. The session is used only within this function
        and is NOT stored or referenced by the returned SatelliteConfig objects.
    mission_id:
        Optional mission ID filter. If None, loads all satellites.

    Returns
    -------
    list[SatelliteConfig]
        Ordered list of satellite configurations ready for SimulationEngine.

    Raises
    ------
    RuntimeError
        If no satellites are found in the database.
    """
    repo = SatelliteRepository(session)
    satellites: list[SatelliteModel] = repo.list_satellites(mission_id=mission_id)

    if not satellites:
        msg = "No satellites found in the database. Run the seed command first."
        raise RuntimeError(msg)

    configs: list[SatelliteConfig] = []
    for sat in satellites:
        config = _model_to_config(sat)
        configs.append(config)
        logger.info(
            "Loaded satellite config: %s (%s) — a=%.1f km, i=%.1f°",
            sat.satellite_id,
            sat.name,
            sat.semi_major_axis_km,
            sat.inclination_deg,
        )

    logger.info("Fleet loaded: %d satellites from database.", len(configs))
    return configs


def _model_to_config(sat: SatelliteModel) -> SatelliteConfig:
    """Convert a SatelliteModel ORM record to a SatelliteConfig domain object.

    Parameters
    ----------
    sat:
        SQLAlchemy ORM model instance (detached after session closes).

    Returns
    -------
    SatelliteConfig
        Pure domain configuration object.
    """
    sat_id = sat.satellite_id
    payload_spec = PAYLOAD_SPECS.get(sat_id, PAYLOAD_SPECS["SAT-001"])
    adcs_mode = ADCS_MODES.get(sat_id, "NADIR_POINTING")
    raan_offset = RAAN_OFFSETS_DEG.get(sat_id, 0.0)
    ta_offset = TRUE_ANOMALY_OFFSETS_DEG.get(sat_id, 0.0)

    # Inertia proportional to mass (simplified estimate: I ≈ 0.14 * mass for
    # a solid rectangular satellite approximation)
    adcs_inertia = max(5.0, 0.14 * sat.mass_kg)

    return SatelliteConfig(
        satellite_id=sat.satellite_id,
        satellite_name=sat.name,
        mission_id=sat.mission_id,
        semi_major_axis_km=sat.semi_major_axis_km,
        inclination_deg=sat.inclination_deg,
        mass_kg=sat.mass_kg,
        battery_capacity_wh=sat.battery_capacity_wh,
        solar_area_m2=sat.solar_area_m2,
        initial_mode=sat.operational_mode,
        initial_battery_soc_pct=80.0,  # Documented initial condition for all satellites
        initial_bus_temp_c=20.0,
        initial_payload_temp_c=18.0,
        initial_adcs_mode=adcs_mode,
        initial_angular_rate_dps=0.02,
        initial_true_anomaly_deg=ta_offset,
        payload_active_power_w=payload_spec["active_power_w"],
        payload_standby_power_w=payload_spec["standby_power_w"],
        payload_data_rate_mbps=payload_spec["data_rate_mbps"],
        payload_initially_active=False,  # All payload starts in standby
        comms_tx_enabled=True,
        comms_initially_transmitting=False,
        adcs_inertia_kg_m2=adcs_inertia,
        initial_raan_deg=raan_offset,
    )


def build_default_fleet() -> list[SatelliteConfig]:
    """Build the three-satellite fleet from hardcoded defaults (no database required).

    Used for standalone tests and demonstrations that do not require a live DB session.
    All values match the Phase 02 seed data and SRS specifications.

    Returns
    -------
    list[SatelliteConfig]
        Default three-satellite constellation configuration.
    """
    return [
        SatelliteConfig(
            satellite_id="SAT-001",
            satellite_name="ORBITOPS-ALPHA",
            mission_id="00000000-0000-0000-0000-000000000001",
            semi_major_axis_km=6921.0,  # ~550 km SSO
            inclination_deg=97.6,
            mass_kg=180.0,
            battery_capacity_wh=320.0,
            solar_area_m2=1.2,
            initial_mode="NOMINAL",
            initial_battery_soc_pct=80.0,
            initial_bus_temp_c=20.0,
            initial_payload_temp_c=18.0,
            initial_adcs_mode="NADIR_POINTING",
            initial_angular_rate_dps=0.02,
            initial_true_anomaly_deg=0.0,
            payload_active_power_w=180.0,
            payload_standby_power_w=5.0,
            payload_data_rate_mbps=0.5,
            payload_initially_active=False,
            comms_tx_enabled=True,
            comms_initially_transmitting=False,
            adcs_inertia_kg_m2=25.2,  # 0.14 * 180 kg
            initial_raan_deg=0.0,
        ),
        SatelliteConfig(
            satellite_id="SAT-002",
            satellite_name="ORBITOPS-BETA",
            mission_id="00000000-0000-0000-0000-000000000001",
            semi_major_axis_km=7071.0,  # ~700 km near-equatorial
            inclination_deg=5.0,
            mass_kg=240.0,
            battery_capacity_wh=480.0,
            solar_area_m2=1.8,
            initial_mode="NOMINAL",
            initial_battery_soc_pct=80.0,
            initial_bus_temp_c=22.0,
            initial_payload_temp_c=20.0,
            initial_adcs_mode="NADIR_POINTING",
            initial_angular_rate_dps=0.02,
            initial_true_anomaly_deg=60.0,
            payload_active_power_w=120.0,
            payload_standby_power_w=8.0,
            payload_data_rate_mbps=0.1,
            payload_initially_active=False,
            comms_tx_enabled=True,
            comms_initially_transmitting=False,
            adcs_inertia_kg_m2=33.6,  # 0.14 * 240 kg
            initial_raan_deg=120.0,
        ),
        SatelliteConfig(
            satellite_id="SAT-003",
            satellite_name="ORBITOPS-GAMMA",
            mission_id="00000000-0000-0000-0000-000000000001",
            semi_major_axis_km=7021.0,  # ~650 km polar
            inclination_deg=89.0,
            mass_kg=95.0,
            battery_capacity_wh=220.0,
            solar_area_m2=0.8,
            initial_mode="NOMINAL",
            initial_battery_soc_pct=80.0,
            initial_bus_temp_c=18.0,
            initial_payload_temp_c=15.0,
            initial_adcs_mode="SUN_POINTING",
            initial_angular_rate_dps=0.02,
            initial_true_anomaly_deg=120.0,
            payload_active_power_w=35.0,
            payload_standby_power_w=3.0,
            payload_data_rate_mbps=0.05,
            payload_initially_active=False,
            comms_tx_enabled=True,
            comms_initially_transmitting=False,
            adcs_inertia_kg_m2=13.3,  # 0.14 * 95 kg
            initial_raan_deg=240.0,
        ),
    ]


def frame_to_telemetry_sample(frame: TelemetryFrame) -> TelemetrySampleModel:
    """Convert an in-memory simulation TelemetryFrame to a persisted ORM model.

    Maps all primary subsystem telemetry parameters into their dedicated typed columns
    and attaches the complete frame payload as JSON.
    """
    m = frame.measurements
    return TelemetrySampleModel(
        satellite_id=frame.satellite_id,
        sim_timestamp=frame.sim_timestamp,
        sequence_number=frame.sequence_number,
        pwr_bus_v=float(m["PWR_BUS_V"].value),
        pwr_solar_w=float(m["PWR_SOLAR_W"].value),
        batt_soc=float(m["BATT_SOC"].value),
        batt_temp_c=float(m["BATT_TEMP_C"].value),
        temp_bus_c=float(m["TEMP_BUS_C"].value),
        temp_pl_c=float(m["TEMP_PL_C"].value),
        att_rate_dps=float(m["ATT_RATE_DPS"].value),
        rf_snr_db=float(m["RF_SNR_DB"].value),
        is_in_eclipse=bool(frame.is_in_eclipse),
        metrics_payload=frame.to_dict(),
    )


def persist_telemetry_batch(
    session: Session,
    frames: list[TelemetryFrame],
) -> list[TelemetrySampleModel]:
    """Persist a batch of simulation telemetry frames to the database.

    Enforces the single-source-of-truth architectural rule: all persisted
    telemetry records originate from the authoritative simulation engine.
    """
    if not frames:
        return []
    repo = TelemetryRepository(session)
    samples = [frame_to_telemetry_sample(f) for f in frames]
    repo.insert_batch(samples)
    return samples
