[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateDir = Join-Path $Root ".dev"
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Test-ListeningPort {
    param([int]$Port)

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Test-ManagedProcess {
    param([string]$Name)

    $pidPath = Join-Path $StateDir "$Name.pid"
    if (-not (Test-Path $pidPath)) {
        return $false
    }

    $rawPid = (Get-Content $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $rawPid) {
        return $false
    }

    $existing = Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue
    return $null -ne $existing
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [int]$Port
    )

    if (Test-ManagedProcess -Name $Name) {
        Write-Host "$Name is already running from .dev/$Name.pid"
        return
    }

    if (Test-ListeningPort -Port $Port) {
        Write-Host "$Name was not started because port $Port is already in use."
        Write-Host "If this is an old dev server, stop it manually or run scripts/stop_dev.ps1 if it was started here."
        return
    }

    $stdoutPath = Join-Path $StateDir "$Name.out.log"
    $stderrPath = Join-Path $StateDir "$Name.err.log"
    $pidPath = Join-Path $StateDir "$Name.pid"

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    Set-Content -Path $pidPath -Value $process.Id -Encoding ASCII
    Write-Host "Started $Name on port $Port (PID $($process.Id)). Logs: .dev/$Name.out.log and .dev/$Name.err.log"
}

if (-not (Test-Path $Python)) {
    throw "Backend Python runtime not found at $Python. Create/install .venv first."
}

Start-ManagedProcess `
    -Name "backend" `
    -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "$BackendPort") `
    -WorkingDirectory $BackendDir `
    -Port $BackendPort

Start-ManagedProcess `
    -Name "frontend" `
    -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "--hostname", "127.0.0.1", "--port", "$FrontendPort") `
    -WorkingDirectory $FrontendDir `
    -Port $FrontendPort

Write-Host ""
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "Backend:  http://127.0.0.1:$BackendPort"
Write-Host "Stop with: make stop"
