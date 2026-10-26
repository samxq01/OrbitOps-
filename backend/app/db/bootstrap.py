"""Database bootstrap, schema verification, and idempotent seed routines."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import (
    VIRTUAL_NORAD_ALPHA,
    VIRTUAL_NORAD_BETA,
    VIRTUAL_NORAD_GAMMA,
)
from app.domain.enums import SatelliteMode, SatelliteType, SubsystemType
from app.models.ground_station import GroundStationModel
from app.models.mission import MissionModel
from app.models.satellite import SatelliteModel, SatelliteSubsystemModel
from app.models.scenario import FaultScenarioModel

logger = logging.getLogger("orbitops.db.bootstrap")

DEFAULT_MISSION_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_MISSION_NAME = "ORBITOPS-MISSION-01"


def seed_virtual_constellation(session: Session) -> dict[str, int]:
    """Idempotently seed the default mission, 3 virtual satellites,
    subsystems, and ground stations.
    """
    # 1. Mission
    mission = session.get(MissionModel, DEFAULT_MISSION_ID)
    if not mission:
        mission = MissionModel(
            mission_id=DEFAULT_MISSION_ID,
            name=DEFAULT_MISSION_NAME,
            start_time=datetime(2026, 10, 26, 0, 0, 0, tzinfo=UTC),
            time_warp_factor=1.0,
            is_active=True,
        )
        session.add(mission)
        session.flush()
        logger.info("Created default mission: %s", DEFAULT_MISSION_NAME)

    # 2. Virtual Satellites Definition matching SRS
    satellite_specs: list[dict[str, Any]] = [
        {
            "satellite_id": "SAT-001",
            "name": "ORBITOPS-ALPHA",
            "norad_id": VIRTUAL_NORAD_ALPHA,
            "satellite_type": SatelliteType.EARTH_OBSERVATION.value,
            "operational_mode": SatelliteMode.NOMINAL.value,
            "semi_major_axis_km": 6921.0,  # ~550 km SSO
            "inclination_deg": 97.6,
            "mass_kg": 180.0,
            "battery_capacity_wh": 320.0,
            "solar_area_m2": 1.2,
            "subsystems": [
                {
                    "type": SubsystemType.POWER.value,
                    "draw_w": 25.0,
                    "temp_c": 20.0,
                    "config": {"nominal_bus_v": 28.0, "battery_cells": 8},
                },
                {
                    "type": SubsystemType.THERMAL.value,
                    "draw_w": 0.0,
                    "temp_c": 21.5,
                    "config": {"heaters_enabled": True, "target_temp_c": 20.0},
                },
                {
                    "type": SubsystemType.ADCS.value,
                    "draw_w": 15.0,
                    "temp_c": 19.0,
                    "config": {"mode": "NADIR_POINTING", "pointing_target": "EARTH_CENTER"},
                },
                {
                    "type": SubsystemType.COMMS.value,
                    "draw_w": 20.0,
                    "temp_c": 22.0,
                    "config": {"band": "S_BAND", "frequency_mhz": 2200.0, "tx_power_w": 10.0},
                },
                {
                    "type": SubsystemType.PAYLOAD.value,
                    "draw_w": 0.0,  # Standby
                    "temp_c": 18.0,
                    "config": {"instrument": "MULTISPECTRAL_IMAGER", "peak_power_w": 180.0},
                },
            ],
        },
        {
            "satellite_id": "SAT-002",
            "name": "ORBITOPS-BETA",
            "norad_id": VIRTUAL_NORAD_BETA,
            "satellite_type": SatelliteType.COMMUNICATION.value,
            "operational_mode": SatelliteMode.NOMINAL.value,
            "semi_major_axis_km": 7071.0,  # ~700 km near-equatorial
            "inclination_deg": 5.0,
            "mass_kg": 240.0,
            "battery_capacity_wh": 480.0,
            "solar_area_m2": 1.8,
            "subsystems": [
                {
                    "type": SubsystemType.POWER.value,
                    "draw_w": 35.0,
                    "temp_c": 22.0,
                    "config": {"nominal_bus_v": 28.0, "solar_wings": 2},
                },
                {
                    "type": SubsystemType.THERMAL.value,
                    "draw_w": 0.0,
                    "temp_c": 26.0,
                    "config": {"heaters_enabled": True, "radiator_area_m2": 0.85},
                },
                {
                    "type": SubsystemType.ADCS.value,
                    "draw_w": 18.0,
                    "temp_c": 20.0,
                    "config": {"mode": "EARTH_POINTING", "stabilization": "3_AXIS"},
                },
                {
                    "type": SubsystemType.COMMS.value,
                    "draw_w": 80.0,
                    "temp_c": 38.0,
                    "config": {"band": "X_BAND", "channels": 4, "tx_power_w": 40.0},
                },
                {
                    "type": SubsystemType.PAYLOAD.value,
                    "draw_w": 20.0,
                    "temp_c": 24.0,
                    "config": {"instrument": "TACTICAL_TRANSPONDER", "bandwidth_mhz": 50.0},
                },
            ],
        },
        {
            "satellite_id": "SAT-003",
            "name": "ORBITOPS-GAMMA",
            "norad_id": VIRTUAL_NORAD_GAMMA,
            "satellite_type": SatelliteType.RESEARCH.value,
            "operational_mode": SatelliteMode.NOMINAL.value,
            "semi_major_axis_km": 7021.0,  # ~650 km polar eccentric
            "inclination_deg": 89.0,
            "mass_kg": 95.0,
            "battery_capacity_wh": 220.0,
            "solar_area_m2": 0.8,
            "subsystems": [
                {
                    "type": SubsystemType.POWER.value,
                    "draw_w": 18.0,
                    "temp_c": 18.0,
                    "config": {"nominal_bus_v": 28.0, "body_mounted_cells": True},
                },
                {
                    "type": SubsystemType.THERMAL.value,
                    "draw_w": 0.0,
                    "temp_c": 12.0,
                    "config": {"heaters_enabled": True, "extreme_cold_protection": True},
                },
                {
                    "type": SubsystemType.ADCS.value,
                    "draw_w": 12.0,
                    "temp_c": 16.0,
                    "config": {"mode": "SUN_POINTING", "coarse_hold": True},
                },
                {
                    "type": SubsystemType.COMMS.value,
                    "draw_w": 15.0,
                    "temp_c": 18.0,
                    "config": {"band": "UHF", "frequency_mhz": 435.0, "beacon": True},
                },
                {
                    "type": SubsystemType.PAYLOAD.value,
                    "draw_w": 35.0,
                    "temp_c": 15.0,
                    "config": {
                        "instrument": "PLASMA_PROBE_MAGNETOMETER",
                        "sampling_rate_hz": 100.0,
                    },
                },
            ],
        },
    ]

    sat_count = 0
    sub_count = 0

    for spec in satellite_specs:
        sat_id = spec["satellite_id"]
        sat = session.get(SatelliteModel, sat_id)
        if not sat:
            sat = SatelliteModel(
                satellite_id=sat_id,
                mission_id=DEFAULT_MISSION_ID,
                name=spec["name"],
                norad_id=spec["norad_id"],
                satellite_type=spec["satellite_type"],
                operational_mode=spec["operational_mode"],
                semi_major_axis_km=spec["semi_major_axis_km"],
                inclination_deg=spec["inclination_deg"],
                mass_kg=spec["mass_kg"],
                battery_capacity_wh=spec["battery_capacity_wh"],
                solar_area_m2=spec["solar_area_m2"],
            )
            session.add(sat)
            session.flush()
            sat_count += 1
            logger.info("Seeded virtual satellite: %s (%s)", sat.name, sat.satellite_id)

        # Seed subsystems
        for sub_spec in spec["subsystems"]:
            stmt = select(SatelliteSubsystemModel).where(
                SatelliteSubsystemModel.satellite_id == sat_id,
                SatelliteSubsystemModel.subsystem_type == sub_spec["type"],
            )
            existing_sub = session.scalars(stmt).first()
            if not existing_sub:
                subsystem = SatelliteSubsystemModel(
                    satellite_id=sat_id,
                    subsystem_type=sub_spec["type"],
                    health_status="NOMINAL",
                    power_draw_w=sub_spec["draw_w"],
                    temperature_c=sub_spec["temp_c"],
                    configuration=sub_spec["config"],
                )
                session.add(subsystem)
                sub_count += 1

    # 3. Virtual Ground Stations matching SRS
    stations_data = [
        {
            "id": "GS-KOUROU",
            "name": "Kourou Ground Station",
            "lat": 5.2,
            "lon": -52.8,
            "min_el": 10.0,
        },
        {
            "id": "GS-SVALBARD",
            "name": "Svalbard Arctic Tracking",
            "lat": 78.2,
            "lon": 15.6,
            "min_el": 10.0,
        },
        {
            "id": "GS-CANBERRA",
            "name": "Canberra Deep Space Station",
            "lat": -35.3,
            "lon": 149.0,
            "min_el": 10.0,
        },
    ]

    station_count = 0
    for st_spec in stations_data:
        st = session.get(GroundStationModel, st_spec["id"])
        if not st:
            st = GroundStationModel(
                station_id=st_spec["id"],
                name=st_spec["name"],
                latitude_deg=st_spec["lat"],
                longitude_deg=st_spec["lon"],
                min_elevation_deg=st_spec["min_el"],
                carrier_freq_mhz=2200.0,
            )
            session.add(st)
            station_count += 1

    # 4. Mandatory Emergency Scenarios matching SRS
    scenarios_data = [
        {
            "id": "SCN-01",
            "name": "Solar Eclipse Power Crisis",
            "sat_id": "SAT-001",
            "fault_type": "ARRAY_DRIVE_STALL",
            "trigger_met": 1800,
        },
        {
            "id": "SCN-02",
            "name": "Communication Blackout",
            "sat_id": "SAT-002",
            "fault_type": "OSCILLATOR_DESYNC",
            "trigger_met": 2400,
        },
        {
            "id": "SCN-03",
            "name": "Thermal Runaway Emergency",
            "sat_id": "SAT-002",
            "fault_type": "RADIATOR_LOUVER_JAM",
            "trigger_met": 3600,
        },
        {
            "id": "SCN-04",
            "name": "Conflicting Sensor Readings",
            "sat_id": "SAT-003",
            "fault_type": "HORIZON_SENSOR_SEU",
            "trigger_met": 1200,
        },
    ]

    scenario_count = 0
    for sc_spec in scenarios_data:
        sc = session.get(FaultScenarioModel, sc_spec["id"])
        if not sc:
            sc = FaultScenarioModel(
                scenario_id=sc_spec["id"],
                name=sc_spec["name"],
                target_satellite_id=sc_spec["sat_id"],
                fault_type=sc_spec["fault_type"],
                trigger_met_sec=sc_spec["trigger_met"],
                parameters={"simulated": True},
                is_active=False,
            )
            session.add(sc)
            scenario_count += 1

    session.flush()

    return {
        "satellites_created": sat_count,
        "subsystems_created": sub_count,
        "stations_created": station_count,
        "scenarios_created": scenario_count,
    }
