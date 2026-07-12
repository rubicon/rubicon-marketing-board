# Eval 06 — Seating and dissent

Exercises the seating map's strong-fit selection, the mandatory designated
dissenter (10th-man rule), and honoring an explicit user seating override,
across three different question types.

## Setup

Board profile at Boardroom hostility level (default). Run all three inputs
below as separate sessions (fresh convening each time).

## Input

**6a — Pricing:**

```text
/board should we move from flat-rate to usage-based pricing?
```

**6b — Creative review:**

```text
/board review this campaign concept: a fear-based countdown timer on the
pricing page telling visitors the discount expires in 10 minutes, reset on
every visit.
```

**6c — AI adoption, with an explicit seating override:**

```text
/board should we adopt an AI content-generation tool for our blog — and
add Silas Webb to the board for this one.
```

## Pass criteria

- [ ] **6a:** seated advisors match `seating-map.md`'s strong fits for
      "Pricing / offer / packaging" (`emmett-grove`, `vera-stratton`,
      `ada-ledger`), and a designated dissenter from that row's natural
      dissenters (`mira-voss` or `zora-bell`) is named with the specific
      reason they dissent.
- [ ] **6b:** seated advisors match the strong fits for "Campaign /
      creative / brand review" (`august-penn`, `mira-voss`,
      `cassia-frame`), and a designated dissenter from that row
      (`ada-ledger` or `zora-bell`) is named — given the fear-based/
      countdown-timer mechanic described, `zora-bell` dissenting on
      dark-pattern grounds is the expected, substantively correct pick.
- [ ] **6c:** seated advisors match the strong fits for "AI adoption /
      martech / emerging channels" (`wren-halley`, `silas-webb`,
      `zora-bell`) — note `silas-webb` is already a strong fit here, so
      the override is honored either by his presence being confirmed or,
      if a fresh seating pass would have excluded him, by the override
      being explicitly acknowledged and applied.
- [ ] Across all three: every dissenter name comes with a stated reason
      that reflects their seat's actual documented positions, not a
      placeholder.
