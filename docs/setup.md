# OrbitOps — Local Setup & Development Guide

This guide describes how to run and verify OrbitOps locally on Windows, macOS, or Linux without external cloud dependencies.

---

## 1. Prerequisites

- **Node.js**: `v20.x` or newer (Tested with `v24.14.x`)
- **Python**: `3.11` or `3.12` (Tested with `3.12.10`)
- **uv**: Fast Python package installer (`uv --version`)
- **Git**: Configured with standard credentials

---

## 2. Repository Cloning & Branch Setup

```bash
git clone https://github.com/samxq01/OrbitOps-.git
cd OrbitOps-
git checkout feature/orbitops-ia3
```

---

## 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Sync dependencies and create virtual environment using uv
uv sync --extra dev

# Run database migrations (applies all 12 tables)
uv run alembic upgrade head

# Seed virtual satellites, subsystems, and ground stations (idempotent)
uv run python -m app.cli.seed

# Run unit, migration, and persistence tests
uv run pytest -v

# Run lint checks
uv run ruff check .

# Start the development server (default: port 8000)
uv run uvicorn app.main:app --reload --port 8000
```

Verify backend health at: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
Interactive API Documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run TypeScript type check
npm run typecheck # or npx tsc --noEmit

# Run ESLint
npm run lint

# Run Next.js development server (default: port 3000)
npm run dev
```

Open your browser at: [http://localhost:3000](http://localhost:3000)

---

## 5. Verification Commands

To perform full system verification matching CI standards:

```powershell
# From repository root (Windows PowerShell):
.\scripts\verify.ps1
```
