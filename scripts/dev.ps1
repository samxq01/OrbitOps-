# ==============================================================================
# OrbitOps Development Launcher (PowerShell)
# ==============================================================================

Write-Host "`n🚀 Launching OrbitOps Local Development Services...`n" -ForegroundColor Cyan

Write-Host "1. Starting Backend API on http://127.0.0.1:8000 (Swagger: /docs)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uv run uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 2

Write-Host "2. Starting Frontend Console on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n🌟 Services initiated in separate console windows.`n" -ForegroundColor Green
