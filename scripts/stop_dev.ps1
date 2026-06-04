[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateDir = Join-Path $Root ".dev"

function Get-ChildProcessIds {
    param([int]$ParentProcessId)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        [int]$child.ProcessId
        Get-ChildProcessIds -ParentProcessId ([int]$child.ProcessId)
    }
}

function Stop-ManagedProcess {
    param([string]$Name)

    $pidPath = Join-Path $StateDir "$Name.pid"
    if (-not (Test-Path $pidPath)) {
        Write-Host "$Name is not tracked as running."
        return
    }

    $rawPid = (Get-Content $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $rawPid) {
        Remove-Item -LiteralPath $pidPath -Force
        Write-Host "$Name had an empty PID file; cleaned it up."
        return
    }

    $trackedPid = [int]$rawPid
    $process = Get-Process -Id $trackedPid -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Remove-Item -LiteralPath $pidPath -Force
        Write-Host "$Name was not running; cleaned up .dev/$Name.pid."
        return
    }

    $processIds = @(Get-ChildProcessIds -ParentProcessId $trackedPid)
    $processIds += $trackedPid
    $processIds = $processIds | Select-Object -Unique

    foreach ($processId in $processIds) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }

    Remove-Item -LiteralPath $pidPath -Force
    Write-Host "Stopped $Name."
}

if (-not (Test-Path $StateDir)) {
    Write-Host "No .dev state directory found."
    return
}

Stop-ManagedProcess -Name "frontend"
Stop-ManagedProcess -Name "backend"
