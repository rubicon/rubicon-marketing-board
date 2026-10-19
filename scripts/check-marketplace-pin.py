#!/usr/bin/env python3
"""Fail when the marketplace pin has drifted from the latest release.

This plugin is listed in the `rubicon` marketplace (`rubicon/ai-skills`) as an
external `github` source pinned to a release tag, so installs follow releases
rather than `main`. The pin does not move on its own: v0.1.2 shipped
2026-09-02 and the pin sat at v0.1.1 for six weeks, because nothing in the
release process required moving it and nothing noticed that it had not moved.

`CLAUDE.md` now documents the step. This check is the part that does not
depend on someone re-reading a document at the one moment it matters.

Read-only by construction. It compares two published values and never changes
either, so it needs no write access to the marketplace repository — which is
what makes detection cheap even though automating the bump itself would not
be.

Usage:
  python3 scripts/check-marketplace-pin.py
  python3 scripts/check-marketplace-pin.py --latest v0.1.3 --pin v0.1.2  # offline

Exit 0 when the pin matches the latest release, 1 when it has drifted, is
missing, or is not a release tag at all, and 2 when a value could not be read.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

PLUGIN_REPO = "rubicon/rubicon-marketing-board"
MARKETPLACE_REPO = "rubicon/ai-skills"
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"

RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")


def looks_like_release_tag(ref):
    """Whether a ref is a tag of the shape this repository publishes.

    A branch or a commit SHA in the pin is a different defect from drift —
    installs stop following releases entirely — but it is still a failure, and
    it must not be compared as though it were a version.
    """
    return bool(ref and RELEASE_TAG.match(ref))


def extract_pin(marketplace, repo_slug):
    """The `ref` the marketplace pins for a repository, or None.

    A local plugin's `source` is a plain path string and pins nothing, so
    anything that is not an object is skipped rather than inspected. Seven of
    the eight real entries are strings; treating `source` as always an object
    crashed this check on the live file.
    """
    for plugin in marketplace.get("plugins") or []:
        source = plugin.get("source")
        if not isinstance(source, dict):
            continue
        if source.get("repo") == repo_slug:
            return source.get("ref")
    return None


def compare_pin(latest_tag, pin, repo_slug):
    """Compare the latest release with the pin. Returns (ok, message).

    Every failure names both values, so the fix needs no further digging. A
    value that could not be determined is a failure, never a pass: "no release
    found" must not read as "no drift".
    """
    if not latest_tag:
        return False, (
            f"{repo_slug}: could not determine the latest release, so drift "
            f"cannot be ruled out (marketplace pin is {pin!r})"
        )
    if not pin:
        return False, (
            f"{repo_slug}: no pin found in {MARKETPLACE_REPO} "
            f"{MARKETPLACE_PATH} — the entry is missing or has no ref, while "
            f"the latest release is {latest_tag}"
        )
    if not looks_like_release_tag(pin):
        return False, (
            f"{repo_slug}: marketplace pin is {pin!r}, which is not a release "
            f"tag — installs no longer follow releases (latest release is "
            f"{latest_tag})"
        )
    if pin != latest_tag:
        return False, (
            f"{repo_slug}: marketplace pin is {pin}, latest release is "
            f"{latest_tag} — marketplace users are on the older release. "
            f"Bump the entry's ref in {MARKETPLACE_REPO} {MARKETPLACE_PATH}."
        )
    return True, f"{repo_slug}: marketplace pin and latest release agree at {latest_tag}"


def _get(url):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_latest_release(repo_slug):
    """The latest published release tag. Drafts and prereleases are excluded
    by the API endpoint itself, which is the behaviour we want: a prerelease
    is not what marketplace users should be pinned to."""
    return _get(f"https://api.github.com/repos/{repo_slug}/releases/latest").get("tag_name")


def fetch_marketplace(repo_slug, path):
    import base64

    payload = _get(f"https://api.github.com/repos/{repo_slug}/contents/{path}")
    return json.loads(base64.b64decode(payload["content"]).decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--latest", help="skip the release lookup and use this tag")
    parser.add_argument("--pin", help="skip the marketplace lookup and use this ref")
    args = parser.parse_args()

    try:
        latest = args.latest or fetch_latest_release(PLUGIN_REPO)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as error:
        print(f"could not read the latest release of {PLUGIN_REPO}: {error}", file=sys.stderr)
        return 2

    if args.pin is not None:
        pin = args.pin
    else:
        try:
            pin = extract_pin(fetch_marketplace(MARKETPLACE_REPO, MARKETPLACE_PATH), PLUGIN_REPO)
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as error:
            print(
                f"could not read {MARKETPLACE_PATH} from {MARKETPLACE_REPO}: {error}",
                file=sys.stderr,
            )
            return 2

    ok, message = compare_pin(latest, pin, PLUGIN_REPO)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
