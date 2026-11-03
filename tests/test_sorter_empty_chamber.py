"""Sorter empty-chamber regression (Codex, 2026-11-01).

run_sort() crashed in binning-sensitivity calculations when chamber
divergences were None (empty chamber => JS undefined, not zero).
These tests use tables where one chamber is empty in both directions.
They must not crash, must report null spreads, stable=False, and a
warning — and must preserve the counting identity.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "sorter"))

import pandas as pd  # noqa: E402
from sorter import run_sort  # noqa: E402


def _df(scores, labels):
    return pd.DataFrame({
        "id": [f"r{i}" for i in range(len(scores))],
        "score": scores, "label": labels,
        "score_source": ["test"] * len(scores),
        "chamber": [""] * len(scores),
        "split": ["test"] * len(scores),
    })


class TestEmptyChamber(unittest.TestCase):
    def test_admitted_empty_does_not_crash(self):
        # All scores below tau: admitted empty, held = all.
        result = run_sort(_df([0.1, 0.2, 0.3], [0, 1, 0]), tau=0.5,
                          split="test", score_source="test")
        self.assertEqual(result["counts"], {"admitted": 0, "held": 3})
        self.assertTrue(result["identity_check"]["ok"])
        self.assertIsNone(result["binnings"]["10"]["label_js_bits"])
        self.assertIsNone(result["binning_sensitivity"]["label_js_spread_bits"])
        self.assertIsNone(result["binning_sensitivity"]["score_js_spread_bits"])
        self.assertFalse(result["binning_sensitivity"]["stable"])
        self.assertTrue(any("undefined" in w for w in result["warnings"]))

    def test_held_empty_does_not_crash(self):
        # All scores at/above tau: held empty, admitted = all.
        result = run_sort(_df([0.6, 0.7, 0.8], [0, 1, 1]), tau=0.5,
                          split="test", score_source="test")
        self.assertEqual(result["counts"], {"admitted": 3, "held": 0})
        self.assertTrue(result["identity_check"]["ok"])
        self.assertIsNone(result["binnings"]["10"]["label_js_bits"])
        self.assertIsNone(result["binning_sensitivity"]["label_js_spread_bits"])
        self.assertFalse(result["binning_sensitivity"]["stable"])


if __name__ == "__main__":
    unittest.main()
