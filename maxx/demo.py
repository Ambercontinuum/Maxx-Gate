"""Demo: Spark proposes -> Maxx gates -> mock tools -> ledger vs. no-gate baseline.

ADOPTED mock wiring 2026-10-28, ADOPTED Spark proposal step 2026-10-29.
Flow per action: Spark proposal (or seeded fallback, labelled) -> gate
decision -> mock tool (or no execution on hold/escalate) -> ledger
update. The gate and ledger are real code; the external tools are
SIMULATED. No real money, no real send/share/book/post/delete.
See MAXX-MOCK-ENVIRONMENT-2026-10-28-PROPOSED.md.
"""
import json
import pathlib

from .gate import decide
from .intake import validate
from .interface import render
from .ledger import Ledger
from .mock_tools import MockReceipt, execute
from .proposal import propose_spark
from .stability import advise
from .temperature import assign

QUEUE = pathlib.Path(__file__).resolve().parent.parent / "data" / "queue.json"


def _load_proposals(queue_path, proposal_source, proposal_client):
    """Return (raw_items, proposal_source_label). Spark first if asked,
    seeded fallback on any failure, labelled with the reason."""
    if proposal_source == "seeded":
        return json.loads(pathlib.Path(queue_path).read_text()), "seeded-queue"
    try:
        items, label = propose_spark(http_post=proposal_client)
        # Validate every proposal before gating anything.
        for item in items:
            validate(item)
        return items, label
    except Exception as exc:  # noqa: BLE001 — fallback is the design, not a hide
        print(f"PROPOSAL_SOURCE: spark failed ({exc}), falling back to seeded queue.")
        return json.loads(pathlib.Path(queue_path).read_text()), "seeded-queue-fallback"


def run_with_mocks(queue_path=QUEUE, proposal_source="spark", proposal_client=None) -> tuple[Ledger, list[MockReceipt]]:
    raw, source_label = _load_proposals(queue_path, proposal_source, proposal_client)
    ledger = Ledger()
    receipts: list[MockReceipt] = []
    print("--- Maxx demo (SYNTHETIC, NO REAL MONEY, NO REAL SEND/SHARE/BOOK/POST/DELETE) ---")
    print(f"PROPOSAL_SOURCE: {source_label} — Spark proposes, Maxx gates; Spark never executes.")
    print()
    for item in raw:
        action = validate(item)
        temp = assign(action)
        stability = advise(action.stability_k, action.flip_rate)
        decision = decide(action, temp, stability)
        receipt = execute(action, decision)
        receipts.append(receipt)
        # Record everything: decision + stability + mock receipt in the ledger.
        ledger.record(action, temp, decision, receipt=receipt, stability=stability)
        print(render(action, temp, stability, decision))
        print(f"Mock tool: {receipt.tool} | {receipt.status} | receipt: {receipt.receipt_id or 'none'}")
        print(f"Mock effect: {receipt.simulated_effect}")
        print(f"Real-world effect: {receipt.real_world_effect}")
        print()
    ledger.check_identities()
    print("--- Ledger (SYNTHETIC, MEASURED vs. no-gate baseline) ---")
    print(f"Tokens in: {ledger.tokens_in} | retained: {ledger.tokens_retained} | discarded: {ledger.tokens_discarded}")
    print(f"Decisions: {ledger.decisions}")
    comp = ledger.baseline_comparison()
    print(f"Attention: baseline {comp['attention_baseline']} checks -> gated {comp['attention_gated']} checks, saved {comp['attention_saved']}")
    print(f"Money: at risk baseline ${comp['money_at_risk_baseline_usd']:.2f} -> held by gate ${comp['money_held_by_gate_usd']:.2f}")
    print(f"Irreversible releases: baseline {comp['irreversible_released_baseline']} -> gated {comp['irreversible_released_gated']}")
    print(f"Mock executions: {sum(1 for r in receipts if r.executed)} executed (wrapped/draft only where gated) | "
          f"{sum(1 for r in receipts if not r.executed)} not executed (held/escalated)")
    return ledger, receipts


def run(queue_path=QUEUE, proposal_source="spark", proposal_client=None) -> Ledger:
    ledger, _receipts = run_with_mocks(queue_path, proposal_source, proposal_client)
    return ledger


if __name__ == "__main__":
    run()
