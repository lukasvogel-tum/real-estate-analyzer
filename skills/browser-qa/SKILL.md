---
name: browser-qa
description: Run or prepare safe browser-based QA for the local UI of this real-estate-analyzer repository. Use when routes, navigation, uploads, chats, redirects, or other visible frontend flows need validation in `/brain`, `/projects`, `/projects/[projectName]`, or `/workspace`, especially once Playwright or a browser automation bridge is available.
---

# Browser QA

1. Read `../../AGENTS.md`, `../../frontend/AGENTS.md`, and `../../docs/browser-qa-workflow.md`.
2. Confirm whether browser automation is available.
3. If automation is unavailable, return a blocked status and name the missing connector:
   - direct Playwright package/config
   - Chrome DevTools MCP bridge
   - Browser-MCP runner
4. If automation is available, run only safe local flows.
5. Cover the affected documented smoke routes:
   - `/brain`
   - `/projects`
   - `/projects/[projectName]` when local data exists
   - `/workspace`
6. Capture findings in reproducible form with severity, steps, observed, expected, and likely module.

Never:

- run destructive actions
- rely on production systems
- fake missing local project data
