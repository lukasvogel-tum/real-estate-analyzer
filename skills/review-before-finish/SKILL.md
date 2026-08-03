---
name: review-before-finish
description: Review a completed or nearly completed change in this real-estate-analyzer repository for bugs, regressions, contract drift, missing validation, and architecture violations. Use when preparing to finish work or when the user asks for a review of backend, frontend, retrieval, upload, or workflow changes.
---

# Review Before Finish

1. Read `../../AGENTS.md` and the nearest area-specific `AGENTS.md`.
2. Review the actual diff or changed files, not just the final intent.
3. Prioritize:
   - behavior regressions
   - backend/frontend contract mismatches
   - missing fallback behavior for optional graph or OpenAI dependencies
   - missing loading/error/empty states in UI
   - stale docs or missing validation
4. Check that the change stayed within the existing architecture.
5. Report findings first, ordered by severity, with file references.

If no findings remain, say so explicitly and note any residual risk such as missing automated tests or blocked browser automation.
