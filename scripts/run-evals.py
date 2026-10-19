#!/usr/bin/env python3
"""Run the board's eval suite against a headless Claude Code session.

This is a MANUAL, pre-release tool. It is deliberately not wired into CI:
every eval spawns a real board session with real seat agents, so a full run
costs real model spend. Run it before a release that changes agents, dossiers,
the orchestrator, or commands — and read the results yourself.

What it does, per eval in `evals/manifest.json`:

  1. Seeds `.claude/board-profile.md` in a throwaway run directory from the
     eval's own `## Setup` profile fence, so the session starts from the
     profile the eval describes rather than whatever the machine happens to
     have.
  2. Spawns a headless session with the eval's `## Input`, rewritten to the
     namespaced command form (a bare `/board` does not resolve under
     `--plugin-dir`).
  3. Captures the board brief the session wrote under `board-sessions/`. That
     FILE is the artifact under test, not the chat transcript: the brief is
     what the board actually produced and what a user would keep.
  4. Checks each pass criterion. Structural criteria are decided mechanically
     here. Judgment criteria go to a separate judge session that must answer
     `pass`, `fail`, or `insufficient_evidence` and quote its evidence.

A judge is not a human. `insufficient_evidence` is a real answer and is never
silently folded into a pass. Calibrate the judge against your own reading
(`--calibrate`) before you trust a green run you did not read.

Cost: a full run is 10 board sessions plus one judge call per judgment
criterion — on the order of a few dollars at Opus prices, more if seats run
long. `--only` and `--dry-run` exist so you do not pay for the whole suite to
debug one eval.

Usage:
  python3 scripts/run-evals.py --dry-run
  python3 scripts/run-evals.py --only 01-decide
  python3 scripts/run-evals.py --only 10-posture-confirmation
  python3 scripts/run-evals.py --calibrate
  python3 scripts/run-evals.py            # the whole suite, with judging
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "evals" / "manifest.json"
RUNS_DIR = REPO / "eval-runs"

VERDICTS = ("pass", "fail", "insufficient_evidence")
PAUSE_MODES = ("override", "observe")

COMMAND_NAMES = ("board", "consult", "redteam", "board-profile")
PLUGIN_NAMESPACE = "rubicon-marketing-board"

# The orchestrator's step 2 confirms the posture with the user before
# convening. A single-shot headless session cannot answer, so without this the
# session stops at the question and no brief is ever written. Eval 10 runs
# WITHOUT this override precisely so the pause itself stays under test.
PAUSE_OVERRIDE = (
    "You are running unattended in a single-shot session: there is no user to "
    "answer you, and anything you ask will go unanswered. Do not ask the user "
    "any clarifying or confirming question. Where the skill tells you to "
    "confirm something with the user, state your detected value and the "
    "evidence for it in the brief, then proceed as if confirmed. Every other "
    "instruction in the skill, including all grounding rules, still binds."
)

JUDGE_SYSTEM = (
    "You are grading one pass criterion for a test of a simulated marketing "
    "advisory board. You are given the board brief the session produced and "
    "one criterion. Decide only that criterion, from the brief alone.\n\n"
    "Answer with a single JSON object and nothing else:\n"
    '{"verdict": "pass" | "fail" | "insufficient_evidence", '
    '"evidence": "<a short verbatim quote from the brief that justifies the '
    'verdict>"}\n\n'
    "Rules: quote the brief, never paraphrase it. If the brief does not "
    "contain enough to decide, answer insufficient_evidence rather than "
    "guessing — a wrong pass is worse than an honest abstention. Do not be "
    "generous: a criterion is met only if the brief plainly meets it."
)


class ManifestError(Exception):
    """The manifest describes something the runner cannot execute."""


# --------------------------------------------------------------------------
# Parsing the eval markdown. The markdown stays the single source of truth for
# the profile, the inputs and the criteria text; the manifest only says how
# each criterion is decided.
# --------------------------------------------------------------------------


def _section(text, heading):
    """Return the body of a `## heading` section, or "" if it is absent.

    Fence-aware on purpose: an eval's Setup fence contains a board profile
    whose own `## Board configuration` headings sit at column zero. Splitting
    on the first `## ` would cut the section off inside that fence.
    """
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return ""
    rest = text[match.end():]

    body = []
    fence = None
    for line in rest.splitlines(keepends=True):
        stripped = line.strip()
        if fence is None:
            opener = re.match(r"^(`{3,})", stripped)
            if opener:
                fence = opener.group(1)
            elif re.match(r"^##\s+", line):
                break
        elif stripped.startswith(fence) and set(stripped) == {"`"}:
            fence = None
        body.append(line)
    return "".join(body)


def _fences(body, language):
    opener = re.compile(rf"^(`{{3,}}){language}\s*$", re.MULTILINE)
    blocks = []
    for match in opener.finditer(body):
        ticks = match.group(1)
        closer = re.compile(rf"^{ticks}\s*$", re.MULTILINE)
        end = closer.search(body, match.end())
        if not end:
            continue
        blocks.append((match.start(), body[match.end(): end.start()].strip("\n")))
    return blocks


def setup_fences(text):
    """Every ```markdown fence in an eval's Setup section, in order.

    What each fence MEANS is the manifest's business, not this function's: in
    eval 01 the single fence is a board profile, in eval 04 it is a prior
    brief to pre-seed, and in eval 08 the two fences are profile variants.
    """
    return [body for _, body in _fences(_section(text, "Setup"), "markdown")]


def extract_inputs(text):
    """The session inputs an eval runs, in order, each with a short label.

    A multi-input eval labels its inputs in prose ("**7a — ...**"); that label
    is what the pass criteria refer to, so it is carried through to the run
    directory and the results.
    """
    body = _section(text, "Input")
    blocks = _fences(body, "text")
    inputs = []
    for offset, block in blocks:
        label = None
        preceding = body[:offset]
        markers = re.findall(r"\*\*([0-9]+[a-z])\b", preceding)
        if markers:
            label = markers[-1]
        inputs.append({"label": label or "main", "text": block.strip()})
    return inputs


def extract_criteria(text):
    """One string per `- [ ]` pass criterion, wrapped lines joined."""
    body = _section(text, "Pass criteria")
    criteria = []
    current = None
    for line in body.splitlines():
        start = re.match(r"^- \[[ xX]\]\s+(.*)$", line)
        if start:
            if current is not None:
                criteria.append(current)
            current = start.group(1).strip()
        elif current is not None:
            if line.strip() == "":
                criteria.append(current)
                current = None
            else:
                current += " " + line.strip()
    if current is not None:
        criteria.append(current)
    return criteria


def resolve_runs(entry, markdown, repo):
    """Expand one eval into the sessions it actually means.

    Three shapes exist in the suite today: one input against one profile;
    several labelled inputs; and one input run against several profiles
    (eval 08 contrasts hostility levels that way). Five evals state their
    profile in prose rather than a fence, so the manifest may name a profile
    file instead; a named file that is missing is an error, never a blank
    profile, because a session with no profile takes a different code path in
    the orchestrator and would be testing something else.
    """
    eval_id = entry.get("id")
    inputs = extract_inputs(markdown)
    if not inputs:
        raise ManifestError(f"{eval_id}: no ```text input fence found")

    fences = setup_fences(markdown)

    def resolve_text(source, what):
        origin = source.get("from")
        if origin == "setup_fence":
            index = source["index"]
            if index >= len(fences):
                raise ManifestError(
                    f"{eval_id}: {what} points at Setup fence {index} but the "
                    f"Setup section has {len(fences)} markdown fence(s)"
                )
            return fences[index]
        if origin == "file":
            path = Path(repo) / source["path"]
            if not path.exists():
                raise ManifestError(
                    f"{eval_id}: {what} file {source['path']} does not exist"
                )
            return path.read_text(encoding="utf-8").strip("\n")
        if origin == "none":
            return None
        raise ManifestError(f"{eval_id}: {what} has unknown source {origin!r}")

    seed_files = [
        {"path": seed["path"], "text": resolve_text(seed, f"seed_files {seed['path']}")}
        for seed in entry.get("seed_files", [])
    ]

    variants = entry.get("profile_variants")
    if variants:
        if len(inputs) != 1:
            raise ManifestError(
                f"{eval_id}: profile_variants needs exactly one input, "
                f"found {len(inputs)}"
            )
        return [
            {
                "label": variant["label"],
                "prompt": namespace_command(inputs[0]["text"]),
                "profile": resolve_text(variant, f"profile_variants {variant['label']}"),
                "seed_files": seed_files,
            }
            for variant in variants
        ]

    if "profile" not in entry:
        raise ManifestError(
            f"{eval_id}: no profile declared — say where it comes from "
            '({"from": "setup_fence", "index": N}, {"from": "file", "path": ...}, '
            'or {"from": "none"}), because a Setup fence is not always a profile'
        )

    profile = resolve_text(entry["profile"], "profile")
    return [
        {
            "label": item["label"],
            "prompt": namespace_command(item["text"]),
            "profile": profile,
            "seed_files": seed_files,
        }
        for item in inputs
    ]


