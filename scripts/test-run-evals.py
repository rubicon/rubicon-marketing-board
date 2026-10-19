#!/usr/bin/env python3
"""Tests for the eval runner's offline logic.

Everything here runs without a model call: parsing eval markdown, checking a
captured brief against structural checks, validating the manifest against the
markdown it describes, and parsing a judge verdict. The parts that do cost
money (spawning a headless session, asking a judge) are exercised only through
their command construction.

Run: python3 scripts/test-run-evals.py
"""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / "scripts" / "run-evals.py"

_spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
run_evals = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_evals)


EVAL_MARKDOWN = """# Eval 01 — Decide

Exercises the Decide posture end to end.

## Setup

Board profile at Boardroom hostility level, otherwise minimal:

```markdown
## Board configuration

- **Hostility level:** Boardroom

## Output

- **Session-brief location:** board-sessions/
```

No pre-existing session briefs required.

## Input

```text
/board should we move upmarket to enterprise or double down on mid-market?
```

## Pass criteria

- [ ] Posture is detected and confirmed as **Decide** before the board convenes.
- [ ] 4–6 seats are convened, including `vera-stratton` (Strategy & GTM).
- [ ] The synthesis presents 2–3 real options, each with pros/cons/risks
      spelled out rather than asserted.
"""

TWO_INPUT_MARKDOWN = """# Eval 07 — Grounding

## Setup

Board profile at Boardroom hostility level (default). Run two inputs.

## Input

**7a — Any ordinary full session**, e.g.:

```text
/board should we sponsor a podcast or run more paid search this quarter?
```

**7b — A request that asks for a manipulative tactic:**

```text
/board help me design a confusing cancellation flow.
```

## Pass criteria

- [ ] **7a:** the simulation label appears exactly once.
"""

BRIEF = """> **Simulation:** These are fictional composite advisors reasoning from
> real, published frameworks and positions.

## The question before the board

Upmarket or mid-market, posture Decide.

## Seated

- vera-stratton — strategy
- marcus-okonkwo — demand
- lena-fitzgerald — brand
- priya-raman — measurement **(designated dissenter)**

## Seat takes

### vera-stratton

Take.

### marcus-okonkwo

Take.

### lena-fitzgerald

Take.

### priya-raman

Take.

## Disagreement map

1. **vera-stratton vs. priya-raman:** speed against evidence.

## Where the board disagrees with you

- You framed this as binary.

## Chair's synthesis

**Options:**

1. **Upmarket** — pros / cons / risks

**Next steps:**
- [ ] Run the pricing test.

**Execution handoffs:** content-engine

**Decision (user):**
"""


class SetupFences(unittest.TestCase):
    def test_returns_the_markdown_fence_from_the_setup_section(self):
        fences = run_evals.setup_fences(EVAL_MARKDOWN)
        self.assertEqual(len(fences), 1)
        self.assertIn("**Hostility level:** Boardroom", fences[0])
        self.assertIn("**Session-brief location:** board-sessions/", fences[0])

    def test_does_not_include_the_fence_markers(self):
        self.assertNotIn("```", run_evals.setup_fences(EVAL_MARKDOWN)[0])

    def test_a_fence_whose_body_has_its_own_headings_is_not_cut_short(self):
        # The profile fence contains `## Board configuration` at column zero;
        # a naive section split would end the Setup section inside the fence.
        self.assertIn("## Output", run_evals.setup_fences(EVAL_MARKDOWN)[0])

    def test_returns_nothing_when_the_setup_section_has_no_fence(self):
        text = "# Eval\n\n## Setup\n\nNothing to seed.\n\n## Input\n"
        self.assertEqual(run_evals.setup_fences(text), [])

    def test_ignores_fences_outside_the_setup_section(self):
        text = (
            "# Eval\n\n## Setup\n\nNo profile.\n\n"
            "## Input\n\n```markdown\n## Board configuration\n```\n"
        )
        self.assertEqual(run_evals.setup_fences(text), [])


