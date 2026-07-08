# Rubicon Marketing Board — Design Specification

- **Date:** 2026-07-08
- **Status:** Draft for review
- **Issue:** [#1](https://github.com/rubicon/rubicon-marketing-board/issues/1)
- **Owner:** Dax Davis

## 1. Overview

Rubicon Marketing Board is a Claude Code plugin that convenes a nine-seat marketing advisory board for marketing leaders. Each seat is a fictional composite persona grounded in the published frameworks of named real-world practitioners. The board advises, challenges, and pressure-tests; it never executes. Execution is handed off to whatever marketing skill packs the user has installed.

The product premise: every marketer says they want honest feedback; this plugin is what happens if you actually mean it.

### Goals

- Give a marketing leader on-demand access to rigorous, framework-backed, multi-perspective counsel across nine marketing disciplines.
- Mechanize honest dissent (10th-man rule, disagreement mapping, configurable hostility) so the board sharpens the user instead of validating them.
- Produce durable session briefs so decisions can be revisited and retrospected against outcomes.
- Work generically for any marketing leader out of the box; personalize through a profile file, never through baked-in user context.

### Non-goals

- **No execution layer.** The board does not write landing pages, run audits, or build campaigns. It names handoffs to installed execution skills (e.g., Corey Haines' `marketingskills`, `digital-marketing-pro`).
- **No impersonation.** Personas draw from the published ideas of named sources; they never claim to be or speak for those people.
- **No decision authority.** The board clarifies the decision landscape; the human decides and is accountable.
- **No duplication of existing execution skill packs.** The ecosystem already provides them abundantly.

## 2. Architecture

A standalone public GitHub repository with the plugin at the repo root, following the standalone-plugin pattern (`digital-marketing-pro`, `marketingskills`).

```text
rubicon-marketing-board/
├── .claude-plugin/
│   ├── plugin.json               # name: rubicon-marketing-board; SemVer version
│   └── marketplace.json          # self-listing so the repo can be added as a marketplace
├── agents/                       # one agent per board seat (9 files)
│   ├── vera-stratton.md
│   ├── cassia-frame.md
│   ├── august-penn.md
│   ├── emmett-grove.md
│   ├── mira-voss.md
│   ├── ada-ledger.md
│   ├── zora-bell.md
│   ├── silas-webb.md
│   └── wren-halley.md
├── skills/
│   └── marketing-board/
│       ├── SKILL.md              # thin orchestrator (see §5)
│       └── references/
│           ├── seating-map.md    # question-type → seats + natural dissenters
│           ├── session-formats.md # output formats per posture
│           └── profile-template.md
├── commands/
│   ├── board.md                  # /board — convene a session
│   ├── consult.md                # /consult — single advisor
│   ├── redteam.md                # /redteam — adversarial pass
│   └── board-profile.md          # /board-profile — create/edit profile
├── dossiers/                     # 40 source dossiers, one per source (incl. 2 document dossiers)
│   ├── roger-martin.md
│   ├── april-dunford.md
│   └── … (see §4)
│   └── advisor-template.md       # template for user-added custom advisors
├── evals/                        # test scenarios (see §11)
├── docs/
│   └── specs/                    # design specs (this file)
├── ARCHITECTURE.md, CLAUDE.md, AGENTS.md, README.md, CHANGELOG.md,
├── LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md
└── .github/workflows/            # CI (see §12)
```

### Why agents-per-seat

A seat's full charter (mandate, frameworks, blind spots, per-posture behavior, voice) loads only inside that seat's subagent context — never into the user's main conversation. Single-seat consults spawn one agent; board sessions spawn seats in parallel. The main context carries only the thin orchestrator plus synthesized outputs. Agents reference dossiers via plugin-relative paths (`${CLAUDE_PLUGIN_ROOT}/dossiers/…`) and load only the dossiers relevant to the question at hand.

## 3. The Bench — nine seats

Each seat is a fictional composite persona. The persona is flavor; the charter, frameworks, rubrics, and blind spots are the substance and always take precedence. Every agent file contains: mandate, embedded frameworks (citing its dossiers), default counter-questions, decision rights, explicit blind spots (other seats are instructed to compensate), per-posture behavior, per-hostility-level behavior, and voice notes.

| # | Persona | Seat | Sources (dossiers) |
|---|---------|------|--------------------|
| 1 | **Vera Stratton** | Marketing Strategy & GTM | Roger Martin, Geoffrey Moore, Mark Ritson |
| 2 | **Cassia Frame** | Positioning & Category | April Dunford, Al Ries & Jack Trout, Play Bigger (Ramadan/Peterson/Lochhead/Maney), Byron Sharp *(in-seat dissenter: distinctiveness vs. differentiation)* |
| 3 | **August Penn** | Creative & Brand Experience | Seth Godin, Donald Miller, Robert McKee, David Ogilvy, Marty Neumeier, Don Norman, Steve Krug |
| 4 | **Emmett Grove** | Growth & Demand Gen | Brian Balfour, Andrew Chen, Elena Verna, Chris Walker, Alex Hormozi |
| 5 | **Mira Voss** | Customer Research & Behavior | Bob Moesta, Teresa Torres, Steve Portigal, Rory Sutherland |
| 6 | **Ada Ledger** | Measurement & ROI | Les Binet & Peter Field, Avinash Kaushik, Claude Hopkins |
| 7 | **Zora Bell** | Ethics, Trust & Responsible AI | Tristan Harris, Safiya Noble, Indra Nooyi, ICC Marketing Code, FEDMA AI charter |
| 8 | **Silas Webb** | Systems & Scale | Donella Meadows, W. Edwards Deming, Satya Nadella |
| 9 | **Wren Halley** | Innovation & Foresight (incl. AI) | Amy Webb, Rita McGrath, Clayton Christensen, Ethan Mollick, Paul Roetzer, Christopher Penn |

Seat-name logic (documented for maintainers): Stratton→strategy, Frame→frame of reference, Penn→the pen, Grove→growth, Mira/Voss→"see"+voice-of-customer, Ledger→the books, Bell→rings the alarm, Webb→web of systems, Halley→the comet seen coming.

**The Synthesizer is a role, not a persona.** It lives in the orchestrator: it structures conflict, preserves dissent, presents options and trade-offs, and never decides. It must avoid false consensus.

**August Penn coherence note:** at seven sources, his charter must be written as one voice (a working Creative Director covering story, art, and experience), not a committee. Dossiers load per-question.

## 4. Dossiers

One file per real-world source, following the structure adapted from `marketingskills`' marketing-council advisor template (credited, see §14): lens, core frameworks (with source and year), documented positions (with sources; at least one contrarian position each), signature questions, best-for / blind spots, voice notes, key works.

Grounding standard: every framework and position must trace to something the source published or said. Two document dossiers (ICC Marketing Code, FEDMA AI charter) hold checklist material rather than persona material.

**Custom advisors:** users can extend the bench. `dossiers/advisor-template.md` defines the format. Public figures require published-source grounding; private advisors (the user's old boss, their CFO) require the user to supply the positions — the plugin must never invent views for a real private person. Custom dossiers live in the user's project (`.claude/board-advisors/`), not the plugin directory, so they survive plugin updates.

## 5. Orchestration

The `marketing-board` skill is the thin orchestrator. Responsibilities:

1. **Load profile** (see §8); if absent, one-time nudge (see §8), then proceed generic.
2. **Detect posture** (see §6) from the user's opening; confirm before convening ("Sounds like you're ideating, not deciding — right?").
3. **Seat the board** for `/board` sessions: 4–6 seats picked via the seating map (question-type → strong fits + natural dissenters), **always including at least one designated dissenter** whose documented positions conflict with the user's lean (10th-man rule; lineage documented: IDF devil's-advocate doctrine, popularized by World War Z). User can override ("add Cassia," "everyone").
4. **Brief the seats**: each spawned agent receives the user's context, profile summary, posture, hostility level, and its designated-dissenter assignment if applicable. Seats run in parallel.
5. **Synthesize** (see §7).
6. **Log the session brief** (see §9).
7. **Hand off**: name concrete next steps and, where the profile lists installed execution packs, the specific skill to execute with.

`/consult <seat>` spawns one agent (with its dossiers) and skips synthesis. `/redteam` convenes with every seat in adversarial stance (see §6).

## 6. Postures

Five session postures; same seats, different stances:

| Posture | User intent | Seat behavior | Synthesis output |
|---------|-------------|---------------|------------------|
| **Decide** | "Help me choose" — open question | Build the option space, argue positions | 2–3 options with pros/cons/risks; trade-off map; decision requested of the user |
| **Pressure-test** | "Here's my call — tear it apart" | Attack the reasoning from their frameworks | Verdicts, weaknesses ranked by severity, what would change their minds |
| **Ideate** | "Give me ideas/direction" | Generate divergently; defer critique | Clustered themes, most promising directions, deferred-critique notes |
| **Retrospect** | "It ran — what do we learn?" | Compare outcomes to the original session brief (re-read it if logged), diagnose deltas | What we got right/wrong and why; extracted lessons; updates to standing assumptions |
| **Brief me** | "Get me smart on X" | Teach from their lenses and dossiers | Structured briefing: what matters, what's contested, what to watch, sources |

`/redteam` is pressure-test at maximum: all seats assume the plan fails and hunt for how (premortem, black swans, worst-case), regardless of hostility level.

## 7. Synthesis format

The synthesizer's board brief contains, in order:

1. **Simulation label** (once, at top): takes are built from each source's published frameworks and positions, not their actual review.
2. **The question before the board** — restatement, stakes, posture.
3. **Seated** — who, why, and who was the designated dissenter.
4. **Seat takes** — each advisor's position: signature questions applied, frameworks applied to the specifics, recommendation with conviction. No name-flavored generic advice: a take that survives with the name swapped is a defect.
5. **Disagreement map** — 2–4 genuine conflicts; the underlying trade-off each represents; what evidence would settle each.
6. **Where the board disagrees with you** — required section; names where advisors pushed back on the *user's* framing or lean, not just on each other. A board that only validates is a mirror.
7. **Chair's synthesis** — recommendation fitted to the user's stage and constraints (never forced consensus; dissent preserved); concrete next steps; tripwires (which advisor's warning to monitor and its signal); execution handoffs.

## 8. Profile

`board-profile.md` personalizes the generic plugin. Location: `~/.claude/board-profile.md` by default; a project-local `.claude/board-profile.md` takes precedence when present.

**Contents** (template in `skills/marketing-board/references/profile-template.md`):

- Role, company, market/category, ICP
- Current goals and initiatives
- Risk appetite
- **Hostility level** (see below)
- Session-brief output location (e.g., an Obsidian vault path); handoff-artifact directory
- Default seats always/never wanted
- **Execution layer:** installed marketing skill packs (names) and the handoff directory

**Hostility levels** — how hard the board pushes:

| Level | Behavior |
|-------|----------|
| **Coach** | Constructive and encouraging; challenges gently; explains reasoning; offers answers readily |
| **Boardroom** *(default)* | Candid professional directness; open disagreement; dissenter rule applies; no softened critiques |
| **Activist** | Assumes the plan is wrong until defended; leads with questions — the user commits to positions before advisors weigh in; attacks weak reasoning; won't accept vague answers. Under Ideate, the user generates first, then the board stresses and extends |

Overridable per session ("convene as activists today").

**`/board-profile` command** — one command, two states:
- No profile: runs an interview (the fields above), offers to import from ecosystem context files if found (`.agents/product-marketing.md`, `brands/<name>/`), writes the file.
- Profile exists: shows current answers; revises conversationally.

**First-session nudge:** any board command without a profile gets one short notice of what the board can't do without context, offers the interview or proceeds generic. Never nags twice.

Ambient `CLAUDE.md` context supplements the profile naturally; the plugin does not depend on it.

## 9. Session logging

Every session ends with a structured brief written to the profile-configured location (default: `board-sessions/` in the current project): date, posture, hostility, seats, the question, seat takes (condensed), disagreement map, synthesis, and a **user-decision line** the user fills or dictates. Retrospect sessions read prior briefs from this location. Filenames: `YYYY-MM-DD-<slug>.md`.

## 10. Grounding rules (non-negotiable, enforced in orchestrator and agents)

- Label every session as simulation, once, at the top.
- No fabricated quotes; direct quotation only with a verifiable source named; otherwise paraphrase attributed to the framework.
- No invented endorsements: an advisor applies their framework to the user's case; the real person is never implied to have an opinion on the user's company.
- Living sources get extra care: positions evolve; time-sensitive claims prefer research; never simulate them commenting on named competitors or controversies.
- Dissent in substance, not caricature: each take is the strongest version of that view.
- When a source's era doesn't cover the topic (Hopkins on TikTok), say so and reason by explicit analogy.
- Ethics floor regardless of hostility level: the board must refuse to help design manipulative, deceptive, or discriminatory tactics; Zora Bell's seat carries the checklists (ICC, FEDMA), and this floor binds all seats.
- The board is advisory; decisions and accountability remain with the human.

## 11. Evals

`evals/` holds test scenarios exercising the board end-to-end: one scenario per posture, a seating-map spot check (question type → expected seats + dissenter present), a grounding check (output contains simulation label; no first-person claims by real sources), and a hostility contrast (same question at Coach vs. Activist produces materially different stance). Evals are the test layer for this repo (prompt content has no unit-testable surface); scenario docs specify inputs and pass criteria so they can be run manually or scripted later.

## 12. Repository, CI, and release engineering

Per the maintainer's repository process policy (public originating repo, GitHub canonical for open source):

- **Done at provisioning (2026-07-08):** public repo `rubicon/rubicon-marketing-board`; description + topics; squash-merge only; auto-delete head branches; Dependabot alerts + security updates; private vulnerability reporting; secret scanning + push protection; CodeQL default setup; branch protection on `main` (PR required, linear history, signed commits, no force-push/deletion, conversation resolution).
- **CI (issue-first, next):** commitlint (Conventional Commits, `@commitlint/config-conventional` type set); PR policy checks (branch regex `^dev/[0-9]+-[a-z0-9.-]+$`, `Closes #N` in body) **with trusted-automation exemptions (Dependabot, release-please) built in from the start**; a `validate-plugin` job (manifest JSON validity, agent/dossier frontmatter, internal link integrity). Required status checks pinned on `main` once these exist.
- **Release automation:** release-please via the shared `rubicon-release-please` GitHub App (manual install step) with 1Password service-account credential sourcing per policy. SemVer; `v`-prefixed tags; release notes with the required witty opening paragraph.
- **Docs set:** universal (README, LICENSE/MIT, CHANGELOG, ARCHITECTURE.md, CLAUDE.md + AGENTS.md pointer stub, .editorconfig) plus public overlay (CONTRIBUTING.md, CODE_OF_CONDUCT.md Contributor Covenant 2.1, SECURITY.md, SUPPORT.md, contrib.rocks grid).
- **README:** badges (CI, release, license, marketplace install); committed SVG header banner; sharp one-liner; intro written in the maintainer's voice (dry, exact, a little sardonic). Premise line: "Every marketer says they want honest feedback; this plugin is what happens if you actually mean it."

## 13. Future ideas (explicitly out of v1)

- Live research pass (pull sources' current takes via installed research skills, with citations)
- Listing in the `rubicon` marketplace in `ai-skills` as an external source
- Scripted eval runner
- Deeper execution-layer integration beyond named handoffs and artifact deposits

## 14. Credits and prior art

- The user's original Personal Board of Directors (five-persona concept, follow-up prompts, session template) — the seed this grows from.
- `coreyhaines31/marketingskills` marketing-council skill — dossier structure, designated-dissenter seating, disagreement map, grounding rules, custom-advisor template. Adopted with credit in README.
- Multi-agent council research and the Perplexity deep-research report (2026-07) — seat charters, decision rights, blind spots, workflow modes, responsible-AI guardrails.
- IDF devil's-advocate doctrine ("Ipcha Mistabra") via the World War Z "10th man" popularization — the dissent mechanism's lineage.
