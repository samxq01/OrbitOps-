# ORBITOPS — AGENTS ENGINEERING CONTRACT

**Project:** OrbitOps — Evidence-Driven Satellite Mission Control & Digital Twin Simulator  
**Tagline:** Observe. Diagnose. Decide. Recover.  
**Academic Target:** Software Engineering IA3  
**GitHub Repository:** `https://github.com/samxq01/OrbitOps-.git`  
**Primary Branch:** `main`  
**Development Branch:** `feature/orbitops-ia3`

---

## 1. Project Vision & Mission

OrbitOps is an educational, ground-control mission operations console and digital twin simulator. It provides operators and software engineering students with an authentic mission operations environment to monitor virtual spacecraft, identify anomalous telemetry symptoms, deduce root causes through evidence proofs, execute verified recovery telecommands, and replay historical incidents.

---

## 2. Strict Simulation-Only Safety Boundaries

> [!CRITICAL]
> OrbitOps is an educational simulation system.
> 1. All satellite coordinates, orbital propagation, power bus voltages, battery states, thermal dissipation, attitude quaternions, RF link budgets, telecommands, and fault scenarios are purely simulated.
> 2. Simulated data MUST NEVER be represented or claimed as real spacecraft telemetry.
> 3. The simulator runs fully locally on a student laptop. No external hardware, satellite networks, or live orbital ground stations are connected.

---

## 3. Technology Stack & Toolchain Standards

| Layer | Technologies | Standards & Constraints |
|---|---|---|
| **Frontend** | Next.js (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, Three.js / React Three Fiber | Strict TypeScript (`strict: true`), dark aerospace theme (`#080F1D` background), zero synthetic telemetry fabricated on frontend. |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite (WAL mode), WebSockets | Centralized settings, explicit CORS (no wildcards), typed schemas, single authoritative state source. |
| **Package Management** | `uv` (Python), `npm` (Node.js) | Lockfiles committed (`uv.lock`, `package-lock.json`), no unregistered ad-hoc packages. |
| **Quality & Linting** | Ruff (Python), ESLint (TypeScript/React), Pytest (Python tests), Playwright (E2E) | Zero lint warnings/errors permitted, 100% test pass rate required before commits. |

---

## 4. Architectural Rules & Single Source of Truth

1. **Authoritative Backend State:**
   The Python FastAPI simulation engine is the **sole authoritative source** of all satellite physical states, telemetry measurements, ground passes, anomaly detections, and command logs. The frontend console is strictly a presentation and command submission interface; it must NEVER invent, synthesize, or manipulate telemetry client-side.

2. **Folder Ownership & Monorepo Structure:**
   - `/backend/app/core/`: Configuration, application lifecycle, security settings.
   - `/backend/app/schemas/`: Typed Pydantic data exchange models.
   - `/backend/app/models/`: SQLAlchemy ORM database models.
   - `/backend/app/api/`: REST routing, dependencies, and WebSocket handlers (`/api/v1/...`).
   - `/backend/app/simulation/`: Pure digital twin differential equations and tick engine.
   - `/backend/tests/`: Automated pytest unit, smoke, and integration test suites.
   - `/frontend/src/app/`: Next.js App Router layouts, routes, and global styles.
   - `/frontend/src/components/`: Modular React components following the dark aerospace design system.
   - `/frontend/src/lib/`: API clients, WebSocket connection handlers, and formatters.
   - `/docs/`: Architectural specifications, SRS documentation, UML diagrams, setup guides.
   - `/scripts/`: Cross-platform local automation scripts.

3. **API & Naming Conventions:**
   - REST endpoints: lower-case with hyphens (`/api/v1/health`, `/api/v1/satellites/{id}/telemetry`).
   - Response structures: Snake_case JSON keys with explicit Pydantic schemas.
   - Telemetry parameters: uppercase subsystem mnemonic identifiers (e.g., `PWR_BUS_V`, `BATT_SOC`, `TEMP_PL_C`, `RF_SNR_DB`).

---

## 5. Command Validation Pipeline

Every spacecraft telecommand uplink must traverse deterministic gates:
$$\text{QUEUED} \longrightarrow \text{VALIDATING} \longrightarrow \text{APPROVED / REJECTED} \longrightarrow \text{EXECUTING} \longrightarrow \text{COMPLETED / FAILED}$$

Commands violating preconditions (e.g., commanding payload activation while in eclipse with battery SOC < 40%, or sending commands outside ground station line-of-sight windows) must be rejected with explicit error codes.

---

## 6. Git Workflow & Phase Commit Conventions

Every engineering task is strictly assigned to one of the 16 phases.
1. **Branch Rule:** All development happens on `feature/orbitops-ia3`. Never commit directly to `main` without authorization.
2. **One Verified Feature Commit per Phase:**
   Format: `feat(phase-XX): concise description`
3. **Commit Gate Checklist:**
   - Run backend tests: `uv run pytest` (must pass 100%)
   - Run backend lint: `uv run ruff check .` (zero errors)
   - Run frontend typecheck: `npm run typecheck` (zero TypeScript errors)
   - Run frontend lint: `npm run lint` (zero ESLint errors)
   - Run frontend build: `npm run build` (successful compilation)
   - Review git status: `git diff --check` (no whitespace/syntax issues, no credentials committed)
4. **Permanent Integrity Invariants:**
   - **Never skip validation:** Every check must actually run.
   - **Never claim unexecuted tests passed:** Always inspect real output.
   - **Never proceed automatically to the next phase:** Stop, report actual commit SHA and push status, and await explicit user instruction.

---

## 7. Master 16-Phase Execution Roadmap

- **Phase 00:** Repository Initialization and Foundation (`feat(phase-00): bootstrap OrbitOps monorepo`)
- **Phase 01:** Requirements, SRS, Architecture, UML Baseline (`feat(phase-01): define requirements and architecture`)
- **Phase 02:** Satellite Domain Models and Database (`feat(phase-02): implement satellite domain and persistence`)
- **Phase 03:** Deterministic Satellite Digital Twin Engine (`feat(phase-03): build deterministic satellite simulator`)
- **Phase 04:** REST APIs and Real-Time Telemetry Streaming (`feat(phase-04): implement telemetry APIs and streaming`)
- **Phase 05:** Professional Mission Control Dashboard (`feat(phase-05): build mission control dashboard`)
- **Phase 06:** Interactive 3D Earth and Orbital Visualization (`feat(phase-06): implement orbital visualization`)
- **Phase 07:** Fault Injection and Emergency Scenarios (`feat(phase-07): implement mission fault scenarios`)
- **Phase 08:** Evidence-Based Anomaly Investigator (`feat(phase-08): add evidence-based anomaly diagnosis`)
- **Phase 09:** Ground Station Communication and Contact Windows (`feat(phase-09): simulate ground station communication`)
- **Phase 10:** Safety-Aware Command Console (`feat(phase-10): implement safe satellite commands`)
- **Phase 11:** Mission Time Machine and Event Replay (`feat(phase-11): implement mission replay`)
- **Phase 12:** Reports, Analytics, and Export (`feat(phase-12): add analytics and incident reports`)
- **Phase 13:** What-If Recovery Simulation (`feat(phase-13): implement what-if recovery simulation`)
- **Phase 14:** Full Integration, Security, and Testing (`feat(phase-14): verify integrated mission operations`)
- **Phase 15:** Final Documentation, IA3 Deliverables, and Release (`feat(phase-15): finalize OrbitOps IA3 release`)
