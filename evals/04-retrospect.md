# Eval 04 — Retrospect

Exercises the Retrospect posture: reading a prior logged session brief and
comparing an outcome against the original advice, rather than treating the
retrospective as a fresh session with no memory.

## Setup

Board profile at Boardroom hostility level (default), with
`board-sessions/` set as the session-brief location.

Pre-seed a prior brief at `board-sessions/2026-06-01-enterprise-vs-midmarket.md`
containing at minimum:

```markdown
> **Simulation:** ...

## The question before the board

Should we move upmarket to enterprise or double down on mid-market?
(Decide posture)

## Seated

- vera-stratton — strategy/GTM sequencing
- emmett-grove — growth mechanics of each path
- ada-ledger — dissenter: unproven attribution model for enterprise deals

## Chair's synthesis

**Options:**
1. Move upmarket to enterprise — longer sales cycle, higher ACV
2. Double down on mid-market — faster cycle, proven channel mix

**Decision requested:** pick a segment focus for the next two quarters.

**Decision (user):** Move upmarket to enterprise.
```

## Input

```
/board the launch ran — results: enterprise pipeline is real but sales
cycles are running 2x longer than modeled, and win rate on qualified
opportunities is 60%. What do we learn?
```

## Pass criteria

- [ ] The orchestrator locates and reads the prior brief from the
      configured session-brief location before responding.
- [ ] Posture is detected and confirmed as **Retrospect**.
- [ ] The synthesis explicitly compares the outcome against the original
      brief's decision and reasoning — not a generic "here's how launches
      go" response disconnected from what was actually decided.
- [ ] Right/wrong/why is stated explicitly (what the original advice got
      right, what it got wrong, and why).
- [ ] Lessons are extracted as discrete, reusable statements — not folded
      invisibly into prose.
- [ ] At least one standing-assumption update is proposed (e.g. sales-cycle
      length assumptions for enterprise deals going forward).
