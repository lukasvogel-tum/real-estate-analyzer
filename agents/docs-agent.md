# Docs Agent

## Mission

Keep repository instructions and workflow documents aligned with the actual codebase.

## Use When

- contracts change
- a new workflow is introduced
- agent rules or validation steps become stale

## Steps

1. Update the smallest set of docs that truly changed.
2. Keep repo-specific guidance in `AGENTS.md` and `docs/`.
3. Prefer concise operational instructions over long narratives.
4. Cross-check commands and route names against the current code.

## Output

- changed docs
- short summary of what was synchronized

## Guardrails

- Avoid speculative docs for features the repo does not actually have.
