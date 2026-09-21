# Windows equivalent of ./verify.sh - runs every check in one command.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
#
# or just double-click VERIFY.bat in the project root.
#
# Nothing here needs the npm registry or a running database, so it works on a
# fresh checkout. The TypeScript step uses the project's own tsc when
# node_modules is present and the generated stubs otherwise.

$root = Split-Path -Parent $PSScriptRoot
$failures = 0

# PowerShell does not treat a failing external command as a terminating error,
# so each step checks $LASTEXITCODE explicitly. Without this the script would
# cheerfully report success after a test suite had failed - which is worse than
# having no check at all.
function Invoke-Step {
    param([string]$Title, [scriptblock]$Command)

    Write-Host ''
    Write-Host "==> $Title" -ForegroundColor White
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host '    FAILED' -ForegroundColor Red
        $script:failures++
    } else {
        Write-Host '    ok' -ForegroundColor Green
    }
}

$venvPython = Join-Path $root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Host 'The backend is not set up yet. Run SETUP.bat first.' -ForegroundColor Red
    exit 1
}

Invoke-Step 'Backend tests' {
    Push-Location "$root\backend"
    $env:PYTHONPATH = '.'
    & $venvPython tests\run_all.py
    Pop-Location
}

Invoke-Step 'Backend static check' {
    Push-Location "$root\backend"
    & $venvPython tools\static_check.py
    Pop-Location
}

Invoke-Step 'API contract' {
    Push-Location $root
    & $venvPython tools\check_api_contract.py
    Pop-Location
}

Invoke-Step 'Translations' {
    Push-Location $root
    & $venvPython tools\check_i18n.py
    Pop-Location
}

Invoke-Step 'TypeScript' {
    $localTsc = Join-Path $root 'frontend\node_modules\.bin\tsc.cmd'
    if (Test-Path $localTsc) {
        Push-Location "$root\frontend"
        & $localTsc --noEmit
        Pop-Location
    } elseif (Get-Command tsc -ErrorAction SilentlyContinue) {
        Push-Location $root
        & $venvPython tools\typecheck\generate_stubs.py | Out-Null
        & tsc -p tools\typecheck\tsconfig.json
        Pop-Location
    } else {
        Write-Host '    skipped: no tsc found and frontend\node_modules is absent.' -ForegroundColor DarkGray
        Write-Host '    Run "cd frontend; npm install" for the authoritative check.' -ForegroundColor DarkGray
        $global:LASTEXITCODE = 0
    }
}

Write-Host ''
if ($failures -eq 0) {
    Write-Host 'All checks passed.' -ForegroundColor Green
} else {
    Write-Host "$failures check(s) failed." -ForegroundColor Red
}
exit $failures
