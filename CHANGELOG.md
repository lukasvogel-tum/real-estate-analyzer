# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]
### Added
- Managed local dev startup helpers for `make run`, `make stop`, and `make restart`.
- Project registry service and API endpoints (`/projects`, `/projects/{project_name}`).
- Chat endpoint supports configurable `top_k` and returns `sources` + richer `evidence`.
- Version control standards documentation and PR template.
- Scope-aware chat (`project`, `realestate_global`, `global`) with shared real estate index support.
- Endpoint aliases for Postman workflows: `/projects/list` and `/projects/info`.
- Multi-format ingestion support for `DOCX`, `XLSX`, `PPTX`, `TXT`, `MD`, and `CSV` uploads.
- Next.js frontend MVP shell with:
  - Projects page (list + upload)
  - Project detail page (project-scoped chat)
  - Workspace page (`realestate_global` + `global` chats)
- SQL metadata database layer (`projects`, `documents`) via SQLAlchemy.
- Upload metadata persistence (file paths, size, extraction status, chunks indexed).
- Postgres-ready DB configuration via `DATABASE_URL` with SQLite fallback for local MVP.
- Long-term deployment note: Docker Compose is a supported future deployment option.
- Upload taxonomy fields: `scope_type`, `scope_id`, `document_type` (backend + frontend).
- Global shared retrieval table `global_brain` for cross-domain global chat context.
- Optional chat metadata filters (`scope_type_filter`, `scope_id_filter`, `document_type_filter`).

### Changed
- `make run` now starts backend and frontend as tracked background processes with logs and PID files under `.dev/`.
- Local startup documentation now treats `make run` as the default full-stack developer command.
- Upload endpoint validates `project_type` and persists project metadata.
- Git ignore rules now exclude local runtime/project artifacts.
- Vector store storage path is now consistently anchored to `backend/lancedb` (absolute path).
- Branch-first workflow is now explicitly mandatory in project guidelines.
- Upload indexing now mirrors project chunks into shared table `realestate_global`.
- Upload now returns explicit `422` errors for unsupported file types or failed extraction.
- Upload processing now catches parser exceptions consistently and returns actionable error details instead of opaque failures.
- Backend CORS defaults now allow both `http://localhost:3000` and `http://127.0.0.1:3000` (override via `CORS_ALLOW_ORIGINS`).

### Removed
- Runtime artifacts from version control tracking (kept locally).
- Legacy root-level artifacts `export_codebase.py`, `codebase.txt`, and top-level `__init__.py`.
