"""Tests for the six pieces. Each piece testable alone."""
import json
import math
import pathlib
import unittest

from maxx.demo import run_with_mocks
from maxx.gate import Budget, GateConfig, decide
from maxx.intake import validate
from maxx.ledger import Ledger
from maxx.mock_tools import execute, mock_delete, mock_send
from maxx.stability import advise, is_missing, jsd, petermann_k
from maxx.temperature import assign


def action(**kw):
    base = {"id": "t1", "type": "draft", "description": "test", "trace": [], "reversible": True}
    base.update(kw)
    return validate(base)


class TestIntake(unittest.TestCase):
    def test_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            validate({"id": "x", "type": "teleport", "description": "nope"})
    def test_rejects_unknown_trace(self):
        with self.assertRaises(ValueError):
            validate({"id": "x", "type": "draft", "description": "nope", "trace": ["vibes"]})


class TestTemperature(unittest.TestCase):
    def test_no_trace_is_cool_floor(self):
        self.assertEqual(assign(action()).temperature, 15)
    def test_irreversible_is_hotter_than_reversible(self):
        cool = assign(action(trace=["person"], reversible=True)).temperature
        hot = assign(action(trace=["person"], reversible=False)).temperature
        self.assertGreater(hot, cool)
    def test_cost_bearer_named(self):
        # Locked pick 4, redefined 2026-11-01: bearer is the operator who
        # pays, recipient is separate and must not appear as the bearer.
        a = action(type="pay", trace=["money", "person"], recipient="utility", reversible=False)
        t = assign(a)
        self.assertEqual("operator", t.cost_bearer)
        self.assertEqual("utility", a.recipient)


class TestGate(unittest.TestCase):
    def test_fail_to_hold_on_missing_signal(self):
        a = action(type="pay", trace=["money"], reversible=False)
        d = decide(a, assign(a), None)
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.permit_id)
    def test_cool_reversible_releases_with_permit(self):
        a = action()
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "release")
        self.assertIsNotNone(d.permit_id)
    def test_curiosity_is_parked(self):
        a = action(type="curiosity")
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "hold")


class TestLedger(unittest.TestCase):
    def test_identities_hold(self):
        ledger = Ledger()
        for kw in ({"type": "draft"}, {"type": "pay", "trace": ["money"], "reversible": False, "amount_usd": 240}):
            a = action(**kw)
            t = assign(a)
            ledger.record(a, t, decide(a, t, advise(1.0, 0.0)))
        ledger.check_identities()
        self.assertEqual(ledger.tokens_in, ledger.tokens_retained + ledger.tokens_discarded)


class TestStability(unittest.TestCase):
    def test_hermitian_k_is_one(self):
        # Orthogonal eigenvectors: K = 1.
        self.assertAlmostEqual(petermann_k([1, 0], [1, 0]), 1.0)
    def test_k_invariant_to_scaling(self):
        self.assertAlmostEqual(petermann_k([2, 0], [3, 0]), petermann_k([1, 0], [1, 0]))
    def test_jsd_in_range(self):
        v = jsd([0.5, 0.5], [0.9, 0.1])
        self.assertTrue(0 <= v <= 1)
    def test_spike_advises_verify(self):
        self.assertEqual(advise(8.5, 0.4).advice, "verify")
        self.assertEqual(advise(1.0, 0.0).advice, "proceed")