def namespace_command(prompt):
    """Rewrite a bare `/board` to the form that resolves under --plugin-dir."""
    for name in COMMAND_NAMES:
        prefix = f"/{name}"
        if prompt.startswith(prefix) and not prompt.startswith(f"/{PLUGIN_NAMESPACE}:"):
            return f"/{PLUGIN_NAMESPACE}:{name}" + prompt[len(prefix):]
    return prompt


# --------------------------------------------------------------------------
# Deciding criteria
# --------------------------------------------------------------------------


def check_structural(check, artifact, context=None):
    """Decide one structural criterion against the captured brief.

    `context` carries the facts that are not in the brief's text — chiefly
    which artifact files the session wrote, which is how eval 10 asserts that
    no brief was produced at all.
    """
    kind = check.get("type")

    if kind == "artifact_count":
        if context is None or "artifact_paths" not in context:
            return {
                "verdict": "insufficient_evidence",
                "evidence": "no artifact listing was available to count",
            }
        paths = context["artifact_paths"]
        expected = check["count"]
        if len(paths) == expected:
            return {
                "verdict": "pass",
                "evidence": f"{len(paths)} artifact(s), as expected",
            }
        return {
            "verdict": "fail",
            "evidence": f"expected {expected} artifact(s), found {len(paths)}: {paths}",
        }

    if kind == "contains_literal":
        wanted = check["text"]
        if wanted in artifact:
            return {"verdict": "pass", "evidence": f"found {wanted!r}"}
        return {"verdict": "fail", "evidence": f"did not find {wanted!r}"}

    if kind == "regex_count":
        expected = check["count"]
        found = len(re.findall(check["pattern"], artifact, re.MULTILINE))
        if found == expected:
            return {
                "verdict": "pass",
                "evidence": f"{check['pattern']!r} matched {found} time(s)",
            }
        return {
            "verdict": "fail",
            "evidence": (
                f"{check['pattern']!r} matched {found} time(s), expected {expected}"
            ),
        }

    if kind == "subsection_count_between":
        start = artifact.find(check["start"])
        if start == -1:
            return {
                "verdict": "fail",
                "evidence": f"section {check['start']!r} is absent",
            }
        end = artifact.find(check["end"], start + len(check["start"]))
        span = artifact[start:] if end == -1 else artifact[start:end]
        found = len(re.findall(r"^###\s+\S", span, re.MULTILINE))
        low, high = check["min"], check["max"]
        if low <= found <= high:
            return {
                "verdict": "pass",
                "evidence": f"{found} subsection(s) between the two headings",
            }
        return {
            "verdict": "fail",
            "evidence": (
                f"{found} subsection(s) between the two headings, expected "
                f"{low}-{high}"
            ),
        }

    if kind == "artifact_path_matches":
        if context is None or "artifact_paths" not in context:
            return {
                "verdict": "insufficient_evidence",
                "evidence": "no artifact listing was available to match",
            }
        paths = context["artifact_paths"]
        pattern = check["pattern"]
        matched = [p for p in paths if re.match(pattern, p)]
        if matched:
            return {"verdict": "pass", "evidence": f"{matched[0]} matches {pattern!r}"}
        return {
            "verdict": "fail",
            "evidence": f"no artifact matches {pattern!r}; found {paths}",
        }

    if kind == "absent_literal":
        unwanted = check["text"]
        if unwanted in artifact:
            return {"verdict": "fail", "evidence": f"found {unwanted!r}, which must not appear"}
        return {"verdict": "pass", "evidence": f"{unwanted!r} is absent, as required"}

    raise ManifestError(f"unknown structural check type: {kind!r}")


