# ==============================================================================
# OrbitOps Verification Suite (PowerShell)
# Runs complete backend & frontend tests, linting, type checks, and build.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "`n🚀 [OrbitOps] Starting Full System Verification...`n" -ForegroundColor Cyan

# 1. Backend Checks
Write-Host ">>> [1/5] Running Backend Pytest Suite..." -ForegroundColor Yellow
Push-Location backend
try {
    uv run pytest -v
    if ($LASTEXITCODE -ne 0) { throw "Backend pytest failed!" }
    Write-Host "✅ Backend tests passed.`n" -ForegroundColor Green

    Write-Host ">>> [2/5] Running Backend Ruff Linting..." -ForegroundColor Yellow
    uv run ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Backend ruff linting failed!" }
    Write-Host "✅ Backend linting passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

# 2. Frontend Checks
Write-Host ">>> [3/5] Running Frontend TypeScript Typecheck..." -ForegroundColor Yellow
Push-Location frontend
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed!" }
    Write-Host "✅ Frontend typecheck passed.`n" -ForegroundColor Green

    Write-Host ">>> [4/5] Running Frontend ESLint..." -ForegroundColor Yellow
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend ESLint failed!" }
    Write-Host "✅ Frontend ESLint passed.`n" -ForegroundColor Green

    Write-Host ">>> [5/5] Running Frontend Production Build..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed!" }
    Write-Host "✅ Frontend production build passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "🌟 ALL SYSTEM CHECKS PASSED SUCCESSFULLY!`n" -ForegroundColor Green
