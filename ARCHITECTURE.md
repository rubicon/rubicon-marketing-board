# Architecture

A Claude Code plugin, at repository root.

## Layout

- `.claude-plugin/` — plugin + marketplace manifests.
- `agents/` — one agent per board seat (nine). A seat's full charter
  (mandate, frameworks, blind spots, posture and hostility behavior, voice)
  loads only inside that seat's subagent context, never the user's main
  conversation. Single-seat consults spawn one agent; board sessions spawn
  seats in parallel.
- `dossiers/` — 40 structured references, one per real-world source an agent
  draws from (lens, frameworks, documented positions, signature questions,
  blind spots, voice notes). Agents load only the dossiers relevant to the
  question. Two are document dossiers (ICC Marketing Code, FEDMA AI charter)
  holding checklist material.
- `skills/marketing-board/` — the thin orchestrator: posture detection,
  seating (with the designated-dissenter rule), synthesis, session logging.
  Its `references/` hold the seating map, per-posture output formats, and the
  profile template.
- `commands/` — `/board`, `/consult`, `/redteam`, `/board-profile` entry
  points; each is a thin pointer into the orchestrator skill.
- `evals/` — scenario documents (inputs + pass criteria) exercising postures,
  seating, grounding, and hostility. The test layer for prompt content.
- `scripts/validate-plugin.sh` — structural validation; run locally and in CI.

## Why agents-per-seat

Context economy: nine seats' worth of doctrine would bloat the main
conversation if carried in one skill. Each agent context carries one charter
plus a few dossiers. The orchestrator carries only roster, rules, and
synthesis discipline.

## Design authority

`docs/specs/2026-07-08-marketing-board-design.md` is the founding spec;
`docs/plans/` holds implementation plans.
