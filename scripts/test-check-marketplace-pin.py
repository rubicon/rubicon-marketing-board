#!/usr/bin/env python3
"""Tests for the marketplace pin drift check.

Everything here is offline: the comparison logic is pure, and the two network
reads live in their own functions that these tests do not touch.

Run: python3 scripts/test-check-marketplace-pin.py
"""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "scripts" / "check-marketplace-pin.py"

_spec = importlib.util.spec_from_file_location("check_pin", CHECKER)
check_pin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_pin)

SLUG = "rubicon/rubicon-marketing-board"

# Shaped after the real rubicon/ai-skills marketplace.json: most entries are
# local plugins whose `source` is a plain STRING path, and only an external
# plugin carries an object. An invented all-objects fixture passed happily
# while the live file crashed the checker on the first string it met.
MARKETPLACE = {
    "plugins": [
        {"name": "pitstop", "source": "./plugins/pitstop"},
        {"name": "salience", "source": "./plugins/salience"},
        {
            "name": "some-other-external",
            "source": {"source": "github", "repo": "rubicon/other", "ref": "v9.9.9"},
        },
        {
            "name": "rubicon-marketing-board",
            "source": {"source": "github", "repo": SLUG, "ref": "v0.1.3"},
        },
        {"name": "loadout", "source": "./plugins/loadout"},
    ]
}


class ExtractPin(unittest.TestCase):
    def test_finds_the_ref_for_the_named_repository(self):
        self.assertEqual(check_pin.extract_pin(MARKETPLACE, SLUG), "v0.1.3")

    def test_is_not_confused_by_a_neighbour_with_a_different_repo(self):
        # The neighbour's v9.9.9 must never be mistaken for our pin.
        self.assertNotEqual(check_pin.extract_pin(MARKETPLACE, SLUG), "v9.9.9")

    def test_returns_none_when_the_entry_is_absent(self):
        self.assertIsNone(check_pin.extract_pin({"plugins": []}, SLUG))

    def test_returns_none_when_the_entry_has_no_ref(self):
        marketplace = {
            "plugins": [{"source": {"source": "github", "repo": SLUG}}]
        }
        self.assertIsNone(check_pin.extract_pin(marketplace, SLUG))

    def test_a_marketplace_with_no_plugins_key_does_not_raise(self):
        self.assertIsNone(check_pin.extract_pin({}, SLUG))

    def test_a_string_source_is_skipped_rather_than_crashing(self):
        """Local plugins pin nothing: their `source` is a path string, and
        seven of the eight real entries look like that."""
        local_only = {"plugins": [{"name": "pitstop", "source": "./plugins/pitstop"}]}
        self.assertIsNone(check_pin.extract_pin(local_only, SLUG))

    def test_a_string_source_before_ours_does_not_stop_the_search(self):
        marketplace = {
            "plugins": [
                {"name": "pitstop", "source": "./plugins/pitstop"},
                {"name": "board", "source": {"repo": SLUG, "ref": "v0.1.3"}},
            ]
        }
        self.assertEqual(check_pin.extract_pin(marketplace, SLUG), "v0.1.3")

    def test_a_null_source_is_skipped(self):
        self.assertIsNone(
            check_pin.extract_pin({"plugins": [{"name": "x", "source": None}]}, SLUG)
        )


class ComparePin(unittest.TestCase):
    def test_an_exact_match_is_ok(self):
        ok, message = check_pin.compare_pin("v0.1.3", "v0.1.3", SLUG)
        self.assertTrue(ok)
        self.assertIn("v0.1.3", message)

    def test_a_stale_pin_is_not_ok(self):
        ok, _ = check_pin.compare_pin("v0.1.3", "v0.1.2", SLUG)
        self.assertFalse(ok)

    def test_a_stale_pin_names_both_values(self):
        _, message = check_pin.compare_pin("v0.1.3", "v0.1.2", SLUG)
        self.assertIn("v0.1.3", message)
        self.assertIn("v0.1.2", message)

    def test_a_missing_pin_is_not_ok_and_says_so(self):
        ok, message = check_pin.compare_pin("v0.1.3", None, SLUG)
        self.assertFalse(ok)
        self.assertIn("no pin", message.lower())

    def test_a_missing_release_is_not_ok_rather_than_vacuously_ok(self):
        # No release to compare against must never read as "no drift".
        ok, message = check_pin.compare_pin(None, "v0.1.3", SLUG)
        self.assertFalse(ok)
        self.assertIn("release", message.lower())

    def test_a_pin_that_is_not_a_tag_is_not_ok(self):
        # A branch or SHA pin means installs no longer follow releases at all,
        # which is a different defect than drift but still a failure.
        for pin in ("main", "9f3c1a2e4b5d6f7a8b9c0d1e2f3a4b5c6d7e8f90"):
            ok, message = check_pin.compare_pin("v0.1.3", pin, SLUG)
            self.assertFalse(ok, f"{pin!r} should not pass")
            self.assertIn(pin, message)

    def test_the_message_always_names_the_repository(self):
        for latest, pin in (("v0.1.3", "v0.1.3"), ("v0.1.3", "v0.1.2"), ("v0.1.3", None)):
            _, message = check_pin.compare_pin(latest, pin, SLUG)
            self.assertIn(SLUG, message)


class TagShape(unittest.TestCase):
    def test_a_v_prefixed_semver_is_a_tag(self):
        self.assertTrue(check_pin.looks_like_release_tag("v0.1.3"))
        self.assertTrue(check_pin.looks_like_release_tag("v10.20.30"))

    def test_a_branch_name_is_not_a_tag(self):
        self.assertFalse(check_pin.looks_like_release_tag("main"))

    def test_a_commit_sha_is_not_a_tag(self):
        self.assertFalse(
            check_pin.looks_like_release_tag("9f3c1a2e4b5d6f7a8b9c0d1e2f3a4b5c6d7e8f90")
        )

    def test_a_bare_semver_without_the_v_is_not_this_repos_tag_shape(self):
        # This repo tags v-prefixed; a bare 0.1.3 would not resolve.
        self.assertFalse(check_pin.looks_like_release_tag("0.1.3"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
