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
