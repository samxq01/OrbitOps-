# OrbitOps

**Evidence-Driven Satellite Mission Control & Digital Twin Simulator**

> **Tagline:** Observe. Diagnose. Decide. Recover.
> **Course:** Software Engineering (IA3 Project)
> **Status:** Phase 03 — Deterministic Satellite Digital Twin Engine

---

## 1. Project Overview

**OrbitOps** is a professional-grade educational satellite mission operations simulator. It provides operators, software engineering students, and aerospace enthusiasts with an authentic mission operations console for managing virtual spacecraft constellations.

Unlike traditional satellite trackers that present disconnected, synthetic numbers, OrbitOps introduces a **Causal Satellite Digital Twin**. Physical subsystems—Power, Thermal, Attitude Determination & Control (ADCS), Communications, and Scientific Payloads—are tightly coupled through deterministic physics models. When anomalies occur, operators utilize an **Evidence-Based Anomaly Investigator** to evaluate competing root-cause hypotheses using verifiable telemetry proofs before executing pre-validated recovery telecommands.

> [!NOTE]
> **Simulation Boundary:** OrbitOps is strictly a training simulator running locally on a student laptop. All spacecraft telemetry, orbital dynamics, ground contact windows, and emergency incidents are simulated.

---

## 2. Core Innovations Planned

- **Innovation A — Causal Satellite Digital Twin:** Coupled subsystem physics where solar exposure, battery charging, payload heat dissipation, and attitude adjustments directly influence one another.
- **Innovation B — Evidence-Based Fault Investigation:** Transparent diagnosis engine comparing observed symptoms against candidate root causes with supporting vs. refuting evidence matrices.
- **Innovation C — Safe Satellite Commands:** Multi-stage validation pipeline (`QUEUED` &rarr; `VALIDATING` &rarr; `APPROVED` &rarr; `EXECUTING`) enforcing contact window, power margin, and interlock rules.
- **Innovation D — Mission Time Machine & Replay:** Scrubbable mission event timeline allowing operators to replay historical incidents and evaluate alternative recovery decisions safely.
- **Innovation E — Reproducible Emergency Scenarios:** Deterministic failure scenarios (Solar Eclipse Crisis, RF Blackout, Thermal Runaway, Conflicting Sensors).

---

## 3. Technology Stack

- **Frontend:** Next.js (App Router), TypeScript (Strict Mode), React 19, Tailwind CSS, Lucide Icons, Three.js / React Three Fiber, Recharts.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Declarative ORM), Alembic migrations, SQLite (WAL mode, foreign key enforcement), WebSockets.
- **Package Management:** `uv` (Fast Python package manager) and `npm` (Node.js).
- **Tooling & Quality:** Ruff, ESLint, Pytest, Playwright.

---

## 4. Repository Structure

