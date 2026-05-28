---
name: bugfix
description: Diagnose and fix regressions, exceptions, API mismatches, validation bugs, retrieval issues, or UI defects in this real-estate-analyzer repository. Use when the task starts from broken behavior in the FastAPI backend, Next.js frontend, upload pipeline, project registry, metadata DB, scope routing, or optional graph integration.
---

# Bugfix

1. Read `../../AGENTS.md` and the nearest area-specific `AGENTS.md`.
2. Reproduce the bug with the smallest reliable command or UI flow.
3. Map the failure path before editing:
   - route or component
   - backend endpoint or service
   - runtime dependency such as OpenAI, Neo4j, local project data, or LanceDB state
4. Patch the smallest surface that fixes the real cause.
5. Preserve current architecture:
   - keep backend orchestration in `backend/main.py`
   - keep backend logic in `backend/services/`
   - keep frontend API access in `frontend/lib/api.ts`
6. Validate the changed surface with at least one targeted command or smoke flow.
7. Update docs if the fix changes behavior, contracts, or operator workflow.

Return:

- root cause
- changed files
- validation performed
- residual risk or dependency on local data/services
