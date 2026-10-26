# OrbitOps — API Contract Specification

**Target Implementation:** Phase 04 (REST APIs and Telemetry Streaming)
**Specification Version:** `1.0`
**Base URL:** `http://127.0.0.1:8000/api/v1`
**WebSocket URL:** `ws://127.0.0.1:8000/api/v1/telemetry/stream`

> [!NOTE]
> All endpoints below are planned specifications for subsequent phases, with the exception of `GET /api/v1/health` which was implemented and verified in Phase 00.

---

## 1. Global Standards & Error Format

All error responses return structured JSON conforming to standard error envelope:

```json
{
  "error": {
    "code": "ERR_PRECONDITION_FAILED",
    "message": "Command rejected: Satellite SAT-001 is not in an active ground station contact window.",
    "details": {
      "satellite_id": "SAT-001",
      "required_elevation_deg": 10.0,
      "current_elevation_deg": -14.2,
      "next_aos_time": "2026-10-26T15:42:10Z"
    },
    "timestamp": "2026-10-26T21:12:00.000Z"
  }
}
```

---

## 2. REST Endpoints Specification

### 2.1 System & Fleet

#### `GET /api/v1/health`
- **Status:** **IMPLEMENTED (Phase 00)**
- **Purpose:** Verifies operational readiness of backend service.
- **Response `200 OK`:**
```json
{
  "service": "orbitops-api",
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "simulation_mode": true,
  "timestamp": "2026-10-26T15:21:21.824Z"
}
```

#### `GET /api/v1/satellites`
- **Status:** PLANNED (Phase 02 / 04)
- **Purpose:** Lists all satellites in the virtual constellation with aggregated health.
- **Response `200 OK`:**
```json
[
  {
    "satellite_id": "SAT-001",
    "name": "ORBITOPS-ALPHA",
    "type": "EARTH_OBSERVATION",
    "operational_mode": "NOMINAL",
    "overall_health": "NOMINAL",
    "battery_soc": 89.2,
    "bus_voltage": 28.1,
    "is_in_eclipse": false,
    "latitude_deg": 34.52,
    "longitude_deg": -118.25,
    "altitude_km": 549.8
  }
]
```

#### `GET /api/v1/satellites/{satellite_id}`
- **Status:** PLANNED (Phase 04)
- **Purpose:** Retrieves complete subsystem configuration and current state for a single satellite.
- **Errors:** `404 Not Found` (`ERR_SATELLITE_NOT_FOUND`).

---

### 2.2 Telemetry & History

#### `GET /api/v1/satellites/{satellite_id}/telemetry`
- **Status:** PLANNED (Phase 04)
- **Query Parameters:**
  - `start_time` (ISO 8601, optional): Filter start time.
  - `end_time` (ISO 8601, optional): Filter end time.
  - `limit` (integer, default: 300, max: 1000): Number of samples to return.
- **Response `200 OK`:**
```json
{
  "satellite_id": "SAT-001",
  "count": 2,
  "samples": [
    {
      "sim_timestamp": "2026-10-26T14:30:00Z",
      "pwr_bus_v": 28.1,
      "pwr_solar_w": 420.0,
      "batt_soc": 90.1,
      "temp_bus_c": 21.4,
      "temp_pl_c": 26.2,
      "att_rate_dps": 0.04,
      "rf_snr_db": 14.1,
      "is_in_eclipse": false
    }
  ]
}
```

---

### 2.3 Incidents & Anomaly Investigation

#### `GET /api/v1/incidents`
- **Status:** PLANNED (Phase 08)
- **Purpose:** Lists all detected incidents across the constellation.
- **Query Parameters:** `status=open|acknowledged|resolved`, `satellite_id`.

#### `GET /api/v1/incidents/{incident_id}`
- **Status:** PLANNED (Phase 08)
- **Purpose:** Returns comprehensive diagnostic report including the Evidence Proof Matrix.
- **Response `200 OK`:**
```json
{
  "incident_id": "INC-2026-001",
  "satellite_id": "SAT-001",
  "title": "Battery Rapid Depletion in Eclipse",
  "severity": "CRITICAL",
  "detected_at": "2026-10-26T14:32:00Z",
  "confidence_score": 0.89,
  "primary_cause": "Solar Array Drive Mechanism Stall with Active Optical Payload",
  "recommended_action": "CMD_SHED_PAYLOAD_LOAD",
  "evidence_proofs": [
    {
      "telemetry_mnemonic": "PWR_SOLAR_W",
      "observed": 0.0,
      "expected": 450.0,
      "polarity": "SUPPORTING",
      "hypothesis": "Array Drive Failure",
      "explanation": "Zero solar generation despite post-eclipse orbital entry."
    },
    {
      "telemetry_mnemonic": "PL_POWER_W",
      "observed": 180.0,
      "expected": 0.0,
      "polarity": "SUPPORTING",
      "hypothesis": "Unmanaged Payload Draw",
      "explanation": "Optical payload remained powered in eclipse, accelerating discharge."
    }
  ]
}
```