CHECK_TYPES = (
    "contains_literal",
    "absent_literal",
    "regex_count",
    "subsection_count_between",
    "artifact_count",
    "artifact_path_matches",
)


def decide_criterion(item, text, artifact, context, judge):
    """Decide one criterion from its checks, its mode, and the judge.

    A structural criterion is the conjunction of its checks. A judgment
    criterion may carry checks too, and there they are PRECONDITIONS: a
    necessary condition that the brief plainly fails settles the criterion as
    a fail, and the judge is never asked — which is both honest and cheaper.
    A precondition passing decides nothing; the judge still rules.
    """
    checks = item.get("checks") or []

    if item["mode"] == "structural":
        results = [check_structural(check, artifact, context) for check in checks]
        for result in results:
            if result["verdict"] != "pass":
                return result
        return {
            "verdict": "pass",
            "evidence": "; ".join(r["evidence"] for r in results),
        }

    for check in checks:
        result = check_structural(check, artifact, context)
        if result["verdict"] == "fail":
            return {
                "verdict": "fail",
                "evidence": f"precondition failed, judge not asked: {result['evidence']}",
            }

    if not artifact.strip():
        return {
            "verdict": "insufficient_evidence",
            "evidence": "the session produced nothing to grade this criterion against",
        }

    return judge(text, artifact)


