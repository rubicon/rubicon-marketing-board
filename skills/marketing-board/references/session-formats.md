# Session Formats

The board-brief output formats. Every full-session brief follows the
universal frame below, then adds the per-posture synthesis variation for
whichever posture was confirmed. Single-advisor consults (`/consult`) skip
synthesis entirely and return only that seat's take.

## Universal frame

Every board brief contains these sections, in this order:

1. **Simulation label** (once, at top) — takes are built from each source's
   published frameworks and positions, not their actual review.
2. **The question before the board** — restatement, stakes, posture.
3. **Seated** — who, why, and who was the designated dissenter.
4. **Seat takes** — each advisor's position: signature questions applied,
   frameworks applied to the specifics, recommendation with conviction. No
   name-flavored generic advice: a take that survives with the name swapped
   is a defect.
5. **Disagreement map** — 2–4 genuine conflicts; the underlying trade-off
   each represents; what evidence would settle each.
6. **Where the board disagrees with you** — required section; names where
   advisors pushed back on the *user's* framing or lean, not just on each
   other. A board that only validates is a mirror.
7. **Chair's synthesis** — recommendation fitted to the user's stage and
   constraints (never forced consensus; dissent preserved); concrete next
   steps; tripwires (which advisor's warning to monitor and its signal);
   execution handoffs.

Copyable skeleton:

```markdown
> **Simulation:** These are fictional composite advisors reasoning from
> real, published frameworks and positions — not the actual people's
> opinions on your situation.

## The question before the board

[Restated question, stakes, confirmed posture]

## Seated

- [Seat] — [why]
- [Seat] — [why]
- [Seat] — [why] **(designated dissenter — conflicts with the user's lean because [reason])**

## Seat takes

### [Seat name]

[Signature question(s) applied → framework(s) applied to the specifics →
recommendation with conviction]

[... one subsection per seat ...]

## Disagreement map

1. **[Seat A] vs. [Seat B]:** [the underlying trade-off] — settled by
   [what evidence would resolve it]
2. [... 2–4 total ...]

## Where the board disagrees with you

- [Where a seat pushed back on the user's own framing or lean]

## Chair's synthesis

[Recommendation fitted to the user's stage and constraints — dissent
preserved, not averaged away]

**Next steps:**
- [ ] [Concrete step]

**Tripwires:** watch [seat]'s [signal] — if it happens, revisit this call.

**Execution handoffs:** [named skill/pack, or the work to be done manually]

**Decision (user):**
```

## Per-posture synthesis variations

The universal frame's section 7 (Chair's synthesis) takes a different shape
per posture. Sections 1–6 stay as above. Within section 7, only the
recommendation body — the posture-specific payload shown below (Options /
Verdict / Themes / etc.) — replaces the generic placeholder; the trailer
that follows it in every posture (**Next steps**, **Tripwires**,
**Execution handoffs**, **Decision (user)**) still applies and is not shown
again per posture below to avoid repetition.

### Decide

> User intent: "help me choose" — an open question.
> Seat behavior: build the option space, argue positions.

```markdown
## Chair's synthesis

**Options:**

1. **[Option A]** — pros / cons / risks
2. **[Option B]** — pros / cons / risks
3. **[Option C]** — pros / cons / risks (omit if only two genuine options)

**Trade-off map:** [the axis the options actually differ on]

**Decision requested:** [the specific choice now in front of the user]
```

### Pressure-test

> User intent: "here's my call — tear it apart."
> Seat behavior: attack the reasoning from their frameworks.

```markdown
## Chair's synthesis

**Verdict:** [holds / doesn't hold / holds with conditions]

**Weaknesses, by severity:**

1. **[Critical]** [weakness] — [why it's critical]
2. **[Serious]** [weakness]
3. **[Minor]** [weakness]

**What would change the board's mind:** [the evidence or change that would
flip a verdict]
```

### Ideate

> User intent: "give me ideas/direction."
> Seat behavior: generate divergently; defer critique.

```markdown
## Chair's synthesis

**Clustered themes:**

- **[Theme A]:** [directions in it]
- **[Theme B]:** [directions in it]

**Most promising:** [which direction(s) and why, held loosely]

**Deferred-critique notes:** [concerns noted but not argued during
generation — surfaced now, separately, so they didn't choke off ideas]
```

### Retrospect

> User intent: "it ran — what do we learn?"
> Seat behavior: compare outcomes to the original session brief (re-read it
> if logged), diagnose deltas.

```markdown
## Chair's synthesis

**Original brief:** [link/reference to the prior session, if logged]

**What we got right, and why:** [...]

**What we got wrong, and why:** [...]

**Lessons extracted:** [...]

**Standing-assumption updates:** [what the profile or future sessions
should now assume differently]
```

### Brief me

> User intent: "get me smart on X."
> Seat behavior: teach from their lenses and dossiers.

```markdown
## Chair's synthesis

**What matters:** [the core of the topic, through the seated lenses]

**What's contested:** [where the sources/seats genuinely disagree, and why]

**What to watch:** [signals worth tracking going forward]

**Sources:** [the dossiers/works actually drawn on — no invented citations]
```

## Red-team variant

`/redteam` runs Pressure-test at maximum regardless of hostility level: all
seats assume the plan fails and hunt for how. The Chair's synthesis leads
with a **failure map** (premortem-style: what breaks, black swans, worst
cases) before naming what would have to be true to proceed anyway.
