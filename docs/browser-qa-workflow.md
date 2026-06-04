# Browser QA Workflow

## Current Status

Environment snapshot taken on 2026-03-14:

- Local browser binaries are present.
- Docker is present.
- `frontend/node_modules` is present.
- No direct Playwright package is installed in `frontend/node_modules`.
- No committed `playwright.config.ts` exists in `frontend/`.
- No Chrome DevTools MCP or Browser-MCP connector was found in this repo or shell path.

Result: the Browser-QA agent is defined and ready, but browser automation is not fully wired in this repository yet. For now, this workflow documents both the intended automated flow and the exact setup gap.

## Safe Local Startup

### Full App

```powershell
make run
```

This starts the backend and frontend together and writes logs to `.dev/`.

Stop after QA:

```powershell
make stop
```

### Optional Graph

```powershell
.\scripts\start_local_graph.ps1
```

The app expects:

- frontend at `http://127.0.0.1:3000`
- backend at `http://127.0.0.1:8000`

## Browser-QA Scope

The Browser-QA agent should focus on the real routes and flows that already exist:

1. `/brain`
2. `/projects`
3. `/projects/[projectName]` when a real local project exists
4. `/workspace` redirect to `/brain`

## Core Smoke Flow

### 1. Start Health Check

- Open `/brain`.
- Confirm the page shell renders.
- Confirm the "Knowledge Layers" panel either loads status data or shows a clear backend error state.
- Confirm the "Refresh Status" button is clickable.

### 2. Navigation Check

- Use sidebar and mobile nav links to move between `/brain` and `/projects`.
- Open `/workspace` directly and confirm redirect behavior.

### 3. Brain Chat Form Check

- Verify the chat panel renders.
- Submit without a query and confirm validation is visible.
- If a working backend and valid local data exist, submit a safe non-destructive query and confirm answer/evidence rendering.

### 4. Projects Dashboard Check

- Confirm the overview cards render.
- Confirm refresh works or fails with a visible error state.
- Verify the upload form renders all expected fields:
  - `scope_type`
  - `scope_id`
  - `document_type`
  - project type selector for project scope
- Submit with empty required fields and confirm validation messages.

### 5. Project Detail Check

- Only run this flow when a real local project exists.
- Open `/projects/[projectName]`.
- Confirm stats render or a clear not-found state appears.
- Confirm the project-scoped chat and locked upload form render.
- Submit an empty query and confirm validation.

### 6. Console Check

- Capture visible console errors, unhandled promise rejections, or repeated network failures.
- Distinguish expected backend-unavailable errors from UI bugs.

## Finding Format

Every finding should be documented in this shape:

- `Severity`: blocker | high | medium | low
- `Route`: exact page URL or route pattern
- `Preconditions`: backend up, graph enabled, existing project required, sample file required, etc.
- `Steps`: numbered reproduction steps
- `Observed`: what actually happened
- `Expected`: what should have happened
- `Evidence`: selector, button label, visible text, console error, or screenshot reference
- `Likely module`: best file or component guess if it is reasonably inferable

## Guardrails

- Use only local or test data.
- Avoid destructive actions and production systems.
- Do not delete user data or indexes as part of QA.
- Prefer validation-only form submissions unless a safe fixture file is explicitly provided.
- If a flow depends on missing seed data, report the block instead of faking the result.

## Activation Path Once Automation Is Added

Any of these is sufficient to activate the Browser-QA agent for automated runs:

1. Add Playwright to `frontend/`:

```powershell
cd frontend
npm.cmd install -D @playwright/test
npx.cmd playwright install chromium
```

2. Commit a `playwright.config.ts` and route-specific smoke tests.
3. Connect a Chrome DevTools MCP or Browser-MCP bridge that can launch and inspect the local app.

Until one of those is present, the Browser-QA agent should return a structured "automation unavailable" status plus the missing setup piece.
