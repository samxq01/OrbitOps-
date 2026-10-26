# OrbitOps — Database Design & Data Model Specification

**Target Implementation:** Phase 02 (Persistence & Domain Models)
**ORM Framework:** SQLAlchemy 2.0 (Declarative Base with Mapped Columns)
**Underlying Engine:** SQLite 3 (WAL Mode Enabled)

---

## 1. Overview and Relational Architecture

The OrbitOps database persistence layer stores spacecraft configuration, historical telemetry feeds, incident evidence trails, ground pass schedules, telecommands, and mission event streams.

```
       +-------------------+
       |     missions      |
       +---------+---------+
                 | 1
                 |
                 | *
       +---------v---------+          +-----------------------+
       |    satellites     | 1 ---- * | satellite_subsystems  |
       +---------+---------+          +-----------------------+
                 |
        +--------+--------+------------------+------------------+
        | 1               | 1                | 1                | 1
        |                 |                  |                  |
        | *               | *                | *                | *
+-------v-------+ +-------v-------+  +-------v-------+  +-------v-------+
|telemetry_     | |incident_      |  |contact_       |  |satellite_     |
|samples        | |records        |  |windows        |  |commands       |
+---------------+ +-------+-------+  +---------------+  +---------------+
                          | 1
                          |
                          | *
                  +-------v-------+
                  |incident_      |
                  |evidence       |
                  +---------------+

Standalone / Stream Tables:
- ground_stations
- fault_scenarios
- mission_events (append-only audit log)
- simulation_checkpoints (state snapshots)
```

---

## 2. Table Specifications

### 2.1 Table: `missions`
Tracks mission simulation runs, execution parameters, and clock baselines.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `mission_id` | `VARCHAR(36)` | **PRIMARY KEY** | UUID identifier for the mission session |
| `name` | `VARCHAR(100)` | `NOT NULL` | Human-readable name (e.g., "ORBITOPS-SIM-01") |
| `start_time` | `DATETIME` | `NOT NULL` | Simulation start timestamp (UTC) |
| `time_warp_factor` | `FLOAT` | `NOT NULL DEFAULT 1.0` | Clock acceleration multiplier ($1.0\times\dots 10.0\times$) |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Active execution flag |
| `created_at` | `DATETIME` | `NOT NULL` | Real-world creation timestamp (UTC) |

### 2.2 Table: `satellites`
Core spacecraft registry defining orbital ephemeris and physical specifications.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `satellite_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique satellite ID (e.g., `SAT-001`) |
| `mission_id` | `VARCHAR(36)` | `FOREIGN KEY (missions.mission_id) ON DELETE CASCADE` | Associated mission ID |
| `name` | `VARCHAR(100)` | `NOT NULL UNIQUE` | Operational name (`ORBITOPS-ALPHA`) |
| `norad_id` | `INTEGER` | `NOT NULL` | Simulated NORAD tracking catalog number |
| `satellite_type` | `VARCHAR(50)` | `NOT NULL` | Type: `EARTH_OBSERVATION`, `COMMUNICATION`, `RESEARCH` |
| `operational_mode`| `VARCHAR(30)` | `NOT NULL DEFAULT 'NOMINAL'` | Current mode: `INITIALIZING`, `NOMINAL`, `SAFE_MODE`, etc. |
| `semi_major_axis_km`| `FLOAT` | `NOT NULL` | Orbit semi-major axis (e.g., $6921.0\ \text{km}$) |
| `inclination_deg` | `FLOAT` | `NOT NULL` | Orbital inclination angle ($0.0\dots 180.0^\circ$) |
| `mass_kg` | `FLOAT` | `NOT NULL` | Spacecraft wet mass in kg |
| `battery_capacity_wh`| `FLOAT`| `NOT NULL` | Total battery energy capacity in Watt-hours |
| `solar_area_m2` | `FLOAT` | `NOT NULL` | Effective solar array surface area in $\text{m}^2$ |

*Indexes:*
- `idx_satellites_mode`: `(operational_mode)`

### 2.3 Table: `satellite_subsystems`
Represents the state of each physical subsystem per satellite.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `subsystem_id` | `VARCHAR(36)` | **PRIMARY KEY** | Subsystem instance UUID |
| `satellite_id` | `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id) ON DELETE CASCADE` | Associated spacecraft |
| `subsystem_type` | `VARCHAR(30)` | `NOT NULL` | Enum: `POWER`, `THERMAL`, `ADCS`, `COMMS`, `PAYLOAD` |
| `health_status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'NOMINAL'` | Health: `NOMINAL`, `WARNING`, `CRITICAL` |
| `power_draw_w` | `FLOAT` | `NOT NULL DEFAULT 0.0` | Active electrical load in Watts |
| `temperature_c` | `FLOAT` | `NOT NULL DEFAULT 20.0`| Subsystem bulk temperature in Celsius |
| `configuration` | `JSON` | `NOT NULL DEFAULT '{}'` | Subsystem specific constants (heaters, gain, etc.) |

*Indexes:*
- `idx_subsystems_sat_type`: `(satellite_id, subsystem_type)` UNIQUE

### 2.4 Table: `telemetry_samples`
High-frequency recorded telemetry frames emitted by the digital twin.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `sample_id` | `VARCHAR(36)` | **PRIMARY KEY** | UUID of telemetry record |
| `satellite_id` | `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id) ON DELETE CASCADE` | Emitting spacecraft |
| `sim_timestamp` | `DATETIME` | `NOT NULL` | Simulated satellite mission timestamp (UTC) |
| `recorded_at` | `DATETIME` | `NOT NULL` | Physical database write timestamp (UTC) |
| `sequence_number`| `BIGINT` | `NOT NULL` | Monotonically increasing frame sequence ID |
| `pwr_bus_v` | `FLOAT` | `NOT NULL` | Bus voltage in Volts |
| `pwr_solar_w` | `FLOAT` | `NOT NULL` | Solar generation in Watts |
| `batt_soc` | `FLOAT` | `NOT NULL` | Battery State of Charge in % |
| `batt_temp_c` | `FLOAT` | `NOT NULL` | Battery core temperature in Celsius |
| `temp_bus_c` | `FLOAT` | `NOT NULL` | Avionics bus temperature in Celsius |
| `temp_pl_c` | `FLOAT` | `NOT NULL` | Payload temperature in Celsius |
| `att_rate_dps` | `FLOAT` | `NOT NULL` | Attitude angular rate in deg/s |
| `rf_snr_db` | `FLOAT` | `NOT NULL` | Downlink signal-to-noise ratio in dB |
| `is_in_eclipse` | `BOOLEAN` | `NOT NULL` | True if satellite is in Earth shadow |
| `metrics_payload`| `JSON` | `NOT NULL` | Extended raw telemetry metrics dictionary |

*Indexes:*
- `idx_telem_sat_simtime`: `(satellite_id, sim_timestamp DESC)`
- `idx_telem_seq`: `(sequence_number)`

### 2.5 Table: `fault_scenarios`
Defines available and active emergency simulation scenarios.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `scenario_id` | `VARCHAR(36)` | **PRIMARY KEY** | Scenario identifier (e.g., `SCN-01`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Scenario title (e.g., "Solar Eclipse Power Crisis") |
| `target_satellite_id`| `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id)` | Spacecraft targeted by fault |
| `fault_type` | `VARCHAR(50)` | `NOT NULL` | Fault code (e.g., `ARRAY_DRIVE_STALL`) |
| `trigger_met_sec` | `INTEGER` | `NOT NULL` | Trigger offset in Mission Elapsed Time seconds |
| `parameters` | `JSON` | `NOT NULL DEFAULT '{}'` | Scenario specific severity parameters |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT FALSE`| Active injection status |