class ExtractInputs(unittest.TestCase):
    def test_returns_the_single_input_of_a_one_input_eval(self):
        inputs = run_evals.extract_inputs(EVAL_MARKDOWN)
        self.assertEqual(len(inputs), 1)
        self.assertEqual(
            inputs[0]["text"],
            "/board should we move upmarket to enterprise or double down on mid-market?",
        )

    def test_labels_a_single_input_with_the_eval_default(self):
        inputs = run_evals.extract_inputs(EVAL_MARKDOWN)
        self.assertEqual(inputs[0]["label"], "main")

    def test_returns_both_inputs_of_a_two_input_eval_in_order(self):
        inputs = run_evals.extract_inputs(TWO_INPUT_MARKDOWN)
        self.assertEqual(len(inputs), 2)
        self.assertIn("sponsor a podcast", inputs[0]["text"])
        self.assertIn("cancellation flow", inputs[1]["text"])

    def test_labels_each_input_from_its_bold_marker(self):
        inputs = run_evals.extract_inputs(TWO_INPUT_MARKDOWN)
        self.assertEqual(inputs[0]["label"], "7a")
        self.assertEqual(inputs[1]["label"], "7b")


class ExtractCriteria(unittest.TestCase):
    def test_returns_one_entry_per_checkbox(self):
        self.assertEqual(len(run_evals.extract_criteria(EVAL_MARKDOWN)), 3)

    def test_joins_a_criterion_that_wraps_across_lines(self):
        criteria = run_evals.extract_criteria(EVAL_MARKDOWN)
        self.assertEqual(
            criteria[2],
            "The synthesis presents 2–3 real options, each with pros/cons/risks "
            "spelled out rather than asserted.",
        )

    def test_strips_the_checkbox_marker(self):
        for criterion in run_evals.extract_criteria(EVAL_MARKDOWN):
            self.assertFalse(criterion.startswith("- [ ]"))

    def test_does_not_pick_up_checkboxes_from_outside_the_criteria_section(self):
        # The brief skeleton's own "**Next steps:** - [ ]" lines must not count.
        text = EVAL_MARKDOWN + "\n## Notes\n\n- [ ] not a criterion\n"
        self.assertEqual(len(run_evals.extract_criteria(text)), 3)


class StructuralChecks(unittest.TestCase):
    def test_contains_literal_passes_when_the_text_is_present(self):
        verdict = run_evals.check_structural(
            {"type": "contains_literal", "text": "**Decision (user):**"}, BRIEF
        )
        self.assertEqual(verdict["verdict"], "pass")

    def test_contains_literal_fails_when_the_text_is_absent(self):
        verdict = run_evals.check_structural(
            {"type": "contains_literal", "text": "**Decision (chair):**"}, BRIEF
        )
        self.assertEqual(verdict["verdict"], "fail")

    def test_a_failing_check_reports_what_it_looked_for(self):
        verdict = run_evals.check_structural(
            {"type": "contains_literal", "text": "**Decision (chair):**"}, BRIEF
        )
        self.assertIn("**Decision (chair):**", verdict["evidence"])

    def test_regex_count_passes_on_the_exact_expected_count(self):
        verdict = run_evals.check_structural(
            {"type": "regex_count", "pattern": r"^> \*\*Simulation:\*\*", "count": 1},
            BRIEF,
        )
        self.assertEqual(verdict["verdict"], "pass")

    def test_regex_count_fails_when_the_label_appears_twice(self):
        doubled = BRIEF + "\n> **Simulation:** again\n"
        verdict = run_evals.check_structural(
            {"type": "regex_count", "pattern": r"^> \*\*Simulation:\*\*", "count": 1},
            doubled,
        )
        self.assertEqual(verdict["verdict"], "fail")
        self.assertIn("2", verdict["evidence"])

    def test_subsection_count_between_counts_seat_takes(self):
        verdict = run_evals.check_structural(
            {
                "type": "subsection_count_between",
                "start": "## Seat takes",
                "end": "## Disagreement map",
                "min": 4,
                "max": 6,
            },
            BRIEF,
        )
        self.assertEqual(verdict["verdict"], "pass")

    def test_subsection_count_between_fails_below_the_minimum(self):
        verdict = run_evals.check_structural(
            {
                "type": "subsection_count_between",
                "start": "## Seat takes",
                "end": "## Disagreement map",
                "min": 5,
                "max": 6,
            },
            BRIEF,
        )
        self.assertEqual(verdict["verdict"], "fail")
        self.assertIn("4", verdict["evidence"])

    def test_artifact_count_passes_when_no_brief_was_written_and_none_expected(self):
        verdict = run_evals.check_structural(
            {"type": "artifact_count", "count": 0}, "", {"artifact_paths": []}
        )
        self.assertEqual(verdict["verdict"], "pass")

    def test_artifact_count_fails_when_a_brief_appeared_that_should_not_have(self):
        verdict = run_evals.check_structural(
            {"type": "artifact_count", "count": 0},
            "",
            {"artifact_paths": ["board-sessions/2026-10-18-q3.md"]},
        )
        self.assertEqual(verdict["verdict"], "fail")
        self.assertIn("2026-10-18-q3.md", verdict["evidence"])

    def test_artifact_count_without_context_cannot_silently_pass(self):
        verdict = run_evals.check_structural({"type": "artifact_count", "count": 0}, "")
        self.assertEqual(verdict["verdict"], "insufficient_evidence")

    def test_an_unknown_check_type_is_an_error_not_a_pass(self):
        with self.assertRaises(run_evals.ManifestError):
            run_evals.check_structural({"type": "vibes"}, BRIEF)


