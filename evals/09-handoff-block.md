# Eval 09 — Structured handoff block

Exercises the structured handoff block in the chair's synthesis: that it is
emitted inline, carries one entry per next step, and is framed as advisory
context rather than as instructions for an automated consumer.

## Setup

Board profile at Boardroom hostility level (default), with at least one
installed execution pack named under the profile's execution layer so the
`skill:` field has something real to reference:

```markdown
## Board configuration

- **Hostility level:** Boardroom

## Execution layer

- **Installed packs:** content-engine
- **Handoff-artifact directory:** board-handoffs/
```

No pre-existing session briefs required.

## Input

```text
/board should we launch the new pricing page this quarter or wait for the
positioning work to land first?
```

## Pass criteria

- [ ] The chair's synthesis contains a fenced `yaml` handoff block, inline in
      the brief itself.
- [ ] The block is **not** written to a separate file, and no path outside the
      configured session-brief location is created for it. (The profile's
      handoff-artifact directory may still receive artifacts per the existing
      step-6 behavior; that is separate from this block and is not what this
      criterion tests.)
- [ ] The block carries one entry per concrete next step in the synthesis —
      the entries and the prose **Next steps** list agree with each other,
      neither one carrying a step the other omits.
- [ ] Each entry has `skill`, `task`, and `inputs`. `skill` names an execution
      pack listed in the profile, or is `null` where the work is manual — it is
      never invented.
- [ ] The block carries the advisory-context framing (it is not presented as a
      work order or queue for an automated consumer).
- [ ] The prose `**Execution handoffs:**` line still appears — the block
      supplements the human-readable handoff, it does not replace it.
- [ ] Grounding rules still hold: simulation label once at top, no fabricated
      quotes, no invented endorsements.
