# Evals

Test scenarios for the board (spec §11). Each file defines a session input and
pass criteria. All criteria must pass. Run the full set before any release
that changes agents, dossiers, the orchestrator, or commands.

Two ways to run them.

## By hand

Install the plugin locally (`claude plugin add ...` or a marketplace add of
this repo), execute the scenario input, and check every criterion yourself.
This is still the authority: a human reading the brief catches things no
script and no judge will.

## With the runner

```bash
python3 scripts/run-evals.py --dry-run        # resolve and validate, spend nothing
python3 scripts/run-evals.py --only 01-decide # one eval
python3 scripts/run-evals.py --calibrate      # the suite, plus a judge-calibration sheet
```

`scripts/run-evals.py` drives each eval through a headless session, captures
the brief it wrote, and decides each pass criterion. It is deliberately
**not** wired into CI: every eval spawns a real board session with real seat
agents, so a full run costs real model spend, and a green run is not a
substitute for reading a brief. Exit codes are 0 all-pass, 1 any fail, 3 any
`insufficient_evidence`, 4 a run that could not be graded at all.

### A run that cannot be graded says so

A session is granted read access to the plugin directory it is testing.
Without that, every seat's read of its dossiers is refused and the board
reasons from its charter alone — while still producing a brief that looks
fine. The first live run did exactly that, and scored nine criteria against a
brief it had never captured.

So the runner refuses to grade a run it cannot trust:

- An eval that expects a brief and produced none is a **run error** (exit 4).
  Nothing is graded and no judge call is paid for. `"expects_artifact": false`
  marks the one eval where no brief is the correct outcome.
- Briefs are captured from anywhere under the run directory, not only
  `board-sessions/`. A brief written to the wrong path is a finding worth
  seeing; a brief that silently vanishes is indistinguishable from a board
  that produced nothing.
- When a session reports being denied a read or a write, those lines are
  printed and the run is blocked. This is a heuristic read of the transcript,
  not a permission API — it errs toward blocking, because a brief produced
  without dossiers is testing a different board than the one you think.

`evals/manifest.json` says how each eval is driven and who decides each
criterion. The markdown files stay the source of truth for the profile, the
inputs and the criteria text.

### What decides a criterion

- **Structural** criteria are decided mechanically from the captured brief:
  heading presence, a count of seat subsections, the simulation label
  appearing exactly once, the brief landing at the configured path, whether
  any brief was written at all, and whether **every** seat subsection carries
  a required line — which is how eval 11 enforces that no take is left
  ambiguous about whether it used user-supplied evidence or dossiers alone.
  A whole-document search cannot catch one seat quietly omitting it; a
  per-subsection check can.
- **Judgment** criteria go to a separate judge session, which must answer
  `pass`, `fail`, or `insufficient_evidence` and quote its evidence from the
  brief. `insufficient_evidence` is a real answer: it is never folded into a
  pass, and it makes the run exit non-zero.

Most criteria in this suite are judgment, not structural — they ask whether a
take applied a real framework to the specifics, whether dissent is genuine,
whether two runs differ in substance rather than wording. That is the nature
of the thing being tested, and pretending otherwise with brittle string
matching would be worse than admitting it.

A judgment criterion may also carry mechanical **preconditions**. A necessary
condition the brief plainly fails settles the criterion as a fail without
paying for a judge call; a precondition passing decides nothing on its own.

### Calibrate the judge before trusting it

`--calibrate` writes `calibration.md` in the run directory: every judgment
criterion, the judge's verdict and quoted evidence, and a blank line for your
own verdict. Grade them yourself and compare. The judge has earned the right
to be read unattended only once its column and yours agree on this suite.
Until then, read the briefs.

### The profile is seeded, not assumed

Each run gets a throwaway directory with `.claude/board-profile.md` written
from what the manifest points at — a fence in the eval's own `## Setup`, or a
shared profile under `evals/profiles/`. A session with no profile takes a
different path through the orchestrator, so "no profile" is a deliberate
setting (`{"from": "none"}`), never an accident. Eval 04 also pre-seeds the
prior brief its Setup describes; a brief the runner seeded is never counted
as a brief the board produced.

### The manifest goes stale loudly

Each entry records `criteria_count`. Edit an eval's pass criteria without
updating the manifest and the runner refuses to run, naming the mismatch,
because the manifest points at criteria by position. It will not silently
grade criterion 5 against the rules for criterion 4.

### Eval 10 is the one that must not be automated away

The orchestrator pauses to confirm the posture and to notice a missing
profile. A single-shot headless session cannot answer a question, so the
runner appends a system prompt telling the orchestrator not to ask —
otherwise every eval would stall at the question.

That suppression would hide a real regression. An orchestrator that stopped
detecting posture, or stopped noticing a missing profile, would still pass
every other eval in the suite, because none of them ever sees the pause. So
`evals/10-posture-confirmation.md` runs with the override **off**
(`"pause_mode": "observe"`) and tests the pause itself. It is the one eval
expected to produce no brief: a brief appearing there is a failure.

### Cost

A full run is one session per input — thirteen sessions across the nine
evals, since evals 06, 07 and 08 run more than once — plus one judge call per
judgment criterion. Expect single-digit dollars at Opus prices, more if seats
run long. `--only` and `--dry-run` exist so debugging one eval does not cost
the whole suite. Run output lands in `eval-runs/<timestamp>/` (gitignored)
with per-run model, CLI version, plugin version, session id, duration and
cost recorded in `results.json`.
