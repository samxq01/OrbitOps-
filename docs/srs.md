# Software Requirements Specification (SRS)
## OrbitOps — Evidence-Driven Satellite Mission Control & Digital Twin Simulator

**Document Identifier:** `ORBITOPS-SRS-V1.0`
**Standard Compliance:** Inspired by IEEE/ISO/IEC 29148:2018
**Project:** Software Engineering IA3 Capstone
**Repository:** `https://github.com/samxq01/OrbitOps-.git`
**Current Baseline:** `Phase 01 — Baseline Specification`
**Author:** OrbitOps Systems Engineering & Architecture Team

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) establishes the definitive functional, non-functional, interface, data, and behavioral requirements for **OrbitOps**, an educational satellite mission operations console and causal digital twin simulator. It serves as the authoritative technical baseline for implementation across Phases 02 through 15 and provides the evaluation baseline for the Software Engineering IA3 milestone.

### 1.2 Scope
OrbitOps is a self-contained, locally deployable desktop web application that simulates ground station mission operations for a constellation of three virtual Low Earth Orbit (LEO) satellites:
1. **ORBITOPS-ALPHA** (Earth Observation)
2. **ORBITOPS-BETA** (Tactical Communications)
3. **ORBITOPS-GAMMA** (Space Weather & Plasma Research)

The software encompasses:
- A deterministic multi-subsystem digital twin simulation engine (Power, Thermal, ADCS, Communications, and Payload).
- Real-time telemetry broadcasting via WebSockets and REST APIs.
- An interactive dark-aerospace mission operations dashboard with 3D orbital trajectory rendering.
- An evidence-based anomaly detection and diagnostic engine evaluating competing root-cause hypotheses with verifiable telemetry proofs.
- A safe telecommand validation pipeline with strict precondition interlocking.
- An append-only event recorder and scrubbable mission time machine for historical playback.
- Reproducible emergency scenarios and post-mortem incident report generation.

### 1.3 Problem Statement
Most educational software representing satellite operations suffers from two critical deficiencies:
1. **Superficial Telemetry:** Educational tools often present disconnected random-number generators disguised as telemetry. Subsystems do not physically interact; battery depletion does not alter thermal states, and solar array exposure does not correlate with orbital day/night cycles.
2. **Opaque Anomaly Handling:** Ground control training tools typically display arbitrary alert popups without diagnostic provenance. Students and operators are told a failure occurred, but they are not provided with deterministic evidence trails or verifiable hypotheses to deduce root causes.

### 1.4 Project Objectives
1. **Causal Fidelity:** Model tightly coupled spacecraft subsystem physics where orbital environment directly influences power generation, component thermal dissipation, battery state of charge, and attitude modes.
2. **Diagnostic Rigor:** Implement an anomaly investigator that presents observable symptoms, evaluates supporting and refuting evidence, scores confidence calibrated by telemetry coverage, and never claims certainty without sufficient data.
3. **Operational Safety:** Enforce deterministic command verification gates (`QUEUED` $\to$ `VALIDATING` $\to$ `APPROVED`/`REJECTED` $\to$ `EXECUTING` $\to$ `COMPLETED`/`FAILED`) preventing dangerous commands (e.g., payload activation in eclipse or commands out-of-contact).
4. **Pedagogical Replay:** Deliver a non-destructive event log and playback scrubber allowing trainees to rewind missions, evaluate alternative actions, and test "what-if" recovery commands in a branching sandbox.
5. **Zero Cloud Infrastructure:** Run entirely on a student laptop using Python FastAPI, SQLite (WAL mode), Next.js, and Three.js without paid subscriptions or external infrastructure.

### 1.5 Intended Audience
- **Software Engineering Faculty & Assessors:** For evaluating software architecture, formal requirements traceability, UML modeling, and testing rigor.
- **Undergraduate Software Engineering Students:** For learning state machines, digital twins, event replay architectures, and safety-critical telecommand pipelines.
- **Aerospace & Operations Trainees:** For training in telemetry monitoring, ground pass scheduling, anomaly diagnosis, and recovery workflows.

### 1.6 Definitions, Acronyms, and Abbreviations
| Term / Acronym | Definition |
|---|---|
| **ADCS** | Attitude Determination and Control System |
| **AOS** | Acquisition of Signal (satellite enters ground station line-of-sight) |
| **Causal Twin** | A simulation where state changes in one subsystem mathematically dictate state changes in coupled subsystems |
| **Doppler Shift** | Frequency change of RF carrier waves due to relative velocity between satellite and ground station |
| **DTO** | Data Transfer Object (Pydantic schema used for API serialization) |
| **Eclipse** | Orbital phase where the Earth occludes solar radiation, dropping solar flux to $0\ \text{W/m}^2$ |
| **Elevation** | Angle above the local horizon of a ground station ($> 10^\circ$ for valid contact) |
| **LOS** | Loss of Signal (satellite drops below minimum elevation angle) |
| **MET** | Mission Elapsed Time (seconds elapsed since simulation epoch) |
| **Precondition** | A flight safety rule that must evaluate to TRUE before a telecommand is uplinking-approved |
| **SOC** | State of Charge of the onboard battery system (expressed in %) |
| **SSO** | Sun-Synchronous Orbit |
| **Subsystem** | An autonomous physical module of the satellite (Power, Thermal, ADCS, Comms, Payload) |
| **Telecommand** | Uplinked digital instruction sent from ground operations to modify satellite state |
| **Telemetry** | Downlinked physical sensor readings and status flags from satellite to ground |
| **UTC** | Coordinated Universal Time (ISO 8601 representation) |
| **WAL** | Write-Ahead Logging (SQLite high-concurrency journal mode) |

