"""Tests for the reusable sidecar package. Run: python3 -m unittest discover -s tests"""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from maxx_sidecar import Fleet, Harness, SidecarClient  # noqa: E402
from maxx_sidecar.mock_tools import execute as mock_execute  # noqa: E402

QUEUE = json.loads((pathlib.Path(__file__).resolve().parent.parent / "data" / "queue.json").read_text())
BY_ID = {a["id"]: a for a in QUEUE}


class TestSidecar(unittest.TestCase):
    def test_single_golden_and_regulation(self):
        with SidecarClient(name="test-demon") as client:
            receipts = Harness(client).run(QUEUE)
            ledger = client.ledger()
        self.assertEqual(ledger["decisions"], {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})
        self.assertEqual((ledger["tokens_in"], ledger["tokens_retained"], ledger["tokens_discarded"]), (800, 400, 400))
        self.assertEqual(ledger["money_held_by_gate_usd"], 1090.0)
        self.assertEqual(ledger["irreversible_released_gated"], 0)
        # Regulation, not just measurement: held/escalated executed nothing.
        for r in receipts:
            if r["decision"] in ("hold", "escalate"):
                self.assertFalse(r["executed"])

    def test_permit_one_use_and_cross_sidecar_isolation(self):
        with SidecarClient(name="demon-a") as a, SidecarClient(name="demon-b") as b:
            gated = a.gate(BY_ID["draft-only"])
            self.assertTrue(a.verify_permit("draft-only", gated["permit_id"])["ok"])
            self.assertFalse(a.verify_permit("draft-only", gated["permit_id"])["ok"])
            gated2 = a.gate(BY_ID["draft-only"])
            # A permit from demon-a fails in demon-b: demons are isolated.
            self.assertFalse(b.verify_permit("draft-only", gated2["permit_id"])["ok"])

    def test_bypass_refused(self):
        action = BY_ID["draft-only"]
        # Validate shape for mock_execute: it needs .id/.type/.proposed_text/.description
        from maxx_sidecar.actions import validate
        act = validate(action)
        receipt = mock_execute(act, "release", permit_verified=False)
        self.assertFalse(receipt.executed)
        receipt = mock_execute(act, "release", permit_verified=True)
        self.assertTrue(receipt.executed)
        self.assertTrue(receipt.executed_content.startswith("DRAFT (not sent):"))

    def test_money_budget_regulates(self):
        # A $240 pay would escalate anyway; use a release with a tiny budget
        # via a custom low-cost action: draft is $0, so instead test that a
        # sidecar with a $100 money budget holds a $240 release-shaped action
        # only if it would release — here the gate escalates pay, so assert
        # the budget path via a direct gate on a reversible money action.
        from maxx_sidecar.actions import validate
        from maxx_sidecar.gate import Budget, decide
        from maxx_sidecar.stability import advise
        act = validate({"id": "buy-240", "type": "draft", "description": "Buy $240 item",
                        "trace": [], "amount_usd": 240, "reversible": True})
        d = decide(act, advise(None, None), Budget(money_usd=100.0))
        self.assertEqual(d.decision, "hold")
        self.assertIn("budget", d.reason_plain)

    def test_token_budget_regulates(self):
        with SidecarClient(name="token-demon", token_budget=300) as client:
            receipts = Harness(client).run(QUEUE)
        # 300 tokens = 3 actions gated normally; the rest hold on budget,
        # including draft-only, which would otherwise release.
        by_id = {r["action_id"]: r for r in receipts}
        self.assertEqual(by_id["draft-only"]["decision"], "hold")
        self.assertIn("token budget", by_id["draft-only"]["reason"])
        self.assertFalse(by_id["draft-only"]["executed"])
        self.assertTrue(any("token budget" in r["reason"] for r in receipts))

    # --- Codex regression tests, 2026-11-01 ---
    def test_harness_never_calls_custom_executor_for_held(self):
        calls = []

        def evil(action, decision, wrapped_version, verified):
            calls.append((action.id, decision))
            return True, "evil-executed", "EVIL"

        with SidecarClient(name="harness-held") as client:
            receipts = Harness(client, executor=evil).run([BY_ID["post-public"]])
        self.assertEqual(calls, [])
        self.assertEqual(receipts[0]["decision"], "hold")
        self.assertFalse(receipts[0]["executed"])
        self.assertEqual(receipts[0]["status"], "harness-blocked-not-executed")

    def test_harness_never_calls_executor_when_permit_fails(self):
        calls = []

        def evil(action, decision, wrapped_version, verified):
            calls.append((action.id, decision))
            return True, "evil-executed", "EVIL"

        class FailingVerify:
            def __init__(self, real):
                self.real = real

            def gate(self, action):
                return self.real.gate(action)

            def verify_permit(self, action_id, permit_id):
                return {"ok": False}

            def ledger(self):
                return self.real.ledger()

            def close(self):
                return self.real.close()

        with SidecarClient(name="harness-fail") as real:
            receipts = Harness(FailingVerify(real), executor=evil).run([BY_ID["draft-only"]])
        self.assertEqual(calls, [])
        self.assertEqual(receipts[0]["decision"], "release")
        self.assertFalse(receipts[0]["permit_verified"])
        self.assertFalse(receipts[0]["executed"])
        self.assertEqual(receipts[0]["status"], "harness-blocked-no-permit")

    def test_harness_wrap_sanitizes_action_for_custom_executor(self):
        # A naive executor that executes action.proposed_text must only
        # ever see the wrapped version, never the original wrong attachment.
        def naive(action, decision, wrapped_version, verified):
            return True, "naive-executed", action.proposed_text

        with SidecarClient(name="harness-wrap") as client:
            receipts = Harness(client, executor=naive).run([BY_ID["send-wrong-attachment"]])
        self.assertEqual(receipts[0]["decision"], "wrap")
        self.assertTrue(receipts[0]["executed"])
        self.assertNotIn("wrong file", receipts[0]["content"])
        self.assertIn("attachment omitted", receipts[0]["content"])

    def test_money_budget_two_outstanding_permits_cannot_overspend(self):
        buy1 = {"id": "buy1", "type": "draft", "description": "Buy1",
                "trace": [], "amount_usd": 60, "reversible": True}
        buy2 = {"id": "buy2", "type": "draft", "description": "Buy2",
                "trace": [], "amount_usd": 60, "reversible": True}
        with SidecarClient(name="budget-100", money_budget=100.0) as client:
            g1 = client.gate(buy1)
            g2 = client.gate(buy2)  # reservation from g1 leaves $40
            self.assertEqual(g1["decision"], "release")
            self.assertEqual(g2["decision"], "hold")  # not a second permit
            self.assertIsNone(g2["permit_id"])
            self.assertTrue(client.verify_permit("buy1", g1["permit_id"])["ok"])
            ledger = client.ledger()
        self.assertEqual(ledger["money_budget_remaining_usd"], 40.0)
        self.assertEqual(ledger["money_released_usd"], 60.0)
        self.assertGreaterEqual(ledger["money_budget_remaining_usd"], 0.0)

    def test_money_budget_verify_atomic_recheck_for_unreserved_permit(self):
        from maxx_sidecar.gate import Budget
        from maxx_sidecar.sidecar import Sidecar
        sc = Sidecar(name="recheck", budget=Budget(money_usd=50.0))
        sc.permits["permit-x"] = {"action_id": "buy", "amount_usd": 60,
                                  "money_reserved": False}
        self.assertFalse(sc.verify("buy", "permit-x")["ok"])
        self.assertEqual(sc.budget.money_usd, 50.0)  # unchanged, never negative
        self.assertNotIn("permit-x", sc.permits)  # failed verify consumes it

    def test_attention_zero_budget_blocks_wrap_and_counts_nothing(self):
        with SidecarClient(name="att-zero", attention_budget=0) as client:
            gated = client.gate(BY_ID["send-wrong-attachment"])
            ledger = client.ledger()
        self.assertNotEqual(gated["decision"], "wrap")
        self.assertEqual(gated["decision"], "hold")
        self.assertIn("attention budget", gated["reason"])
        self.assertEqual(ledger["attention_gated"], 0)
        # A release still works under zero attention: that is the
        # attention a gate saves, not a check it consumes.
        with SidecarClient(name="att-zero-release", attention_budget=0) as client:
            gated = client.gate(BY_ID["draft-only"])
            ledger = client.ledger()
        self.assertEqual(gated["decision"], "release")
        self.assertEqual(ledger["attention_gated"], 0)

    def test_combined_budgets_money_and_zero_attention(self):
        # Codex follow-up, 2026-11-01: money $100 + attention 0 + $101
        # proposal previously produced attention_required=True and
        # attention_gated=1. It must now hold with no attention counted.
        proposal = {"id": "buy101", "type": "draft", "description": "Buy $101",
                    "trace": [], "amount_usd": 101, "reversible": True}
        with SidecarClient(name="combo-budgets", money_budget=100.0,
                           attention_budget=0) as client:
            gated = client.gate(proposal)
            ledger = client.ledger()
        self.assertEqual(gated["decision"], "hold")
        self.assertFalse(gated["attention_required"])
        self.assertIn("money budget", gated["reason"])
        self.assertIn("attention budget", gated["reason"])
        self.assertEqual(ledger["attention_gated"], 0)
        self.assertEqual(ledger["money_budget_remaining_usd"], 100.0)

    def test_money_hold_still_counts_attention_when_budget_available(self):
        # The combined-budgets fix must not flip ordinary money holds:
        # with attention budget available, a money hold is a human-review
        # item and still counts as attention-required.
        proposal = {"id": "buy101", "type": "draft", "description": "Buy $101",
                    "trace": [], "amount_usd": 101, "reversible": True}
        with SidecarClient(name="money-only", money_budget=100.0,
                           attention_budget=10) as client:
            gated = client.gate(proposal)
            ledger = client.ledger()
        self.assertEqual(gated["decision"], "hold")
        self.assertTrue(gated["attention_required"])
        self.assertEqual(ledger["attention_gated"], 1)

    def test_gate_is_threshold_door_monotonic(self):
        # Testable physics correspondence, door form: as cost (temperature)
        # rises with other factors fixed, the decision never becomes more
        # permissive. release < wrap < hold < escalate in restrictiveness.
        from maxx_sidecar.actions import validate
        from maxx_sidecar.gate import decide
        from maxx_sidecar.stability import advise
        order = {"release": 0, "wrap": 1, "hold": 2, "escalate": 3}
        cases = [
            ([], "release"),
            (["person"], "release"),
            (["person", "schedule"], "wrap"),
            (["money", "person"], "hold"),
            (["money", "person", "contract"], "escalate"),
        ]
        last = -1
        for trace, _expected in cases:
            act = validate({"id": "x", "type": "send", "description": "x",
                            "trace": trace, "amount_usd": 0, "reversible": True})
            d = decide(act, advise(1.0, 0.0))
            self.assertGreaterEqual(order[d.decision], last)
            last = order[d.decision]

    def test_fleet_separate_ledgers_same_total(self):
        fleet = Fleet()
        fleet.add("billing", [BY_ID["pay-240"], BY_ID["book-trip"]])
        fleet.add("comms", [BY_ID["send-wrong-attachment"], BY_ID["share-folder"], BY_ID["post-public"]])
        fleet.add("files", [BY_ID["delete-files"], BY_ID["draft-only"], BY_ID["curiosity-hole"]])
        results = fleet.run_all()
        self.assertEqual(len(results), 3)
        agg = fleet.aggregate(results)
        self.assertEqual(agg["decisions"], {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})


if __name__ == "__main__":
    unittest.main()