def parse_judge_response(raw):
    """Parse a judge reply into the fixed schema, abstaining when unsure."""
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        text = brace.group(0) if brace else text

    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return {
            "verdict": "insufficient_evidence",
            "evidence": f"judge reply was not JSON: {raw.strip()[:200]!r}",
        }

    verdict = parsed.get("verdict")
    evidence = (parsed.get("evidence") or "").strip()

    if verdict not in VERDICTS:
        return {
            "verdict": "insufficient_evidence",
            "evidence": f"judge returned an out-of-schema verdict: {verdict!r}",
        }
    if verdict == "pass" and not evidence:
        return {
            "verdict": "insufficient_evidence",
            "evidence": "judge passed the criterion without quoting any evidence",
        }
    return {"verdict": verdict, "evidence": evidence}


# --------------------------------------------------------------------------
# Manifest validation. The manifest points at criteria by position, so it goes
# stale the moment someone edits an eval. These checks make that loud.
# --------------------------------------------------------------------------


def validate_entry(entry, markdown):
    problems = []
    eval_id = entry.get("id", "<no id>")
    criteria = extract_criteria(markdown)
    declared = entry.get("criteria_count")

    if declared != len(criteria):
        problems.append(
            f"{eval_id}: criteria_count is {declared} but "
            f"{entry.get('file')} has {len(criteria)} pass criteria — "
            "the manifest is stale against the eval"
        )

    if entry.get("pause_mode") not in PAUSE_MODES:
        problems.append(
            f"{eval_id}: pause_mode {entry.get('pause_mode')!r} is not one of "
            f"{list(PAUSE_MODES)}"
        )

    seen = set()
    for item in entry.get("criteria", []):
        index = item.get("index")
        if not isinstance(index, int) or index < 1 or index > len(criteria):
            problems.append(
                f"{eval_id}: criterion index {index!r} is outside 1-{len(criteria)}"
            )
            continue
        seen.add(index)
        mode = item.get("mode")
        if mode not in ("structural", "judge"):
            problems.append(f"{eval_id}: criterion {index} has unknown mode {mode!r}")
        elif mode == "structural" and not item.get("checks"):
            problems.append(
                f"{eval_id}: criterion {index} is structural but carries no checks"
            )
        for check in item.get("checks") or []:
            if check.get("type") not in CHECK_TYPES:
                problems.append(
                    f"{eval_id}: criterion {index} uses unknown check type "
                    f"{check.get('type')!r}"
                )

    missing = sorted(set(range(1, len(criteria) + 1)) - seen)
    if missing:
        problems.append(
            f"{eval_id}: pass criteria {missing} are not covered by the manifest — "
            "every criterion must be decided structurally or sent to the judge"
        )

    return problems


