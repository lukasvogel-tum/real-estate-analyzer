# Version Control Strategy

## Ziel
Nachvollziehbare, sichere und release-faehige Entwicklung mit kleinen, reviewbaren Aenderungen.

## Branching Model
- `main`: immer stabil und deploybar.
- Feature-Branches: `feat/<scope>-<short-description>`
- Bugfix-Branches: `fix/<scope>-<short-description>`
- Hotfix-Branches: `hotfix/<scope>-<short-description>`

## Commit Standard (Conventional Commits)
Format:
`<type>(<scope>): <summary>`

Beispiele:
- `feat(api): add project registry endpoints`
- `fix(rag): handle missing relevance scores`
- `docs(status): update project status`

Erlaubte Typen:
`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`

## Pull Request Regeln
- 1 PR = 1 fachlich zusammenhaengende Aenderung.
- Kleine PRs bevorzugen (idealerweise < 400 Zeilen Diff ohne Generated/Data Files).
- PR muss enthalten:
  - Zweck + Auswirkungen
  - Testhinweise
  - ggf. API-Aenderungen

## Schutzregeln fuer `main` (GitHub Settings)
- Require pull request before merging.
- Require at least 1 approval.
- Dismiss stale approvals when new commits are pushed.
- Require status checks to pass (sobald CI aktiv ist).
- Require branches to be up to date before merging.
- Restrict direct pushes to `main`.

## Release-Strategie
- Semantische Versionierung: `vMAJOR.MINOR.PATCH`
- Tagging nur auf `main`:
  - `v0.1.0` fuer erstes stabiles Inkrement
  - `PATCH` fuer Bugfixes
  - `MINOR` fuer neue, rueckwaertskompatible Features
  - `MAJOR` fuer Breaking Changes

## Changelog Prozess
- `CHANGELOG.md` nach Keep-a-Changelog pflegen.
- Jede PR mit nutzerrelevanter Aenderung bekommt einen Eintrag in `Unreleased`.

## Datenhygiene
Folgende Dateien bleiben lokal und werden nicht versioniert:
- `backend/lancedb/`
- `backend/projects/**/files/`
- `backend/projects/**/text/`
- `backend/projects/_registry.json`
- `projects/`

## Team-Workflow (empfohlen)
1. `git checkout main && git pull`
2. `git checkout -b feat/<scope>-<topic>`
3. Kleine Commits nach Conventional Commits
4. PR nach `main` mit Template
5. Squash-Merge oder Rebase-Merge (linearer Verlauf)
6. Release-Tag bei stabilem Stand
