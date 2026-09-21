# Starts the web app. Run from anywhere: powershell -ExecutionPolicy Bypass -File .\scripts\start-web.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\frontend"
if (-not (Test-Path node_modules)) {
    Write-Host 'The frontend is not set up yet. Run scripts\setup.ps1 first.' -ForegroundColor Red
    exit 1
}
Write-Host 'Starting the web app on http://localhost:5173 ...' -ForegroundColor Cyan
npm run dev