# --------------------------------------------------------------------------
# Running sessions
# --------------------------------------------------------------------------


def build_session_command(prompt, plugin_dir, model, pause_mode):
    argv = [
        "claude",
        "-p",
        prompt,
        "--plugin-dir",
        str(plugin_dir),
        # --plugin-dir loads the plugin; it does NOT grant permission to read
        # the plugin's own content files. Without this, every seat's read of
        # ${CLAUDE_PLUGIN_ROOT}/dossiers/*.md is refused and the board reasons
        # with no dossiers and no canonical brief format, while still producing
        # a plausible-looking brief. Verified against a live session.
        "--add-dir",
        str(plugin_dir),
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "acceptEdits",
        "--strict-mcp-config",
    ]
    if pause_mode == "override":
        argv += ["--append-system-prompt", PAUSE_OVERRIDE]
    return argv


def build_judge_command(model):
    return [
        "claude",
        "-p",
        "--model",
        model,
        "--output-format",
        "json",
        "--strict-mcp-config",
        "--append-system-prompt",
        JUDGE_SYSTEM,
    ]


def _run(argv, cwd, stdin_text=None, timeout=1800):
    started = time.time()
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_s": round(time.time() - started, 1),
    }


def _session_fields(stdout):
    """Pull the fields worth logging out of `--output-format json`."""
    try:
        payload = json.loads(stdout)
    except (ValueError, TypeError):
        return {"result": stdout, "session_id": None, "total_cost_usd": None}
    if isinstance(payload, list):
        payload = payload[-1] if payload else {}
    return {
        "result": payload.get("result"),
        "session_id": payload.get("session_id"),
        "total_cost_usd": payload.get("total_cost_usd"),
        "num_turns": payload.get("num_turns"),
        "is_error": payload.get("is_error"),
    }