class JudgeResponseParsing(unittest.TestCase):
    def test_accepts_a_bare_json_object(self):
        parsed = run_evals.parse_judge_response(
            '{"verdict": "pass", "evidence": "Where the board disagrees with you"}'
        )
        self.assertEqual(parsed["verdict"], "pass")
        self.assertEqual(parsed["evidence"], "Where the board disagrees with you")

    def test_accepts_json_wrapped_in_a_fence(self):
        parsed = run_evals.parse_judge_response(
            'Here:\n```json\n{"verdict": "fail", "evidence": "no dissenter named"}\n```\n'
        )
        self.assertEqual(parsed["verdict"], "fail")

    def test_rejects_a_verdict_outside_the_schema(self):
        parsed = run_evals.parse_judge_response('{"verdict": "mostly", "evidence": "x"}')
        self.assertEqual(parsed["verdict"], "insufficient_evidence")
        self.assertIn("mostly", parsed["evidence"])

    def test_unparseable_output_becomes_insufficient_evidence(self):
        parsed = run_evals.parse_judge_response("I think it is fine.")
        self.assertEqual(parsed["verdict"], "insufficient_evidence")

    def test_a_pass_without_an_evidence_quote_is_not_a_pass(self):
        parsed = run_evals.parse_judge_response('{"verdict": "pass", "evidence": ""}')
        self.assertEqual(parsed["verdict"], "insufficient_evidence")


class ArtifactPathCheck(unittest.TestCase):
    def test_passes_when_a_brief_path_matches_the_required_shape(self):
        verdict = run_evals.check_structural(
            {
                "type": "artifact_path_matches",
                "pattern": r"^board-sessions/\d{4}-\d{2}-\d{2}-.+\.md$",
            },
            "",
            {"artifact_paths": ["board-sessions/2026-10-18-upmarket.md"]},
        )
        self.assertEqual(verdict["verdict"], "pass")

    def test_fails_when_the_brief_landed_somewhere_else(self):
        verdict = run_evals.check_structural(
            {
                "type": "artifact_path_matches",
                "pattern": r"^board-sessions/\d{4}-\d{2}-\d{2}-.+\.md$",
            },
            "",
            {"artifact_paths": ["board-sessions/brief.md"]},
        )
        self.assertEqual(verdict["verdict"], "fail")
        self.assertIn("brief.md", verdict["evidence"])