### 2.6 Table: `incident_records`
Anomalies detected by the Anomaly Investigator.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `incident_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique incident reference (e.g., `INC-2026-001`) |
| `satellite_id` | `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id)` | Spacecraft experiencing incident |
| `title` | `VARCHAR(150)` | `NOT NULL` | Summary headline of anomaly |
| `severity` | `VARCHAR(20)` | `NOT NULL` | Severity: `INFO`, `WARNING`, `CRITICAL` |
| `detected_at` | `DATETIME` | `NOT NULL` | Simulation timestamp when detected |
| `resolved_at` | `DATETIME` | `NULL` | Simulation timestamp when resolved |
| `acknowledged` | `BOOLEAN` | `NOT NULL DEFAULT FALSE`| Operator acknowledgment flag |
| `confidence_score`| `FLOAT` | `NOT NULL` | Calibrated diagnosis confidence ($0.0\dots 1.0$) |
| `primary_cause` | `VARCHAR(100)` | `NOT NULL` | Leading hypothesized root cause |
| `recommended_action`| `VARCHAR(100)`| `NOT NULL` | Suggested recovery telecommand |

*Indexes:*
- `idx_incidents_sat_sev`: `(satellite_id, severity, acknowledged)`

### 2.7 Table: `incident_evidence`
Deterministic proof records supporting or refuting failure hypotheses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `evidence_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique evidence item UUID |
| `incident_id` | `VARCHAR(36)` | `FOREIGN KEY (incident_records.incident_id) ON DELETE CASCADE` | Associated incident |
| `telemetry_mnemonic`| `VARCHAR(50)`| `NOT NULL` | Parameter investigated (e.g., `PWR_SOLAR_W`) |
| `observed_value` | `FLOAT` | `NOT NULL` | Actual measured value from telemetry |
| `expected_value` | `FLOAT` | `NOT NULL` | Expected nominal physical value |
| `polarity` | `VARCHAR(20)` | `NOT NULL` | `SUPPORTING` or `CONTRADICTING` |
| `hypothesis` | `VARCHAR(100)` | `NOT NULL` | Hypothesis being tested |
| `explanation` | `TEXT` | `NOT NULL` | Physical rationale explaining the proof |

*Indexes:*
- `idx_evidence_incident`: `(incident_id)`

