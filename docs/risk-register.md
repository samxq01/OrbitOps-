# OrbitOps — Risk Register & Architecture Decision Records (ADR)

**Milestone:** Phase 01 (Baseline Specification)
**Target Submission:** Software Engineering IA3

---

## 1. Risk Register

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy | Detection / Verification Method |
|---|---|---|---|---|---|
| **RSK-01** | **Inconsistent Simulated Telemetry:** Subsystem values mathematically contradict (e.g., solar arrays generating power during eclipse or battery charging with negative current). | Low | High | Enforce strict lumped-parameter physics equations in `backend/domain/subsystems/` where solar flux is an explicit multiplier on generation. | Automated unit tests asserting $P_{\text{solar}} = 0$ in eclipse and $dE/dt < 0$ when $P_{\text{load}} > P_{\text{solar}}$. |
| **RSK-02** | **Simulation Time Drift:** Wall-clock delays causing simulation tick desynchronization between backend engine and client visualizer. | Medium | Medium | Decouple simulation clock (`sim_time`) from wall-clock time; pass explicit sequence IDs and simulation timestamps in all WebSocket frames. | Drift check comparing `sim_time` progression against tick counter. |
| **RSK-03** | **SQLite Concurrent Write Contention:** Concurrent high-frequency telemetry writes and operator telecommand submissions causing `sqlite3.OperationalError: database is locked`. | Medium | High | Enable Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), configure 5000ms busy timeout, and batch telemetry inserts in a dedicated background task. | High-frequency stress test writing 50 samples/sec while executing commands. |
| **RSK-04** | **WebSocket Disconnection Churn:** Network interruptions or browser tab sleep causing stale telemetry gauges and unhandled exceptions. | High | Medium | Implement automatic exponential backoff reconnection in frontend client (`useTelemetryStream`) with amber connection status indicators. | Intentional socket termination test verifying auto-reconnection within 3 seconds. |
| **RSK-05** | **3D Rendering Performance Degradation:** High GPU draw call overhead in Three.js causing browser lag ($< 20\ \text{FPS}$) on entry-level student laptops. | Medium | Medium | Optimize 3D assets: use low-polygon Earth sphere ($\le 64$ segments), compressed textures ($\le 2048\times 1024$), and simplified orbit line geometries. | FPS counter benchmark asserting $\ge 30\ \text{FPS}$ sustained. |
| **RSK-06** | **Unsafe Spacecraft State Transitions:** Invalid or unvalidated telecommands forcing spacecraft into destructive configurations (e.g., high-power payload active in critical safe mode). | Low | Critical | Multi-stage command validation pipeline enforcing flight preconditions before approval; autonomous hardware interlocks overriding software commands. | Precondition rejection unit tests (`TC-23`, `TC-24`). |
| **RSK-07** | **Replay State Pollution:** Historical playback seeking altering current live simulation state or corrupting active mission telemetry. | Low | High | Strict memory isolation: Replay Engine operates on a read-only stream from the event database; active simulation engine runs in a separate execution context. | Replay isolation assertion test (`TC-25`). |
| **RSK-08** | **Unrealistic Physics Claims:** Overpromising orbital fidelity (claiming J2 perturbations or full flexible-body dynamics) leading to academic criticism. | Low | Medium | Explicitly label all equations as educational first-order lumped approximations in SRS, code documentation, and UI banners. | Peer documentation review. |
| **RSK-09** | **Browser Automation Sandbox Restrictions:** Headless Playwright drivers failing to download in offline or restricted sandbox environments. | High | Low | Retain primary test verification through automated Pytest, strict TypeScript typechecking, and Next.js static production builds; document browser limitations transparently. | Execution report transparency. |
| **RSK-10** | **Scope Expansion (Feature Creep):** Attempting to implement advanced features before core digital twin foundation is stable. | Medium | High | Strictly follow the 16-phase sequential roadmap with verification gates and user authorization before advancing between phases. | Phase commit gate enforcement in `AGENTS.md`. |

---

## 2. Architecture Decision Records (ADR)

### ADR-01: Modular Monolith vs. Microservices Architecture
- **Context:** An operations console requires handling real-time telemetry streaming, orbital mechanics calculations, incident diagnosis, and database persistence.
- **Decision:** Adopt a **Modular Monolith** with a unified Python FastAPI backend and a Next.js App Router frontend.
- **Rejected Alternative:** Microservices architecture (separate services for Telemetry, Orbit, Command, and Persistence communicating over RabbitMQ or gRPC).
- **Rationale:** Microservices introduce excessive operational complexity (Docker Compose, networking orchestration, distributed tracing) unsuitable for local student laptop execution. The modular monolith preserves strict layer boundaries via Python packages (`domain/`, `models/`, `api/`) while executing in a single, predictable OS process.

### ADR-02: SQLite in WAL Mode vs. PostgreSQL / Redis
- **Context:** The system needs persistent storage for satellite configurations, mission events, and high-frequency telemetry samples.
- **Decision:** Use **SQLite 3** configured with Write-Ahead Logging (`WAL`) mode and SQLAlchemy 2.0.
- **Rejected Alternative:** PostgreSQL with Redis cache.
- **Rationale:** SQLite requires zero external server setup, runs out of the box on Windows, macOS, and Linux, and stores all mission state in a single portable `.sqlite3` file. In WAL mode, SQLite supports concurrent read operations without blocking background write batches, comfortably satisfying our 3 samples/sec workload.

### ADR-03: Single Authoritative Backend State vs. Client-Side Telemetry Synthesis
- **Context:** Deciding where simulation differential equations and orbital ephemeris calculations should execute.
- **Decision:** The **Python FastAPI backend is the sole authoritative state source**. The Next.js frontend is strictly a presentation and command submission console.
- **Rejected Alternative:** Generating or interpolating simulated telemetry directly in the browser via JavaScript.
- **Rationale:** Allows full headless automated testing of the digital twin engine without browser dependencies, guarantees identical telemetry for multiple connected operators, and enforces true mission operations architecture.

### ADR-04: Coupled First-Order Physics vs. High-Fidelity Spacecraft Propagators (SGP4/SPICE)
- **Context:** Selecting the mathematical modeling approach for spacecraft subsystems and orbital paths.
- **Decision:** Implement **coupled first-order lumped-parameter differential equations** and simplified circular Keplerian orbital propagation.
- **Rejected Alternative:** Integrating NASA SPICE kernels or SGP4 NORAD two-line element propagators.
- **Rationale:** High-fidelity orbital propagators add external C-binding dependencies (`sgp4`, `cspice`) that introduce cross-platform installation failures on student laptops. Furthermore, educational mission operations requires reproducible, controllable scenarios (e.g., triggering eclipses on demand) which is straightforward with deterministic parametric models.

### ADR-05: Append-Only Event Store for Mission Time Machine Replay
- **Context:** Enabling operators to inspect historical anomalies and replay recorded telemetry without state corruption.
- **Decision:** Implement an **append-only event store** (`mission_events` table) with monotonic sequence numbers.
- **Rejected Alternative:** Overwriting current state with historical snapshots.
- **Rationale:** Overwriting active state risks irrecoverable corruption if a user scrubs backward. An append-only stream allows the Replay Engine to read historical frames non-destructively while the active simulation continues uninterrupted or remains safely paused.