class TestGateProposedPatch(unittest.TestCase):
    """PROPOSED patch tests 2026-10-28 (Bird 1). Bands are scaffold values, NOT locked."""

    def test_off_is_missing_not_present(self):
        self.assertTrue(is_missing(advise(None, None)))
        self.assertTrue(is_missing(None))

    def test_off_fail_to_hold_irreversible(self):
        a = action(type="pay", trace=["money"], reversible=False)
        d = decide(a, assign(a), advise(None, None))
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.permit_id)

    def test_off_reversible_releases_but_says_missing(self):
        a = action()
        d = decide(a, assign(a), advise(None, None))
        self.assertEqual(d.decision, "release")
        self.assertIn("missing", d.reason_plain)

    def test_verify_blocks_cool_reversible_release(self):
        a = action()
        d = decide(a, assign(a), advise(8.5, 0.4))
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.permit_id)

    def test_verify_blocks_wrap(self):
        a = action(type="send", trace=["person"], reversible=False, proposed_text="hi")
        # verify + irreversible: fail-to-hold does not apply (signal present),
        # verify step holds before the wrap band is reached.
        d = decide(a, assign(a), advise(8.5, 0.4))
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.wrapped_version)

    def test_cool_irreversible_no_trace_holds(self):
        # No trace + irreversible = 15 floor + 15 = 30 degrees; pre-patch released.
        a = action(type="delete", trace=[], reversible=False)
        self.assertEqual(assign(a).temperature, 30)
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.permit_id)

    def test_escalate_reason_truthful_reversible(self):
        a = action(type="draft", trace=["money", "contract", "person"], reversible=True)
        self.assertGreaterEqual(assign(a).temperature, 85)
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "escalate")
        self.assertIn("reversible", d.reason_plain)
        self.assertNotIn("irreversible", d.reason_plain)

    def test_escalate_reason_truthful_irreversible(self):
        a = action(type="pay", trace=["money", "person"], reversible=False)
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "escalate")
        self.assertIn("irreversible", d.reason_plain)

    def test_budget_none_preserves_release(self):
        a = action()
        d = decide(a, assign(a), advise(1.0, 0.0), budget=None)
        self.assertEqual(d.decision, "release")

    def test_budget_sufficient_preserves_release(self):
        a = action(type="draft", amount_usd=50)
        d = decide(a, assign(a), advise(1.0, 0.0), budget=Budget(remaining_usd=100))
        self.assertEqual(d.decision, "release")

    def test_budget_insufficient_blocks_release_only(self):
        a = action(type="draft", amount_usd=240)
        d = decide(a, assign(a), advise(1.0, 0.0), budget=Budget(remaining_usd=100))
        self.assertEqual(d.decision, "hold")
        self.assertIsNone(d.permit_id)
        self.assertIn("budget", d.reason_plain)

    def test_bands_injectable_proposed_not_locked(self):
        a = action(type="pay", trace=["money", "person"], reversible=False)
        d = decide(a, assign(a), advise(1.0, 0.0), config=GateConfig(escalate_at=95))
        # 90 degrees: no longer escalates under the injected config; falls to hold band.
        self.assertEqual(d.decision, "hold")


class TestMockTools(unittest.TestCase):
    """PROPOSED mock environment tests 2026-10-28. SYNTHETIC only, no network."""

    def test_held_executes_nothing(self):
        a = action(type="pay", trace=["money"], reversible=False, amount_usd=240)
        d = decide(a, assign(a), None)  # missing signal + irreversible -> hold
        r = execute(a, d)
        self.assertFalse(r.executed)
        self.assertEqual(r.status, "mock-not-executed")
        self.assertIsNone(r.receipt_id)
        self.assertIsNone(r.executed_content)

    def test_escalated_executes_nothing(self):
        a = action(type="book", trace=["money", "schedule"], reversible=False, amount_usd=850)
        d = decide(a, assign(a), advise(8.5, 0.4))  # STUB K, escalate band
        self.assertEqual(d.decision, "escalate")
        r = execute(a, d)
        self.assertFalse(r.executed)
        self.assertIsNone(r.receipt_id)

    def test_wrapped_executes_wrapped_version_only(self):
        a = action(type="send", trace=["person"], reversible=False,
                   proposed_text="Hi, here is the report (wrong file attached).")
        d = decide(a, assign(a), advise(1.1, 0.0))
        self.assertEqual(d.decision, "wrap")
        r = mock_send(a, d)
        self.assertTrue(r.executed)
        self.assertEqual(r.status, "mock-wrapped-executed")
        self.assertEqual(r.executed_content, d.wrapped_version)
        # The mock executes ONLY the wrapped version, never the original as
        # a send. The wrapped version must NOT echo the wrong attachment.
        self.assertNotEqual(r.status, "mock-executed")
        self.assertNotIn("wrong file attached", r.executed_content)
        self.assertIn("attachment omitted", r.executed_content)

    def test_delete_wrap_executes_archive_only(self):
        a = action(type="delete", trace=["device"], reversible=False)
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "wrap")
        r = mock_delete(a, d)
        self.assertIn("Archive instead of delete", r.executed_content)

    def test_released_has_mock_receipt_and_permit(self):
        a = action()  # cool reversible draft
        d = decide(a, assign(a), advise(1.0, 0.0))
        self.assertEqual(d.decision, "release")
        r = execute(a, d)
        self.assertTrue(r.executed)
        self.assertIsNotNone(r.receipt_id)
        self.assertTrue(r.receipt_id.startswith("mock-"))
        self.assertIn("not sent", r.executed_content.lower())

    def test_release_without_permit_executes_nothing(self):
        from maxx.gate import GateDecision
        a = action()
        d = GateDecision("release", None, "fake release, no permit", None)
        r = execute(a, d)
        self.assertFalse(r.executed)
        self.assertIsNone(r.receipt_id)

    def test_wrap_without_wrapped_version_executes_nothing(self):
        from maxx.gate import GateDecision
        a = action(type="send", trace=["person"], reversible=False)
        d = GateDecision("wrap", None, "fake wrap, no version", None)
        r = execute(a, d)
        self.assertFalse(r.executed)

    def test_mock_receipt_states_no_real_effect(self):
        a = action()
        d = decide(a, assign(a), advise(1.0, 0.0))
        r = execute(a, d)
        self.assertIn("SYNTHETIC", r.real_world_effect)
        self.assertIn("no real money", r.real_world_effect.lower())

    def test_mock_layer_has_no_network_imports(self):
        import pathlib
        src = pathlib.Path(__file__).resolve().parent.parent.joinpath("maxx", "mock_tools.py").read_text()
        for banned in ("import http", "import socket", "import urllib", "import requests",
                        "urlopen", "requests.", "socket."):
            self.assertNotIn(banned, src, f"mock layer must not contain {banned}")

    def test_demo_flow_preserves_golden_8(self):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            ledger, receipts = run_with_mocks()
        self.assertEqual(ledger.decisions, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})
        self.assertEqual((ledger.tokens_in, ledger.tokens_retained, ledger.tokens_discarded), (800, 400, 400))
        self.assertEqual(ledger.money_held_usd, 1090.0)
        self.assertEqual(ledger.irreversible_released, 0)
        self.assertEqual(ledger.irreversible_released_baseline, 6)
        by_id = {r.action_id: r for r in receipts}
        self.assertFalse(by_id["pay-240"].executed)
        self.assertFalse(by_id["book-trip"].executed)
        self.assertFalse(by_id["post-public"].executed)
        self.assertFalse(by_id["curiosity-hole"].executed)
        self.assertTrue(by_id["draft-only"].executed)
        self.assertEqual(by_id["send-wrong-attachment"].status, "mock-wrapped-executed")


