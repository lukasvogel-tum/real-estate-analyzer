---
name: feature-implementation
description: Implement an incremental feature in this real-estate-analyzer repository while preserving the existing FastAPI plus Next.js architecture. Use when adding or extending UI flows, API endpoints, upload metadata behavior, project workspace capabilities, chat behavior, or graph-aware features without redesigning the whole system.
---

# Feature Implementation

1. Read `../../AGENTS.md`, `../../docs/project-structure.md`, and the nearest area-specific `AGENTS.md`.
2. Derive the feature from the current structure instead of introducing a new architecture.
3. Map the affected layers before editing:
   - backend routes
   - backend services
   - frontend route/component
   - shared types and docs
4. Keep changes narrow:
   - thin route files in `frontend/app/`
   - reusable UI in `frontend/components/`
   - business logic in `backend/services/`
5. If the backend response shape changes, update:
   - `frontend/lib/types.ts`
   - `frontend/lib/api.ts`
   - relevant docs
6. Validate the feature with the closest command or smoke path.
7. Update workflow docs when the new behavior changes how future agents should operate.

Return:

- implemented behavior
- files changed
- validation performed
- follow-up gaps if the feature depended on missing local prerequisites
