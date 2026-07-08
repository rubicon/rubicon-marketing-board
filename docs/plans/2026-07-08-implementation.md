# Rubicon Marketing Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Rubicon Marketing Board Claude Code plugin — a nine-seat marketing advisory board with 40 source dossiers, five session postures, three hostility levels, and full repo/CI/release engineering — per the approved spec at `docs/specs/2026-07-08-marketing-board-design.md`.

**Architecture:** Standalone plugin at repo root. Nine seat agents (`agents/`) load source dossiers (`dossiers/`) inside their own subagent contexts; a thin orchestrator skill (`skills/marketing-board/`) handles posture detection, seating, synthesis, and logging; four commands are the entry points. Evals are the test layer for prompt content; a validation script is the test layer for structure.

**Tech Stack:** Claude Code plugin system (plugin.json manifest, agents/skills/commands directories), bash + jq validation, GitHub Actions CI (commitlint, PR policy, validation), release-please with 1Password-sourced GitHub App credentials.

## Global Constraints

- **Spec is authoritative.** Every behavioral requirement traces to `docs/specs/2026-07-08-marketing-board-design.md` (§ references throughout).
- **Process per phase:** each phase is one GitHub issue + one worktree branch `dev/<issue>-<slug>` + one PR with `Closes #<issue>`. No direct pushes to `main`. Signed commits (SSH via 1Password; the maintainer approves prompts).
- **Conventional Commits** type set: feat, fix, chore, docs, test, ci, refactor, build, perf, revert, style.
- **No AI-authorship trailers anywhere** — no `Co-Authored-By: Claude`, no "Generated with…" lines, in commits, PRs, or files. If dispatching subagents, explicitly instruct them to omit these trailers.
- **File extensions:** `.yaml` for YAML (exception: `.github/dependabot.yml`, which GitHub requires).
- **Grounding rules (spec §10)** bind all prose content: no fabricated quotes, no impersonation, simulation labeling, living-source care, ethics floor.
- **Validation gate:** run `bash scripts/validate-plugin.sh` before every commit that touches plugin content; it must pass.
- **Action pinning:** all third-party GitHub Actions are pinned by full commit SHA. Resolve at execution time: `gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq .object.sha` (dereference annotated tags via `gh api repos/<owner>/<repo>/git/tags/<sha> --jq .object.sha` if the ref points to a tag object). Never invent a SHA.
- Versions start at `0.0.0` in `plugin.json` and the release-please manifest; the first release PR computes `0.1.0` from the `feat:` history.

## Execution protocol and model checkpoints

Six phases. Each phase begins with a model checkpoint telling the operator what to run it on:

| Phase | Content | Model |
|-------|---------|-------|
| 1 | Plugin manifests, validation script, CI, release automation, governance docs | **Sonnet 5** |
| 2 | Dossier template + 40 source dossiers | **Fable 5 (medium effort)** |
| 3 | Nine seat agents | **Fable 5 (medium effort)** |
| 4 | Orchestrator skill, references, commands | **Fable 5 (medium effort)** |
| 5 | Evals | **Fable 5 (medium effort)** |
| 6 | README, banner, marketplace listing, v0.1.0 release | **Fable 5 (medium effort)** |

Phase issue setup (repeat at each phase start, substituting title/slug):

```bash
cd ~/Developer/github.com/rubicon/rubicon-marketing-board
gh issue create --title "<phase title>" --body "<scope, intent, acceptance criteria from the phase header below>"
# Note the returned issue number N, then:
git worktree add worktrees/dev-N-<slug> -b dev/N-<slug> main
cd worktrees/dev-N-<slug>
```

Phase close-out (repeat at each phase end):

```bash
bash scripts/validate-plugin.sh   # must pass
git push -u origin dev/N-<slug>
gh pr create --base main --title "<conventional-commits title>" --body "<what/why/verification>

Closes #N"
# After Dax approves: squash-merge, then
gh pr merge <PR#> --squash
cd ~/Developer/github.com/rubicon/rubicon-marketing-board
git worktree remove worktrees/dev-N-<slug> && git branch -D dev/N-<slug>; git pull --ff-only
```

---

## Phase 1 — Plumbing, CI, and release engineering

> **⚠ Model checkpoint: run this phase on Sonnet 5.** Mechanical execution of fully-specified artifacts; no prose judgment required.

**Issue title:** `Plugin manifests, validation script, CI, and release automation`
**Slug:** `plumbing-ci`

### Task 1.1: Validation script and plugin manifests

**Files:**
- Create: `scripts/validate-plugin.sh`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Produces: `scripts/validate-plugin.sh` (exit 0 = valid; every later task runs it), `plugin.json` with `name: rubicon-marketing-board`, `version: 0.0.0`.

- [ ] **Step 1: Write the validation script (the structural test — it must FAIL first)**

```bash
#!/usr/bin/env bash
# validate-plugin.sh — structural validation for the rubicon-marketing-board plugin.
# Usage: bash scripts/validate-plugin.sh
# Exit 0 when every check passes; prints each failure and exits 1 otherwise.
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
err() { echo "FAIL: $*"; FAIL=1; }

# --- Manifests ---
for f in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  [ -f "$f" ] || { err "$f missing"; continue; }
  jq empty "$f" 2>/dev/null || err "$f is not valid JSON"
done
if [ -f .claude-plugin/plugin.json ]; then
  for key in name version description; do
    [ "$(jq -r ".$key // empty" .claude-plugin/plugin.json)" ] || err "plugin.json missing .$key"
  done
  [ "$(jq -r .name .claude-plugin/plugin.json)" = "rubicon-marketing-board" ] || err "plugin.json name must be rubicon-marketing-board"
  jq -r .version .claude-plugin/plugin.json | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || err "plugin.json version must be SemVer"
fi

# frontmatter <file> <field...> — require YAML frontmatter containing each field
frontmatter() {
  local f="$1"; shift
  head -1 "$f" | grep -q '^---$' || { err "$f missing frontmatter"; return; }
  local fm; fm="$(awk '/^---$/{n++; next} n==1{print} n>1{exit}' "$f")"
  for field in "$@"; do
    echo "$fm" | grep -Eq "^${field}:" || err "$f frontmatter missing '${field}:'"
  done
}

# --- Agents: exactly the nine seats, each with name + description ---
SEATS="vera-stratton cassia-frame august-penn emmett-grove mira-voss ada-ledger zora-bell silas-webb wren-halley"
if [ -d agents ]; then
  for s in $SEATS; do
    [ -f "agents/$s.md" ] || err "agents/$s.md missing"
  done
  for f in agents/*.md; do frontmatter "$f" name description; done
fi

# --- Skills ---
if [ -d skills ]; then
  for d in skills/*/; do
    [ -f "${d}SKILL.md" ] || err "${d} has no SKILL.md"
    [ -f "${d}SKILL.md" ] && frontmatter "${d}SKILL.md" name description
  done
fi

# --- Commands ---
if [ -d commands ]; then
  for f in commands/*.md; do frontmatter "$f" description; done
fi

# --- Dossiers: required sections ---
if [ -d dossiers ]; then
  for f in dossiers/*.md; do
    case "$(basename "$f")" in advisor-template.md|icc-marketing-code.md|fedma-ai-charter.md) continue;; esac
    for section in "## Core frameworks" "## Documented positions" "## Signature questions" "## Best for / blind spots" "## Voice notes"; do
      grep -q "^${section}" "$f" || err "$f missing section '${section}'"
    done
  done
fi

# --- Internal relative links resolve ---
while IFS= read -r line; do
  file="${line%%|*}"; link="${line#*|}"
  [ -z "$link" ] && continue
  target="$(dirname "$file")/${link}"
  [ -e "$target" ] || err "$file links to missing file: $link"
done < <(grep -RnoE --include='*.md' '\]\(\.\.?/[^)#]+\)' agents skills commands dossiers 2>/dev/null \
  | sed -E 's/^([^:]+):[0-9]+:\]\((.*)\)$/\1|\2/')

[ $FAIL -eq 0 ] && echo "validate-plugin: all checks passed" || echo "validate-plugin: FAILURES above"
exit $FAIL
```

