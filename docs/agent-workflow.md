# Agent Workflow

## Purpose

This repository uses a main-agent plus specialist-role workflow that is compatible with the current codebase and with a future `obra/superpowers` style setup.

Because `obra/superpowers` was not available here on 2026-03-14, the internal workflow lives in:

- `AGENTS.md`
- `backend/AGENTS.md`
- `frontend/AGENTS.md`
- `agents/*.md`
- `skills/*/SKILL.md`

## Role Definitions

### Explorer Agent

- Mission: map impacted files, data flow, dependencies, and risk before implementation
- Default mode: read-only
- Output:
  - short analysis
  - affected file list
  - risk notes

### Implementer Agent

- Mission: make the smallest complete change inside an assigned file set
- Default mode: edit only files explicitly assigned by the main agent
- Output:
  - completed patch
  - short rationale
  - follow-up validation needs

### Tester/Triage Agent

- Mission: run the most relevant commands, separate environment issues from regressions, and point to likely root cause
- Default mode: read-only except temporary runtime artifacts created by commands
- Output:
  - command status
  - failing point
  - likely cause
  - recommended next step

### Reviewer Agent

- Mission: inspect the diff for bugs, regressions, missing updates, and architecture violations
- Default mode: read-only
- Output:
  - findings first
  - blockers vs non-blockers
  - suggested fixes or tests

### Docs Agent

- Mission: keep docs, `AGENTS.md`, and skill/workflow files aligned with behavior changes
- Default mode: edit docs only unless asked otherwise
- Output:
  - updated docs
  - short summary of what changed

### Browser-QA Agent

- Mission: run safe local browser flows, detect visible issues, and report reproducible findings
- Default mode: no file edits, no destructive actions
- Output:
  - tested routes and flows
  - findings with steps and severity
  - console/runtime observations

## Coordination Rules

- The main agent owns planning, file assignment, and final integration.
- Only one agent edits a given file at a time.
- Preferred ownership split:
  - Explorer: read-only
  - Implementer: product code or docs patch
  - Tester/Triage: command execution
  - Reviewer: read-only diff review
  - Docs: docs-only edits
  - Browser-QA: browser execution only
- If a task is small and isolated, the main agent can perform all roles sequentially without spawning separate agents.

## Default Workflows

### Bugfix Workflow

1. Use `skills/bugfix/SKILL.md`.
2. Run Explorer pass to confirm failing path and smallest fix surface.
3. Assign a narrow file set to the Implementer.
4. Run Tester/Triage on the changed surface.
5. Run Reviewer before finish if behavior, API contract, or retrieval logic changed.
6. Run Docs Agent if contract, workflow, or agent instructions changed.

### Feature Workflow

1. Use `skills/feature-implementation/SKILL.md`.
2. Explorer maps impacted backend, frontend, types, and docs.
3. Implementer adds the feature without re-architecting the app.
4. Tester/Triage validates the relevant commands or manual smoke flow.
5. Reviewer checks for regressions and missing cross-layer sync.
6. Docs Agent updates docs when the feature changes user flows or contracts.

### Test Triage Workflow

1. Use `skills/test-triage/SKILL.md`.
2. Start with the nearest failing command, not the broadest command.
3. Separate:
  - missing prerequisites
  - environment misconfiguration
  - genuine code regressions
4. Stop once the first actionable root cause is isolated, unless the user asked for a fix too.

### Review Workflow

1. Use `skills/review-before-finish/SKILL.md`.
2. Review the actual diff, not just final file snapshots.
3. Prioritize:
  - behavior regressions
  - API/type drift
  - missing fallback handling
  - UI state regressions
  - missing docs or validation

## Handoffs

Each role should hand back compact, implementation-ready artifacts:

- Explorer -> impacted file list plus risk summary
- Implementer -> changed files plus why
- Tester/Triage -> command results plus first failing point
- Reviewer -> findings with file references
- Docs -> changed docs plus coverage note
- Browser-QA -> reproducible findings with route, steps, expected, observed, severity

## When To Skip Roles

- Skip Browser-QA for backend-only changes unless the change affects a visible UI flow.
- Skip Reviewer only for tiny docs-only updates.
- Skip Docs Agent only when behavior, contracts, and workflows are unchanged.