### 2.8 Table: `ground_stations`
Geographical and operational definitions of ground tracking stations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `station_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique station key (e.g., `GS-KOUROU`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Station name |
| `latitude_deg` | `FLOAT` | `NOT NULL` | Latitude in degrees ($-90.0\dots +90.0$) |
| `longitude_deg` | `FLOAT` | `NOT NULL` | Longitude in degrees ($-180.0\dots +180.0$) |
| `min_elevation_deg`| `FLOAT`| `NOT NULL DEFAULT 10.0` | Minimum contact elevation horizon angle |
| `carrier_freq_mhz` | `FLOAT`| `NOT NULL DEFAULT 2200.0`| S-band carrier downlink frequency |

### 2.9 Table: `contact_windows`
Calculated line-of-sight communication passes.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `window_id` | `VARCHAR(36)` | **PRIMARY KEY** | Contact pass UUID |
| `station_id` | `VARCHAR(36)` | `FOREIGN KEY (ground_stations.station_id)` | Tracking ground station |
| `satellite_id` | `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id)` | Spacecraft passing overhead |
| `aos_time` | `DATETIME` | `NOT NULL` | Acquisition of Signal timestamp |
| `los_time` | `DATETIME` | `NOT NULL` | Loss of Signal timestamp |
| `max_elevation_deg`| `FLOAT` | `NOT NULL` | Peak elevation angle reached during pass |
| `duration_sec` | `INTEGER` | `NOT NULL` | Pass duration in seconds |

*Indexes:*
- `idx_windows_sat_aos`: `(satellite_id, aos_time, los_time)`

### 2.10 Table: `satellite_commands`
Operator telecommands submitted through the validation pipeline.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `command_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique command UUID |
| `satellite_id` | `VARCHAR(36)` | `FOREIGN KEY (satellites.satellite_id)` | Target spacecraft |
| `command_mnemonic`| `VARCHAR(50)`| `NOT NULL` | Instruction code (`CMD_SHED_PAYLOAD`) |
| `parameters` | `JSON` | `NOT NULL DEFAULT '{}'` | Command arguments |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'QUEUED'` | Pipeline state: `QUEUED`, `VALIDATING`, etc. |
| `rejection_reason`| `VARCHAR(200)`| `NULL` | Failure message if rejected |
| `submitted_by` | `VARCHAR(50)` | `NOT NULL DEFAULT 'operator'` | Submitting user role |
| `submitted_at` | `DATETIME` | `NOT NULL` | Submission timestamp |
| `executed_at` | `DATETIME` | `NULL` | Execution confirmation timestamp |

*Indexes:*
- `idx_commands_sat_status`: `(satellite_id, status)`

### 2.11 Table: `mission_events`
Append-only chronological audit log of all simulation state changes.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `event_id` | `VARCHAR(36)` | **PRIMARY KEY** | Unique event UUID |
| `sequence_number`| `BIGINT` | `NOT NULL UNIQUE` | Strict monotonic sequence number |
| `event_type` | `VARCHAR(50)` | `NOT NULL` | Event code (`MODE_TRANSITION`, `FAULT_INJECTED`) |
| `satellite_id` | `VARCHAR(36)` | `NULL` | Related satellite (if applicable) |
| `sim_timestamp` | `DATETIME` | `NOT NULL` | Simulation timestamp |
| `recorded_at` | `DATETIME` | `NOT NULL` | Wall-clock write timestamp |
| `payload` | `JSON` | `NOT NULL DEFAULT '{}'` | Event context metadata |

*Indexes:*
- `idx_events_seq`: `(sequence_number)`
- `idx_events_simtime`: `(sim_timestamp)`

### 2.12 Table: `simulation_checkpoints`
Periodic full-system state snapshots enabling rewind and crash recovery.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `checkpoint_id` | `VARCHAR(36)` | **PRIMARY KEY** | Checkpoint UUID |
| `mission_id` | `VARCHAR(36)` | `FOREIGN KEY (missions.mission_id)` | Mission session |
| `sim_timestamp` | `DATETIME` | `NOT NULL` | Simulation timestamp of snapshot |
| `snapshot_data` | `JSON` | `NOT NULL` | Serialized state dictionary of all satellites |
| `created_at` | `DATETIME` | `NOT NULL` | Wall-clock creation timestamp |

---

## 3. Storage Assumptions & Retention Policies

1. **Volume Estimate:**
   - 3 satellites $\times 1\ \text{sample/sec} = 3\ \text{samples/sec}$.
   - Storing full metrics payload ($\sim 350\ \text{bytes/sample}$) generates $\sim 3.78\ \text{MB/hour}$.
   - A typical 4-hour active student simulation session requires $\approx 15\ \text{MB}$ of SQLite disk storage, well within laptop constraints.
2. **Indexing Strategy:**
   - Queries for live charting retrieve telemetry by `(satellite_id, sim_timestamp DESC) LIMIT 300`, which executes in $< 1\ \text{ms}$ over the composite B-tree index.
3. **WAL Concurrency Assurance:**
   - With `PRAGMA journal_mode=WAL;`, reader threads (REST queries, WebSocket publishers) never block the background telemetry writer thread.
