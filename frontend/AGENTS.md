# Frontend Agent Notes

## Purpose

Work inside `frontend/` by extending the current dashboard-style Next.js app rather than rebuilding it. The UI already has a clear shell, shared primitives, and route-specific dashboard components.

## Placement Rules

- Keep route files in `frontend/app/` thin and mostly compositional.
- Put reusable layout/state components in `frontend/components/app/`.
- Put reusable primitive UI in `frontend/components/ui/`.
- Put route-level or feature-level screens in `frontend/components/`.
- Keep backend contracts centralized in:
  - [`lib/api.ts`](/c:/Users/lukas/Documents/real-estate-analyzer/frontend/lib/api.ts)
  - [`lib/types.ts`](/c:/Users/lukas/Documents/real-estate-analyzer/frontend/lib/types.ts)

## UI And UX Rules

- Preserve the current shell and route expectations:
  - `/brain` is the default landing experience
  - `/projects` is the workspace list and upload surface
  - `/projects/[projectName]` is the focused project workspace
  - `/workspace` redirects to `/brain`
- Maintain explicit loading, empty, success, and error states when touching async UI.
- Reuse existing building blocks like `PageHeader`, `SectionCard`, `EmptyState`, and `LoadingSkeleton` before adding new wrappers.
- Keep copy and behavior aligned with the actual backend capabilities. Do not promise flows that the API does not support.

## Validation

- Preferred commands from `frontend/`:
  - `npm.cmd run lint`
  - `npm.cmd run build`
- If PowerShell blocks `npm.ps1`, use `npm.cmd`.
- If a change affects a documented browser smoke flow, update `docs/browser-qa-workflow.md` when needed.
