# Backend Agent Notes

## Purpose

Work inside `backend/` conservatively. The backend is the source of truth for upload orchestration, project registry, scope-aware retrieval, metadata persistence, and optional graph augmentation.

## Placement Rules

- Keep [`main.py`](/c:/Users/lukas/Documents/real-estate-analyzer/backend/main.py) slim.
- Add or change request-independent logic in `services/`.
- Add low-level helpers in `utils/`.
- Keep file-system paths anchored from backend-local base directories, not from the current working directory.

## Stability Rules

- Preserve the current upload and chat contracts unless the task explicitly changes them.
- Preserve graceful fallback behavior when Neo4j, OpenAI, or shared indexes are unavailable.
- When changing metadata or registry behavior, check both:
  - `services/metadata_db.py`
  - `services/project_registry.py`
- When changing retrieval behavior, inspect both:
  - `services/rag.py`
  - `services/scope_retriever.py`
  - `services/vectorstore.py`

## Runtime State

- Treat `backend/projects/`, `backend/scopes/`, `backend/lancedb/`, and `backend/metadata.db` as local state, not disposable fixtures.
- Never delete runtime data to "fix" a bug unless the user explicitly requests it.

## Validation

- Minimum backend sanity check:
  - `.\.venv\Scripts\python.exe -m compileall backend`
- Use local Uvicorn only when the task needs runtime verification:
  - `cd backend`
  - `..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`
- If graph-related behavior matters, use the existing scripts rather than ad hoc Docker commands.