class TestLedgerRecording(unittest.TestCase):
    """ADOPTED 2026-10-28: record everything — decision, stability, mock receipt."""

    def test_demo_flow_records_receipts_in_ledger(self):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            ledger, receipts = run_with_mocks()
        ledger.check_identities()
        self.assertEqual(len(ledger.receipts), 8)
        self.assertEqual(len(ledger.entries), 8)
        for entry, receipt in zip(ledger.entries, receipts):
            self.assertEqual(entry["mock_receipt_id"], receipt.receipt_id)
            self.assertEqual(entry["mock_tool"], receipt.tool)
            self.assertEqual(entry["mock_status"], receipt.status)
            self.assertEqual(entry["mock_executed"], receipt.executed)
            self.assertIn("SYNTHETIC", entry["mock_real_world_effect"])
        # Held/escalated recorded as not executed, wrapped/draft as executed.
        by_id = {e["id"]: e for e in ledger.entries}
        self.assertFalse(by_id["pay-240"]["mock_executed"])
        self.assertFalse(by_id["book-trip"]["mock_executed"])
        self.assertTrue(by_id["send-wrong-attachment"]["mock_executed"])
        self.assertTrue(by_id["draft-only"]["mock_executed"])
        # Stability and wrap are recorded, not just printed.
        self.assertEqual(by_id["book-trip"]["stability_k"], 8.5)
        self.assertIsNotNone(by_id["send-wrong-attachment"]["wrapped_version"])


class TestSparkProposal(unittest.TestCase):
    """ADOPTED 2026-10-29: Spark proposes, Maxx gates. No network in tests."""

    def _fake_spark(self, items):
        def post(url, payload, key):
            self.assertIn("api.meta.ai", url)
            self.assertEqual(payload["model"], "muse-spark-1.3")
            return {"choices": [{"message": {"content": json.dumps(items)}}]}
        return post

    def test_spark_proposals_flow_through_gate_unchanged(self):
        import io, contextlib, json
        seeded = json.loads(pathlib.Path("data/queue.json").read_text())
        proposals = [{k: v for k, v in item.items() if k not in ("stability_k", "flip_rate")}
                     for item in seeded]
        with contextlib.redirect_stdout(io.StringIO()):
            ledger, receipts = run_with_mocks(proposal_source="spark", proposal_client=self._fake_spark(proposals))
        self.assertEqual(ledger.decisions, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})
        self.assertEqual((ledger.tokens_in, ledger.tokens_retained, ledger.tokens_discarded), (800, 400, 400))
        self.assertEqual(ledger.money_held_usd, 1090.0)

    def test_spark_failure_falls_back_to_seeded_queue(self):
        import io, contextlib
        def failing(url, payload, key):
            raise RuntimeError("network down")
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ledger, _ = run_with_mocks(proposal_source="spark", proposal_client=failing)
        self.assertIn("falling back to seeded queue", buf.getvalue())
        self.assertEqual(ledger.decisions, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})

    def test_no_key_falls_back_without_calling_api(self):
        import io, contextlib, os
        self.assertIsNone(os.environ.get("MODEL_API_KEY"))
        self.assertIsNone(os.environ.get("META_API_KEY"))
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ledger, _ = run_with_mocks(proposal_source="spark", proposal_client=None)
        self.assertIn("falling back to seeded queue", buf.getvalue())
        self.assertEqual(ledger.decisions, {"release": 1, "hold": 2, "wrap": 3, "escalate": 2})


if __name__ == "__main__":
    unittest.main()