```
OrbitOps/
├── backend/                  # FastAPI Authoritative Backend Service & Persistence
│   ├── alembic/              # Alembic Schema Migrations (12 Core Tables)
│   ├── app/
│   │   ├── api/v1/           # API Routers & Endpoints (/api/v1/health)
│   │   ├── cli/              # Management Commands (Idempotent DB Seeder)
│   │   ├── core/             # Configuration & Lifecycle Settings
│   │   ├── db/               # Centralized Engine, Session Local, Pragmas & Bootstrap
│   │   ├── domain/           # Pure Domain Enums, Constants & Custom Exceptions
│   │   ├── models/           # SQLAlchemy 2.0 Typed Declarative ORM Models
│   │   ├── repositories/     # Data Access Repositories (Satellite, Telemetry, Events...)
│   │   ├── schemas/          # Pydantic v2 Serialization DTOs
│   │   ├── simulation/       # Pure Digital Twin Physics Engine & Orchestrator
│   │   └── main.py           # Application Entrypoint
│   ├── tests/                # Automated Pytest Suite (Unit, Domain, Physics, Snapshots, Integration)
│   ├── alembic.ini           # Alembic Database Migration Configuration
│   ├── pyproject.toml        # Python Dependencies & Ruff Configuration
│   └── uv.lock               # Deterministic Python Lockfile
├── frontend/                 # Next.js App Router Frontend
│   ├── src/
│   │   ├── app/              # Layouts, Global CSS, and Route Handlers
│   │   ├── components/       # Dark Aerospace UI Shell & Widgets
│   │   └── lib/              # API Client & Telemetry Utilities
│   ├── package.json          # Node Dependencies & Build Scripts
│   ├── tsconfig.json         # Strict TypeScript Configuration
│   └── package-lock.json     # Node Dependency Lockfile
├── docs/                     # Architectural, SRS, Data Model, and Roadmap Docs
│   ├── overview.md           # Project Overview & Innovations
│   ├── architecture.md       # Modular Monolith & Subsystem Design
│   ├── simulation-spec.md    # Coupled Spacecraft Physics & Update Order
│   ├── data-model.md         # 12-Table SQLite Schema & Integrity Constraints
│   ├── srs.md                # Software Requirements Specification (SRS)
│   ├── requirements-traceability.md # Requirements Traceability Matrix (RTM)
│   ├── test-plan.md          # Master Test Plan & Verification Catalog
│   ├── setup.md              # Local Setup Instructions
│   └── roadmap.md            # 16-Phase Execution Roadmap
├── scripts/                  # Cross-Platform Local Scripts
│   ├── dev.ps1               # Local Development Launcher
│   └── verify.ps1            # Full Quality Verification Suite
├── .editorconfig             # Standardized Code Formatting Rules
├── .env.example              # Safe Configuration Template
├── .gitignore                # Comprehensive Ignore Rules
├── AGENTS.md                 # Engineering Invariants & AI Pair Programming Contract
└── README.md                 # Root Documentation
```

---

## 5. Prerequisites

- **Node.js:** `v20+` (Tested on `v24.14.x`)
- **Python:** `3.11+` (Tested on `3.12.10`)
- **uv:** `uv --version` (Tested on `0.11.x`)
- **Git:** Git configured with your user details

---

## 6. Installation & Quick Start

### 1. Clone & Checkout Development Branch

```bash
git clone https://github.com/samxq01/OrbitOps-.git
cd OrbitOps-
git checkout feature/orbitops-ia3
```

### 2. Run Backend API & Database Setup

```bash
cd backend
uv sync --extra dev

# Run Alembic migrations (creates 12 relational tables)
uv run alembic upgrade head

# Seed virtual satellites (SAT-001 Alpha, SAT-002 Beta, SAT-003 Gamma)
uv run python -m app.cli.seed

# Run standalone digital twin simulation demonstration
uv run python -m app.simulation.demo

# Start development API server
uv run uvicorn app.main:app --reload --port 8000
```
- API Health Status: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run Frontend Console

```bash
cd frontend
npm install
npm run dev
```
- Mission Operations Console: [http://localhost:3000](http://localhost:3000)

---

## 7. Testing & Quality Verification

Run all test suites locally:

### Backend Tests & Linting
```bash
cd backend
uv run pytest -v       # Run automated unit, physics, snapshot & integration tests (199 passed)
uv run ruff check .    # Run Python code quality linting (0 errors)
uv run ruff format --check . # Run formatting checks (100% formatted)
```

### Frontend Typecheck, Linting & Build
```bash
cd frontend
npm run typecheck      # Run strict TypeScript compiler verification
npm run lint           # Run ESLint checks
npm run build          # Run Next.js production bundle compilation
```

### Full Verification Script
```powershell
.\scripts\verify.ps1
```

---

## 8. Current Implementation Phase

**Current Phase:** `Phase 03 — Deterministic Satellite Digital Twin Engine`
**Git Checkpoint:** `feat(phase-03): build deterministic satellite simulator`
**Active Development Branch:** `feature/orbitops-ia3`