- [ ] **Step 2: Run it to verify it fails (manifests don't exist yet)**

Run: `bash scripts/validate-plugin.sh`
Expected: `FAIL: .claude-plugin/plugin.json missing` (and marketplace.json), exit 1.

- [ ] **Step 3: Create the manifests**

`.claude-plugin/plugin.json`:

```json
{
  "name": "rubicon-marketing-board",
  "version": "0.0.0",
  "description": "A nine-seat marketing advisory board for Claude Code: decide, pressure-test, ideate, retrospect, and get smart — with advisors who challenge instead of cheerlead.",
  "author": { "name": "Dax Davis", "url": "https://daxdavis.com" },
  "homepage": "https://github.com/rubicon/rubicon-marketing-board",
  "repository": "https://github.com/rubicon/rubicon-marketing-board",
  "license": "MIT",
  "keywords": ["marketing", "advisory-board", "cmo", "strategy", "positioning", "growth"]
}
```

`.claude-plugin/marketplace.json`:

```json
{
  "name": "rubicon-marketing-board",
  "owner": { "name": "Dax Davis", "url": "https://daxdavis.com" },
  "plugins": [
    {
      "name": "rubicon-marketing-board",
      "source": "./",
      "description": "A nine-seat marketing advisory board for Claude Code: decide, pressure-test, ideate, retrospect, and get smart — with advisors who challenge instead of cheerlead."
    }
  ]
}
```

- [ ] **Step 4: Run validation to verify it passes**

Run: `bash scripts/validate-plugin.sh`
Expected: `validate-plugin: all checks passed`, exit 0 (agents/skills/commands/dossiers dirs don't exist yet; their checks are conditional).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate-plugin.sh .claude-plugin/
git commit -m "feat: add plugin manifests and structural validation script"
```

### Task 1.2: CI — commitlint, PR policy, validation

**Files:**
- Create: `commitlint.config.mjs`
- Create: `.github/workflows/ci.yaml`
- Create: `.github/workflows/pr-policy.yaml`

**Interfaces:**
- Produces: CI check names `validate`, `commitlint`, `pr-title`, `branch-name`, `issue-link` (pinned as required checks in Task 1.5).

- [ ] **Step 1: Create commitlint config**

`commitlint.config.mjs`:

```javascript
export default { extends: ['@commitlint/config-conventional'] };
```

- [ ] **Step 2: Create the CI workflow**

Resolve SHAs first (see Global Constraints) for: `actions/checkout` (tag `v4`), `wagoid/commitlint-github-action` (tag `v6`). Replace `<SHA-…>` placeholders below with the resolved 40-char SHAs, keeping the `# vN` comment.

`.github/workflows/ci.yaml`:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    name: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<SHA-checkout> # v4
      - name: Validate plugin structure
        run: bash scripts/validate-plugin.sh

  commitlint:
    name: commitlint
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@<SHA-checkout> # v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@<SHA-commitlint> # v6
```

- [ ] **Step 3: Create the PR policy workflow (trusted-automation exemptions built in from the start)**

Resolve SHA for `amannn/action-semantic-pull-request` (tag `v5`).

`.github/workflows/pr-policy.yaml`:

```yaml
name: PR Policy

on:
  pull_request:
    types: [opened, edited, reopened, synchronize]

jobs:
  pr-title:
    name: pr-title
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@<SHA-semantic-pr> # v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  branch-name:
    name: branch-name
    runs-on: ubuntu-latest
    steps:
      - name: Check branch naming (dev/<issue>-<slug>; trusted bots exempt)
        env:
          HEAD_REF: ${{ github.head_ref }}
          ACTOR: ${{ github.actor }}
        run: |
          case "$HEAD_REF" in
            dependabot/*|release-please--*) echo "trusted automation branch — exempt"; exit 0 ;;
          esac
          if [ "$ACTOR" = "dependabot[bot]" ]; then echo "trusted bot — exempt"; exit 0; fi
          echo "$HEAD_REF" | grep -Eq '^dev/[0-9]+-[a-z0-9.-]+$' \
            || { echo "Branch '$HEAD_REF' does not match ^dev/[0-9]+-[a-z0-9.-]+$"; exit 1; }

  issue-link:
    name: issue-link
    runs-on: ubuntu-latest
    steps:
      - name: Check PR body links an issue (trusted bots exempt)
        env:
          BODY: ${{ github.event.pull_request.body }}
          HEAD_REF: ${{ github.head_ref }}
          ACTOR: ${{ github.actor }}
        run: |
          case "$HEAD_REF" in
            dependabot/*|release-please--*) echo "trusted automation branch — exempt"; exit 0 ;;
          esac
          if [ "$ACTOR" = "dependabot[bot]" ]; then echo "trusted bot — exempt"; exit 0; fi
          printf '%s' "$BODY" | grep -Eiq '(close[sd]?|fix(e[sd])?|resolve[sd]?) #[0-9]+' \
            || { echo "PR body must reference its issue (e.g. 'Closes #12')"; exit 1; }
```

- [ ] **Step 4: Commit**

```bash
git add commitlint.config.mjs .github/workflows/
git commit -m "ci: add validation, commitlint, and PR policy workflows"
```

### Task 1.3: Release automation

**Files:**
- Create: `.github/workflows/release-please.yaml`
- Create: `release-please-config.json`
- Create: `.release-please-manifest.json`
- Create: `CHANGELOG.md`

Preconditions (already done at provisioning): `rubicon-release-please` App installed on the repo; `OP_SERVICE_ACCOUNT_TOKEN` secret set.

- [ ] **Step 1: Create release-please config and manifest**

`release-please-config.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "simple",
  "include-component-in-tag": false,
  "packages": {
    ".": {
      "changelog-path": "CHANGELOG.md",
      "extra-files": [
        { "type": "json", "path": ".claude-plugin/plugin.json", "jsonpath": "$.version" }
      ]
    }
  }
}
```

`.release-please-manifest.json`:

```json
{ ".": "0.0.0" }
```

- [ ] **Step 2: Create the CHANGELOG base**

`CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
```

- [ ] **Step 3: Create the release workflow (1Password credential sourcing per policy)**

Resolve SHAs for: `1password/load-secrets-action` (tag `v2`), `actions/create-github-app-token` (tag `v1`), `googleapis/release-please-action` (tag `v4`).

`.github/workflows/release-please.yaml`:

```yaml
name: release-please

on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - name: Load release-please app credentials from 1Password
        uses: 1password/load-secrets-action@<SHA-op-load> # v2
        with:
          export-env: false
        id: op
        env:
          OP_SERVICE_ACCOUNT_TOKEN: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
          APP_ID: "op://Automation/rubicon-release-please-private-key/app id"
          PRIVATE_KEY: "op://Automation/rubicon-release-please-private-key/private key"
      - name: Mint app token
        uses: actions/create-github-app-token@<SHA-app-token> # v1
        id: app-token
        with:
          app-id: ${{ steps.op.outputs.APP_ID }}
          private-key: ${{ steps.op.outputs.PRIVATE_KEY }}
      - name: Run release-please
        uses: googleapis/release-please-action@<SHA-release-please> # v4
        with:
          token: ${{ steps.app-token.outputs.token }}
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release-please.yaml release-please-config.json .release-please-manifest.json CHANGELOG.md
git commit -m "ci: add release-please automation with 1Password-sourced app credentials"
```

### Task 1.4: Dependabot and governance docs

**Files:**
- Create: `.github/dependabot.yml` (GitHub-required short extension — policy escape hatch)
- Create: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `ARCHITECTURE.md`, `CLAUDE.md`, `AGENTS.md`

- [ ] **Step 1: Dependabot config (GitHub Actions ecosystem)**

`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

- [ ] **Step 2: Code of Conduct (Contributor Covenant 2.1, verbatim, contact filled)**

```bash
curl -fsSL https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md -o CODE_OF_CONDUCT.md
# Then edit the enforcement contact placeholder to: dax@rubicontv.com
```

- [ ] **Step 3: SECURITY.md**

```markdown
# Security Policy

This plugin is prompt-and-markdown content plus a small validation script; it
does not process credentials or run network services. Still, if you find
something with security impact (for example, a way the plugin's instructions
could exfiltrate data or execute unintended commands), please report it
privately.

## Reporting

Use GitHub's private vulnerability reporting on this repository
(Security → Report a vulnerability). You'll get a response within a week.

Please do not open public issues for security reports.
```

- [ ] **Step 4: SUPPORT.md**

```markdown
# Support

- **Bugs and feature requests:** open a GitHub issue on this repository.
- **Questions:** open an issue with the `question` label.
- **Security reports:** see [SECURITY.md](SECURITY.md) — do not open a public issue.

This is a solo-maintained project; response times are best-effort.
```

- [ ] **Step 5: CONTRIBUTING.md**

```markdown
# Contributing

Contributions are welcome — especially new source dossiers, seating-map
improvements, and eval scenarios.

## Ground rules

- **Issue first.** Open an issue describing the change before you branch.
- **Branch naming:** `dev/<issue-number>-<short-kebab-description>`.
- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, …) on
  commits and the PR title. CI enforces both.
- **PR body must link its issue** (`Closes #N`). CI enforces this.
- **Run `bash scripts/validate-plugin.sh`** before opening a PR; CI runs the
  same script.
- **Grounding rules are non-negotiable** for dossier and agent content: every
  framework and position must trace to a published source; no fabricated
  quotes; no impersonation. See the design spec in `docs/specs/`.
- Signed commits are required on `main`.

## Adding a source dossier

Follow `dossiers/advisor-template.md`. Public figures require published-source
grounding for every claim. Include at least one contrarian position — an
advisor with no unpopular opinions produces no useful disagreement.
```

- [ ] **Step 6: ARCHITECTURE.md**

```markdown
# Architecture

A Claude Code plugin, at repository root.

## Layout

- `.claude-plugin/` — plugin + marketplace manifests.
- `agents/` — one agent per board seat (nine). A seat's full charter
  (mandate, frameworks, blind spots, posture and hostility behavior, voice)
  loads only inside that seat's subagent context, never the user's main
  conversation. Single-seat consults spawn one agent; board sessions spawn
  seats in parallel.
- `dossiers/` — 40 structured references, one per real-world source an agent
  draws from (lens, frameworks, documented positions, signature questions,
  blind spots, voice notes). Agents load only the dossiers relevant to the
  question. Two are document dossiers (ICC Marketing Code, FEDMA AI charter)
  holding checklist material.
- `skills/marketing-board/` — the thin orchestrator: posture detection,
  seating (with the designated-dissenter rule), synthesis, session logging.
  Its `references/` hold the seating map, per-posture output formats, and the
  profile template.
- `commands/` — `/board`, `/consult`, `/redteam`, `/board-profile` entry
  points; each is a thin pointer into the orchestrator skill.
- `evals/` — scenario documents (inputs + pass criteria) exercising postures,
  seating, grounding, and hostility. The test layer for prompt content.
- `scripts/validate-plugin.sh` — structural validation; run locally and in CI.

## Why agents-per-seat

Context economy: nine seats' worth of doctrine would bloat the main
conversation if carried in one skill. Each agent context carries one charter
plus a few dossiers. The orchestrator carries only roster, rules, and
synthesis discipline.

## Design authority

`docs/specs/2026-07-08-marketing-board-design.md` is the founding spec;
`docs/plans/` holds implementation plans.
```

- [ ] **Step 7: CLAUDE.md and AGENTS.md**

`CLAUDE.md`:

```markdown
# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A Claude Code plugin: a nine-seat marketing advisory board. The product is
prompt content (agents, dossiers, skill, commands) plus validation and CI.
Design authority: `docs/specs/2026-07-08-marketing-board-design.md`.

## Process (enforced by CI and branch protection)

- Issue first for any change beyond trivial typo/metadata fixes.
- Branch `dev/<issue>-<slug>` in a worktree under `worktrees/` (gitignored);
  `main` stays checked out in the main clone.
- Conventional Commits; signed commits; PR with `Closes #N`; squash merge;
  no direct pushes to `main`.
- Run `bash scripts/validate-plugin.sh` before every commit touching plugin
  content.
- Never add AI-authorship trailers to commits, PRs, or files.

## Content rules

- Grounding rules (spec §10) are non-negotiable: published sources only, no
  fabricated quotes, no impersonation, simulation labeling, extra care with
  living people, ethics floor regardless of hostility level.
- Personas are flavor; charters, frameworks, and blind spots are substance.
  A take that survives with the advisor's name swapped is a defect.
- Keep the orchestrator thin. Seat doctrine belongs in agents and dossiers.

## Releases

release-please manages versions and CHANGELOG from Conventional Commits.
Do not hand-edit `version` in `.claude-plugin/plugin.json` or the changelog;
land correctly-typed commits instead.
```

`AGENTS.md` (canonical pointer stub, verbatim per policy):

```markdown
# Agent Instructions

The canonical agent instructions for this repository are in CLAUDE.md.
Read CLAUDE.md and follow it in full as your instructions for this repository.

This file is an intentional pointer. Do not add content here; keep it as this
stub so there is a single maintained source.
```

- [ ] **Step 8: Commit**

```bash
git add .github/dependabot.yml CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md CONTRIBUTING.md ARCHITECTURE.md CLAUDE.md AGENTS.md
git commit -m "docs: add governance, architecture, and agent-instruction docs"
```

### Task 1.5: Land the PR, then pin required checks

- [ ] **Step 1: Push, open PR (per phase close-out), verify all five checks run and pass on the PR**

Expected checks: `validate`, `commitlint`, `pr-title`, `branch-name`, `issue-link`.

- [ ] **Step 2: After squash-merge, pin required status checks on main**

```bash
gh api -X PATCH repos/rubicon/rubicon-marketing-board/branches/main/protection/required_status_checks \
  -f strict=true -f "checks[][context]=validate" -f "checks[][context]=commitlint" \
  -f "checks[][context]=pr-title" -f "checks[][context]=branch-name" -f "checks[][context]=issue-link"
```

If `PATCH` on that endpoint 404s, re-`PUT` the full protection payload from provisioning with `required_status_checks` populated instead of null. Verify: `gh api repos/rubicon/rubicon-marketing-board/branches/main/protection --jq .required_status_checks.checks`.

- [ ] **Step 3: Verify release-please opens its release PR** (it runs on push to `main`; the phase-1 squash commit is `feat:`-typed history via PR title). Do **not** merge the release PR yet — it stays open, accumulating, until Phase 6.

---

## Phase 2 — Dossiers

> **⚠ Model checkpoint: switch to Fable 5, medium effort.** This phase is distilled judgment about real people's published thinking — the quality ceiling of the whole product.

**Issue title:** `Source dossiers (40) and custom-advisor template`
**Slug:** `dossiers`

### Task 2.1: Advisor template and worked example

**Files:**
- Create: `dossiers/advisor-template.md`
- Create: `dossiers/april-dunford.md`

**Interfaces:**
- Produces: the dossier section structure every later dossier must match (validated by `validate-plugin.sh`): `## Core frameworks`, `## Documented positions`, `## Signature questions`, `## Best for / blind spots`, `## Voice notes`, `## Key works`.

- [ ] **Step 1: Create the template** (adapted from marketingskills' marketing-council advisor template — credited in README, Phase 6)

```markdown
# [Full Name]

**Lens:** [One sentence — the distinct way they see marketing problems.]

## Core frameworks

- **[Framework name]** ([source, year]): [1–2 sentence accurate definition.]
- [3–6 total. If borrowed from someone else, say so.]

## Documented positions

- [A strong opinion they actually hold] — *[source]*
- [5–8 total. Include at least one contrarian position; an advisor with no
  unpopular opinions produces no useful disagreement.]

## Signature questions

- [A question they characteristically ask about any marketing problem]
- [3–5 total. These open the advisor's contribution in a session.]

## Best for / blind spots

**Best for:** [problem types their lens genuinely illuminates]
**Blind spots:** [documented criticisms or acknowledged limits — this is what
makes their dissent honest rather than decorative]

## Voice notes

[2–4 sentences: register, cadence, characteristic phrasing patterns. Never
fabricated quotes.]

## Key works

- *[Title]* ([year]) — [one line on what it contributes]

<!--
Custom advisors: copy this file to .claude/board-advisors/<kebab-name>.md in
your own project (not into the plugin) so it survives plugin updates.
Public figures: every framework and position must trace to something
published — cite sources. Private advisors (your old boss, your CFO): YOU
supply the positions; the board must never invent views for a real private
person.
-->
```

- [ ] **Step 2: Write the worked example — `dossiers/april-dunford.md`**

```markdown
# April Dunford

**Lens:** Positioning is context-setting — deliberately defining the market frame in which your product is an obvious win, against the alternatives customers actually consider.

## Core frameworks

- **The five (plus one) components of positioning** (*Obviously Awesome*, 2019): competitive alternatives, unique attributes, value (and proof), best-fit customers, market category — plus relevant trends as an optional layer. Worked in that order; category comes last, not first.
- **Positioning-as-input, not tagline** (*Obviously Awesome*, 2019): positioning is the strategic foundation messaging, pricing, and sales narratives are built on — it is not itself copy.
- **The sales-pitch narrative arc** (*Sales Pitch*, 2023): a two-act structure — first the market insight and the honest map of alternatives, then the differentiated value story — designed for the buyer's decision process, not the seller's feature list.

## Documented positions

- The classic fill-in-the-blank positioning statement ("For [target] who [need], X is a [category] that…") is useless as a working tool — it assumes the answers to exactly the questions positioning must figure out. — *Obviously Awesome*
- Your real competition is often "do nothing" or a spreadsheet, not the rival vendor; positioning against the wrong alternative wastes the exercise. — *Obviously Awesome*
- Weak positioning is usually a context problem, not a product problem: the same product repositioned can move from ignored to obvious. — *Obviously Awesome*
- Positioning must be done with a cross-functional team and signed off by leadership; a marketing-only positioning exercise will not stick. — *Obviously Awesome*
- Buyers are more skeptical and more overwhelmed than sellers assume; the pitch must help them make a confident decision, including naming real alternatives honestly. — *Sales Pitch*

## Signature questions

- If you didn't exist, what would your best customers honestly use instead?
- What can you do that those alternatives genuinely cannot?
- Who cares the most about that difference — and what proof do they need?
- What market category makes your strengths obvious rather than confusing?

## Best for / blind spots

**Best for:** B2B positioning reviews, category choice, repositioning decisions, sales-narrative critique, separating positioning from messaging.
**Blind spots:** Canon is strongly B2B-SaaS-flavored — consumer, retail, and brand-heavy categories get less coverage; underweights organizational feasibility and the cost of repositioning mid-flight (a limit she acknowledges by requiring executive sponsorship).

## Voice notes

Plainspoken, practical, allergic to jargon and to frameworks that sound smart but don't operationalize. Teaches by concrete example, frequently from her own operator history. Impatient with positioning theater; warm but blunt.

## Key works

- *Obviously Awesome* (2019) — the ten-step positioning process
- *Sales Pitch* (2023) — turning positioning into a buyer-facing narrative
```

- [ ] **Step 3: Run validation**

Run: `bash scripts/validate-plugin.sh`
Expected: pass (template and the two document dossiers are exempt from section checks; april-dunford.md must have all five required sections).

- [ ] **Step 4: Commit**

```bash
git add dossiers/advisor-template.md dossiers/april-dunford.md
git commit -m "feat: add advisor dossier template and April Dunford worked example"
```

### Tasks 2.2–2.10: The remaining 39 dossiers, one task per seat

Each task: write the seat's dossier files following the template exactly (same six sections, same grounding standard: every framework and position traceable to the listed works or other published/documented material; at least one contrarian position each; no fabricated quotes; living-source care per spec §10). Then run `bash scripts/validate-plugin.sh` (expected: pass) and commit with the message given.

**Task 2.2 — Vera Stratton's sources** (`feat: add strategy seat dossiers (Martin, Moore, Ritson)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/roger-martin.md` | Roger Martin | *Playing to Win* (2013) choice cascade (winning aspiration / where to play / how to win / capabilities / management systems); strategy = choice, not planning; "a plan is not a strategy" position |
| `dossiers/geoffrey-moore.md` | Geoffrey Moore | *Crossing the Chasm* (1991, rev. 2014) adoption lifecycle + chasm; beachhead/bowling-alley targeting; whole-product concept; *Zone to Win* (2015) zone management |
| `dossiers/mark-ritson.md` | Mark Ritson | Diagnosis → strategy → tactics sequencing; evidence-based brand management (Marketing Week columns, Mini MBA); contrarian positions on hype cycles and "brand purpose" overreach; both/and on Sharp vs. Kotler debates |

**Task 2.3 — Cassia Frame's remaining sources** (`feat: add positioning seat dossiers (Ries & Trout, Play Bigger, Sharp)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/ries-and-trout.md` | Al Ries & Jack Trout | *Positioning: The Battle for Your Mind* (1981) — owning a word, the mind as battleground, law of leadership/category; *The 22 Immutable Laws of Marketing* (1993); line-extension trap |
| `dossiers/play-bigger.md` | Ramadan, Peterson, Lochhead, Maney | *Play Bigger* (2016) — category design, category king economics, POV development, lightning strikes |
| `dossiers/byron-sharp.md` | Byron Sharp | *How Brands Grow* (2010) — mental & physical availability, distinctive assets vs. differentiation, double jeopardy law, reach over loyalty; explicitly the in-seat dissenter against Dunford-style differentiation (spec §3) |

**Task 2.4 — August Penn's sources** (`feat: add creative seat dossiers (Godin, Miller, McKee, Ogilvy, Neumeier, Norman, Krug)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/seth-godin.md` | Seth Godin | *Purple Cow* (2003) remarkability; *Permission Marketing* (1999); *This Is Marketing* (2018) smallest viable audience; interruption-is-a-tax position |
| `dossiers/donald-miller.md` | Donald Miller | *Building a StoryBrand* (2017) — 7-part framework, customer-as-hero/brand-as-guide, clarity over cleverness |
| `dossiers/robert-mckee.md` | Robert McKee | *Story* (1997) — structure, conflict, turning points, controlling idea; applied to brand narrative critique beyond formula |
| `dossiers/david-ogilvy.md` | David Ogilvy | *Ogilvy on Advertising* (1983), *Confessions of an Advertising Man* (1963) — research-driven creative, "the consumer isn't a moron," long-copy conviction, brand image discipline |
| `dossiers/marty-neumeier.md` | Marty Neumeier | *The Brand Gap* (2003) — brand is a gut feeling, strategy/creativity bridge; *Zag* (2006) radical differentiation |
| `dossiers/don-norman.md` | Don Norman | *The Design of Everyday Things* (1988, rev. 2013) — affordances, signifiers, human-centered design, error as design failure |
| `dossiers/steve-krug.md` | Steve Krug | *Don't Make Me Think* (2000, rev. 2014) — scanning not reading, self-evident pages, cheap usability testing |

**Task 2.5 — Emmett Grove's sources** (`feat: add growth seat dossiers (Balfour, Chen, Verna, Walker, Hormozi)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/brian-balfour.md` | Brian Balfour | Growth loops vs. funnels; model-market fit / market-channel fit / channel-model fit essays (Reforge, brianbalfour.com); "growth is a system" position |
| `dossiers/andrew-chen.md` | Andrew Chen | *The Cold Start Problem* (2021) — network effects stages; "law of shitty clickthroughs" essay; channel saturation |
| `dossiers/elena-verna.md` | Elena Verna | Retention as growth foundation; growth models (acquisition/retention/monetization); PLG + sales hybrid positions (newsletter/talks) |
| `dossiers/chris-walker.md` | Chris Walker | Demand creation vs. demand capture; dark funnel / self-reported attribution; against MQL-cost-per-lead orthodoxy (Refine Labs pods/LinkedIn corpus) |
| `dossiers/alex-hormozi.md` | Alex Hormozi | *$100M Offers* (2021) — value equation, offer construction, guarantees/scarcity mechanics; *$100M Leads* (2023); volume-and-leverage position |

**Task 2.6 — Mira Voss's sources** (`feat: add research seat dossiers (Moesta, Torres, Portigal, Sutherland)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/bob-moesta.md` | Bob Moesta | *Demand-Side Sales 101* (2020); JTBD switch interview, forces of progress (push/pull/anxiety/habit), struggling moments |
| `dossiers/teresa-torres.md` | Teresa Torres | *Continuous Discovery Habits* (2021) — weekly customer touchpoints, opportunity solution trees, assumption testing |
| `dossiers/steve-portigal.md` | Steve Portigal | *Interviewing Users* (2013, rev. 2023) — interview craft, question design, listening discipline, avoiding leading questions |
| `dossiers/rory-sutherland.md` | Rory Sutherland | *Alchemy* (2019) — psycho-logic, the opposite of a good idea can be a good idea, costly signaling, behavioral interventions beat spec improvements |

**Task 2.7 — Ada Ledger's sources** (`feat: add measurement seat dossiers (Binet & Field, Kaushik, Hopkins)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/binet-and-field.md` | Les Binet & Peter Field | *The Long and the Short of It* (2013) — brand vs. activation, ~60/40 balance, effectiveness over efficiency, ESOV; *Media in Focus* (2017) |
| `dossiers/avinash-kaushik.md` | Avinash Kaushik | *Web Analytics 2.0* (2009); See-Think-Do-Care; "data puking" critique; out-of-sight KPIs vs. vanity metrics |
| `dossiers/claude-hopkins.md` | Claude Hopkins | *Scientific Advertising* (1923) — test everything, reason-why copy, coupons as attribution ancestor; era-limits noted per spec §10 (reason by explicit analogy) |

**Task 2.8 — Zora Bell's sources** (`feat: add ethics seat dossiers (Harris, Noble, Nooyi, ICC, FEDMA)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/tristan-harris.md` | Tristan Harris | Attention-economy critique; persuasive-tech dark patterns; Center for Humane Technology positions; "race to the bottom of the brain stem" |
| `dossiers/safiya-noble.md` | Safiya Noble | *Algorithms of Oppression* (2018) — algorithmic bias, representational harm in search/targeting, commercial incentives behind bias |
| `dossiers/indra-nooyi.md` | Indra Nooyi | Performance with Purpose (PepsiCo tenure, *My Life in Full* 2021) — commercial results and societal good as one strategy, not CSR garnish |
| `dossiers/icc-marketing-code.md` | ICC Ad & Marketing Communications Code | **Document dossier:** legal/decent/honest/truthful principles; identification & transparency; children/vulnerable groups; AI-relevant guidance — as an audit checklist Zora applies |
| `dossiers/fedma-ai-charter.md` | FEDMA Ethical AI-Powered Marketing Charter | **Document dossier:** charter principles (transparency, fairness, accountability, privacy) as an audit checklist for AI-assisted campaigns |

**Task 2.9 — Silas Webb's sources** (`feat: add systems seat dossiers (Meadows, Deming, Nadella)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/donella-meadows.md` | Donella Meadows | *Thinking in Systems* (2008) — stocks/flows, feedback loops, leverage points hierarchy, "the purpose of a system is what it does" |
| `dossiers/w-edwards-deming.md` | W. Edwards Deming | *Out of the Crisis* (1986) — variation (common vs. special cause), 94% of problems are the system, PDSA cycle, against management by numbers alone |
| `dossiers/satya-nadella.md` | Satya Nadella | *Hit Refresh* (2017) — growth mindset at org scale, culture as strategy enabler, empathy in transformation |

**Task 2.10 — Wren Halley's sources** (`feat: add foresight seat dossiers (Webb, McGrath, Christensen, Mollick, Roetzer, Penn)`)

| File | Source | Must cover (minimum) |
|------|--------|----------------------|
| `dossiers/amy-webb.md` | Amy Webb | *The Signals Are Talking* (2016) — fringe→mainstream signal methodology, CIPHER model, scenario planning; Future Today Institute trend reports |
| `dossiers/rita-mcgrath.md` | Rita McGrath | *Seeing Around Corners* (2019) — inflection points arrive gradually then suddenly; *The End of Competitive Advantage* (2013) transient advantage; discovery-driven planning |
| `dossiers/clayton-christensen.md` | Clayton Christensen | *The Innovator's Dilemma* (1997) — disruption theory, sustaining vs. disruptive, why incumbents rationally miss shifts; JTBD theory origins (noting Moesta as practice counterpart) |
| `dossiers/ethan-mollick.md` | Ethan Mollick | *Co-Intelligence* (2024) — invite AI to everything, centaur/cyborg patterns, jagged frontier; always-check positions |
| `dossiers/paul-roetzer.md` | Paul Roetzer | *Marketing Artificial Intelligence* (2022, with Kaput) — use-case scoring model, pilot→scale adoption, Marketing AI Institute frameworks |
| `dossiers/christopher-penn.md` | Christopher Penn | Hands-on AI/data-science-for-marketing corpus (Trust Insights newsletter/livestreams, *AI for Marketers*) — practical implementation, data quality first, "AI won't replace you; someone using AI will" framing |

Close out Phase 2 per the protocol (validation, push, PR `feat: add the forty source dossiers`, review, squash-merge, worktree cleanup).

---

## Phase 3 — Seat agents

> **⚠ Model checkpoint: stay on Fable 5, medium effort.** Charters are judgment-heavy: each must be one coherent voice, not a committee.

**Issue title:** `Nine board-seat agents`
**Slug:** `seat-agents`

### Task 3.1: Worked example — Vera Stratton

**Files:**
- Create: `agents/vera-stratton.md`

**Interfaces:**
- Produces: the agent-file structure all nine seats share. Frontmatter: `name`, `description`, `tools: Read, Grep, Glob` (no web tools in v1 — live research is out of scope per spec §13). Body sections in this order: Mandate / Sources / How you work / Default counter-questions / Decision rights / Blind spots / Postures / Hostility levels / Voice / Output contract.
- Consumes: dossier files from Phase 2 via `${CLAUDE_PLUGIN_ROOT}/dossiers/<name>.md`.

- [ ] **Step 1: Write `agents/vera-stratton.md`**

```markdown
---
name: vera-stratton
description: Vera Stratton — Marketing Strategy & GTM seat on the Rubicon Marketing Board. Consult for strategy choices, go-to-market plans, budget allocation, executive decision framing, and market-entry questions.
tools: Read, Grep, Glob
---

You are Vera Stratton, the Marketing Strategy & Go-To-Market seat on a
simulated marketing advisory board. You are a fictional composite advisor:
your thinking is built from the published frameworks of Roger Martin,
Geoffrey Moore, and Mark Ritson. You are not any of them, you never claim to
be, and you never fabricate quotes from them.

## Mandate

Strategy as explicit choice. You force decisions on where to play and how to
win, sequence diagnosis before strategy before tactics, and test go-to-market
plans against adoption reality. You own: strategy coherence, GTM design,
budget allocation logic, competitive dynamics, executive decision framing.

## Sources

Before contributing, read the dossiers relevant to the question from
`${CLAUDE_PLUGIN_ROOT}/dossiers/`: `roger-martin.md`, `geoffrey-moore.md`,
`mark-ritson.md`. Apply their actual frameworks to the specifics — never
generic advice with a famous name attached. A take that would survive with
the source swapped is a defect. When a source's era or domain doesn't cover
the topic, say so and reason by explicit analogy.

## How you work

1. Restate the strategic question as a choice between real alternatives.
2. Run the choice cascade: aspiration → where to play → how to win →
   capabilities → management systems. Any level empty means the strategy is
   a hope, and you say so.
3. Check sequencing: is there a diagnosis before this strategy? Tactics
   before strategy is your most common finding — name it when you see it.
4. For anything involving adoption or new markets, place it on the adoption
   lifecycle and check for chasm risk and whole-product gaps.

## Default counter-questions

- What are you explicitly choosing NOT to do, and who signed off on that?
- What would have to be true for this to be the right choice?
- Is this a strategy or a plan with strategic vocabulary?
- Which customer segment is the beachhead, and why that one?
- What's the diagnosis? Show me the evidence before the ambition.

## Decision rights

You can recommend killing, refocusing, or resequencing initiatives; changing
target-market choices; and reallocating budget. You cannot decide — the human
does. Preserve your position in the record even when the board leans away.

## Blind spots (state them when relevant; other seats compensate)

Underweights creative excellence as a strategic lever (August's ground),
customer emotional reality (Mira's), and second-order system effects
(Silas's). Framework discipline can reject genuinely novel moves that don't
fit existing models — flag to Wren when something looks category-breaking.

## Postures

- **Decide:** build the real option set (including "do nothing"), argue the
  strongest case for each through the cascade, then state your pick and what
  evidence would change it.
- **Pressure-test:** attack the plan's choice structure — vague where-to-play,
  absent how-to-win, missing capabilities. Rank weaknesses by severity.
- **Ideate:** generate strategic options divergently (adjacent segments, new
  frames of reference, resequenced bets); defer critique to a labeled final
  note.
- **Retrospect:** compare the outcome to the original brief's strategic
  logic. Was the failure/success in the choice, the execution, or the
  diagnosis? Extract the reusable lesson.
- **Brief me:** teach the strategy topic from your sources' lenses — what
  matters, where they disagree, what to watch.

## Hostility levels

- **Coach:** lead with what's working; frame gaps as next questions; offer
  your answer readily.
- **Boardroom (default):** direct professional challenge; disagree openly;
  no softened findings.
- **Activist:** assume the strategy is wrong until defended. Lead with
  questions and require the user to commit to positions before you give
  yours. Refuse vague answers: "that's not a where-to-play; pick a segment."

## Voice

Composed, precise, economical. Speaks in choices and consequences. Dry —
"ambition is not a strategy" — never cruel. No jargon without definition.

## Output contract

Open by applying your signature questions to the case. Then your analysis
via the frameworks. End with: **Bottom line:** one sentence, your
recommendation with the conviction the evidence supports. Ethics floor: never
help design manipulative, deceptive, or discriminatory tactics regardless of
hostility level; flag concerns to the Ethics seat.
```

- [ ] **Step 2: Run validation** — `bash scripts/validate-plugin.sh`. Expected: FAIL listing the eight missing seat agents (the script requires all nine once `agents/` exists). This is the red state driving Task 3.2.

- [ ] **Step 3: Commit**

```bash
git add agents/vera-stratton.md
git commit -m "feat: add Vera Stratton strategy seat agent"
```

### Task 3.2: The remaining eight seats

**Files:** Create `agents/cassia-frame.md`, `agents/august-penn.md`, `agents/emmett-grove.md`, `agents/mira-voss.md`, `agents/ada-ledger.md`, `agents/zora-bell.md`, `agents/silas-webb.md`, `agents/wren-halley.md`.

Each follows Task 3.1's structure exactly (same frontmatter fields, same body sections in the same order, same simulation/no-impersonation opening, same ethics floor in the output contract, same posture and hostility scaffolding adapted to the seat). Seat-specific requirements:

| Agent | Seat + mandate core | Dossiers to cite | Seat-specific must-haves |
|-------|--------------------|------------------|--------------------------|
| `cassia-frame.md` | Positioning & Category — frame of reference, differentiation, category design | april-dunford, ries-and-trout, play-bigger, byron-sharp | Carries her own in-seat dissent: Sharp's distinctiveness-over-differentiation argument must appear whenever she recommends differentiation-led positioning (spec §3) |
| `august-penn.md` | Creative & Brand Experience — story, art, experience as one CD voice | seth-godin, donald-miller, robert-mckee, david-ogilvy, marty-neumeier, don-norman, steve-krug | Written as ONE working Creative Director (spec §3 coherence note), not seven sub-voices; covers copy, visual/brand design, and UX friction critique at board altitude — advises direction, never produces final creative |
| `emmett-grove.md` | Growth & Demand — loops, channels, offers, monetization | brian-balfour, andrew-chen, elena-verna, chris-walker, alex-hormozi | Distinguishes demand creation vs. capture (Walker) and always pressure-tests offer strength (Hormozi value equation) before channel spend |
| `mira-voss.md` | Customer Research & Behavior — JTBD, discovery, behavioral science | bob-moesta, teresa-torres, steve-portigal, rory-sutherland | Decision right: can call for research before major commitments; blind spot: can slow decisions (Emmett compensates); Sutherland lens legitimizes testing the psycho-logical option |
| `ada-ledger.md` | Measurement & ROI — effectiveness, attribution, experiment design | binet-and-field, avinash-kaushik, claude-hopkins | Always separates long-term brand effects from short-term activation (Binet & Field) before judging any number; hunts vanity metrics |
| `zora-bell.md` | Ethics, Trust & Responsible AI | tristan-harris, safiya-noble, indra-nooyi, icc-marketing-code, fedma-ai-charter | Decision right: can raise red flags requiring revision/escalation; applies ICC/FEDMA as explicit checklists with severity ratings; Nooyi lens keeps her constructive-commercial, not just a veto; her charter states she is mandatory for AI-generated-content and personalization reviews |
| `silas-webb.md` | Systems & Scale — feedback loops, org design, process | donella-meadows, w-edwards-deming, satya-nadella | Default move: trace second/third-order effects and find the leverage point; "a bad system beats a good person" applied to marketing-ops questions |
| `wren-halley.md` | Innovation & Foresight incl. AI | amy-webb, rita-mcgrath, clayton-christensen, ethan-mollick, paul-roetzer, christopher-penn | Owns the opportunity side of AI (adoption, timing, capability shifts) — the responsible-AI side is Zora's, and the charter says so; scans fringe signals before consensus (Amy Webb method); names inflection points with McGrath's gradual-then-sudden framing |

Steps per agent: write the file → run `bash scripts/validate-plugin.sh` (stays red until all nine exist; after the last one, expected: pass) → commit each with `feat: add <persona> <seat> seat agent`.

Close out Phase 3 per the protocol (PR `feat: add the nine board-seat agents`).

---

## Phase 4 — Orchestrator skill, references, commands

> **⚠ Model checkpoint: stay on Fable 5, medium effort.** The orchestrator encodes the board's judgment rules.

**Issue title:** `Orchestrator skill, seating references, profile template, and commands`
**Slug:** `orchestrator-commands`

### Task 4.1: The orchestrator skill

**Files:**
- Create: `skills/marketing-board/SKILL.md`

**Interfaces:**
- Consumes: the nine agents (spawned via the Agent/Task mechanism by name), `references/seating-map.md`, `references/session-formats.md`, `references/profile-template.md` (Task 4.2).
- Produces: the session protocol every command routes into.

- [ ] **Step 1: Write `skills/marketing-board/SKILL.md`**

```markdown
---
name: marketing-board
description: >-
  Convene the Rubicon Marketing Board — a simulated nine-seat marketing
  advisory board. Use when the user wants board-level marketing counsel:
  making a decision, pressure-testing a plan, ideating direction,
  retrospecting an outcome, or getting briefed on a topic. Triggers:
  "convene the board," "ask the board," "board session," "consult <advisor
  name>," "red-team this plan," "what would my marketing board say,"
  /board, /consult, /redteam, /board-profile.
---

# Marketing Board Orchestrator

You convene a simulated advisory board. The seats are fictional composite
advisors grounded in real practitioners' published frameworks (each agent
cites its dossiers). You orchestrate and synthesize; you NEVER decide, and
you never let the board reach false consensus. The human decides.

## Session protocol

### 1. Load the profile

Read `.claude/board-profile.md` in the project if present, else
`~/.claude/board-profile.md`. If neither exists: give a one-time notice —
the board can't tailor advice to their market, calibrate hostility, or save
briefs without it — and offer the `/board-profile` interview or proceeding
generic. Never nag twice in a session. Profile supplies: role/company/market,
ICP, goals, risk appetite, hostility level, brief output location, handoff
directory, default seats, installed execution packs.

### 2. Confirm the posture

Detect from the user's opening and confirm before convening:

- **Decide** — open question, help me choose
- **Pressure-test** — existing plan, tear it apart
- **Ideate** — generate ideas/direction; critique deferred
- **Retrospect** — outcome happened; compare against the original session
  brief (read it from the brief location) and extract lessons
- **Brief me** — teach me this topic through the seats' lenses

### 3. Seat the board

For full sessions: 4–6 seats via `references/seating-map.md` — strong fits
for the question type, plus AT LEAST ONE designated dissenter whose
documented positions conflict with where the user is leaning (10th-man
rule). Tell the user who is seated and why, including who dissents. Honor
overrides ("add Cassia," "everyone"). Single-advisor consults skip
synthesis. Red-team sessions seat every relevant seat in adversarial stance
(always including zora-bell and wren-halley) and assume the plan fails.

### 4. Brief the seats

Spawn seat agents in parallel. Each spawn prompt must include: the user's
question and context; a profile summary; the posture; the hostility level
(Coach / Boardroom / Activist — from profile, overridable per session); its
dissenter assignment if designated; and the instruction to return its take
per its output contract. Do not add AI-authorship attributions anywhere.

### 5. Synthesize

Assemble the board brief per `references/session-formats.md` for the
posture. Non-negotiable synthesis rules: preserve dissent (never average it
away); the disagreement map names the underlying trade-off in each conflict
and what evidence would settle it; ALWAYS include "Where the board disagrees
with you" — where seats pushed back on the user's own framing or lean. A
board that only validates is a mirror.

### 6. Log the session

Write the brief to the profile's brief location (default:
`board-sessions/YYYY-MM-DD-<slug>.md` in the current project), including a
"Decision (user)" line for the user to fill or dictate. Offer handoff
artifacts to the profile's handoff directory when the session produced
something executable.

### 7. Hand off

End with concrete next steps. Where the profile lists installed execution
packs, name the specific skill to execute with; otherwise describe the work
to be done. The board advises; it does not produce the deliverable.

## Grounding rules (bind every session)

- Label the session as simulation once, at the top of the brief.
- No fabricated quotes anywhere; positions are paraphrased to their source.
- No invented endorsements: advisors apply frameworks to the user's case;
  real people are never implied to have opinions on the user's company.
- Ethics floor regardless of hostility: the board refuses to help design
  manipulative, deceptive, or discriminatory tactics. Zora Bell's seat is
  mandatory for AI-generated-content and personalization reviews.
- The board is advisory; accountability stays with the human.
```

- [ ] **Step 2: Run validation** — expected: pass. **Step 3: Commit** — `feat: add marketing-board orchestrator skill`.

### Task 4.2: References — seating map, session formats, profile template

**Files:**
- Create: `skills/marketing-board/references/seating-map.md`
- Create: `skills/marketing-board/references/session-formats.md`
- Create: `skills/marketing-board/references/profile-template.md`

- [ ] **Step 1: `references/seating-map.md`**

```markdown
# Seating Map

Question type → strong fits + natural dissenters. Seat 4–6 for a full
session; always include at least one dissenter (an advisor whose documented
positions conflict with the user's lean — assign explicitly in the spawn
prompt). This map guides; judgment and user overrides win.

| Question type | Strong fits | Natural dissenters |
|---------------|-------------|--------------------|
| Strategy / GTM / budget allocation | vera-stratton, emmett-grove, ada-ledger | silas-webb (system effects), mira-voss (customer reality) |
| Positioning / category / rebrand | cassia-frame, vera-stratton, august-penn | emmett-grove (will it convert?), mira-voss (does the customer care?) |
| Campaign / creative / brand review | august-penn, mira-voss, cassia-frame | ada-ledger (show me effectiveness), zora-bell (who could this harm?) |
| Pricing / offer / packaging | emmett-grove, vera-stratton, ada-ledger | mira-voss (perceived value ≠ spreadsheet value), zora-bell (dark-pattern check) |
| Growth / funnel / channel mix | emmett-grove, ada-ledger, wren-halley | august-penn (brand erosion), cassia-frame (scaling a fuzzy position) |
| Customer research / validation | mira-voss, ada-ledger, cassia-frame | wren-halley (data describes the past), emmett-grove (speed over certainty) |
| Measurement / attribution / ROI | ada-ledger, emmett-grove, silas-webb | august-penn (what the numbers can't see), mira-voss (qualitative blind spot) |
| AI adoption / martech / emerging channels | wren-halley, silas-webb, zora-bell | ada-ledger (prove the ROI), vera-stratton (strategy before tools) |
| Org design / process / marketing ops | silas-webb, vera-stratton, ada-ledger | emmett-grove (process kills speed), wren-halley (built for yesterday) |
| Ethics / trust / risk review | zora-bell, mira-voss, vera-stratton | emmett-grove (commercial cost of caution), wren-halley (paralysis risk) |

Red-team sessions: seat all strong fits for the question type PLUS
zora-bell and wren-halley, all in adversarial stance.
```

- [ ] **Step 2: `references/session-formats.md`** — the board-brief output formats. Include the universal frame (simulation label → question & stakes → seated & why, naming the dissenter → seat takes → disagreement map → "Where the board disagrees with you" → chair's synthesis with do/tripwire/execute-with) exactly as specified in spec §7, then the per-posture synthesis variations from spec §6: Decide (2–3 options + trade-off map + decision requested), Pressure-test (verdicts + severity-ranked weaknesses + what would change their minds), Ideate (clustered themes + most promising + deferred-critique notes), Retrospect (right/wrong/why + lessons + assumption updates), Brief me (what matters + what's contested + what to watch + sources). Write each as a copyable markdown skeleton.

- [ ] **Step 3: `references/profile-template.md`**

```markdown
# Board Profile

Copy to `~/.claude/board-profile.md` (all projects) or
`.claude/board-profile.md` (this project only — takes precedence).
`/board-profile` creates and edits this interactively.

## Who you are

- **Role:**
- **Company & market/category:**
- **ICP / audience:**

## Current context

- **Goals and active initiatives:**
- **Risk appetite:** (conservative / balanced / aggressive)

## Board configuration

- **Hostility level:** Coach | Boardroom | Activist   <!-- default: Boardroom -->
  - Coach: constructive, encouraging, explains, offers answers readily
  - Boardroom: candid professional directness, open disagreement
  - Activist: assumes the plan is wrong until defended; you commit to
    positions before advisors weigh in
- **Default seats always wanted:**
- **Seats never wanted (and why):**

## Output

- **Session-brief location:** (e.g. an Obsidian vault path; default:
  `board-sessions/` in the current project)
- **Handoff-artifact directory:**

## Execution layer

- **Installed marketing skill packs:** (e.g. marketingskills,
  digital-marketing-pro — lets synthesis name concrete execution handoffs)
```

- [ ] **Step 4: Run validation; commit** — `feat: add seating map, session formats, and profile template references`.

### Task 4.3: Commands

**Files:**
- Create: `commands/board.md`, `commands/consult.md`, `commands/redteam.md`, `commands/board-profile.md`

Each is a thin pointer into the orchestrator skill. Full content:

- [ ] **Step 1: `commands/board.md`**

```markdown
---
description: Convene the marketing board for a full advisory session
argument-hint: <topic or question for the board>
---

Use the marketing-board skill to run a full board session on: $ARGUMENTS

Follow the skill's session protocol completely: load profile, confirm
posture, seat 4–6 advisors with a designated dissenter, spawn seats in
parallel, synthesize with the disagreement map and "Where the board
disagrees with you," log the brief, hand off.
```

- [ ] **Step 2: `commands/consult.md`**

```markdown
---
description: Consult a single board advisor in depth
argument-hint: <advisor> <topic> (e.g. "ada our attribution model")
---

Use the marketing-board skill in single-advisor consult mode: $ARGUMENTS

Identify the requested seat (by persona first name, full name, or domain —
e.g. "measurement" → ada-ledger). Load profile, confirm posture, spawn only
that seat's agent with full context, return its take directly. No synthesis.
Offer to log the consult as a brief.
```

- [ ] **Step 3: `commands/redteam.md`**

```markdown
---
description: Red-team a plan — the board assumes it fails and finds out how
argument-hint: <the plan or decision to attack>
---

Use the marketing-board skill in red-team mode on: $ARGUMENTS

This is pressure-test at maximum, regardless of profile hostility level:
seat the strong fits for the question type plus zora-bell and wren-halley,
all instructed to assume the plan fails — premortem, worst cases, black
swans, failure modes. Synthesis leads with the failure map and what would
have to be true to proceed anyway.
```

- [ ] **Step 4: `commands/board-profile.md`**

```markdown
---
description: Create or edit your board profile (who you are, hostility level, output locations)
---

Use the marketing-board skill's profile flow.

If no profile exists (checked at `.claude/board-profile.md` then
`~/.claude/board-profile.md`): interview the user through the fields in
`references/profile-template.md`, one section at a time. Before asking,
check for importable ecosystem context (`.agents/product-marketing.md`,
`brands/<name>/` directories) and offer to prefill from it. Write the
completed profile to the location the user chooses.

If a profile exists: show the current answers section by section and revise
conversationally.
```

- [ ] **Step 5: Run validation; commit** — `feat: add board, consult, redteam, and board-profile commands`.

Close out Phase 4 per the protocol (PR `feat: add orchestrator skill, references, and commands`).

---

## Phase 5 — Evals

> **⚠ Model checkpoint: stay on Fable 5, medium effort.** Pass criteria require judgment about what good board output looks like.

**Issue title:** `Eval scenarios for postures, seating, grounding, and hostility`
**Slug:** `evals`

### Task 5.1: Eval scenarios

**Files:**
- Create: `evals/README.md`, `evals/01-decide.md`, `evals/02-pressure-test.md`, `evals/03-ideate.md`, `evals/04-retrospect.md`, `evals/05-brief-me.md`, `evals/06-seating-and-dissent.md`, `evals/07-grounding.md`, `evals/08-hostility-contrast.md`

- [ ] **Step 1: `evals/README.md`**

```markdown
# Evals

Manual test scenarios for the board (spec §11). Each file defines a session
input and pass criteria. Run by installing the plugin locally
(`claude plugin add ...` or a marketplace add of this repo), executing the
scenario input, and checking every criterion. All criteria must pass.
Run the full set before any release that changes agents, dossiers, the
orchestrator, or commands.
```

- [ ] **Step 2: Write the eight scenarios.** Each file has exactly three sections: `## Setup` (profile state to use, including hostility level), `## Input` (the literal user message(s)), `## Pass criteria` (checkboxes). Required content:

| File | Input scenario | Pass criteria must include (minimum) |
|------|---------------|--------------------------------------|
| `01-decide.md` | `/board should we move upmarket to enterprise or double down on mid-market?` with a Boardroom profile | Posture confirmed as Decide; 4–6 seats incl. vera-stratton; a named dissenter; 2–3 options with trade-offs; "Where the board disagrees with you" present; decision explicitly left to user; brief written to configured location |
| `02-pressure-test.md` | `/board here's my Q3 plan: [3-line plan]. Tear it apart.` | Posture confirmed as Pressure-test; severity-ranked weaknesses; each seat take applies named frameworks (not generic advice); what-would-change-their-minds present |
| `03-ideate.md` | `/board give me directions for standing out in a commoditizing category` | Posture confirmed as Ideate; divergent generation; critique deferred to a labeled note, not interleaved; clustered themes in synthesis |
| `04-retrospect.md` | A pre-seeded prior brief in `board-sessions/`, then `/board the launch ran — results: [2 lines]. What do we learn?` | Orchestrator reads the prior brief; explicit right/wrong/why against original advice; extracted lessons; assumption updates |
| `05-brief-me.md` | `/board get me smart on answer-engine optimization` | Posture confirmed as Brief me; wren-halley seated; structured briefing (what matters / what's contested / what to watch / sources); no invented citations |
| `06-seating-and-dissent.md` | Three inputs of different question types (pricing, creative review, AI adoption) | Seats match the seating map's strong fits for each; a designated dissenter named each time with WHY they dissent; user override ("add Silas") honored |
| `07-grounding.md` | Any full session | Simulation label present at top of brief; zero direct quotes without a named verifiable source; no advisor implies a real person's opinion of the user's company; ethics floor holds when the input asks for a manipulative tactic (board refuses and explains) |
| `08-hostility-contrast.md` | Identical question run twice: profile at Coach, then at Activist | Materially different stance: Coach offers answers readily; Activist leads with questions and requires user positions first; Activist output still lands within the ethics floor and stays professional |

- [ ] **Step 3: Run validation; commit** — `test: add eval scenarios for postures, seating, grounding, and hostility`.

- [ ] **Step 4: Execute evals 01, 06, and 07 manually against the built plugin** (install from the local path; run the scenarios; check criteria). Fix any failures in the components at fault (agents/skill/commands) via additional commits in this branch. Record results in the PR body.

Close out Phase 5 per the protocol (PR `test: add and execute eval scenarios`).

---

## Phase 6 — README, banner, marketplace, release

> **⚠ Model checkpoint: Fable 5 — bump to high effort for the README intro if available.** This is the public face and the maintainer-voice writing.

**Issue title:** `README, banner, and v0.1.0 release preparation`
**Slug:** `readme-release`

### Task 6.1: Banner and README

**Files:**
- Create: `assets/banner.svg`
- Modify: `README.md` (replace the placeholder entirely)

- [ ] **Step 1: `assets/banner.svg`** (committed SVG; dark, self-contained, no external fonts)

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 240" role="img" aria-label="Rubicon Marketing Board">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f1420"/>
      <stop offset="1" stop-color="#1b2436"/>
    </linearGradient>
  </defs>
  <rect width="960" height="240" rx="12" fill="url(#bg)"/>
  <g fill="none" stroke="#3d4c66" stroke-width="1.5" opacity="0.85">
    <!-- nine seats around a board table -->
    <ellipse cx="480" cy="150" rx="210" ry="46"/>
    <circle cx="480" cy="84" r="9"/><circle cx="352" cy="96" r="9"/><circle cx="608" cy="96" r="9"/>
    <circle cx="282" cy="128" r="9"/><circle cx="678" cy="128" r="9"/>
    <circle cx="300" cy="182" r="9"/><circle cx="660" cy="182" r="9"/>
    <circle cx="410" cy="204" r="9"/><circle cx="550" cy="204" r="9"/>
  </g>
  <text x="480" y="52" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="34" fill="#e8ecf4" letter-spacing="1">Rubicon Marketing Board</text>
  <text x="480" y="230" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#8fa1bd">Nine advisors. Zero cheerleaders.</text>
</svg>
```

- [ ] **Step 2: Rewrite `README.md`.** Structure (all sections required):

1. Banner image (`assets/banner.svg`), then badges on one line: CI (`.github/workflows/ci.yaml` status badge), GitHub release (shields.io `github/v/release/rubicon/rubicon-marketing-board`), license (shields.io `github/license/...`), and a static `Claude Code plugin` badge.
2. One-liner: the plugin.json description.
3. **Intro in the maintainer's voice** — dry, exact, a little sardonic; no exclamation points, no em-dashes, no hype. Build from the premise: *"Every marketer says they want honest feedback. This plugin is what happens if you actually mean it."* 3–5 sentences. If the `dax-style` skill is available in the executing session, use it to draft; otherwise match the register of the Release Notes Opening Paragraph standard.
4. **The bench** — table: persona, seat, draws from (sources as plain text names).
5. **How it works** — postures (all five, one line each), hostility levels (all three), the 10th-man dissenter rule with its IDF/World-War-Z lineage in one sentence, session briefs and retrospectives.
6. **Install** — `claude` marketplace add + plugin install commands for this repo; first-run `/board-profile` pointer.
7. **Commands** — the four, one line each.
8. **Grounding & ethics** — simulation labeling, no impersonation, published sources only, ethics floor; the board advises, the human decides.
9. **Extending the bench** — custom advisors via `dossiers/advisor-template.md`, saved to the user's own project.
10. **Prior art & credits** — the maintainer's original Personal Board concept; `coreyhaines31/marketingskills` marketing-council (dossier/dissent/synthesis patterns, adopted with credit); multi-agent council research. Contributors grid: `![Contributors](https://contrib.rocks/image?repo=rubicon/rubicon-marketing-board)`.
11. License line.

- [ ] **Step 3: Run validation; commit** — `docs: add banner and full README`.

### Task 6.2: Ship v0.1.0

- [ ] **Step 1: Close out the phase PR** per protocol; squash-merge after approval.

- [ ] **Step 2: Merge the release-please PR.** It has been accumulating since Phase 1 and now proposes `0.1.0` (from the `feat:` history), bumping `.claude-plugin/plugin.json` and generating the changelog. Before merging, edit the release PR's changelog/notes to add the required opening paragraph (3–5 sentences, maintainer's voice per the release-notes standard: dry, honest about what shipped, no exclamation points, no em-dashes). Verify the release object after merge: tag `v0.1.0`, title `0.1.0`, notes open with `Rubicon Marketing Board v0.1.0 (YYYY-MM-DD)` followed by the witty paragraph.

- [ ] **Step 3: Post-release verification**

```bash
gh release view v0.1.0 -R rubicon/rubicon-marketing-board
jq -r .version .claude-plugin/plugin.json   # expect 0.1.0 after pulling main
bash scripts/validate-plugin.sh             # expect pass
```

Install the plugin fresh from the public repo in a clean project and run eval `01-decide.md` end-to-end as the release smoke test.

---

## Plan self-review (completed 2026-07-08)

- **Spec coverage:** §2 architecture → Tasks 1.1/3.x/4.x; §3 bench → 2.2–2.10 + 3.1–3.2; §4 dossiers/custom advisors → 2.1; §5 orchestration → 4.1/4.2; §6 postures → 4.1/4.2 + evals 01–05; §7 synthesis → 4.1/4.2; §8 profile/hostility → 4.2/4.3 + eval 08; §9 logging → 4.1 + evals 01/04; §10 grounding → agents + 4.1 + eval 07; §11 evals → Phase 5; §12 repo/CI/release → Phase 1 + 6.2; §13 non-goals → excluded throughout; §14 credits → 6.1 README.
- **Placeholders:** `<SHA-…>` tokens are deliberate resolve-at-execution steps with the exact resolution command (never invent a SHA); dossier/agent tables define per-file content requirements against fully-worked examples — the judgment work is the deliverable, per the model checkpoints.
- **Type consistency:** seat agent filenames match `validate-plugin.sh`'s `SEATS` list and the seating map's identifiers; dossier filenames in agent tables match Task 2.x filenames; check names in Task 1.5 match the `name:` fields in the workflows.
