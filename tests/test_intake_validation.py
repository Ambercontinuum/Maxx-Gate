"""Regression tests for the two intake defects found in verification
(2026-11-04): `reversible` must be an actual boolean (the string "false"
used to coerce to True, letting an irreversible action look reversible),
and `amount_usd` must be finite and non-negative (a -100 amount used to
inflate a money budget). Same rules as the sidecar intake.
"""
import math
import unittest

from maxx.intake import validate

BASE = {"id": "a1", "type": "pay", "description": "Pay a bill",
        "trace": ["money"], "amount_usd": 25, "reversible": False}


class TestIntakeValidation(unittest.TestCase):
    def test_valid_action_unchanged(self):
        a = validate(dict(BASE))
        self.assertEqual(a.amount_usd, 25.0)
        self.assertIs(a.reversible, False)

    def test_reversible_string_false_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, reversible="false"))

    def test_reversible_string_true_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, reversible="true"))

    def test_reversible_int_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, reversible=1))

    def test_reversible_missing_defaults_true(self):
        raw = dict(BASE)
        del raw["reversible"]
        self.assertIs(validate(raw).reversible, True)

    def test_negative_amount_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, amount_usd=-100))

    def test_infinite_amount_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, amount_usd=math.inf))

    def test_nan_amount_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, amount_usd=math.nan))

    def test_bool_amount_rejected(self):
        with self.assertRaises(ValueError):
            validate(dict(BASE, amount_usd=True))

    def test_zero_amount_allowed(self):
        self.assertEqual(validate(dict(BASE, amount_usd=0)).amount_usd, 0.0)


if __name__ == "__main__":
    unittest.main()
