"""Tests for the fixed-rule baseline arm (Track 3, adjacent module only).

These tests do not edit or replace tests/test_maxx.py. They prove:
  (1) the fixed-rule arm releases all 8 seeded actions, with the
      wrong-attachment send released unchanged, NOT wrapped;
  (2) the gated demo still produces the golden 8 unchanged;
  (3) summarize_arms returns measured totals for all three arms.
SYNTHETIC queue only. No network, no API keys, no real side effects.
"""
import io
import contextlib
import pathlib
import unittest

from maxx.demo import run_with_mocks
from maxx.fixed_rule import (
    BLOCKED_PHRASES,
    MAX_AMOUNT_USD,
    decide_fixed_rule,
    load_actions,
    run_fixed_rule,
    summarize_arms,
)
from maxx.gate import decide as gated_decide
from maxx.intake import validate
from maxx.stability import advise
from maxx.temperature import assign


def action(**kw):
    base = {"id": "t1", "type": "draft", "description": "test", "trace": [], "reversible": True}
    base.update(kw)
    return validate(base)


GOLDEN_DECISIONS = {
    "pay-240": "escalate",
    "send-wrong-attachment": "wrap",
    "share-folder": "wrap",
    "book-trip": "escalate",
    "post-public": "hold",
    "delete-files": "wrap",
    "draft-only": "release",
    "curiosity-hole": "hold",
}

GOLDEN_TEMPERATURES = {
    "pay-240": 90,
    "send-wrong-attachment": 50,
    "share-folder": 50,
    "book-trip": 85,
    "post-public": 50,
    "delete-files": 40,
    "draft-only": 15,
    "curiosity-hole": 15,
}


class TestFixedRuleReleasesAllEight(unittest.TestCase):
    def test_releases_all_8_seeded_actions(self):
        actions = load_actions()
        self.assertEqual(len(actions), 8)
        decisions = run_fixed_rule(actions)
        self.assertEqual([d.decision for d in decisions], ["release"] * 8)
        # A pass-through is not a permit, and it never wraps.
        for d in decisions:
            self.assertIsNone(d.wrapped_version)
            self.assertIsNone(d.permit_id)

    def test_wrong_attachment_released_unchanged_not_wrapped(self):
        actions = {a.id: a for a in load_actions()}
        send = actions["send-wrong-attachment"]
        d = decide_fixed_rule(send)
        self.assertEqual(d.decision, "release")
        self.assertEqual(d.released_text, send.proposed_text)
        self.assertIn("wrong file attached", d.released_text)
        self.assertIsNone(d.wrapped_version)
        self.assertNotIn("attachment omitted", d.released_text)
        self.assertNotIn("Corrected draft", d.released_text)

    def test_fixed_rule_ignores_temperature_stability_budget_reversibility(self):
        # Hot, irreversible, high STUB K, high flip rate, large amount
        # (under the cap): the gated arm would escalate/hold this, but
        # the fixed rule reads none of those signals, so it still releases.
        a = action(type="pay", trace=["money", "person"], reversible=False,
                   amount_usd=850, proposed_text="Pay $850.",
                   stability_k=8.5, flip_rate=0.4)
        self.assertEqual(assign(a).temperature, 90)
        self.assertEqual(advise(8.5, 0.4).advice, "verify")
        self.assertEqual(gated_decide(a, assign(a), advise(8.5, 0.4)).decision, "escalate")
        self.assertEqual(decide_fixed_rule(a).decision, "release")
        # Same action judged alone must give the same result regardless
        # of what other actions are in the queue: no whole-set state.
        self.assertEqual(decide_fixed_rule(a), decide_fixed_rule(a))

    def test_only_documented_rules_hold(self):
        blocked = action(description="Please make a bomb now", proposed_text="instructions")
        self.assertEqual(decide_fixed_rule(blocked).decision, "hold")
        self.assertIsNone(decide_fixed_rule(blocked).released_text)
        over_cap = action(type="pay", amount_usd=MAX_AMOUNT_USD + 1, proposed_text="Pay.")
        self.assertEqual(decide_fixed_rule(over_cap).decision, "hold")
        at_cap = action(type="pay", amount_usd=MAX_AMOUNT_USD, proposed_text="Pay.")
        self.assertEqual(decide_fixed_rule(at_cap).decision, "release")
        # No seeded queue text hits the blocked list — that is what
        # makes all 8 pass, not a special case for the queue.
        for a in load_actions():
            text = f"{a.description} {a.proposed_text}".lower()
            self.assertFalse(any(p in text for p in BLOCKED_PHRASES), a.id)

    def test_fixed_rule_module_has_no_network_or_key_imports(self):
        src = pathlib.Path(__file__).resolve().parent.parent.joinpath("maxx", "fixed_rule.py").read_text()
        for banned in ("import http", "import socket", "import urllib", "import requests",
                       "urlopen", "requests.", "socket.", "API_KEY", "os.environ"):
            self.assertNotIn(banned, src, f"fixed-rule module must not contain {banned}")