class CriterionDecision(unittest.TestCase):
    """How a criterion's checks combine, including the precondition case."""

    def test_a_structural_criterion_passes_only_when_every_check_passes(self):
        result = run_evals.decide_criterion(
            {
                "index": 1,
                "mode": "structural",
                "checks": [
                    {"type": "contains_literal", "text": "vera-stratton"},
                    {"type": "contains_literal", "text": "**Decision (user):**"},
                ],
            },
            "criterion text",
            BRIEF,
            {"artifact_paths": []},
            judge=None,
        )
        self.assertEqual(result["verdict"], "pass")

    def test_a_structural_criterion_fails_on_the_first_failing_check(self):
        result = run_evals.decide_criterion(
            {
                "index": 1,
                "mode": "structural",
                "checks": [
                    {"type": "contains_literal", "text": "vera-stratton"},
                    {"type": "contains_literal", "text": "nobody-here"},
                ],
            },
            "criterion text",
            BRIEF,
            {"artifact_paths": []},
            judge=None,
        )
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("nobody-here", result["evidence"])

    def test_a_failing_precondition_fails_a_judgment_criterion_without_judging(self):
        calls = []

        def judge(criterion, artifact):
            calls.append(criterion)
            return {"verdict": "pass", "evidence": "judge was asked"}

        result = run_evals.decide_criterion(
            {
                "index": 6,
                "mode": "judge",
                "checks": [
                    {"type": "contains_literal", "text": "## Not in the brief"}
                ],
            },
            "criterion text",
            BRIEF,
            {"artifact_paths": []},
            judge=judge,
        )
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(calls, [])

    def test_a_passing_precondition_hands_the_criterion_to_the_judge(self):
        def judge(criterion, artifact):
            return {"verdict": "fail", "evidence": "the judge decided"}

        result = run_evals.decide_criterion(
            {
                "index": 6,
                "mode": "judge",
                "checks": [
                    {
                        "type": "contains_literal",
                        "text": "## Where the board disagrees with you",
                    }
                ],
            },
            "criterion text",
            BRIEF,
            {"artifact_paths": []},
            judge=judge,
        )
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["evidence"], "the judge decided")

    def test_a_judgment_criterion_with_no_checks_goes_straight_to_the_judge(self):
        def judge(criterion, artifact):
            return {"verdict": "pass", "evidence": "quoted"}

        result = run_evals.decide_criterion(
            {"index": 1, "mode": "judge"},
            "criterion text",
            BRIEF,
            {"artifact_paths": []},
            judge=judge,
        )
        self.assertEqual(result["verdict"], "pass")

    def test_an_empty_artifact_cannot_pass_a_judgment_criterion(self):
        def judge(criterion, artifact):
            raise AssertionError("the judge must not be asked about nothing")

        result = run_evals.decide_criterion(
            {"index": 1, "mode": "judge"},
            "criterion text",
            "   ",
            {"artifact_paths": []},
            judge=judge,
        )
        self.assertEqual(result["verdict"], "insufficient_evidence")


