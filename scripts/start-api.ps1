# Starts the API. Run from anywhere: powershell -ExecutionPolicy Bypass -File .\scripts\start-api.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"
$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host 'The backend is not set up yet. Run scripts\setup.ps1 first.' -ForegroundColor Red
    exit 1
}
Write-Host 'Starting the API on http://localhost:8000 ...' -ForegroundColor Cyan
& $venvPython -m uvicorn app.main:app --reload --port 8000
