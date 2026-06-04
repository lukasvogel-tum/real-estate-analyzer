# Project Structure

## Overview

This repository is a two-process local application:

- `backend/`: FastAPI API for upload, retrieval, project registry, metadata DB, and optional graph features
- `frontend/`: Next.js App Router UI for Brain, Projects, and project-detail workspaces
- `scripts/`: local helper scripts for Neo4j lifecycle
- `docs/`: project and workflow documentation

The local app has a root developer command for the normal two-process stack. Neo4j is optional and still started separately when graph testing is needed.

## Runtime Commands

### Full Local App

From repo root:

```powershell
make run
```

Notes:

- Starts the FastAPI backend at `http://127.0.0.1:8000`.
- Starts the Next.js frontend at `http://127.0.0.1:3000`.
- Writes PID and log files under `.dev/`.
- Stop both managed processes with `make stop`.
- Restart both with `make restart`.
- `make run` is a local developer convenience wrapper. It does not containerize the app; it uses the existing `.venv`, `npm.cmd`, local runtime data, and local environment files.

### Backend Only

From repo root:

```powershell
make backend
```

Equivalent manual command:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Notes:

- `backend/.env` is loaded automatically by the backend.
- `OPENAI_API_KEY` is required for embedding/chat behavior that hits OpenAI.
- Graph behavior is optional and controlled by `GRAPH_ENABLED` and `NEO4J_*`.

### Frontend Only

From repo root:

```powershell
make frontend
```

Notes:

- Default backend base URL is `http://127.0.0.1:8000`.
- If `npm.ps1` is blocked in PowerShell, use `npm.cmd`.

### Local Graph

From repo root:

```powershell
.\scripts\start_local_graph.ps1
.\scripts\stop_local_graph.ps1
```

Equivalent manual command:

```powershell
docker compose --env-file backend/.env up -d neo4j
```

### Validation Commands

Backend sanity:

```powershell
.\.venv\Scripts\python.exe -m compileall backend
```

Frontend lint:

```powershell
cd frontend
npm.cmd run lint
```

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

## Backend Structure

### `backend/main.py`

- Defines API routes
- Normalizes request inputs
- Orchestrates uploads, retrieval, project lookup, and system status
- Should stay thin

### `backend/services/`

- `rag.py`: retrieval scoring, metadata filtering, answer generation, evidence shaping
- `scope_retriever.py`: scope routing and fallback retrieval behavior
- `vectorstore.py`: LanceDB table access and shared index mirroring
- `project_registry.py`: file-based registry plus metadata DB merge logic
- `metadata_db.py`: SQLAlchemy models, schema compatibility, and upload/project persistence
- `graph_db.py`: optional Neo4j connection and status
- `graph_ingest.py`: graph writes during upload
- `graph_extraction.py`: optional structured entity/relationship extraction
- `graph_queries.py`: graph facts for chat augmentation
- `system_status.py`: aggregate health/status payloads
- `analysis_schema.py`: structured analysis model definitions for future features

### `backend/utils/`

- `extract_file.py`: extract text from supported file types
- `text_splitter.py`: create chunked LangChain documents with metadata
- `embeddings.py`: initialize embeddings

### Backend Runtime Data

These paths are part of the product's local state:

- `backend/projects/`
- `backend/scopes/`
- `backend/lancedb/`
- `backend/metadata.db`

Agents should treat them as user state, not disposable fixtures.

## Frontend Structure

### `frontend/app/`

- `page.tsx`: redirects root to `/brain`
- `brain/page.tsx`: renders the Brain dashboard
- `projects/page.tsx`: renders the Projects dashboard
- `projects/[projectName]/page.tsx`: server wrapper for the client detail screen
- `workspace/page.tsx`: legacy redirect to `/brain`
- `layout.tsx`: app shell entry point

### `frontend/components/`

- `BrainDashboard.tsx`: global Brain screen with knowledge-layer status
- `ProjectsDashboard.tsx`: workspace overview and upload entry point
- `ProjectDetailClient.tsx`: project-specific stats, chat, and upload flow
- `ScopeChatPanel.tsx`: reusable chat form/result panel
- `UploadForm.tsx`: reusable upload form with scope metadata

### `frontend/components/app/`

Reusable app-specific building blocks:

- `app-shell.tsx`
- `page-header.tsx`
- `section-card.tsx`
- `empty-state.tsx`
- `loading-skeleton.tsx`
- `confirm-dialog.tsx`
- `data-table.tsx`

### `frontend/components/ui/`

shadcn/Radix-style primitives used across the app.

### `frontend/lib/`

- `api.ts`: backend calls and API error handling
- `types.ts`: shared TypeScript shapes
- `project-utils.ts`: project-type normalization and labels
- `utils.ts`: generic UI helpers

## Architecture Rules To Preserve

- Keep route files thin and feature screens in components.
- Keep backend business logic out of `main.py`.
- Keep API shape changes synchronized across backend, frontend types, and docs.
- Preserve scope semantics across upload, retrieval, and UI labels.
- Preserve graceful fallback behavior for optional graph functionality.

## Current Workflow Gaps

These are important when planning future Codex work:

- No committed backend unit/integration test suite
- No CI configuration in this repo
- No committed Playwright or browser-automation runner yet
- Browser-QA therefore depends on future setup or manual verification for now
