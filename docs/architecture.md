# OrbitOps — System Architecture

## 1. Architectural Philosophy: The Modular Monolith

OrbitOps is structured as a **modular monolith**. It avoids distributed microservice sprawl, container orchestration complexity, and cloud dependencies so it can run reliably on a standard student laptop while preserving high cohesion, low coupling, and enterprise-grade boundaries.

```
+------------------------------------------------------------------------+
|                              FRONTEND                                  |
|            Next.js App Router | React | Tailwind CSS | Three.js        |
|                                                                        |
|  +--------------------+  +--------------------+  +------------------+  |
|  |  Mission Overview  |  | Orbital 3D Viewer  |  |  Command Console |  |
|  +--------------------+  +--------------------+  +------------------+  |
|  +--------------------+  +--------------------+  +------------------+  |
|  |  Live Telemetry    |  | Incident Center    |  |  Scenario Studio |  |
|  +--------------------+  +--------------------+  +------------------+  |
+-----------------------------------^------------------------------------+
                                    | HTTP / REST + WebSockets
+-----------------------------------v------------------------------------+
|                              BACKEND                                   |
|                FastAPI | Pydantic v2 | SQLAlchemy 2.0                  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Mission Simulation Engine                       |  |
|  |  - High-frequency numerical integration (Euler/RK4)              |  |
|  |  - Physics Subsystem models: Power, Thermal, ADCS, Comms, Payload|  |
|  +------------------------------------------------------------------+  |
|                                    |                                   |
|  +---------------------------------v--------------------------------+  |
|  |                  Incident & Evidence Evaluator                   |  |
|  |  - Rule-based anomaly matcher with supporting/counter evidence   |  |
|  +------------------------------------------------------------------+  |
|                                    |                                   |
|  +---------------------------------v--------------------------------+  |
|  |                  Safe Command Validation Engine                  |  |
|  |  - Precondition gates: contact windows, power margin, interlocks |  |
|  +------------------------------------------------------------------+  |
|                                    |                                   |
|  +---------------------------------v--------------------------------+  |
|  |                     Persistence & Replay                         |  |
|  |  - SQLite (WAL mode) with append-only event recording            |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
```

---

## 2. Core Architectural Rules

1. **Authoritative Backend State:**
   The backend is the sole source of truth for spacecraft coordinates, subsystem parameters, flight modes, and incident triggers. The frontend never synthesizes or fabricates simulated values.

2. **Strict Separation of Concerns:**
   - `schemas/`: Pydantic data exchange models (DTOs) for request/response serialization.
   - `models/`: SQLAlchemy ORM models for database persistence.
   - `core/`: Application settings, logging, and security configurations.
   - `simulation/`: Pure domain logic containing the physical and logical equations of the digital twin.
   - `api/`: REST routing, dependency injection, and WebSocket handlers.

3. **Deterministic & Replay-Safe:**
   The simulation clock is decoupled from wall-clock time, enabling pause, step, fast-forward, and historical mission replay without mutating live operational state.
