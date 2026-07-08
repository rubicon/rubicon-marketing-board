# Contributing

Contributions are welcome — especially new source dossiers, seating-map
improvements, and eval scenarios.

## Ground rules

- **Issue first.** Open an issue describing the change before you branch.
- **Branch naming:** `dev/<issue-number>-<short-kebab-description>`.
- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, …) on
  commits and the PR title. CI enforces both.
- **PR body must link its issue** (`Closes #N`). CI enforces this.
- **Run `bash scripts/validate-plugin.sh`** before opening a PR; CI runs the
  same script.
- **Grounding rules are non-negotiable** for dossier and agent content: every
  framework and position must trace to a published source; no fabricated
  quotes; no impersonation. See the design spec in `docs/specs/`.
- Signed commits are required on `main`.

## Adding a source dossier

Follow `dossiers/advisor-template.md`. Public figures require published-source
grounding for every claim. Include at least one contrarian position — an
advisor with no unpopular opinions produces no useful disagreement.