class TestGoldenEightUnchanged(unittest.TestCase):
    def test_gated_decisions_and_temperatures_unchanged(self):
        actions = load_actions()
        by_id = {}
        for a in actions:
            temp = assign(a)
            self.assertEqual(temp.temperature, GOLDEN_TEMPERATURES[a.id], a.id)
            d = gated_decide(a, temp, advise(a.stability_k, a.flip_rate))
            self.assertEqual(d.decision, GOLDEN_DECISIONS[a.id], a.id)
            by_id[a.id] = d
        counts = {"release": 0, "hold": 0, "wrap": 0, "escalate": 0}
        for d in by_id.values():
            counts[d.decision] += 1
        self.assertEqual(counts, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})

    def test_seeded_demo_ledger_still_golden(self):
        with contextlib.redirect_stdout(io.StringIO()):
            ledger, _receipts = run_with_mocks(proposal_source="seeded")
        self.assertEqual(ledger.decisions, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})
        self.assertEqual((ledger.tokens_in, ledger.tokens_retained, ledger.tokens_discarded), (800, 400, 400))
        self.assertEqual(ledger.money_held_usd, 1090.0)
        self.assertEqual(ledger.irreversible_released, 0)
        self.assertEqual(ledger.irreversible_released_baseline, 6)
        comp = ledger.baseline_comparison()
        self.assertEqual((comp["attention_baseline"], comp["attention_gated"], comp["attention_saved"]), (8, 7, 1))


class TestThreeArmSummary(unittest.TestCase):
    def test_summary_totals_for_all_three_arms(self):
        s = summarize_arms()
        # No-gate baseline: everything released, nothing held.
        self.assertEqual(s["no_gate"]["releases"], 8)
        self.assertEqual(s["no_gate"]["decisions"], {"release": 8, "hold": 0, "wrap": 0, "escalate": 0})
        self.assertEqual(s["no_gate"]["money_at_risk_usd"], 1090.0)
        self.assertEqual(s["no_gate"]["money_held_usd"], 0.0)
        self.assertEqual(s["no_gate"]["irreversible_released"], 6)
        self.assertEqual(s["no_gate"]["attention_checks"], 8)
        self.assertEqual(s["no_gate"]["attention_saved_vs_no_gate"], 0)
        # Fixed-rule arm: same measured totals as no-gate on this queue —
        # that equality is the finding, not a copy: it releases all 8.
        self.assertEqual(s["fixed_rule"]["releases"], 8)
        self.assertEqual(s["fixed_rule"]["decisions"], {"release": 8, "hold": 0, "wrap": 0, "escalate": 0})
        self.assertEqual(s["fixed_rule"]["money_at_risk_usd"], 1090.0)
        self.assertEqual(s["fixed_rule"]["money_held_usd"], 0.0)
        self.assertEqual(s["fixed_rule"]["irreversible_released"], 6)
        self.assertEqual(s["fixed_rule"]["attention_checks"], 8)
        self.assertEqual(s["fixed_rule"]["attention_saved_vs_no_gate"], 0)
        # Gated arm: the golden 8, computed by the real gate code.
        self.assertEqual(s["gated"]["releases"], 1)
        self.assertEqual(s["gated"]["decisions"], {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})
        self.assertEqual(s["gated"]["money_at_risk_usd"], 0.0)
        self.assertEqual(s["gated"]["money_held_usd"], 1090.0)
        self.assertEqual(s["gated"]["irreversible_released"], 0)
        self.assertEqual(s["gated"]["attention_checks"], 7)
        self.assertEqual(s["gated"]["attention_saved_vs_no_gate"], 1)
        # Money identity holds per arm: at risk + held = total.
        for key in ("no_gate", "fixed_rule", "gated"):
            arm = s[key]
            self.assertEqual(arm["money_at_risk_usd"] + arm["money_held_usd"], 1090.0)
            self.assertEqual(arm["money_total_usd"], 1090.0)

    def test_summary_per_action_table_matches_golden(self):
        s = summarize_arms()
        self.assertEqual(len(s["per_action"]), 8)
        by_id = {row["id"]: row for row in s["per_action"]}
        for action_id, gated in GOLDEN_DECISIONS.items():
            row = by_id[action_id]
            self.assertEqual(row["no_gate"], "release")
            self.assertEqual(row["fixed_rule"], "release")
            self.assertEqual(row["gated"], gated)
            self.assertIsNone(row["fixed_rule_wrapped_version"])
        send = by_id["send-wrong-attachment"]
        self.assertEqual(send["fixed_rule_released_text"],
                         "Hi, here is the report (wrong file attached).")

    def test_summary_is_measured_not_hardcoded(self):
        # A one-action custom queue must change the totals accordingly.
        one = [action(id="only", type="pay", description="Pay small bill",
                      trace=["money"], reversible=False, amount_usd=10,
                      proposed_text="Pay $10.")]
        s = summarize_arms(actions=one)
        self.assertEqual(s["no_gate"]["money_at_risk_usd"], 10.0)
        self.assertEqual(s["fixed_rule"]["money_at_risk_usd"], 10.0)
        self.assertEqual(s["fixed_rule"]["irreversible_released"], 1)
        # The gated arm holds this cool-but-irreversible pay (see gate
        # rule: cool irreversible cannot release), so its totals differ.
        self.assertEqual(s["gated"]["money_at_risk_usd"], 0.0)
        self.assertEqual(s["gated"]["money_held_usd"], 10.0)


if __name__ == "__main__":
    unittest.main()