### 1.7 References
1. IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*.
2. Larson, W. J., & Wertz, J. R. — *Space Mission Analysis and Design (SMAD)*, 3rd Edition, Microcosm Press.
3. ECSS-E-ST-70-41C — *Space engineering: Telemetry and telecommand packet utilization*, European Cooperation for Space Standardization.
4. OrbitOps Repository Baseline: [https://github.com/samxq01/OrbitOps-.git](https://github.com/samxq01/OrbitOps-.git).

---

## 2. Overall Description

### 2.1 Product Perspective
OrbitOps operates as a client-server modular monolith. The Python FastAPI backend serves as the single authoritative digital twin simulation and state authority. The Next.js frontend renders an information-dense aerospace mission operations console.

```
+-------------------------------------------------------------------------+
|                  OPERATOR DESKTOP BROWSER (Next.js)                     |
|  [Mission Shell] <-> [Telemetry Gauges] <-> [3D Globe] <-> [Command UI] |
+-----------------------------------^-------------------------------------+
                                    | HTTP / REST + WebSockets
+-----------------------------------v-------------------------------------+
|                  FASTAPI MISSION OPERATIONS ENGINE                      |
|  +------------------------+  +-------------------+  +----------------+  |
|  | Subsystem Integrator   |  | Anomaly Diagnosis |  | Safe Command   |  |
|  | (Power/Thermal/ADCS)   |  | & Evidence Proofs |  | Validation Gate|  |
|  +------------------------+  +-------------------+  +----------------+  |
|  +-------------------------------------------------------------------+  |
|  |            SQLite WAL Persistence & Append-Only Event Store        |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

### 2.2 Product Capabilities
- **Fleet Digital Twin:** Simultaneously advances physical states for three distinct virtual satellites.
- **Subsystem Coupled Physics:**
  - *Power:* Calculates solar irradiance as a function of orbital sun-visibility, power generation, bus load, battery discharge, and depth of charge.
  - *Thermal:* Calculates conductive/radiative balance, internal heat dissipation from active transmitters/payloads, and heater duty cycles.
  - *ADCS:* Simulates nadir-pointing, sun-pointing, and safe-mode tumbling states.
  - *Communications:* Simulates carrier signal strength ($E_b/N_0$), Doppler drift, bit error rate, and ground station visibility windows.
  - *Payload:* Models instrument duty cycle, memory buffer fill levels, and science data downlink.
- **Evidence-Based Anomaly Investigation:** Translates raw telemetry threshold breaches into structured incident reports, correlates symptoms with physical equations, and constructs a supporting vs. refuting evidence matrix.
- **Precondition Command Uplink:** Guards commands against dangerous flight states (e.g., rejecting high-power payload activation while in eclipse or battery SOC $< 40\%$).
- **Mission Time Machine:** Scrubbable timeline with historical incident replay and isolated "what-if" branching sandboxes.

### 2.3 Operating Environment
- **Host OS:** Windows 10/11, macOS 13+, or Ubuntu 22.04 LTS.
- **Hardware Minimum:** 4-core x86_64 or ARM64 CPU, 8 GB RAM, 2 GB available disk space, 1920x1080 display resolution.
- **Runtimes:** Python 3.11/3.12 (managed via `uv`), Node.js v20+ / npm 10+.
- **Browser:** Chromium-based browser (Chrome, Edge) or Firefox with WebGL enabled for 3D globe rendering.

### 2.4 User Classes and Characteristics
1. **Mission Operator (Primary Trainee):** Monitors live telemetry streams, reviews subsystem health status, responds to active alarms, reviews diagnostic evidence, drafts recovery commands, and inspects historical flight data.
2. **Mission Administrator (Instructor / Supervisor):** Injects anomaly scenarios (solar eclipse power crisis, thermal degradation, etc.), controls simulation clock speed (pause, $1\times, 5\times, 10\times$), resets mission states, and manages system configuration.
3. **Observer (Auditor / Student):** Read-only user permitted to view the dashboard, 3D visualization, telemetry history, and generated mission debrief reports without commanding authority.

### 2.5 Assumptions and Dependencies
- The simulation runs entirely on a single developer workstation without distributed cloud infrastructure.
- The simulation time-step default is $\Delta t = 1.0\ \text{second}$, adjustable up to $10\times$ acceleration.
- SQLite Write-Ahead Logging (WAL) is supported on the host filesystem.
- WebGL 2.0 hardware acceleration is supported by the client browser.

### 2.6 Simulation-Only Safety Boundaries
> [!CRITICAL]
> OrbitOps is an educational software system. All satellite telemetry parameters, orbital ephemeris calculations, transmitter signal-to-noise ratios, ground station passes, and telecommands are synthetic mathematical representations. Simulated values must never be represented or claimed as real spacecraft telemetry. No physical satellite networks, hardware-in-the-loop, or RF ground transceivers are connected.

---

## 3. Virtual Satellites & Mandatory Fault Scenarios

### 3.1 Virtual Satellite Constellation
OrbitOps simulates three distinct, configurable virtual spacecraft:

```
+---------------------------------------------------------------------------------------------+
|                               ORBITOPS VIRTUAL CONSTELLATION                                |
+-----------------------+-----------------------------+---------------------------------------+
| 1. ORBITOPS-ALPHA     | 2. ORBITOPS-BETA            | 3. ORBITOPS-GAMMA                     |
| Earth Observation     | Tactical Communications     | Space Weather Research                |
| Orbit: 550 km SSO     | Orbit: 700 km Equatorial    | Orbit: 650 km Polar Eccentric         |
| Payload: Optical Multi| Payload: S/X Transponders   | Payload: Magnetometer & Plasma Probe  |
| High Peak Power Draw  | High Thermal Dissipation    | High Sensitive Radiation Limits       |
+-----------------------+-----------------------------+---------------------------------------+
```

1. **ORBITOPS-ALPHA — Earth Observation Satellite**
   - **ID:** `SAT-001`
   - **Orbit:** 550 km Sun-Synchronous Orbit (SSO), Inclination $97.6^\circ$, Period $\approx 95.6\ \text{min}$.
   - **Nominal Power:** Solar array generating $450\ \text{W}$ peak, $320\ \text{Wh}$ Li-ion battery pack.
   - **Nominal Thermal:** Operating range $-10^\circ\text{C}$ to $+40^\circ\text{C}$.
   - **Payload:** High-resolution multispectral imager requiring $180\ \text{W}$ active power. Duty cycle restricted to sunlit passes with battery $\text{SOC} \ge 60\%$.
2. **ORBITOPS-BETA — Tactical Communications Satellite**
   - **ID:** `SAT-002`
   - **Orbit:** 700 km Circular Equatorial, Inclination $5.0^\circ$, Period $\approx 98.8\ \text{min}$.
   - **Nominal Power:** Dual solar wings generating $600\ \text{W}$ peak, $480\ \text{Wh}$ battery.
   - **Nominal Thermal:** Operating range $-15^\circ\text{C}$ to $+45^\circ\text{C}$. High internal thermal dissipation from continuous RF traveling wave tube amplifiers (TWTA).
   - **Payload:** Multi-channel S/X-band transponder. Transmits continuous telemetry beacon and downlink burst during ground passes.
3. **ORBITOPS-GAMMA — Space Weather Research Satellite**
   - **ID:** `SAT-003`
   - **Orbit:** 650 km Polar Eccentric ($e = 0.05$), Inclination $89.0^\circ$, Period $\approx 97.7\ \text{min}$.
   - **Nominal Power:** Body-mounted solar cells generating $280\ \text{W}$ peak, $220\ \text{Wh}$ battery.
   - **Nominal Thermal:** Wide operating range $-30^\circ\text{C}$ to $+60^\circ\text{C}$ with survival heaters.
   - **Payload:** Fluxgate magnetometer and Langmuir plasma probe sensitive to electromagnetic interference and battery voltage ripple.

### 3.2 Four Mandatory Fault Scenarios

| Scenario ID | Name | Initial Conditions | Fault Trigger Event | Observable Symptoms | Recovery Actions | Success / Failure Criteria |
|---|---|---|---|---|---|---|
| **SCN-01** | **Solar Eclipse Power Crisis** | `ORBITOPS-ALPHA` in nominal ops ($\text{SOC} = 88\%$). | Satellite enters Earth eclipse; primary solar array drive mechanism fails to track sun on exit. | Solar array output drops to $0\ \text{W}$; battery discharges rapidly at $-1.8\%\ \text{SOC/min}$; bus voltage sags from $28.2\ \text{V}$ to $< 24.0\ \text{V}$. | 1. Shed non-critical payload load.<br>2. Orient solar array to emergency sun-pointing bias.<br>3. Force satellite into `SAFE_MODE`. | **Success:** Battery stabilized above $35\%$ SOC; bus voltage $\ge 24.5\ \text{V}$.<br>**Failure:** Battery $\text{SOC} < 20\%$, causing irreversible power brownout. |
| **SCN-02** | **Communication Blackout** | `ORBITOPS-BETA` approaching Madrid ground pass. | Transponder local oscillator phase desynchronization triggered at AOS $-60\ \text{s}$. | Receiver locked flag turns FALSE; downlink SNR drops from $14.2\ \text{dB}$ to $< 1.5\ \text{dB}$; telemetry packets dropped; command ACK timeout. | 1. Switch to redundant secondary B-side transponder.<br>2. Reboot comms baseband processor.<br>3. Adjust uplink carrier center frequency. | **Success:** Carrier lock re-acquired, telemetry packet reception rate $\ge 98\%$.<br>**Failure:** Ground contact window elapses without contact. |
| **SCN-03** | **Thermal Runaway Emergency** | `ORBITOPS-BETA` executing continuous high-rate data relay. | Radiator louvers jam shut; transponder power amplifier dissipation remains at $120\ \text{W}$. | Amplifier temperature climbs past critical threshold ($+65^\circ\text{C}$ at $+1.2^\circ\text{C/min}$); thermal sensor alert triggered; adjacent bus electronics heat up. | 1. Power down high-power RF amplifier.<br>2. Activate payload low-power sleep.<br>3. Slew satellite attitude to orient radiator surface to deep space cold-sink. | **Success:** Amplifier temperature stabilizes below $+45^\circ\text{C}$.<br>**Failure:** Component temperature exceeds $+75^\circ\text{C}$ causing simulated hardware burnout. |
| **SCN-04** | **Conflicting Sensor Readings** | `ORBITOPS-GAMMA` nominal attitude hold in polar orbit. | Primary earth horizon sensor optical photodiode suffers simulated single-event latchup (SEU). | Horizon sensor reports rapid roll error ($+4.8^\circ/\text{s}$), whereas 3-axis fiber-optic gyro indicates zero angular rate ($< 0.01^\circ/\text{s}$); attitude kalman residual spikes. | 1. Cross-examine sun-sensor and gyro telemetry proof.<br>2. Disqualify corrupt horizon sensor input from ADCS filter.<br>3. Revert ADCS mode to coarse sun-pointing. | **Success:** False attitude correction avoided; satellite nominal pointing maintained.<br>**Failure:** ADCS fires thrusters based on bad sensor, inducing unrecoverable tumble ($> 15^\circ/\text{s}$). |

---

## 4. User Roles and Educational Enforcement

OrbitOps targets an educational simulation environment and explicitly avoids unnecessary OAuth/LDAP complexity while maintaining clear role boundaries:

```
                +---------------------+
                |      Observer       | (Read-Only: Telemetry, 3D Globe, Reports)
                +----------^----------+
                           |
                +----------+----------+
                |   Mission Operator  | (Operational: Acknowledge Alerts, Queue Commands)
                +----------^----------+
                           |
                +----------+----------+
                | Mission Admin       | (Supervisory: Inject Faults, Clock, Config)
                +---------------------+
```

1. **Role Identification & Local Context:**
   - Active roles are selected via the local operations console session header: `Mission Operator`, `Mission Administrator`, or `Observer`.
   - The selected role is conveyed to the backend via a standard request header: `X-OrbitOps-Role: [operator|admin|observer]`.
2. **Deterministic Role Enforcement Rules:**
   - **Observer:** Permitted to query `GET` endpoints for fleet status, telemetry streams, and incident reports. Any `POST`, `PUT`, or `DELETE` attempt (e.g., submitting a telecommand or injecting a fault) is deterministically rejected with `HTTP 403 Forbidden` (`ERR_ROLE_UNAUTHORIZED`).
   - **Mission Operator:** Authorized to acknowledge incidents, configure diagnostic evidence trails, and submit telecommands through the validation pipeline. Prohibited from injecting scenarios or modifying global simulation clock rates.
   - **Mission Administrator:** Full authority, including scenario injection, simulation pause/reset/step, and system parameter reconfiguration.

---

## 5. Functional Requirements

### 5.1 Category 1: Satellite Fleet Management
- **FR-001:** The system shall maintain an in-memory and persistent registry for three virtual satellites (`ORBITOPS-ALPHA`, `ORBITOPS-BETA`, `ORBITOPS-GAMMA`), each characterized by unique ID, orbital parameters, operational mode, and subsystem configurations.
  *Priority:* High | *Related Module:* Satellite Registry | *Phase:* 02 | *Acceptance:* Registry returns full satellite metadata matching Section 3.1.
- **FR-002:** The system shall support querying the active operational mode of any registered satellite (`INITIALIZING`, `NOMINAL`, `DEGRADED`, `SAFE_MODE`, `EMERGENCY`, `RECOVERY`, `OFFLINE`).
  *Priority:* High | *Related Module:* Satellite Registry | *Phase:* 02 | *Acceptance:* Operational mode reflects valid state machine states.
- **FR-003:** The system shall provide configurable physical constants for each virtual satellite (mass, battery capacity in Wh, solar array surface area, radiator area) without requiring system recompilation.
  *Priority:* Medium | *Related Module:* Core Config | *Phase:* 02 | *Acceptance:* Modifying satellite parameters in configuration updates simulation calculations.

### 5.2 Category 2: Mission Simulation Engine
- **FR-004:** The system shall advance digital twin state in discrete simulation ticks with configurable integration step size ($\Delta t = 1.0\ \text{s}$ nominal).
  *Priority:* High | *Related Module:* Simulation Engine | *Phase:* 03 | *Acceptance:* Differential state update equations execute deterministically per tick.
- **FR-005:** The system shall provide simulation clock controls allowing an Administrator to `PAUSE`, `RESUME`, `STEP` (single tick), and set time warp multipliers ($1\times, 2\times, 5\times, 10\times$).
  *Priority:* High | *Related Module:* Simulation Clock | *Phase:* 03 | *Acceptance:* Clock state transitions alter tick frequency without corrupting state history.
- **FR-006:** The system shall compute orbital day/night eclipse entry and exit times for each satellite using simplified spherical Earth geometry ($R_\text{Earth} = 6371\ \text{km}$) and line-of-sight solar intersection.
  *Priority:* High | *Related Module:* Orbit Propagator | *Phase:* 03 | *Acceptance:* Solar flux transitions between nominal ($\sim 1361\ \text{W/m}^2$) and eclipse ($0\ \text{W/m}^2$) based on orbital position.

### 5.3 Category 3: Telemetry Collection & Generation
- **FR-007:** The simulation engine shall generate coupled subsystem telemetry for each active satellite on every simulation tick:
  - *Power:* `PWR_SOLAR_W`, `PWR_BUS_V`, `BATT_SOC`, `BATT_TEMP_C`, `BATT_CURRENT_A`.
  - *Thermal:* `TEMP_BUS_C`, `TEMP_PAYLOAD_C`, `TEMP_RADIO_C`, `HEATER_STATUS`.
  - *ADCS:* `ATT_ROLL_DEG`, `ATT_PITCH_DEG`, `ATT_YAW_DEG`, `ATT_RATE_DPS`, `ADCS_MODE`.
  - *Comms:* `RF_CARRIER_LOCK`, `RF_SNR_DB`, `RF_TX_POWER_W`, `RF_DOPPLER_HZ`.
  - *Payload:* `PL_STATUS`, `PL_POWER_W`, `PL_STORAGE_MB`.
  *Priority:* High | *Related Module:* Telemetry Generator | *Phase:* 03 | *Acceptance:* Telemetry output contains all mnemonics with physically consistent correlated values.
- **FR-008:** The system shall stream telemetry frames via WebSockets to connected client consoles at an adjustable refresh rate ($1\ \text{Hz}$ to $10\ \text{Hz}$).
  *Priority:* High | *Related Module:* Telemetry Streamer | *Phase:* 04 | *Acceptance:* WebSocket client receives JSON telemetry frames with sequence numbers and simulation timestamps.
- **FR-009:** The system shall store telemetry samples in the persistent database with indexing on `(satellite_id, simulation_timestamp)` for historical inspection.
  *Priority:* High | *Related Module:* Persistence | *Phase:* 02 | *Acceptance:* Telemetry records can be retrieved across arbitrary historical time windows.

### 5.4 Category 4: Satellite Health Monitoring
- **FR-010:** The system shall evaluate incoming telemetry against a multi-tier threshold matrix (`NOMINAL`, `WARNING`, `CRITICAL`) for every subsystem parameter.
  *Priority:* High | *Related Module:* Health Monitor | *Phase:* 05 | *Acceptance:* Out-of-bounds telemetry automatically transitions parameter health state.
- **FR-011:** The system shall display aggregated subsystem health status (Green/Amber/Red) on the frontend dashboard with visual indicators and audible alert tickers.
  *Priority:* High | *Related Module:* Frontend Dashboard | *Phase:* 05 | *Acceptance:* Health status cards update dynamically upon threshold violation.
- **FR-012:** When an unrecovered critical parameter persists for longer than the grace threshold (e.g., $\text{SOC} < 25\%$ for $> 120\ \text{s}$), the system shall trigger an automatic autonomous safe-mode transition.
  *Priority:* High | *Related Module:* Digital Twin | *Phase:* 03 | *Acceptance:* Autonomous safe-mode transition occurs, shutting down payload loads.

### 5.5 Category 5: 3D Orbital Visualization
- **FR-013:** The frontend shall render an interactive 3D Earth globe with realistic day/night lighting terminator line and country outlines using Three.js / React Three Fiber.
  *Priority:* Medium | *Related Module:* 3D Orbit Viewer | *Phase:* 06 | *Acceptance:* Globe renders at $\ge 30\ \text{FPS}$ with correct sun angle illumination.
- **FR-014:** The system shall project the real-time calculated position, ground track trail, and future orbit trajectory ($\ge 1\ \text{orbit}$ ahead) for all three virtual satellites onto the 3D globe.
  *Priority:* Medium | *Related Module:* 3D Orbit Viewer | *Phase:* 06 | *Acceptance:* Satellite positions match backend orbital coordinates within $\pm 0.1^\circ$ latitude/longitude.
- **FR-015:** The 3D viewer shall display ground station locations and visual communication cones representing visibility limits ($\ge 10^\circ$ elevation angle).
  *Priority:* Low | *Related Module:* 3D Orbit Viewer | *Phase:* 06 | *Acceptance:* Station cones turn green during active contact passes.

### 5.6 Category 6: Scenario and Fault Injection
- **FR-016:** The system shall provide an executable catalog of the four mandatory fault scenarios (Solar Eclipse Power Crisis, Communication Blackout, Thermal Runaway, Conflicting Sensor Readings).
  *Priority:* High | *Related Module:* Fault Injector | *Phase:* 07 | *Acceptance:* Administrator can trigger any scenario with predictable initial conditions.
- **FR-017:** Fault injection shall support scheduled triggers based on either Mission Elapsed Time (MET) or state conditional triggers (e.g., trigger when entering eclipse).
  *Priority:* Medium | *Related Module:* Fault Injector | *Phase:* 07 | *Acceptance:* Faults activate precisely at the scheduled timestamp or condition.
- **FR-018:** The system shall record a high-priority `FAULT_INJECTED` mission event containing scenario metadata, targeted satellite, and timestamp.
  *Priority:* High | *Related Module:* Event Store | *Phase:* 07 | *Acceptance:* Mission log contains verifiable record of fault activation.

### 5.7 Category 7: Anomaly Detection and Explanation
- **FR-019:** When telemetry breaches critical limits or abnormal residual thresholds are detected, the system shall instantiate an `IncidentRecord` containing incident ID, satellite ID, detected symptoms, and timestamp.
  *Priority:* High | *Related Module:* Anomaly Investigator | *Phase:* 08 | *Acceptance:* New incident appears in Incident Center with associated telemetry snapshot.
- **FR-020:** The Anomaly Investigator shall evaluate competing root-cause hypotheses by assembling a deterministic evidence proof matrix listing supporting evidence and contradicting evidence.
  *Priority:* High | *Related Module:* Anomaly Investigator | *Phase:* 08 | *Acceptance:* Proof matrix accurately differentiates between genuine hardware faults and sensor SEUs.
- **FR-021:** The Anomaly Investigator shall output a calibrated confidence score ($0\%\dots 100\%$) and suggest appropriate recovery action procedures without stating certainty when evidence is insufficient.
  *Priority:* High | *Related Module:* Anomaly Investigator | *Phase:* 08 | *Acceptance:* Incomplete telemetry coverage produces lower confidence scores ($< 70\%$).

### 5.8 Category 8: Ground Station Communication
- **FR-022:** The system shall model a distributed network of three virtual ground stations:
  1. *GS-KOUROU* ($5.2^\circ\text{N}, 52.8^\circ\text{W}$)
  2. *GS-SVALBARD* ($78.2^\circ\text{N}, 15.6^\circ\text{E}$)
  3. *GS-CANBERRA* ($35.3^\circ\text{S}, 149.0^\circ\text{E}$).
  *Priority:* High | *Related Module:* Ground Station Scheduler | *Phase:* 09 | *Acceptance:* Station coordinates and elevation masks ($10^\circ$) configured.
- **FR-023:** The system shall compute upcoming contact pass windows (AOS time, LOS time, maximum elevation, duration) for each satellite over the next 24 simulation hours.
  *Priority:* High | *Related Module:* Ground Station Scheduler | *Phase:* 09 | *Acceptance:* Pass schedule correctly identifies valid geometric visibility windows.
- **FR-024:** The system shall simulate uplink/downlink RF link budget during ground passes, calculating path loss, Doppler frequency shift ($\Delta f$), and carrier lock state.
  *Priority:* Medium | *Related Module:* Ground Station Scheduler | *Phase:* 09 | *Acceptance:* Doppler curve peaks at closest approach (zenith elevation).

### 5.9 Category 9: Command Validation and Execution
- **FR-025:** Every operator-initiated telecommand shall follow a deterministic finite state lifecycle: `QUEUED` $\to$ `VALIDATING` $\to$ `APPROVED` or `REJECTED` $\to$ `EXECUTING` $\to$ `COMPLETED` or `FAILED`.
  *Priority:* High | *Related Module:* Command Validator | *Phase:* 10 | *Acceptance:* Command status transitions strictly match the state lifecycle.
- **FR-026:** The Command Validator shall enforce strict flight preconditions before approving any telecommand:
  - Check 1: Satellite must be in active ground station contact (elevation $\ge 10^\circ$, carrier lock active), unless command is flagged as a timed onboard macro.
  - Check 2: Battery $\text{SOC} \ge 35\%$ for non-essential payload activation commands.
  - Check 3: Satellite must not be in `EMERGENCY` or locked `SAFE_MODE` without explicit override token.
  *Priority:* High | *Related Module:* Command Validator | *Phase:* 10 | *Acceptance:* Commands violating preconditions are rejected with detailed failure reasons.
- **FR-027:** Upon approval and uplink execution, the simulation engine shall apply the commanded state modification (e.g., `SET_HEATER_OVERRIDE`, `SHED_PAYLOAD_LOAD`, `SET_ADCS_MODE`), record the result, and log the state delta.
  *Priority:* High | *Related Module:* Command Validator | *Phase:* 10 | *Acceptance:* Spacecraft state modifies precisely according to command parameters.

### 5.10 Category 10: Historical Events and Replay
- **FR-028:** The system shall persist an append-only event stream recording all significant mission events (`SIMULATION_STARTED`, `FAULT_INJECTED`, `THRESHOLD_BREACHED`, `INCIDENT_CREATED`, `COMMAND_QUEUED`, `COMMAND_EXECUTED`, `MODE_TRANSITION`).
  *Priority:* High | *Related Module:* Event Store | *Phase:* 11 | *Acceptance:* Events are recorded with monotonically increasing sequence IDs and UTC timestamps.
- **FR-029:** The system shall provide a Mission Time Machine playback controller allowing operators to seek, pause, and replay historical mission telemetry and incidents without corrupting the running simulation.
  *Priority:* High | *Related Module:* Replay Engine | *Phase:* 11 | *Acceptance:* Replay view streams historical frames while active simulation remains untouched or paused.
- **FR-030:** Replay mode shall clearly display a prominent visual `REPLAY MODE ACTIVE` indicator to prevent operator confusion with live telemetry.
  *Priority:* High | *Related Module:* Frontend Replay | *Phase:* 11 | *Acceptance:* Banner prominently displayed across entire console during replay.

### 5.11 Category 11: Mission Analytics and Reports
- **FR-031:** The system shall compute operational analytics across simulation runs, including total flight hours, eclipse duration percentage, mean battery depth of discharge, and telemetry loss count.
  *Priority:* Medium | *Related Module:* Analytics Service | *Phase:* 12 | *Acceptance:* Analytics metrics match computed mathematical aggregates.
- **FR-032:** The system shall generate downloadable structured incident debrief reports in JSON and printable HTML/PDF formats containing timeline, telemetry charts, proof matrix, and recovery verification.
  *Priority:* High | *Related Module:* Report Generator | *Phase:* 12 | *Acceptance:* Exported incident report includes all diagnostic proofs and operator commands.
- **FR-033:** The system shall provide a "What-If" recovery sandbox allowing operators to fork an incident state, test alternative recovery commands, and preview projected battery/thermal outcomes without affecting live state.
  *Priority:* Medium | *Related Module:* Sandbox Engine | *Phase:* 13 | *Acceptance:* Sandbox branches state and simulates projected 15-minute outcome.

### 5.12 Category 12: Configuration and User Permissions
- **FR-034:** The system shall provide an application settings API allowing dynamic configuration of CORS origins, simulation parameters, and persistence retention policies.
  *Priority:* Low | *Related Module:* Core Settings | *Phase:* 02 | *Acceptance:* Settings modifications persist across application restarts.
- **FR-035:** The system shall enforce role-based access rules (Mission Operator, Mission Administrator, Observer) rejecting unauthorized commands with HTTP 403.
  *Priority:* High | *Related Module:* API Security | *Phase:* 04 | *Acceptance:* Observer role commands fail validation with `ERR_ROLE_UNAUTHORIZED`.
- **FR-036:** The system shall provide automated database cleanup and compaction routines to prune historical high-frequency telemetry samples older than a configurable retention threshold while retaining incident windows.
  *Priority:* Low | *Related Module:* Persistence | *Phase:* 02 | *Acceptance:* Compaction prunes nominal telemetry while preserving incident time windows.

---

## 6. Non-Functional Requirements

| ID | Category | Requirement Statement | Target / Metric | Verification Method |
|---|---|---|---|---|
| **NFR-001** | **Performance** | Digital twin physics step calculation time per tick across all 3 virtual satellites. | $\le 25\ \text{ms}$ per simulation tick | Benchmark test suite |
| **NFR-002** | **Performance** | Telemetry WebSocket broadcast latency from engine calculation to client receipt. | $\le 100\ \text{ms}$ on local loopback | End-to-end latency measurement |
| **NFR-003** | **Performance** | 3D orbital globe rendering frame rate on standard integrated GPU (Intel Iris/UHD). | $\ge 30\ \text{FPS}$ sustained | Browser performance profiler |
| **NFR-004** | **Reliability** | Digital twin determinism: identical random seeds and scenario inputs must produce bitwise identical telemetry trajectories. | $100\%$ reproducible state trajectories | Automated regression test |
| **NFR-005** | **Availability** | Local backend server availability during continuous 4-hour simulation execution without memory leaks ($< 250\ \text{MB}$ heap growth). | Zero unhandled process crashes | 4-hour endurance test script |
| **NFR-006** | **Maintainability** | Code quality and test coverage across domain simulation logic. | Zero Ruff lint errors; $\ge 85\%$ test coverage on simulation core | Ruff & Pytest-cov |
| **NFR-007** | **Data Integrity** | SQLite transaction durability and write serialization under concurrent telemetry writes and command uplinks. | Zero database locked errors; SQLite WAL mode enabled | Concurrency stress test |
| **NFR-008** | **Security** | Telecommand uplink sanitization and injection prevention. | All command parameters strictly typed and validated via Pydantic v2 schemas | Security boundary fuzz testing |
| **NFR-009** | **Portability** | Full system execution without external cloud services or operating-system-specific compiled C extensions. | Pure Python + TypeScript running across Windows, macOS, and Linux | Cross-platform CI verification |
| **NFR-010** | **Usability** | Critical alarm discoverability: any out-of-bounds telemetry event must be visually prominent to operator. | Visible within $\le 1.0\ \text{s}$ of telemetry breach | UI visual review |
| **NFR-011** | **Simulation Integrity**| Simulation time isolation: historical event replay must not mutate or desynchronize active simulation clock. | Zero state side-effects on active mission during replay | Isolated state assertion tests |
| **NFR-012** | **Fault Tolerance** | Client disconnection recovery: if frontend browser tab is closed or disconnected, backend continues simulation seamlessly. | Backend state continues advancing uninterrupted | WebSocket disconnect test |

---

## 7. External Interface Requirements

### 7.1 Web Interface
- **Theme:** Dark aerospace operations console (`#080F1D` base background, `#111C2E` panel cards, `#18263B` elevated surfaces, `#42C8FF` cyan accents, `#729CFF` secondary blue accents).
- **Typography:** `Inter` or `Geist` for labels, `JetBrains Mono` for telemetry values, coordinates, and timestamps.
- **Safety Indicator:** High-contrast warning banner: `SIMULATION ENVIRONMENT ONLY — ALL SATELLITE DATA IS SYNTHETIC`.

### 7.2 REST API Specification (Planned Prefix: `/api/v1`)
- `GET /api/v1/health`: Operational health check. (Implemented in Phase 00)
- `GET /api/v1/missions`: Active mission metadata, elapsed time, and status.
- `GET /api/v1/satellites`: Fleet registry and summary health.
- `GET /api/v1/satellites/{id}`: Detailed spacecraft configuration, coordinates, and subsystem state.
- `GET /api/v1/satellites/{id}/telemetry`: Telemetry history query with time window filters.
- `GET /api/v1/incidents`: Incident log, open alarms, and diagnostic proof matrices.
- `POST /api/v1/incidents/{id}/acknowledge`: Operator incident acknowledgment.
- `POST /api/v1/commands`: Telecommand submission to the validation pipeline.
- `GET /api/v1/ground-stations`: Ground station network status and upcoming pass schedule.
- `POST /api/v1/scenarios/{id}/trigger`: Emergency fault scenario activation.
- `GET /api/v1/replays`: Historical mission logs and playback scrubbing sessions.
- `GET /api/v1/reports/{id}`: Generated incident debrief and post-mortem report.

### 7.3 Telemetry WebSocket Protocol
- **Endpoint:** `ws://127.0.0.1:8000/api/v1/telemetry/stream`
- **Envelope Structure:**
```json
{
  "event_type": "TELEMETRY_FRAME",
  "schema_version": "1.0",
  "satellite_id": "SAT-001",
  "sequence_number": 4092,
  "simulation_time": "2026-10-26T14:32:10.000Z",
  "recorded_at": "2026-10-26T21:15:02.128Z",
  "payload": {
    "subsystems": {
      "power": { "bus_v": 28.1, "solar_w": 412.5, "soc": 89.2, "batt_temp_c": 18.4 },
      "thermal": { "bus_temp_c": 22.1, "payload_temp_c": 28.6, "radio_temp_c": 34.1 },
      "adcs": { "mode": "SUN_POINTING", "roll_deg": 0.12, "pitch_deg": -0.05, "yaw_deg": 180.2 },
      "comms": { "carrier_lock": true, "snr_db": 13.8, "tx_power_w": 10.0 },
      "payload": { "status": "STANDBY", "power_w": 15.0, "storage_mb": 1240.5 }
    },
    "health_status": "NOMINAL"
  }
}
```

---

## 8. Data Requirements & Subsystem Units

All physical sensor parameters in OrbitOps are strictly typed with SI aerospace units:

| Subsystem | Parameter Mnemonic | Physical Meaning | Data Type | Nominal Range | Warning Limit | Unit |
|---|---|---|---|---|---|---|
| **Power** | `PWR_BUS_V` | Unregulated Power Bus Voltage | Float | $26.0\dots 30.0$ | $< 24.5$ or $> 32.0$ | Volts ($\text{V}$) |
| **Power** | `PWR_SOLAR_W` | Total Solar Array Generation | Float | $0.0\dots 600.0$ | N/A ($0$ in eclipse) | Watts ($\text{W}$) |
| **Power** | `BATT_SOC` | Battery State of Charge | Float | $40.0\dots 100.0$ | $< 35.0$ (Crit $< 20.0$) | Percent ($\%$) |
| **Power** | `BATT_CURRENT_A`| Battery Charge/Discharge Rate | Float | $-12.0\dots +15.0$ | $> +18.0$ or $< -15.0$ | Amperes ($\text{A}$) |
| **Thermal** | `TEMP_BUS_C` | Main Avionics Bus Temp | Float | $+5.0\dots +35.0$ | $< 0.0$ or $> +45.0$ | Celsius ($^\circ\text{C}$) |
| **Thermal** | `TEMP_PL_C` | Optical / Scientific Payload Temp | Float | $+10.0\dots +30.0$ | $< -5.0$ or $> +40.0$ | Celsius ($^\circ\text{C}$) |
| **Thermal** | `TEMP_RAD_C` | RF Power Amplifier Temp | Float | $+15.0\dots +50.0$ | $> +65.0$ (Crit $> 75.0$)| Celsius ($^\circ\text{C}$) |
| **ADCS** | `ATT_RATE_DPS` | Spacecraft Angular Rate | Float | $0.0\dots 0.5$ | $> 2.0$ (Tumble $> 5.0$) | $\text{deg/s}$ |
| **ADCS** | `ATT_ERROR_DEG` | Pointing Offset from Target | Float | $0.0\dots 1.0$ | $> 3.5$ | Degrees ($^\circ$) |
| **Comms** | `RF_SNR_DB` | Downlink Signal-to-Noise Ratio | Float | $10.0\dots 18.0$ | $< 6.0$ (Loss $< 2.0$) | Decibels ($\text{dB}$) |
| **Comms** | `RF_DOPPLER_HZ`| Carrier Doppler Frequency Shift | Float | $-45000\dots +45000$| N/A | Hertz ($\text{Hz}$) |
| **Payload** | `PL_STORAGE_MB`| Solid State Buffer Storage Used | Float | $0.0\dots 8192.0$ | $> 7500.0$ | Megabytes ($\text{MB}$) |

---

## 9. Use Case Specifications

### 9.1 UC-01: Monitor Live Fleet Telemetry
- **Primary Actor:** Mission Operator
- **Preconditions:** Backend simulation engine is active; WebSocket stream established.
- **Trigger:** Operator opens Mission Overview or Live Telemetry dashboard.
- **Main Success Flow:**
  1. Frontend establishes WebSocket connection to `/api/v1/telemetry/stream`.
  2. Backend streams live telemetry frames at $1\ \text{Hz}$ rate.
  3. Frontend renders real-time telemetry gauges (bus voltage, battery SOC, thermal readings, carrier lock).
  4. Operator views nominal status indicators with green operational badges.
- **Postconditions:** Operator maintains live situational awareness of all three satellites.

### 9.2 UC-02: Investigate Anomaly & Review Evidence Proofs
- **Primary Actor:** Mission Operator
- **Preconditions:** Anomaly detected; `IncidentRecord` created by Anomaly Investigator.
- **Trigger:** Warning banner pulses on dashboard or operator selects Incident Center.
- **Main Success Flow:**
  1. Operator clicks on the active incident (e.g., `INC-2026-004: Battery Rapid Depletion`).
  2. System displays incident overview: timestamp, affected satellite (`SAT-001`), and detected symptoms.
  3. System presents candidate root causes ranked by probability.
  4. System renders the Evidence Proof Matrix showing corroborating telemetry vs. counter-evidence.
  5. Operator evaluates the confidence score ($88\%$) and reads the suggested recovery action.
- **Alternative Flow (Sensor Latchup):**
  - If evidence reveals conflicting readings (gyro zero rate vs. horizon sensor rate spike), Investigator highlights sensor failure rather than physical spacecraft tumble.
- **Postconditions:** Operator reaches an evidence-backed diagnosis without guessing.

### 9.3 UC-03: Execute Precondition-Validated Recovery Command
- **Primary Actor:** Mission Operator
- **Preconditions:** Operator has identified recovery action; telecommand queue is open.
- **Trigger:** Operator submits telecommand (e.g., `CMD_SHED_PAYLOAD_LOAD`).
- **Main Success Flow:**
  1. Operator selects command from authorized operational catalog and inputs parameters.
  2. System assigns command ID and sets status to `QUEUED`.
  3. Command Validator evaluates preconditions:
     - Check: Is satellite currently within ground station line-of-sight? $\to$ Yes ($18.4^\circ$ elevation).
     - Check: Is ground transponder locked? $\to$ Yes.
     - Check: Is battery $\text{SOC} \ge 35\%$ for load switch? $\to$ Yes ($42\%$).
  4. Status transitions to `APPROVED` and subsequently `EXECUTING`.
  5. Simulation engine receives telecommand packet, powers down payload instrument load, and logs state transition.
  6. Status transitions to `COMPLETED`. Operator observes immediate drop in bus power load.
- **Exception Flow (Precondition Violation):**
  - If satellite is out-of-contact ($< 10^\circ$ elevation), Command Validator rejects command: status `REJECTED`, error `ERR_OUT_OF_CONTACT_WINDOW`. Operator is notified with next AOS countdown.
- **Postconditions:** Spacecraft state safely updated or rejected with auditable log record.

### 9.4 UC-04: Replay Historical Mission Incident (Time Machine)
- **Primary Actor:** Mission Operator / Observer
- **Preconditions:** Historical telemetry and events exist in the database.
- **Trigger:** User accesses the Mission Replay tab.
- **Main Success Flow:**
  1. User selects a recorded scenario or incident from the mission event log.
  2. System initializes Replay Engine in a read-only historical playback stream.
  3. High-visibility `REPLAY MODE ACTIVE` warning banner is displayed across the console.
  4. User drags the scrub bar back in time to $T - 5\ \text{min}$ before the anomaly occurred.
  5. Dashboard updates telemetry gauges, 3D orbit position, and alerts corresponding precisely to that historical timestamp.
  6. Active running simulation continues in background or remains safely paused without data corruption.
- **Postconditions:** Historical flight sequence evaluated without mutating active live mission state.

---

## 10. Verification & Quality Acceptance

| Acceptance Gate | Success Threshold | IA3 Phase Alignment |
|---|---|---|
| Functional Requirements Coverage | $100\%$ of FR-001 through FR-036 mapped to tests and architecture | Phase 01 |
| UML Diagram Conformance | All 5 diagrams syntactically valid and structurally aligned with SRS | Phase 01 |
| Automated Pytest Suite | $100\%$ pass rate across unit and smoke tests | Ongoing (Phases 00–15) |
| Python Code Quality | $0$ Ruff linting errors; $0$ formatting errors | Ongoing (Phases 00–15) |
| Frontend Type Safety | $0$ TypeScript errors in strict mode (`strict: true`) | Ongoing (Phases 00–15) |
| Frontend Linting | $0$ ESLint errors / warnings | Ongoing (Phases 00–15) |
| Production Build | Next.js production build compiles successfully | Ongoing (Phases 00–15) |
