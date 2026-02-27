# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]
### Added
- Project registry service and API endpoints (`/projects`, `/projects/{project_name}`).
- Chat endpoint supports configurable `top_k` and returns `sources` + richer `evidence`.
- Version control standards documentation and PR template.

### Changed
- Upload endpoint validates `project_type` and persists project metadata.
- Git ignore rules now exclude local runtime/project artifacts.
- Vector store storage path is now consistently anchored to `backend/lancedb` (absolute path).
- Branch-first workflow is now explicitly mandatory in project guidelines.

### Removed
- Runtime artifacts from version control tracking (kept locally).
- Legacy root-level artifacts `export_codebase.py`, `codebase.txt`, and top-level `__init__.py`.
