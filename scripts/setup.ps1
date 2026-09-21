# One-shot local setup for MPLAD Insight (Windows PowerShell).
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# PowerShell does not treat a failing external command as a terminating error,
# so every one of them is checked explicitly. Without this the script would
# happily report success after pip had failed.
function Invoke-Step {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "    $Description" -ForegroundColor DarkGray
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host ''
        Write-Host "FAILED: $Description (exit code $LASTEXITCODE)" -ForegroundColor Red
        Write-Host 'Scroll up for the error. Nothing after this point has run.' -ForegroundColor Red
        exit 1
    }
}

function Resolve-Python {
    foreach ($candidate in @('python', 'py')) {
        try {
            $raw = & $candidate --version 2>&1
            if ($LASTEXITCODE -ne 0) { continue }
            if ($raw -match '(\d+)\.(\d+)') {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -ge 11) { return $candidate }
                Write-Host "Found $raw, but Python 3.11 or newer is required." -ForegroundColor Red
                exit 1
            }
        } catch { continue }
    }
    Write-Host 'Python was not found on PATH.' -ForegroundColor Red
    Write-Host 'Install it from python.org and tick "Add python.exe to PATH".' -ForegroundColor Red
    exit 1
}

Write-Host '==> Checking prerequisites' -ForegroundColor Cyan
$python = Resolve-Python
Write-Host "    Python: $(& $python --version)"
try { Write-Host "    Node:   $(node --version)" }
catch {
    Write-Host 'Node.js was not found on PATH. Install the LTS build from nodejs.org.' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '==> Backend' -ForegroundColor Cyan
Set-Location "$root\backend"

$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Invoke-Step 'creating the virtual environment' { & $python -m venv .venv }
}
Invoke-Step 'upgrading pip'          { & $venvPython -m pip install --upgrade pip --quiet }
Invoke-Step 'installing packages'    { & $venvPython -m pip install -r requirements.txt }

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    $secret = & $venvPython -c "import secrets; print(secrets.token_urlsafe(48))"
    (Get-Content .env) `
        -replace 'JWT_SECRET_KEY=change-me-generate-a-long-random-secret', "JWT_SECRET_KEY=$secret" |
        Set-Content .env
    Write-Host '    created backend\.env with a generated JWT_SECRET_KEY' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '==> Seeding the database' -ForegroundColor Cyan
Invoke-Step 'generating sample works' { & $venvPython -m seed.seed_data --reset --projects 600 }

Write-Host ''
Write-Host '==> Checks' -ForegroundColor Cyan
Invoke-Step 'running the tests'  { & $venvPython -m tests.run_all }
Invoke-Step 'static analysis'    { & $venvPython tools\static_check.py }

Write-Host ''
Write-Host '==> Frontend' -ForegroundColor Cyan
Set-Location "$root\frontend"
Invoke-Step 'installing packages' { npm install }
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Invoke-Step 'production build'    { npm run build }

Set-Location $root
Invoke-Step 'API contract check' { & "$root\backend\.venv\Scripts\python.exe" tools\check_api_contract.py }

Write-Host ''
Write-Host '========================================================' -ForegroundColor Green
Write-Host ' Setup complete.' -ForegroundColor Green
Write-Host '========================================================' -ForegroundColor Green
Write-Host ''
Write-Host ' Start the API (terminal 1):'
Write-Host "   cd `"$root\backend`""
Write-Host '   .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000'
Write-Host ''
Write-Host ' Start the web app (terminal 2):'
Write-Host "   cd `"$root\frontend`""
Write-Host '   npm run dev'
Write-Host ''
Write-Host ' Web app:  http://localhost:5173'
Write-Host ' API docs: http://localhost:8000/docs'
Write-Host ''
Write-Host " Sign-in details: $root\backend\.seed-credentials.txt"
Write-Host ' (delete that file when you are finished)'
Write-Host ''
