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
