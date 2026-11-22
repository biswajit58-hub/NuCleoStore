# run.ps1 - start NucleoStore (backend + frontend) in one step
# Usage: .\run.ps1     (or right-click -> Run with PowerShell)
# Stop:  Ctrl+C

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

Write-Host ""
Write-Host "NucleoStore launcher" -ForegroundColor Cyan
Write-Host "  project root: $root" -ForegroundColor DarkGray
Write-Host ""

# --- sanity checks ---
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: .venv not found." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "ERROR: frontend dependencies not installed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$python = Join-Path $root ".venv\Scripts\python.exe"

function Wait-Port {
    param([int]$Port, [int]$TimeoutSec = 45)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $c.Connect("127.0.0.1", $Port)
            $c.Close()
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

# --- start backend in its own window (visible logs, no silent failures) ---
Write-Host "[1/2] Starting FastAPI on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; & '$python' -m uvicorn backend.api.main:app --port 8000"
)

# --- start frontend in its own window ---
Write-Host "[2/2] Starting Next.js on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\frontend'; npm run dev"
)

# --- wait for both ports ---
Write-Host ""
Write-Host "Waiting for servers to be ready ..." -ForegroundColor DarkGray
$backendOk  = Wait-Port -Port 8000 -TimeoutSec 45
$frontendOk = Wait-Port -Port 3000 -TimeoutSec 90

if (-not $backendOk) {
    Write-Host ""
    Write-Host "ERROR: FastAPI did not start on port 8000." -ForegroundColor Red
    Write-Host "Check the backend window for the actual error." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not $frontendOk) {
    Write-Host ""
    Write-Host "ERROR: Next.js did not start on port 3000." -ForegroundColor Red
    Write-Host "Check the frontend window for the actual error." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Both servers are up." -ForegroundColor Green
Write-Host "  Backend:  http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000"     -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening browser ..." -ForegroundColor DarkGray
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Close the two server windows to stop." -ForegroundColor Yellow
Write-Host "This launcher window can be closed." -ForegroundColor DarkGray