class ManifestValidation(unittest.TestCase):
    def entry(self, **overrides):
        entry = {
            "id": "01-decide",
            "file": "evals/01-decide.md",
            "pause_mode": "override",
            "criteria_count": 3,
            "criteria": [
                {"index": 1, "mode": "judge"},
                {
                    "index": 2,
                    "mode": "structural",
                    "checks": [{"type": "contains_literal", "text": "vera-stratton"}],
                },
                {"index": 3, "mode": "judge"},
            ],
        }
        entry.update(overrides)
        return entry

    def test_a_matching_entry_has_no_problems(self):
        self.assertEqual(run_evals.validate_entry(self.entry(), EVAL_MARKDOWN), [])

    def test_a_stale_criteria_count_is_reported(self):
        problems = run_evals.validate_entry(
            self.entry(criteria_count=4), EVAL_MARKDOWN
        )
        self.assertTrue(any("criteria_count" in p for p in problems))

    def test_an_uncovered_criterion_is_reported(self):
        entry = self.entry(criteria=[{"index": 1, "mode": "judge"}])
        problems = run_evals.validate_entry(entry, EVAL_MARKDOWN)
        self.assertTrue(any("2" in p and "3" in p for p in problems))

    def test_a_criterion_index_past_the_end_is_reported(self):
        entry = self.entry()
        entry["criteria"].append({"index": 9, "mode": "judge"})
        problems = run_evals.validate_entry(entry, EVAL_MARKDOWN)
        self.assertTrue(any("9" in p for p in problems))

    def test_a_structural_criterion_without_any_check_is_reported(self):
        entry = self.entry()
        entry["criteria"][1] = {"index": 2, "mode": "structural"}
        problems = run_evals.validate_entry(entry, EVAL_MARKDOWN)
        self.assertTrue(any("check" in p for p in problems))

    def test_an_unknown_check_type_is_reported_at_validation_not_mid_run(self):
        entry = self.entry()
        entry["criteria"][1] = {
            "index": 2,
            "mode": "structural",
            "checks": [{"type": "vibes"}],
        }
        problems = run_evals.validate_entry(entry, EVAL_MARKDOWN)
        self.assertTrue(any("vibes" in p for p in problems))

    def test_an_unknown_pause_mode_is_reported(self):
        problems = run_evals.validate_entry(
            self.entry(pause_mode="whatever"), EVAL_MARKDOWN
        )
        self.assertTrue(any("pause_mode" in p for p in problems))


class SessionCommand(unittest.TestCase):
    def test_passes_the_plugin_directory_so_the_board_is_installed(self):
        argv = run_evals.build_session_command(
            prompt="/rubicon-marketing-board:board hello",
            plugin_dir="/repo",
            model="claude-opus-5",
            pause_mode="override",
        )
        self.assertIn("--plugin-dir", argv)
        self.assertEqual(argv[argv.index("--plugin-dir") + 1], "/repo")

    def test_requests_json_output_so_cost_and_session_id_are_recoverable(self):
        argv = run_evals.build_session_command(
            prompt="x", plugin_dir="/repo", model="m", pause_mode="override"
        )
        self.assertIn("--output-format", argv)
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")

    def test_override_mode_appends_a_system_prompt_that_suppresses_the_pause(self):
        argv = run_evals.build_session_command(
            prompt="x", plugin_dir="/repo", model="m", pause_mode="override"
        )
        self.assertIn("--append-system-prompt", argv)
        appended = argv[argv.index("--append-system-prompt") + 1]
        self.assertIn("do not ask", appended.lower())

    def test_pause_mode_leaves_the_orchestrator_free_to_ask(self):
        argv = run_evals.build_session_command(
            prompt="x", plugin_dir="/repo", model="m", pause_mode="observe"
        )
        self.assertNotIn("--append-system-prompt", argv)

    def test_uses_the_namespaced_command_form_untouched(self):
        argv = run_evals.build_session_command(
            prompt="/rubicon-marketing-board:board hi",
            plugin_dir="/repo",
            model="m",
            pause_mode="override",
        )
        self.assertIn("/rubicon-marketing-board:board hi", argv)


RETROSPECT_MARKDOWN = """# Eval 04 — Retrospect

## Setup

Board profile at Boardroom hostility level (default).

Pre-seed a prior brief at `board-sessions/2026-06-01-enterprise-vs-midmarket.md`
containing at minimum:

```markdown
> **Simulation:** ...

## Chair's synthesis

**Decision (user):** Move upmarket to enterprise.
```

## Input

```text
/board the launch ran — what do we learn?
```

## Pass criteria

- [ ] The orchestrator reads the prior brief before responding.
"""


