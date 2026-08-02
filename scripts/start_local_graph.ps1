$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot "backend\.env"

if (-not (Test-Path $envFile)) {
    throw "backend/.env not found. Copy backend/.env.example to backend/.env, set NEO4J_PASSWORD, and run this script again."
}

Write-Host "Starting Neo4j with env file: $envFile"
docker compose --env-file $envFile up -d neo4j