#### `POST /api/v1/incidents/{incident_id}/acknowledge`
- **Status:** PLANNED (Phase 08)
- **Header:** `X-OrbitOps-Role: operator`
- **Response `200 OK`:** `{ "incident_id": "INC-2026-001", "acknowledged": true }`.

---

### 2.4 Command Pipeline

#### `POST /api/v1/commands`
- **Status:** PLANNED (Phase 10)
- **Purpose:** Submits an operator telecommand to the multi-stage validation pipeline.
- **Request Body:**
```json
{
  "satellite_id": "SAT-001",
  "command_mnemonic": "CMD_SHED_PAYLOAD_LOAD",
  "parameters": {
    "subsystem": "PAYLOAD",
    "target_power_state": "OFF"
  }
}
```
- **Response `200 OK` (Approved & Queued):**
```json
{
  "command_id": "CMD-9021",
  "satellite_id": "SAT-001",
  "command_mnemonic": "CMD_SHED_PAYLOAD_LOAD",
  "status": "APPROVED",
  "submitted_at": "2026-10-26T21:12:00Z",
  "validation_passed": true,
  "precondition_checks": {
    "ground_contact_active": true,
    "power_margin_sufficient": true,
    "interlocks_cleared": true
  }
}
```
- **Error `422 Unprocessable Entity` (Precondition Rejection):**
```json
{
  "command_id": "CMD-9022",
  "status": "REJECTED",
  "rejection_reason": "ERR_PRECONDITION_CONTACT_REQUIRED",
  "message": "Cannot uplink command: satellite is outside line-of-sight of any active ground station."
}
```

---

### 2.5 Ground Stations & Pass Schedules

#### `GET /api/v1/ground-stations`
- **Status:** PLANNED (Phase 09)
- **Purpose:** Returns network status of all ground stations and active contact passes.

#### `GET /api/v1/ground-stations/passes`
- **Status:** PLANNED (Phase 09)
- **Query Parameters:** `satellite_id`, `window_hours` (default: 24).
- **Response `200 OK`:**
```json
[
  {
    "window_id": "WIN-101",
    "station_id": "GS-KOUROU",
    "satellite_id": "SAT-001",
    "aos_time": "2026-10-26T15:45:00Z",
    "los_time": "2026-10-26T15:56:30Z",
    "max_elevation_deg": 64.2,
    "duration_sec": 690,
    "status": "UPCOMING"
  }
]
```

---

### 2.6 Simulation Scenarios & Clock Control

#### `POST /api/v1/scenarios/{scenario_id}/trigger`
- **Status:** PLANNED (Phase 07)
- **Header:** `X-OrbitOps-Role: admin`
- **Purpose:** Triggers an emergency fault scenario (e.g., `SCN-01`).
- **Response `200 OK`:**
```json
{
  "scenario_id": "SCN-01",
  "name": "Solar Eclipse Power Crisis",
  "target_satellite": "SAT-001",
  "status": "TRIGGERED",
  "triggered_at_sim_time": "2026-10-26T14:31:00Z"
}
```

#### `POST /api/v1/missions/clock`
- **Status:** PLANNED (Phase 03)
- **Header:** `X-OrbitOps-Role: admin`
- **Request Body:** `{ "action": "SET_WARP", "time_warp_factor": 5.0 }` or `{ "action": "PAUSE" }`.

---

## 3. Real-Time Telemetry WebSocket Contract

- **Endpoint:** `/api/v1/telemetry/stream`
- **Transport:** Standard RFC 6455 WebSocket over HTTP/1.1
- **Frame Frequency:** $1.0\ \text{Hz}$ nominal

```json
{
  "event_type": "TELEMETRY_FRAME",
  "schema_version": "1.0",
  "satellite_id": "SAT-001",
  "sequence_number": 1284,
  "simulation_time": "2026-10-26T14:32:00.000Z",
  "recorded_at": "2026-10-26T21:14:00.120Z",
  "payload": {
    "coordinates": {
      "latitude_deg": 12.4,
      "longitude_deg": -45.2,
      "altitude_km": 550.1,
      "is_in_eclipse": false
    },
    "power": {
      "bus_v": 28.2,
      "solar_w": 448.0,
      "soc": 91.4,
      "batt_current_a": 4.2
    },
    "thermal": {
      "bus_temp_c": 22.0,
      "pl_temp_c": 24.5,
      "radio_temp_c": 31.0
    },
    "adcs": {
      "mode": "NADIR_POINTING",
      "rate_dps": 0.02
    },
    "comms": {
      "locked": true,
      "snr_db": 14.5
    },
    "health_status": "NOMINAL"
  }
}
```