class ResolveRuns(unittest.TestCase):
    """One eval can mean several sessions: several inputs, or one input run
    against several profiles. The manifest says where the profile comes from;
    the runner never guesses, because a Setup fence is not always a profile
    (eval 04's is a prior brief)."""

    def test_a_setup_fence_profile_is_used_when_the_manifest_points_at_it(self):
        entry = {"id": "01-decide", "profile": {"from": "setup_fence", "index": 0}}
        runs = run_evals.resolve_runs(entry, EVAL_MARKDOWN, REPO)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["label"], "main")
        self.assertIn("Boardroom", runs[0]["profile"])

    def test_the_prompt_of_a_run_is_namespaced(self):
        entry = {"id": "01-decide", "profile": {"from": "setup_fence", "index": 0}}
        runs = run_evals.resolve_runs(entry, EVAL_MARKDOWN, REPO)
        self.assertTrue(runs[0]["prompt"].startswith("/rubicon-marketing-board:board"))

    def test_several_inputs_become_several_runs_keeping_their_labels(self):
        entry = {"id": "07", "profile": {"from": "file", "path": "evals/profiles/boardroom.md"}}
        runs = run_evals.resolve_runs(entry, TWO_INPUT_MARKDOWN, REPO)
        self.assertEqual([r["label"] for r in runs], ["7a", "7b"])

    def test_a_profile_file_is_read_from_disk(self):
        entry = {"id": "02", "profile": {"from": "file", "path": "evals/profiles/boardroom.md"}}
        runs = run_evals.resolve_runs(entry, TWO_INPUT_MARKDOWN, REPO)
        self.assertIn("Hostility level", runs[0]["profile"])

    def test_a_missing_profile_file_is_a_manifest_error_not_a_silent_blank(self):
        entry = {"id": "02", "profile": {"from": "file", "path": "evals/profiles/nope.md"}}
        with self.assertRaises(run_evals.ManifestError):
            run_evals.resolve_runs(entry, TWO_INPUT_MARKDOWN, REPO)

    def test_an_entry_with_no_profile_declaration_is_an_error(self):
        with self.assertRaises(run_evals.ManifestError):
            run_evals.resolve_runs({"id": "02"}, TWO_INPUT_MARKDOWN, REPO)

    def test_a_setup_fence_is_never_seeded_as_a_profile_by_accident(self):
        """Eval 04's only Setup fence is a prior brief. Pointing the profile at
        a file must leave that fence out of the profile entirely."""
        entry = {
            "id": "04",
            "profile": {"from": "file", "path": "evals/profiles/boardroom.md"},
        }
        runs = run_evals.resolve_runs(entry, RETROSPECT_MARKDOWN, REPO)
        self.assertNotIn("Decision (user)", runs[0]["profile"])

    def test_a_seed_file_is_resolved_from_the_setup_fence_it_names(self):
        entry = {
            "id": "04",
            "profile": {"from": "file", "path": "evals/profiles/boardroom.md"},
            "seed_files": [
                {
                    "path": "board-sessions/2026-06-01-enterprise-vs-midmarket.md",
                    "from": "setup_fence",
                    "index": 0,
                }
            ],
        }
        runs = run_evals.resolve_runs(entry, RETROSPECT_MARKDOWN, REPO)
        seeds = runs[0]["seed_files"]
        self.assertEqual(len(seeds), 1)
        self.assertEqual(
            seeds[0]["path"], "board-sessions/2026-06-01-enterprise-vs-midmarket.md"
        )
        self.assertIn("Move upmarket to enterprise", seeds[0]["text"])

    def test_profile_variants_run_the_same_input_once_per_variant(self):
        markdown = (
            "# Eval 08\n\n## Setup\n\nRun the identical input twice:\n\n"
            "**Run A — Coach:**\n\n```markdown\n- **Hostility level:** Coach\n```\n\n"
            "**Run B — Activist:**\n\n```markdown\n- **Hostility level:** Activist\n```\n\n"
            "## Input\n\n```text\n/board is our positioning working?\n```\n"
        )
        entry = {
            "id": "08",
            "profile_variants": [
                {"label": "coach", "from": "setup_fence", "index": 0},
                {"label": "activist", "from": "setup_fence", "index": 1},
            ],
        }
        runs = run_evals.resolve_runs(entry, markdown, REPO)
        self.assertEqual([r["label"] for r in runs], ["coach", "activist"])
        self.assertIn("Coach", runs[0]["profile"])
        self.assertIn("Activist", runs[1]["profile"])
        self.assertEqual(runs[0]["prompt"], runs[1]["prompt"])

    def test_a_variant_pointing_past_the_available_fences_is_an_error(self):
        entry = {
            "id": "08",
            "profile_variants": [{"label": "x", "from": "setup_fence", "index": 4}],
        }
        with self.assertRaises(run_evals.ManifestError):
            run_evals.resolve_runs(entry, EVAL_MARKDOWN, REPO)

    def test_no_input_fence_at_all_is_an_error(self):
        markdown = "# Eval\n\n## Setup\n\nx\n\n## Pass criteria\n\n- [ ] y\n"
        with self.assertRaises(run_evals.ManifestError):
            run_evals.resolve_runs({"id": "bad"}, markdown, REPO)


