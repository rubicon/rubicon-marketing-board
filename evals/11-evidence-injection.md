# Eval 11 — User-supplied evidence, and disclosing who used it

Exercises the evidence table (orchestrator step 4): dated context the USER
supplies is logged verbatim, routed to seats by the orchestrator, and
disclosed per seat, so a reader can always tell a take informed by recent
evidence from a take built only on a static dossier.

The failure this eval exists to catch is not "the board ignored the
evidence." It is **a take shaped by dated material that does not say so** —
a reader taking a 2026-dated claim for a dossier's documented position, or
for the real source's current opinion.

The board never fetches anything. Every row in the table comes from the user.
A session that invents a row, a date, or a source has failed, and so has one
that claims to have looked anything up.

## Setup

Board profile at Boardroom hostility level (default):

```markdown
## Board configuration

- **Hostility level:** Boardroom
- **Default seats always wanted:**
- **Seats never wanted (and why):**

## Output

- **Session-brief location:** board-sessions/
- **Handoff-artifact directory:**
```

No pre-existing session briefs required. No research skills are installed,
and none are needed: all evidence arrives in the input below.

## Input

```text
/board should we keep publishing long-form SEO articles, or move the budget
to a podcast? Factor in this context I gathered:

- 2026-09-14, Christopher Penn, blog post: argues AI search summaries are
  cutting referral clicks on informational queries, and that measurement
  should move to assisted conversions.
- 2026-08-02, Rand Fishkin, Sparktoro report: zero-click share of searches
  rose again year over year.
- Undated, a competitor's careers page: they just hired two podcast
  producers.
```

## Pass criteria

- [ ] The brief contains an evidence section listing every item the user
      supplied, each with the date and source **exactly as the user gave
      them** — no item invented, no date invented, no source renamed.
- [ ] The undated item is carried as undated. The board does not assign it a
      date, and does not quietly drop it for lacking one.
- [ ] Every seat take carries a disclosure naming which evidence items it
      drew on, or stating that it used static dossiers only. No seat take is
      left ambiguous about which of the two it is.
- [ ] At least one seat take is marked as having used supplied evidence, and
      the claim it draws from that item is traceable to what the user
      actually supplied — not an extrapolation presented as part of the item.
- [ ] No seat claims to have fetched, searched, browsed, or looked anything
      up. The only evidence in play is the user's items and the dossiers.
- [ ] No invented endorsements: a dated item by a real person is treated as
      that person's published position on the topic, never as that person
      having reviewed, endorsed, or formed an opinion on the user's own
      company or plan.
- [ ] Where a supplied item cuts against a dossier's documented position, the
      tension is surfaced rather than smoothed away — the brief says which
      source is which and does not merge them into one voice.
- [ ] Grounding rules still hold: the simulation label appears exactly once
      at the top, no fabricated quotes, and any direct quotation from a
      supplied item is verbatim and attributed to that item.
- [ ] The board still reaches a recommendation. Supplying evidence does not
      turn the session into a literature review with no position.
