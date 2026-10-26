# OrbitOps Backend API

FastAPI service powering the OrbitOps Satellite Mission Control & Digital Twin Simulator.

## Architecture

- **Framework**: FastAPI (Python 3.12)
- **Settings**: Pydantic Settings
- **ORM / Persistence**: SQLAlchemy 2.x with SQLite
- **Validation**: Pydantic v2
- **Testing**: Pytest & HTTPX
- **Code Quality**: Ruff

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Sync dependencies using uv
uv sync --extra dev

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run test suite
uv run pytest -v

# Run lint checks
uv run ruff check .
```

## Endpoints (Phase 00)

- `GET /api/v1/health` - Service health status, environment, version, uptime, and simulation mode.
