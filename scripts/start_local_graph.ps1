$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot "backend\.env"
$exampleEnvFile = Join-Path $repoRoot "backend\.env.example"

if (-not (Test-Path $envFile)) {
    Write-Host "backend/.env not found. Falling back to backend/.env.example for local graph startup."
    $envFile = $exampleEnvFile
}

Write-Host "Starting Neo4j with env file: $envFile"
docker compose --env-file $envFile up -d neo4j