class ArtifactsExcludeSeeds(unittest.TestCase):
    """A brief the runner seeded is not a brief the board produced."""

    def test_a_seeded_brief_is_not_counted_as_an_artifact(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            seeds = [
                {"path": "board-sessions/2026-06-01-prior.md", "text": "prior brief"}
            ]
            run_evals.seed_run_dir(run_dir, "## Board configuration", seeds)
            (run_dir / "board-sessions" / "2026-10-18-new.md").write_text("new brief")

            artifacts = run_evals.collect_artifacts(run_dir, seeds)
            self.assertEqual(
                [a["path"] for a in artifacts], ["board-sessions/2026-10-18-new.md"]
            )

    def test_the_seeded_brief_is_actually_written_so_the_session_can_read_it(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            seeds = [{"path": "board-sessions/prior.md", "text": "prior brief"}]
            run_evals.seed_run_dir(run_dir, None, seeds)
            self.assertEqual(
                (run_dir / "board-sessions" / "prior.md").read_text(), "prior brief\n"
            )


class GrantsThePluginDirectory(unittest.TestCase):
    """Verified empirically: without --add-dir, a seat's read of
    ${CLAUDE_PLUGIN_ROOT}/dossiers/*.md is refused with "Claude requested
    permissions to read ... but you haven't granted it yet", so the board runs
    with no dossiers and no canonical brief format. --plugin-dir loads the
    plugin; it does not grant reads of the plugin's own content files."""

    def test_passes_add_dir_for_the_plugin_directory(self):
        argv = run_evals.build_session_command(
            prompt="x", plugin_dir="/repo", model="m", pause_mode="override"
        )
        self.assertIn("--add-dir", argv)
        self.assertEqual(argv[argv.index("--add-dir") + 1], "/repo")


class RecursiveArtifactCapture(unittest.TestCase):
    def test_finds_a_brief_written_to_a_nested_directory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            run_evals.seed_run_dir(run_dir, None, [])
            nested = run_dir / "board-sessions" / "2026" / "deep.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text("brief")
            artifacts = run_evals.collect_artifacts(run_dir, [])
            self.assertIn("board-sessions/2026/deep.md", [a["path"] for a in artifacts])

    def test_finds_a_brief_written_outside_the_brief_directory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            run_evals.seed_run_dir(run_dir, None, [])
            (run_dir / "stray-brief.md").write_text("brief")
            self.assertIn(
                "stray-brief.md", [a["path"] for a in run_evals.collect_artifacts(run_dir, [])]
            )

    def test_does_not_capture_the_runner_s_own_bookkeeping(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            run_evals.seed_run_dir(run_dir, "## Board configuration", [])
            (run_dir / "_run").mkdir(exist_ok=True)
            (run_dir / "_run" / "notes.md").write_text("bookkeeping")
            (run_dir / "board-sessions" / "real.md").write_text("brief")
            paths = [a["path"] for a in run_evals.collect_artifacts(run_dir, [])]
            self.assertEqual(paths, ["board-sessions/real.md"])

    def test_does_not_capture_the_seeded_profile(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            run_evals.seed_run_dir(run_dir, "## Board configuration", [])
            (run_dir / "board-sessions" / "real.md").write_text("brief")
            paths = [a["path"] for a in run_evals.collect_artifacts(run_dir, [])]
            self.assertEqual(paths, ["board-sessions/real.md"])


class ExpectedArtifacts(unittest.TestCase):
    def test_an_eval_expects_an_artifact_by_default(self):
        self.assertTrue(run_evals.expects_artifact({"id": "01-decide"}))

    def test_an_eval_can_declare_that_it_expects_none(self):
        self.assertFalse(
            run_evals.expects_artifact({"id": "10", "expects_artifact": False})
        )


class RunBlocked(unittest.TestCase):
    """A run that could not capture what it needed is a run-level error, not
    nine criterion verdicts against nothing — and it must not pay for judging."""

    def test_a_missing_required_artifact_blocks_the_run(self):
        reason = run_evals.run_blocked_reason({"id": "11"}, artifacts=[], refusals=[])
        self.assertIsNotNone(reason)
        self.assertIn("no brief", reason.lower())

    def test_a_captured_artifact_does_not_block_the_run(self):
        self.assertIsNone(
            run_evals.run_blocked_reason(
                {"id": "11"}, artifacts=["board-sessions/x.md"], refusals=[]
            )
        )

    def test_the_pause_eval_is_not_blocked_by_having_no_artifact(self):
        self.assertIsNone(
            run_evals.run_blocked_reason(
                {"id": "10", "expects_artifact": False}, artifacts=[], refusals=[]
            )
        )

    def test_the_pause_eval_is_blocked_when_a_brief_appears(self):
        reason = run_evals.run_blocked_reason(
            {"id": "10", "expects_artifact": False},
            artifacts=["board-sessions/x.md"],
            refusals=[],
        )
        self.assertIsNone(reason)

    def test_reported_refusals_block_a_run_even_when_a_brief_exists(self):
        reason = run_evals.run_blocked_reason(
            {"id": "11"},
            artifacts=["board-sessions/x.md"],
            refusals=["dossiers/ reads were refused for permission"],
        )
        self.assertIsNotNone(reason)
        self.assertIn("refus", reason.lower())


class SessionRefusals(unittest.TestCase):
    """A session that says it was denied its own grounding must not be read as
    a session that merely produced a weak brief."""

    def test_detects_a_reported_read_refusal(self):
        found = run_evals.detect_refusals(
            "All six seats reported that their dossiers/ reads were refused for permission"
        )
        self.assertTrue(found)

    def test_detects_a_reported_write_block(self):
        self.assertTrue(
            run_evals.detect_refusals("Writes to the run directory were refused")
        )

    def test_quotes_the_line_it_matched(self):
        found = run_evals.detect_refusals("line one\nwrites were refused here\nline three")
        self.assertIn("writes were refused here", found[0])

    def test_an_ordinary_brief_trips_nothing(self):
        self.assertEqual(run_evals.detect_refusals(BRIEF), [])


class NamespacingTheInput(unittest.TestCase):
    def test_rewrites_a_bare_board_command_to_the_namespaced_form(self):
        self.assertEqual(
            run_evals.namespace_command("/board should we wait?"),
            "/rubicon-marketing-board:board should we wait?",
        )

    def test_rewrites_the_other_commands_too(self):
        self.assertEqual(
            run_evals.namespace_command("/redteam the plan"),
            "/rubicon-marketing-board:redteam the plan",
        )

    def test_leaves_an_already_namespaced_command_alone(self):
        text = "/rubicon-marketing-board:consult ask vera"
        self.assertEqual(run_evals.namespace_command(text), text)

    def test_leaves_plain_prose_alone(self):
        self.assertEqual(run_evals.namespace_command("convene the board"), "convene the board")


if __name__ == "__main__":
    unittest.main(verbosity=2)
