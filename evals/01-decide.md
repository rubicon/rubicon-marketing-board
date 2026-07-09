# Eval 01 — Decide

Exercises the Decide posture end to end: option generation, trade-off
mapping, dissent preservation, and the decision being left to the user.

## Setup

Board profile at Boardroom hostility level, otherwise minimal:

```markdown
## Board configuration

- **Hostility level:** Boardroom
- **Default seats always wanted:**
- **Seats never wanted (and why):**

## Output

- **Session-brief location:** board-sessions/
- **Handoff-artifact directory:**
```

No pre-existing session briefs required.

## Input

```
/board should we move upmarket to enterprise or double down on mid-market?
```

## Pass criteria

- [ ] Posture is detected and confirmed as **Decide** before the board convenes.
- [ ] 4–6 seats are convened, including `vera-stratton` (Strategy & GTM).
- [ ] A designated dissenter is named, with a stated reason grounded in
      their seat's documented positions (this input is a genuinely open
      A-or-B question with no clear user lean, so the reason may cite
      system/customer/measurement risk either option carries, rather than
      conflict with a specific lean).
- [ ] The synthesis presents 2–3 real options (not a single recommendation
      dressed as options), each with pros/cons/risks.
- [ ] A trade-off map names the actual axis the options differ on.
- [ ] "Where the board disagrees with you" is present and names at least
      one place a seat pushed back on the user's own framing.
- [ ] The chair's synthesis explicitly states the decision is requested of
      the user — it does not make the call on their behalf.
- [ ] The brief is written to the profile's configured session-brief
      location (`board-sessions/YYYY-MM-DD-<slug>.md`) with a "Decision
      (user)" line left for the user to fill.
