# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A Claude Code plugin: a nine-seat marketing advisory board. The product is
prompt content (agents, dossiers, skill, commands) plus validation and CI.
Design authority: `docs/specs/2026-07-08-marketing-board-design.md`.
Execution playbook (phase issue setup, worktree conventions, model
checkpoints, the Sonnet-writers + Opus-review-pass protocol): see
`docs/plans/2026-07-08-implementation.md`. Directory map: see
`ARCHITECTURE.md`.

## Process (enforced by CI and branch protection)

- Issue first for any change beyond trivial typo/metadata fixes.
- Branch `dev/<issue>-<slug>` in a worktree under `worktrees/` (gitignored);
  `main` stays checked out in the main clone.
- Conventional Commits; signed commits; PR with `Closes #N`; squash merge;
  no direct pushes to `main`.
- Run `bash scripts/validate-plugin.sh` before every commit touching plugin
  content.
- Never add AI-authorship trailers to commits, PRs, or files.
- Don't create an empty `commands/` (or similar globbed) directory ahead of
  its files — `validate-plugin.sh`'s glob checks fail ungracefully on an
  empty match.

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
release-please regenerates both the release PR's body and the CHANGELOG.md
on its branch on every push to `main` — a hand-edited release-notes opening
paragraph must be reapplied as the last step immediately before merging the
release PR, not earlier. After merge, verify the actual GitHub Release's
notes (`gh release view <tag> --json body`) — they are not reliably carried
over from the PR body, and need `gh release edit` if empty.

A release is not finished until the marketplace pin is bumped. This plugin
is listed in the `rubicon` marketplace (`rubicon/ai-skills`) as an external
`github` source pinned to a release tag, so installs follow releases rather
than `main`. That pin does not move on its own: after cutting a release,
open an issue and PR in `rubicon/ai-skills` updating the
`rubicon-marketing-board` entry's `ref` in `.claude-plugin/marketplace.json`
to the new tag. Skipping it leaves marketplace users on the previous
release — v0.1.2 shipped 2026-09-02 and the pin sat at v0.1.1 for six weeks.
`.github/workflows/marketplace-pin-drift.yaml` now checks this on every
release and weekly, so a forgotten or unmerged bump surfaces on its own
instead of waiting to be noticed; it is read-only and never moves the pin.
