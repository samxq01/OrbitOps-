# OrbitOps Backend API

FastAPI service powering the OrbitOps Satellite Mission Control & Digital Twin Simulator.

## Architecture

- **Framework**: FastAPI (Python 3.12)
- **Settings**: Pydantic Settings (`app.core.config`)
- **ORM / Persistence**: SQLAlchemy 2.0 Declarative ORM with SQLite (WAL mode, foreign key enforcement)
- **Migrations**: Alembic (`alembic/`)
- **Domain Layer**: Pure typed domain models, enums, constants, exceptions (`app.domain/`)
- **Repositories**: Isolated data access patterns for missions, satellites, subsystems, telemetry, incidents, commands, events (`app.repositories/`)
- **Validation**: Pydantic v2
- **Testing**: Pytest & HTTPX
- **Code Quality**: Ruff

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Sync dependencies using uv
uv sync --extra dev

# Run database migrations (creates 12 tables)
uv run alembic upgrade head

# Seed initial virtual constellation (SAT-001 Alpha, SAT-002 Beta, SAT-003 Gamma)
uv run python -m app.cli.seed

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run full test suite (23 unit, migration, domain, and persistence tests)
uv run pytest -v

# Run lint checks
uv run ruff check .
```

## Database Architecture (Phase 02)

12 core operational tables managed under SQLAlchemy 2.0 and Alembic:
1. `missions`: Active mission definition and time warp rate.
2. `satellites`: Virtual spacecraft catalog (`SAT-001`, `SAT-002`, `SAT-003`).
3. `satellite_subsystems`: POWER, THERMAL, ADCS, COMMS, PAYLOAD per spacecraft.
4. `telemetry_samples`: Time-series telemetry snapshots with composite indexing.
5. `fault_scenarios`: SCN-01 through SCN-04 emergency scenarios.
6. `incident_records`: Detected anomalies and diagnosis states.
7. `incident_evidence`: Evidence proof evaluations.
8. `ground_stations`: Ground station network (Kourou, Svalbard, Canberra).
9. `contact_windows`: Ground station line-of-sight pass windows.
10. `satellite_commands`: Command audit pipeline.
11. `mission_events`: Append-only monotonic event log.
12. `simulation_checkpoints`: State recovery snapshots.

## Endpoints

- `GET /api/v1/health` - Service health status, environment, version, uptime, and simulation mode.
