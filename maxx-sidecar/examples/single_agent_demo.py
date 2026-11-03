"""Single-agent demo: one agent, one harness, one demon sidecar.
SYNTHETIC, NO REAL MONEY, NO REAL SEND/SHARE/BOOK/POST/DELETE.
Run: python3 examples/single_agent_demo.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from maxx_sidecar import Harness, SidecarClient  # noqa: E402

QUEUE = pathlib.Path(__file__).resolve().parent.parent / "data" / "queue.json"


def main():
    queue = json.loads(QUEUE.read_text())
    print("--- Maxx sidecar: one agent, one harness, one demon ---")
    print("Agent proposes -> Harness -> Demon sidecar (separate process, regulates cost) -> Mock tools")
    print()
    with SidecarClient(name="demo-demon") as client:
        harness = Harness(client)
        receipts = harness.run(queue)
        for r in receipts:
            print(f"[{r['action_id']}] {r['decision'].upper()} | temp {r['temperature']:.0f} | {r['reason']}")
            print(f"    mock: {r['status']} executed={r['executed']} | real-world effect: NONE — SYNTHETIC ONLY")
        ledger = harness.ledger()
    print()
    print(f"Tokens: {ledger['tokens_in']} in / {ledger['tokens_retained']} retained / {ledger['tokens_discarded']} discarded")
    print(f"Decisions: {ledger['decisions']}")
    print(f"Attention: {ledger['attention_baseline']} -> {ledger['attention_gated']}, saved {ledger['attention_saved']}")
    print(f"Money: ${ledger['money_at_risk_baseline_usd']:.2f} at risk -> ${ledger['money_held_by_gate_usd']:.2f} held")
    print(f"Irreversible releases: baseline {ledger['irreversible_released_baseline']} -> gated {ledger['irreversible_released_gated']}")
    assert ledger["decisions"] == {"release": 1, "hold": 2, "wrap": 3, "escalate": 2}
    assert (ledger["tokens_in"], ledger["tokens_retained"], ledger["tokens_discarded"]) == (800, 400, 400)
    assert ledger["money_held_by_gate_usd"] == 1090.0 and ledger["irreversible_released_gated"] == 0
    print("Golden check PASSED.")


if __name__ == "__main__":
    main()
