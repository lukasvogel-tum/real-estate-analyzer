---
name: test-triage
description: Triage failing validation commands, broken local startup, lint/build errors, or runtime setup issues in this real-estate-analyzer repository. Use when the goal is to isolate the first actionable failure across the FastAPI backend, Next.js frontend, local graph setup, or repo tooling without immediately performing a broad refactor.
---

# Test Triage

1. Read `../../AGENTS.md` and `../../docs/project-structure.md`.
2. Start with the nearest relevant command, not the broadest possible command.
3. Prefer this order:
   - backend syntax/import sanity
   - frontend lint
   - frontend build
   - service startup
   - graph-specific startup
4. Separate failures into:
   - missing prerequisite
   - local environment policy issue
   - missing runtime data
   - genuine code regression
5. Stop once the first actionable root cause is isolated unless the user asked for a fix too.

Useful commands:

- `.\.venv\Scripts\python.exe -m compileall backend`
- `cd frontend && npm.cmd run lint`
- `cd frontend && npm.cmd run build`
- `.\scripts\start_local_graph.ps1`

Return:

- status
- commands run
- first failing point
- likely owner module
- recommended next action
