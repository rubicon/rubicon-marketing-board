# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A Claude Code plugin: a nine-seat marketing advisory board. The product is
prompt content (agents, dossiers, skill, commands) plus validation and CI.
Design authority: `docs/specs/2026-07-08-marketing-board-design.md`.

## Process (enforced by CI and branch protection)

- Issue first for any change beyond trivial typo/metadata fixes.
- Branch `dev/<issue>-<slug>` in a worktree under `worktrees/` (gitignored);
  `main` stays checked out in the main clone.
- Conventional Commits; signed commits; PR with `Closes #N`; squash merge;
  no direct pushes to `main`.
- Run `bash scripts/validate-plugin.sh` before every commit touching plugin
  content.
- Never add AI-authorship trailers to commits, PRs, or files.

## Content rules

- Grounding rules (spec §10) are non-negotiable: published sources only, no
  fabricated quotes, no impersonation, simulation labeling, extra care with
  living people, ethics floor regardless of hostility level.
- Personas are flavor; charters, frameworks, and blind spots are substance.
  A take that survives with the advisor's name swapped is a defect.
- Keep the orchestrator thin. Seat doctrine belongs in agents and dossiers.

## Releases

release-please manages versions and CHANGELOG from Conventional Commits.
Do not hand-edit `version` in `.claude-plugin/plugin.json` or the changelog;
land correctly-typed commits instead.
