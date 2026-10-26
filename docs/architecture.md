# OrbitOps — System Architecture Specification

**Document Version:** `1.1`
**Architecture Style:** Modular Monolith with Decoupled Presentation
**Target Milestone:** Software Engineering IA3

---

## 1. High-Level Context Diagram (C4 Level 1)

OrbitOps is structured as a client-server modular monolith running locally on a single developer workstation without distributed cloud dependencies.

```
+---------------------------------------------------------------------------------------+
|                                    USER CONTEXT                                       |
|                                                                                       |
|    +----------------------+   +----------------------+   +---------------------+      |
|    |   Mission Operator   |   |    Mission Admin     |   |      Observer       |      |
|    +----------+-----------+   +----------+-----------+   +----------+----------+      |
+---------------|--------------------------|--------------------------|-----------------+
                |                          |                          |
                +--------------------------+--------------------------+
                                           | HTTP (REST) / WebSockets (Port 3000 / 8000)
                                           v
+---------------------------------------------------------------------------------------+
|                         ORBITOPS MISSION CONTROL PLATFORM                             |
|                                                                                       |
|  +---------------------------------------------------------------------------------+  |
|  |                            FRONTEND WEB CONSOLE                                 |  |
|  |  - Next.js (App Router), React 19, Strict TypeScript, Tailwind CSS, Lucide      |  |
|  |  - Three.js / React Three Fiber (3D Earth & Orbit Path Visualization)           |  |
|  |  - Recharts (High-frequency multi-subsystem telemetry trend charts)              |  |
|  +---------------------------------------^-----------------------------------------+  |
|                                          | In-process IPC / Local Loopback            |
|  +---------------------------------------v-----------------------------------------+  |
|  |                          FASTAPI AUTHORITATIVE BACKEND                          |  |
|  |  - API Routing & WebSocket Session Manager (`/api/v1/...`)                       |  |
|  |  - Centralized Application Config & Explicit CORS Enforcer                      |  |
|  |  - Pydantic v2 DTO Serialization Layer                                          |  |
|  |  +---------------------------------------------------------------------------+  |  |
|  |  |                        CORE SIMULATION DOMAIN                             |  |  |
|  |  |  - Deterministic Digital Twin Simulation Engine (Euler / Runge-Kutta)      |  |  |
|  |  |  - Spacecraft Subsystem Models: Power, Thermal, ADCS, Comms, Payload      |  |  |
|  |  |  - Ground Station Visibility & Doppler Link Budget Calculator             |  |  |
|  |  |  - Anomaly Investigator & Evidence Matrix Evaluator                      |  |  |
|  |  |  - Safety-Critical Telecommand Precondition Validation Pipeline         |  |  |
|  |  |  - Append-Only Event Stream & Scrubbable Time Machine Replay Engine       |  |  |
|  |  +---------------------------------------------------------------------------+  |  |
|  |  +---------------------------------------------------------------------------+  |  |
|  |  |                     PERSISTENCE LAYER (SQLAlchemy 2.0)                    |  |  |
|  |  |  - SQLite 3 with Write-Ahead Logging (WAL) Mode                           |  |  |
|  |  |  - Tables: missions, satellites, telemetry_samples, commands, events     |  |  |
|  |  +---------------------------------------------------------------------------+  |  |
|  +---------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles & Invariants

1. **Authoritative Backend State:**
   The Python FastAPI engine is the **sole source of truth** for all satellite orbital positions, power generation curves, battery SOC, temperatures, and alarm states. The frontend console strictly formats and presents backend-owned state; it never synthesizes or manipulates telemetry client-side.
2. **Decoupled Simulation Domain:**
   All digital twin differential equations, subsystem models, and anomaly evaluation rules are written as pure Python domain classes without dependencies on FastAPI, HTTP requests, or database sessions. This ensures $100\%$ headless testability with sub-millisecond execution times.
3. **Strict Layer Separation:**
   - `schemas/`: Pydantic v2 Data Transfer Objects (DTOs) for request/response serialization.
   - `domain/`: Pure business and physical simulation logic (independent of ORM).
   - `models/`: SQLAlchemy 2.0 ORM models for database persistence.
   - `api/`: FastAPI route handlers, dependency injection, and WebSocket broadcasters.
   - `core/`: Application settings, logging, and security definitions.
4. **Temporal Dualism (Simulation Time vs. Recording Time):**
   Every stored metric and emitted frame maintains two distinct timestamps:
   - `sim_timestamp`: The satellite's internal Mission Elapsed Time (MET) or simulated orbital UTC.
   - `recorded_at`: The physical wall-clock UTC timestamp when the host computer processed the event.
5. **Replay Non-Interference:**
   The Mission Time Machine operates over an append-only event log. Replaying past telemetry streams or seeking historical anomalies is performed in an isolated read-only channel and never mutates the active running simulation.
6. **Precondition-Gated Telecommands:**
   Commands cannot jump directly to spacecraft bus execution. Every command must pass deterministic server-side gates (`QUEUED` $\to$ `VALIDATING` $\to$ `APPROVED`/`REJECTED` $\to$ `EXECUTING` $\to$ `COMPLETED`/`FAILED`).

---

## 3. Backend Architecture (Modular Monolith)

### 3.1 Subsystem Decomposition
```
backend/app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── health.py           # Health and status checks (Phase 00)
│   │   │   ├── missions.py         # Mission lifecycle & clock control
│   │   │   ├── satellites.py       # Satellite registry & state inspection
│   │   │   ├── telemetry.py        # Telemetry historical queries & stream
│   │   │   ├── incidents.py        # Anomaly records & evidence proofs
│   │   │   ├── commands.py         # Telecommand submission & queue
│   │   │   ├── ground_stations.py  # Pass schedules & link budgets
│   │   │   ├── scenarios.py        # Emergency scenario injection
│   │   │   ├── replays.py          # Mission Time Machine playback
│   │   │   └── reports.py          # Post-mortem debrief generation
│   │   └── router.py               # Master API router
├── core/
│   ├── config.py                   # Centralized Pydantic settings
│   └── logging.py                  # Structured console & file logging
├── domain/                         # Pure Simulation Domain (Zero I/O)
│   ├── clock.py                    # Simulation clock with warp & step
│   ├── orbit.py                    # Spherical Keplerian propagator & eclipse
│   ├── ground.py                   # Station visibility & Doppler math
│   ├── subsystems/
│   │   ├── base.py                 # Abstract subsystem interface
│   │   ├── power.py                # Solar array, battery SOC, bus voltage
│   │   ├── thermal.py              # Dissipation, radiation, heater loop
│   │   ├── adcs.py                 # Pointing modes, momentum, angular rate
│   │   ├── comms.py                # Carrier lock, SNR, transponder state
│   │   └── payload.py              # Instrument duty cycles & buffer
│   ├── anomaly/
│   │   ├── detector.py             # Threshold evaluator & residual checker
│   │   └── investigator.py         # Hypothesis ranker & evidence proof matrix
│   └── commands/
│       ├── validator.py            # Precondition flight safety rules
│       └── executor.py             # Spacecraft bus state modifier
├── models/                         # SQLAlchemy 2.0 Persistence
│   ├── base.py
│   ├── satellite.py
│   ├── telemetry.py
│   ├── incident.py
│   ├── command.py
│   └── event.py
└── schemas/                        # Pydantic v2 Request/Response DTOs
```

### 3.2 Simulation Loop Execution Pipeline
Each simulation tick executes through a deterministic pipeline:
$$\text{Clock Step } (\Delta t) \longrightarrow \text{Propagate Orbit} \longrightarrow \text{Compute Eclipse} \longrightarrow \text{Update Subsystems} \longrightarrow \text{Evaluate Anomaly} \longrightarrow \text{Process Commands} \longrightarrow \text{Broadcast Frame}$$

```
   +--------------------------------------------------------------+
   |                  SIMULATION TICK (dt = 1.0s)                 |
   +--------------------------------------------------------------+
                                  |
                                  v
   +--------------------------------------------------------------+
   | 1. Propagate Orbital Position & Eclipse Condition            |
   |    - Update Latitude, Longitude, Altitude                    |
   |    - Calculate Sun Vector: In Sunlight (1361 W/m2) or Eclipse |
   +--------------------------------------------------------------+
                                  |
                                  v
   +--------------------------------------------------------------+
   | 2. Integrated Subsystem Step                                 |
   |    - Power: Solar input -> Bus load balance -> Battery SOC   |
   |    - Thermal: Heat generation - Radiated loss -> Equilibrium |
   |    - ADCS: Pointing mode & attitude rate integration         |
   |    - Comms: Ground station visibility cone & Doppler shift   |
   |    - Payload: Instrument science collection & memory buffer  |
   +--------------------------------------------------------------+
                                  |
                                  v
   +--------------------------------------------------------------+
   | 3. Anomaly Detection & Hypothesis Evaluation                 |
   |    - Compare telemetry against threshold matrix              |
   |    - If breach: Generate Incident & Compile Evidence Matrix  |
   +--------------------------------------------------------------+
                                  |
                                  v
   +--------------------------------------------------------------+
   | 4. Command Pipeline & Telecommand Execution                  |
   |    - Advance APPROVED commands to EXECUTING                  |
   |    - Apply commanded state delta to target subsystem         |
   +--------------------------------------------------------------+
                                  |
                                  v
   +--------------------------------------------------------------+
   | 5. Telemetry Broadcast & State Persistence                   |
   |    - Publish JSON frame to active WebSocket sessions        |
   |    - Buffer sample into SQLite WAL write batch               |
   +--------------------------------------------------------------+
