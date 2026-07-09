<p align="center">
  <img src="assets/banner.svg" alt="Rubicon Marketing Board" width="100%">
</p>

<p align="center">
  <a href="https://github.com/rubicon/rubicon-marketing-board/actions/workflows/ci.yaml"><img src="https://github.com/rubicon/rubicon-marketing-board/actions/workflows/ci.yaml/badge.svg" alt="CI"></a>
  <a href="https://github.com/rubicon/rubicon-marketing-board/releases"><img src="https://img.shields.io/github/v/release/rubicon/rubicon-marketing-board" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/rubicon/rubicon-marketing-board" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-2B2D42" alt="Claude Code plugin">
</p>

A nine-seat marketing advisory board for Claude Code: decide, pressure-test, ideate, retrospect, and get smart — with advisors who challenge instead of cheerlead.

Rubicon Marketing Board is a Claude Code plugin that seats a nine-member simulated marketing advisory board: fictional composite advisors covering strategy, positioning, creative, growth, customer research, measurement, ethics, systems, and foresight, each grounded in the published frameworks of real practitioners (Roger Martin, Geoffrey Moore, Mark Ritson, and company) rather than vibes. Every marketer says they want honest feedback. This plugin is what happens if you actually mean it: every session seats a designated dissenter whose documented views cut against wherever you are already leaning, and the written brief that comes out includes a disagreement map and a mandatory "Where the board disagrees with you" section. Run `/board` to convene the full table, `/consult` to corner one advisor, or `/redteam` to have the board assume your plan has already failed and work out how. Three hostility settings (Coach, Boardroom, Activist) let you decide how expensive you want the honesty to be.

## The Bench

Nine seats. Each is a fictional composite advisor: the reasoning is built from real, published frameworks belonging to the people listed, not an impersonation of them.

| Persona | Seat | Draws from |
|---|---|---|
| Vera Stratton | Strategy & GTM | Roger Martin, Geoffrey Moore, Mark Ritson |
| Cassia Frame | Positioning & Category | April Dunford, Al Ries & Jack Trout, the *Play Bigger* authors (Ramadan, Peterson, Lochhead, Maney), Byron Sharp |
| August Penn | Creative & Brand Experience | Seth Godin, Donald Miller, Robert McKee, David Ogilvy, Marty Neumeier, Don Norman, Steve Krug |
| Emmett Grove | Growth & Demand | Brian Balfour, Andrew Chen, Elena Verna, Chris Walker, Alex Hormozi |
| Mira Voss | Customer Research & Behavior | Bob Moesta, Teresa Torres, Steve Portigal, Rory Sutherland |
| Ada Ledger | Measurement & ROI | Les Binet & Peter Field, Avinash Kaushik, Claude Hopkins |
| Zora Bell | Ethics, Trust & Responsible AI | Tristan Harris, Safiya Noble, Indra Nooyi, plus the ICC Advertising Code and the FEDMA AI Charter as standing checklists |
| Silas Webb | Systems & Scale | Donella Meadows, W. Edwards Deming, Satya Nadella |
| Wren Halley | Innovation & Foresight | Amy Webb, Rita McGrath, Clayton Christensen, Ethan Mollick, Paul Roetzer, Christopher Penn |

## How It Works

**Postures** — same seats, different stance, set per session:

- **Decide** — the board builds the option set, argues each one, and asks you to choose.
- **Pressure-test** — the board attacks your existing plan and ranks the damage by severity.
- **Ideate** — the board generates directions divergently; critique is deferred, not interleaved.
- **Retrospect** — the board reads the original session brief back against what actually happened and extracts the lesson.
- **Brief me** — the board teaches you a topic through its members' lenses.

**Hostility levels** — set in your profile, overridable per session:

- **Coach** — constructive, explains itself, offers an answer readily.
- **Boardroom** (default) — candid professional disagreement, findings stated plainly.
- **Activist** — assumes your plan is wrong until you defend it, and won't hand you an answer until you've committed to a position first.

**The 10th-man rule.** Every full session seats at least one designated dissenter whose documented positions conflict with wherever you're leaning — a practice with real lineage: the IDF's institutionalized devil's-advocate doctrine (*Ipcha Mistabra*), popularized outside military circles as the "10th man" by *World War Z*.

**Session briefs and retrospectives.** Every session is logged to a written brief with a disagreement map, a required "Where the board disagrees with you" section, and a decision line left for you to fill in. Run `/board` again later in Retrospect posture and it reads that prior brief back to check what the board got right, what it got wrong, and why.

## Install

```
claude plugin marketplace add rubicon/rubicon-marketing-board
claude plugin install rubicon-marketing-board@rubicon-marketing-board
```

First run, use `/board-profile` to tell the board who you are, your hostility-level default, and where to save session briefs — the board can convene without a profile, but it's generic until you do.

## Commands

- `/board <topic>` — convene a full board session.
- `/consult <advisor> <topic>` — one seat, in depth, no synthesis.
- `/redteam <plan>` — pressure-test at maximum: the board assumes your plan fails and hunts for how.
- `/board-profile` — create or edit your profile.

## Grounding & Ethics

The board is labeled as simulation once, at the top of every brief. No advisor's take is a fabricated quote or an implied endorsement of your specific company — sources are applied as frameworks to your case, never as if the named person reviewed it personally. Every framework and position traces to something actually published. The ethics floor holds at every hostility level: the board will not help design manipulative, deceptive, or discriminatory tactics, and the Ethics seat is mandatory for any review of AI-generated content or AI-driven personalization. The board is advisory. The decision, and the accountability for it, stay with you.

## Extending the Bench

Have a private advisor the board doesn't have — an old boss, your own CFO, a specific person whose judgment you trust? Copy `dossiers/advisor-template.md` into `.claude/board-advisors/<kebab-name>.md` in your own project (not into the plugin, so it survives updates). For a real, named public figure, every framework and position still needs to trace to something they actually published. For a private person, you supply the views — the board will never invent an opinion for someone real.

## Prior Art & Credits

This plugin grows out of the maintainer's original Personal Board of Directors concept — a five-persona advisory prompt with follow-up questions and a session template that predates this repo. The dossier structure, designated-dissenter seating, disagreement map, and grounding rules adapt patterns from `coreyhaines31/marketingskills`'s marketing-council skill, credited here with thanks. Seat charters, decision rights, blind spots, and the posture/hostility model draw on broader multi-agent-council research and a deep-research pass conducted in July 2026. The dissent mechanism's lineage runs through the IDF's *Ipcha Mistabra* doctrine and its "10th man" popularization via *World War Z*.

## License

MIT
