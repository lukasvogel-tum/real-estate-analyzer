# Local Neo4j Setup

This project can run Neo4j locally via Docker Compose for the optional graph layer.

## Prerequisites

- Docker Desktop installed and running
- Python backend dependencies installed in `.venv`

## Configure local credentials

1. Copy the template:

   ```powershell
   Copy-Item backend/.env.example backend/.env
   ```

2. In `backend/.env`, keep or set:

   - `GRAPH_ENABLED=true`
   - `NEO4J_URI=bolt://127.0.0.1:7687`
   - `NEO4J_USERNAME=neo4j`
   - `NEO4J_PASSWORD=<your-local-password>`
   - `NEO4J_DATABASE=neo4j`

Use a local password that is not reused elsewhere. `backend/.env` is ignored by Git and must never be committed.

## Start Neo4j

From the repository root:

```powershell
docker compose --env-file backend/.env up -d neo4j
```

Convenience helper:

```powershell
.\scripts\start_local_graph.ps1
```

The helper requires `backend/.env` so a password is always supplied explicitly.

## Verify Neo4j

- Browser UI: `http://127.0.0.1:7474`
- Bolt: `bolt://127.0.0.1:7687`

The backend exposes:

```text
GET /system/knowledge-status
```

Expected graph status once Neo4j is running and the backend uses matching environment variables:

- `package_available: true`
- `configured: true`
- `active: true`
- `connected: true`

## Start the backend with graph enabled

Run the backend from the `backend` directory so it loads `backend/.env`:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Stop Neo4j

```powershell
docker compose down
```

Convenience helper:

```powershell
.\scripts\stop_local_graph.ps1
```

To remove local Neo4j data as well:

```powershell
docker compose down -v
```