```

---

## 4. Frontend Architecture (Next.js App Router)

The frontend console is built with modular components following a dark aerospace design system.

### 4.1 Component Tree & Data Distribution
```
RootLayout (app/layout.tsx)
└── ConsoleShell (app/page.tsx)
    ├── Sidebar (Navigation & Phase Tracker)
    ├── Header (Simulation Warning Banner, UTC Clock, Mission Status)
    └── Main Content Router
        ├── OverviewDashboard (Fleet Health Matrix & Innovations)
        ├── OrbitViewer3D (Three.js Earth Globe, Orbit Cones) [Phase 06]
        ├── TelemetryConsole (Gauges, Recharts Real-Time Graphs) [Phase 05]
        ├── IncidentCenter (Diagnostic Proof Matrix & Hypotheses) [Phase 08]
        ├── CommandConsole (Precondition Pipeline & Uplink Queue) [Phase 10]
        ├── GroundPassScheduler (AOS/LOS Trackers, Elevation) [Phase 09]
        └── MissionTimeMachine (Timeline Scrubber & Replay) [Phase 11]
```

### 4.2 State Management Strategy
1. **Live Telemetry Store:** Custom React Hook (`useTelemetryStream`) maintaining a high-performance in-memory ring buffer (last 300 samples per parameter) for smooth 60fps charting without triggering React root re-renders.
2. **Incident & Alert Store:** React Context (`IncidentContext`) tracking active open alarms, unacknowledged warnings, and diagnostic proof matrices.
3. **Command Queue State:** Synchronized via REST polling and WebSocket event confirmations to reflect server-authoritative command statuses.

---

## 5. Persistence Layer & Concurrency Model

### 5.1 SQLite Configuration
- **Journal Mode:** Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
- **Synchronous Flag:** `PRAGMA synchronous=NORMAL;` (delivers optimal performance with reliable crash durability).
- **Busy Timeout:** `PRAGMA busy_timeout=5000;` (prevents database locking contention between background telemetry writers and operator command transactions).

### 5.2 Telemetry Retention & Compaction Strategy
- High-frequency $1\ \text{Hz}$ nominal telemetry is retained in full resolution for 4 hours of mission time.
- Beyond 4 hours, non-incident nominal telemetry is downsampled to $0.1\ \text{Hz}$ (1 sample every 10 seconds).
- Telemetry associated with an active incident window ($T - 10\ \text{min}$ to $T + 15\ \text{min}$) is permanently locked and protected from compaction.

---

## 6. Failure Handling & Resilience

| Failure Mode | Architectural Containment Strategy |
|---|---|
| **WebSocket Connection Drop** | Frontend automatically attempts exponential backoff reconnection ($1\text{s}, 2\text{s}, 4\text{s}, 8\text{s}$ up to $15\text{s}$). Dashboard displays amber `STREAM INTERRUPTED` pill without freezing UI. |
| **Backend Process Termination** | SQLite WAL file guarantees zero corruption of committed events. Upon restart, simulation clock restores from the latest `SimulationCheckpoint`. |
| **Invalid Operator Input** | Pydantic v2 schemas reject malformed commands at the API boundary with structured `HTTP 422` error details before reaching domain logic. |
| **Unrecoverable Spacecraft Anomaly** | If battery drops below critical threshold ($< 20\%$), autonomous hardware interlock forces `SAFE_MODE`, cutting all payload loads to preserve spacecraft bus survival. |
| **WebGL Context Loss** | Three.js orbital viewer catches context loss events and renders a graceful 2D ground-track fallback projection map. |

---

## 7. Local Workstation Deployment Topology

The entire system runs as two local development processes:
1. **Backend Service:** Python 3.12 process managed by `uvicorn` on `http://127.0.0.1:8000`.
2. **Frontend Console:** Next.js Node.js server on `http://localhost:3000`.

Communication occurs over localhost TCP loopback (`127.0.0.1`), ensuring zero exposure to external networks and zero cloud subscription dependencies.
