# Local Neo4j Setup

This project can run Neo4j locally via Docker Compose for the graph layer.

## Prerequisites

- Docker Desktop installed and running
- Python backend dependencies installed in `.venv`

## Recommended Local Config

1. Create `backend/.env` from `backend/.env.example`.
2. Keep these graph values for local development:
   - `GRAPH_ENABLED=true`
   - `NEO4J_URI=bolt://127.0.0.1:7687`
   - `NEO4J_USERNAME=neo4j`
   - `NEO4J_PASSWORD=familyoffice_local_dev_password`
   - `NEO4J_DATABASE=neo4j`

## Start Neo4j

From repo root:

```powershell
docker compose --env-file backend/.env up -d neo4j
```

If you do not want to create `backend/.env` first, you can also use the example file:

```powershell
docker compose --env-file backend/.env.example up -d neo4j
```

Convenience helper:

```powershell
.\scripts\start_local_graph.ps1
```

## Verify Neo4j

- Browser UI: `http://127.0.0.1:7474`
- Bolt: `bolt://127.0.0.1:7687`

The backend exposes:

```text
GET /system/knowledge-status
```

Expected graph status once Neo4j is running and backend uses matching ENV:

- `package_available: true`
- `configured: true`
- `active: true`
- `connected: true`

## Start Backend With Graph Enabled

Run the backend from the `backend` directory so it picks up `backend/.env` automatically:

```powershell
cd backend
..\ .venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Corrected command without the spacing issue:

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
