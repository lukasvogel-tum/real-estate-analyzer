# Codex Working Agreement

## Project Identity

This repository is a local-first real-estate analysis workspace with:

- a FastAPI backend in `backend/`
- a Next.js App Router frontend in `frontend/`
- a document upload -> extraction -> chunking -> LanceDB RAG pipeline
- optional Neo4j graph augmentation for shared knowledge and chat context

The goal is steady, reviewable evolution of the current product. Prefer clarifying and reinforcing the existing structure over redesigning it.

## Current Tooling Snapshot

- `obra/superpowers` was not available in this environment on 2026-03-14.
- The internal replacement for that workflow lives in:
  - `skills/`
  - `agents/`
  - `docs/agent-workflow.md`
  - `docs/browser-qa-workflow.md`
- Local browsers and Docker are installed, but no committed Playwright setup, Chrome DevTools MCP bridge, or Browser-MCP runner is wired into this repo yet.

## Non-Negotiable Architecture Rules

- Keep [`backend/main.py`](/c:/Users/lukas/Documents/real-estate-analyzer/backend/main.py) focused on API routes, request validation, and orchestration.
- Put backend business logic in `backend/services/`.
- Put low-level backend helpers in `backend/utils/`.
- Preserve the current scope model and naming:
  - upload scopes: `project`, `domain`, `global`
  - chat scopes: `project`, `realestate_global`, `global`
- Preserve current runtime storage roots unless the task explicitly requires a migration:
  - `backend/projects/`
  - `backend/scopes/`
  - `backend/lancedb/`
  - `backend/metadata.db`
- Keep graph features optional and resilient. Missing OpenAI or Neo4j must degrade gracefully instead of breaking the whole app.
- Keep frontend page files thin. Route files in `frontend/app/` should mostly compose dashboard/client components.
- Reuse the existing frontend layering:
  - `frontend/components/ui/` for low-level primitives
  - `frontend/components/app/` for reusable app-shell and stateful layout pieces
  - feature screens in `frontend/components/`
  - API contracts in `frontend/lib/types.ts`
  - API calls in `frontend/lib/api.ts`

## Change Strategy

- Prefer small, reviewable patches over broad cleanup.
- Respect the dirty worktree. Do not revert or rewrite unrelated user changes.
- Only refactor when it directly reduces risk for the task at hand.
- If a backend response shape changes, update frontend types, client usage, and docs in the same change.
- If a frontend workflow changes, update the browser-QA instructions when the affected flow is one of the documented smoke paths.

## Refactoring Rules

- Avoid opportunistic renames, moves, or abstraction passes.
- Do not collapse backend services into `main.py`.
- Do not bypass `frontend/lib/api.ts` with ad hoc fetch code.
- Do not duplicate route or scope logic that already exists in `backend/services/scope_retriever.py`, `backend/services/project_registry.py`, or `frontend/lib/project-utils.ts`.

## Validation Rules

- Run the smallest relevant validation for the changed surface.
- Favor these repo-native checks:
  - backend syntax/import sanity: `.\.venv\Scripts\python.exe -m compileall backend`
  - frontend lint: `npm.cmd run lint`
  - frontend production build when routing or type shape changed: `npm.cmd run build`
  - optional graph start/stop: `.\scripts\start_local_graph.ps1` and `.\scripts\stop_local_graph.ps1`
- This repo currently has no committed automated test suite. When no formal test exists, document the manual or smoke validation you performed.
- In PowerShell on this machine, prefer `npm.cmd` and `npx.cmd` if `npm.ps1` or `npx.ps1` is blocked by execution policy.

## Risks And Uncertainty

- If OpenAI, Neo4j, or local data state influence behavior, call that out explicitly.
- When a project-specific route depends on existing indexed data, do not invent fixtures silently. Report the dependency or create safe local fixtures only if the task clearly requires it.
- Treat runtime data and local indexes as user-owned state. Avoid deleting or resetting them unless the user explicitly asks.

## Subagents And Skills

- Use the skill in `skills/` that best matches the task before improvising a new workflow.
- Use subagent definitions in `agents/` when the task benefits from decomposition.
- Default role split:
  - Explorer: read-only impact mapping
  - Implementer: isolated code/doc changes
  - Tester/Triage: command execution and failure isolation
  - Reviewer: read-only diff review
  - Docs: documentation sync
  - Browser-QA: browser flow validation when automation is available
- Keep one editing owner per file. Do not let multiple agents modify the same file concurrently.
- Explorer, Reviewer, and Tester/Triage should stay read-only unless the main agent explicitly hands them an edit scope.

## Browser-QA Rules

- Use the Browser-QA agent only in safe local or test context.
- Focus on the real product flows in this repo:
  - `/brain`
  - `/projects`
  - `/projects/[projectName]`
  - `/workspace` redirect
- Check navigation, obvious UI breakage, form validation, empty states, backend-down states, and browser console errors.
- Do not run destructive actions, production actions, or mass data mutations.
- Document findings in a way that an Implementer can act on immediately:
  - route
  - preconditions
  - exact steps
  - observed behavior
  - expected behavior
  - severity
  - likely module or file

## Expected Codex Output

- For implementation tasks, report:
  - what changed
  - key file paths
  - validation performed
  - residual risks or assumptions
- For review tasks, report findings first, ordered by severity, with file references.
- Keep summaries short and operational. Avoid long theory dumps.

## Primary References

- [`docs/project-structure.md`](/c:/Users/lukas/Documents/real-estate-analyzer/docs/project-structure.md)
- [`docs/agent-workflow.md`](/c:/Users/lukas/Documents/real-estate-analyzer/docs/agent-workflow.md)
- [`docs/browser-qa-workflow.md`](/c:/Users/lukas/Documents/real-estate-analyzer/docs/browser-qa-workflow.md)