def seed_run_dir(run_dir, profile, seed_files=()):
    (run_dir / ".claude").mkdir(parents=True, exist_ok=True)
    (run_dir / "board-sessions").mkdir(parents=True, exist_ok=True)
    if profile is not None:
        (run_dir / ".claude" / "board-profile.md").write_text(
            profile + "\n", encoding="utf-8"
        )
    for seed in seed_files:
        path = run_dir / seed["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(seed["text"] + "\n", encoding="utf-8")


def collect_artifacts(run_dir, seed_files=()):
    """Every markdown file the BOARD wrote anywhere under the run directory.

    Deliberately not scoped to `board-sessions/*.md`: a session that writes its
    brief somewhere else would otherwise be indistinguishable from a session
    that produced nothing, and eval 10 depends on "no artifact" meaning no
    artifact. A brief captured from the wrong path is a finding; a brief that
    vanishes is a lie.

    Excluded: the runner's own bookkeeping under `_run/`, the seeded profile
    under `.claude/`, and any file the runner seeded itself.
    """
    seeded = {seed["path"] for seed in seed_files}
    found = []
    for path in sorted(run_dir.rglob("*.md")):
        rel = str(path.relative_to(run_dir))
        if rel.startswith("_run/") or rel.startswith(".claude/") or rel in seeded:
            continue
        found.append({"path": rel, "text": path.read_text(encoding="utf-8")})
    return found


def expects_artifact(entry):
    """Whether this eval requires the board to have written a brief.

    True for every eval except the pause eval, which asserts the opposite.
    """
    return entry.get("expects_artifact", True)


# Phrases a session uses when it reports being denied its own grounding. This
# is a heuristic read of the transcript, not a permission API, so it is
# surfaced as a warning that something invalidated the run — never silently
# folded into a criterion verdict.
REFUSAL_MARKERS = (
    "permission",
    "were refused",
    "was refused",
    "refused for permission",
    "write-blocked",
    "writes to the run directory",
    "haven't granted",
    "could not read",
    "unreadable",
)


def run_blocked_reason(entry, artifacts, refusals):
    """Why this run cannot be graded, or None when it can.

    Two blocking conditions, both learned from a live run that scored nine
    criteria against a brief it never captured:

    - An eval that expects a brief did not produce one the runner can see.
    - The session reported being denied a read or a write, which means the
      board was not working from its own dossiers or canonical formats. The
      brief may look fine and still be testing a different board.
    """
    if expects_artifact(entry) and not artifacts:
        return (
            "no brief was captured, and this eval expects one — nothing was "
            "graded and no judge was paid"
        )
    if refusals:
        return (
            "the session reported being denied a read or a write, so it was "
            f"not working from its own grounding: {refusals[0][:160]}"
        )
    return None


def detect_refusals(text):
    """Lines where a session reported being denied a read or a write."""
    hits = []
    for line in (text or "").splitlines():
        lowered = line.lower()
        if any(marker in lowered for marker in REFUSAL_MARKERS):
            hits.append(line.strip())
    return hits


def files_outside_allowed(run_dir):
    """Paths the session created outside the brief location it was given."""
    allowed_prefixes = ("board-sessions/", ".claude/")
    stray = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = str(path.relative_to(run_dir))
        if rel.startswith(allowed_prefixes) or rel.startswith("_run/"):
            continue
        stray.append(rel)
    return stray


def judge_criterion(criterion, artifact, model, run_dir):
    prompt = (
        "## Criterion\n\n"
        f"{criterion}\n\n"
        "## Board brief\n\n"
        f"{artifact}\n"
    )
    outcome = _run(build_judge_command(model), cwd=run_dir, stdin_text=prompt, timeout=600)
    fields = _session_fields(outcome["stdout"])
    parsed = parse_judge_response(fields.get("result") or outcome["stdout"])
    parsed["judge_session_id"] = fields.get("session_id")
    parsed["judge_cost_usd"] = fields.get("total_cost_usd")
    return parsed


def run_eval(entry, markdown, args, run_root):
    eval_id = entry["id"]
    criteria = extract_criteria(markdown)
    runs = resolve_runs(entry, markdown, REPO)

    record = {
        "id": eval_id,
        "file": entry["file"],
        "pause_mode": entry["pause_mode"],
        "inputs": [],
        "criteria": [],
    }

    artifacts_by_label = {}
    for item in runs:
        label = item["label"]
        run_dir = run_root / eval_id / label
        if run_dir.exists():
            shutil.rmtree(run_dir)
        seed_run_dir(run_dir, item["profile"], item["seed_files"])

        prompt = item["prompt"]
        argv = build_session_command(prompt, REPO, args.model, entry["pause_mode"])

        if args.dry_run:
            record["inputs"].append(
                {"label": label, "prompt": prompt, "argv": argv, "dry_run": True}
            )
            continue

        outcome = _run(argv, cwd=run_dir, timeout=args.timeout)
        fields = _session_fields(outcome["stdout"])
        artifacts = collect_artifacts(run_dir, item["seed_files"])
        artifacts_by_label[label] = artifacts

        (run_dir / "_run").mkdir(exist_ok=True)
        (run_dir / "_run" / "session.json").write_text(
            json.dumps(
                {
                    "prompt": prompt,
                    "argv": argv,
                    "returncode": outcome["returncode"],
                    "stderr": outcome["stderr"][-4000:],
                    "duration_s": outcome["duration_s"],
                    **fields,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        record["inputs"].append(
            {
                "label": label,
                "prompt": prompt,
                "returncode": outcome["returncode"],
                "duration_s": outcome["duration_s"],
                "session_id": fields.get("session_id"),
                "total_cost_usd": fields.get("total_cost_usd"),
                "num_turns": fields.get("num_turns"),
                "artifacts": [a["path"] for a in artifacts],
                "files_outside_allowed": files_outside_allowed(run_dir),
                "refusals": detect_refusals(fields.get("result") or ""),
                "transcript_tail": (fields.get("result") or "")[-2000:],
            }
        )

    if args.dry_run:
        return record

    # One brief is the artifact under test. A multi-input eval is graded
    # against all briefs it produced, concatenated in input order, because its
    # criteria are written per input label.
    joined = "\n\n".join(
        f"<!-- input {label} / {a['path']} -->\n{a['text']}"
        for label in [i["label"] for i in runs]
        for a in artifacts_by_label.get(label, [])
    )
    transcripts = "\n\n".join(
        f"<!-- transcript {i['label']} -->\n{i.get('transcript_tail', '')}"
        for i in record["inputs"]
    )

    context = {
        "artifact_paths": [
            a["path"]
            for label in artifacts_by_label
            for a in artifacts_by_label[label]
        ]
    }

    refusals = [r for item in record["inputs"] for r in item.get("refusals", [])]
    record["refusals"] = refusals
    blocked = run_blocked_reason(entry, context["artifact_paths"], refusals)
    if blocked:
        record["run_error"] = blocked
        for item in entry.get("criteria", []):
            record["criteria"].append(
                {
                    "index": item["index"],
                    "mode": item["mode"],
                    "graded_against": item.get("grade_against", "artifact"),
                    "criterion": criteria[item["index"] - 1],
                    "verdict": "insufficient_evidence",
                    "evidence": f"run blocked: {blocked}",
                }
            )
        return record

    def judge(text, artifact):
        return judge_criterion(text, artifact, args.judge_model, run_root)

    for item in entry.get("criteria", []):
        index = item["index"]
        text = criteria[index - 1]
        source = transcripts if item.get("grade_against") == "transcript" else joined
        result = decide_criterion(item, text, source, context, judge)
        record["criteria"].append(
            {
                "index": index,
                "mode": item["mode"],
                "graded_against": item.get("grade_against", "artifact"),
                "criterion": text,
                **result,
            }
        )

    return record


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def summarize(records):
    counts = {v: 0 for v in VERDICTS}
    for record in records:
        for criterion in record["criteria"]:
            counts[criterion["verdict"]] = counts.get(criterion["verdict"], 0) + 1
    return counts


def print_report(records):
    for record in records:
        print(f"\n{record['id']}  ({record['pause_mode']})")
        if record.get("run_error"):
            print(f"  RUN BLOCKED: {record['run_error']}")
        for line in record.get("refusals", [])[:3]:
            print(f"  session reported: {line[:150]}")
        for item in record["inputs"]:
            if item.get("dry_run"):
                print(f"  [dry-run] {item['label']}: {item['prompt']}")
                continue
            stray = item.get("files_outside_allowed") or []
            print(
                f"  {item['label']}: exit {item['returncode']}, "
                f"{item['duration_s']}s, cost {item.get('total_cost_usd')}, "
                f"artifacts {item['artifacts'] or 'NONE'}"
                + (f", STRAY FILES {stray}" if stray else "")
            )
        for criterion in record["criteria"]:
            mark = {"pass": "PASS", "fail": "FAIL", "insufficient_evidence": "????"}[
                criterion["verdict"]
            ]
            print(f"    {mark} [{criterion['mode'][:5]}] {criterion['index']}. "
                  f"{criterion['criterion'][:88]}")
            if criterion["verdict"] != "pass":
                print(f"           -> {criterion['evidence'][:200]}")


def write_calibration(run_root, records):
    """A sheet for a human to grade the same criteria the judge graded.

    Agreement between the two columns is the only thing that earns the judge
    the right to be read unattended.
    """
    lines = [
        "# Judge calibration",
        "",
        "Grade each judgment criterion yourself from the brief, then compare.",
        "The judge is trustworthy on this suite only once its column and yours",
        "agree. Fill in `human:` with pass / fail / insufficient_evidence.",
        "",
    ]
    for record in records:
        lines.append(f"## {record['id']}")
        lines.append("")
        for criterion in record["criteria"]:
            if criterion["mode"] != "judge":
                continue
            lines.append(f"- criterion {criterion['index']}: {criterion['criterion']}")
            lines.append(f"  - judge: {criterion['verdict']}")
            lines.append(f"  - evidence: {criterion['evidence'][:300]}")
            lines.append("  - human: ")
            lines.append("")
    path = run_root / "calibration.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", action="append", default=[], metavar="EVAL_ID")
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--judge-model", default="claude-opus-5")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the manifest and print the commands; spend nothing",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="also write a sheet for grading the judge against your own reading",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["evals"]
    if args.only:
        entries = [e for e in entries if e["id"] in args.only]
        unknown = set(args.only) - {e["id"] for e in manifest["evals"]}
        if unknown:
            print(f"unknown eval id(s): {sorted(unknown)}", file=sys.stderr)
            return 2
    if not entries:
        print("no evals selected", file=sys.stderr)
        return 2

    problems = []
    markdowns = {}
    for entry in entries:
        path = REPO / entry["file"]
        if not path.exists():
            problems.append(f"{entry['id']}: {entry['file']} does not exist")
            continue
        markdowns[entry["id"]] = path.read_text(encoding="utf-8")
        problems += validate_entry(entry, markdowns[entry["id"]])

    if problems:
        print("manifest does not match the evals:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if not shutil.which("claude") and not args.dry_run:
        print("the `claude` CLI is not on PATH", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = RUNS_DIR / stamp
    run_root.mkdir(parents=True, exist_ok=True)

    cli_version = "dry-run"
    if not args.dry_run:
        cli_version = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True
        ).stdout.strip()
    plugin_version = json.loads(
        (REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    ).get("version")

    records = [run_eval(e, markdowns[e["id"]], args, run_root) for e in entries]
    counts = summarize(records)

    meta = {
        "started_utc": stamp,
        "model": args.model,
        "judge_model": args.judge_model,
        "cli_version": cli_version,
        "plugin_version": plugin_version,
        "dry_run": args.dry_run,
        "evals": [e["id"] for e in entries],
        "verdict_counts": counts,
        "total_cost_usd": round(
            sum(
                (i.get("total_cost_usd") or 0)
                for r in records
                for i in r["inputs"]
            )
            + sum(
                (c.get("judge_cost_usd") or 0)
                for r in records
                for c in r["criteria"]
            ),
            4,
        ),
    }
    (run_root / "results.json").write_text(
        json.dumps({"meta": meta, "evals": records}, indent=2), encoding="utf-8"
    )

    print_report(records)
    print(f"\nrun: {run_root}")
    print(
        f"verdicts: {counts.get('pass', 0)} pass, {counts.get('fail', 0)} fail, "
        f"{counts.get('insufficient_evidence', 0)} insufficient_evidence"
    )
    if not args.dry_run:
        print(f"cost: ${meta['total_cost_usd']}")

    if args.calibrate and not args.dry_run:
        print(f"calibration sheet: {write_calibration(run_root, records)}")

    if args.dry_run:
        return 0
    if any(r.get("run_error") for r in records):
        return 4
    if counts.get("fail"):
        return 1
    if counts.get("insufficient_evidence"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
