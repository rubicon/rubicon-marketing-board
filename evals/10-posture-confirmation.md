# Eval 10 — Posture confirmation and the profile notice

Exercises the two places the orchestrator is supposed to STOP and talk to the
user before convening: the missing-profile notice (step 1) and the posture
confirmation (step 2).

This eval exists because the scripted runner suppresses both pauses. A
headless single-shot session cannot answer a question, so
`scripts/run-evals.py` appends a system prompt telling the orchestrator not to
ask — otherwise every other eval would stall at the question and produce no
brief. That suppression is a testing convenience, and it would hide a real
regression: an orchestrator that silently stopped detecting posture, or
stopped noticing a missing profile, would still pass every other eval in the
suite, because those evals never see the pause.

So this eval is run WITHOUT the override (`pause_mode: observe` in
`evals/manifest.json`). Its subject is the pause itself, not the brief. It is
the one eval in the suite that is expected to produce **no** session brief,
and a brief appearing here is a failure, not a success.

## Setup

**No board profile at all.** Do not create `.claude/board-profile.md` in the
project and make sure no `~/.claude/board-profile.md` is visible to the
session — the first criterion is about what the board does when it has no
profile to read.

No pre-existing session briefs required.

## Input

```text
/board here is our Q3 plan: triple paid search, cut brand spend to zero, and
move the whole team onto demand gen. Tear it apart.
```

## Pass criteria

- [ ] With no profile present, the session gives the missing-profile notice
      once, naming what the board cannot do without one (tailor advice to the
      market, calibrate hostility, save briefs) and offering either the
      `/board-profile` interview or proceeding generic. It does not invent a
      profile, and it does not silently assume one.
- [ ] The session detects the posture as **Pressure-test** — the input hands
      over an existing plan and asks for it to be attacked — and states that
      detection explicitly rather than leaving it implicit.
- [ ] The session asks the user to confirm the posture (or to correct it)
      before convening any seats. The question is actually put to the user; a
      statement of the posture with no invitation to correct it does not
      count.
- [ ] No seat takes appear and no synthesis appears: the session stops at the
      question instead of convening the board on an unconfirmed posture.
- [ ] No session brief is written. Nothing is created under the
      session-brief location, because no session was held.
- [ ] The pause is a question to the user, not a refusal: the session does not
      decline the request or lecture the user, it asks and waits.
