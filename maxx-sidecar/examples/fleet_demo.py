"""Fleet demo: three harnesses, three demons — same queue, partitioned.
SYNTHETIC, NO REAL MONEY, NO REAL SEND/SHARE/BOOK/POST/DELETE.
Run: python3 examples/fleet_demo.py

Partition (covers all 8 golden actions, no action in two harnesses):
  billing-demon: pay-240, book-trip        -> escalate 2
  comms-demon:   send-wrong-attachment, share-folder, post-public -> wrap 2, hold 1
  files-demon:   delete-files, draft-only, curiosity-hole -> wrap 1, release 1, hold 1
Aggregate must equal the single-sidecar golden: 1/2/3/2, 800/400/400, $1,090.
Each sidecar's ledger stays separate; the aggregate is read-only.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from maxx_sidecar import Fleet  # noqa: E402

QUEUE = json.loads((pathlib.Path(__file__).resolve().parent.parent / "data" / "queue.json").read_text())
BY_ID = {a["id"]: a for a in QUEUE}
PARTS = {
    "billing-demon": ["pay-240", "book-trip"],
    "comms-demon": ["send-wrong-attachment", "share-folder", "post-public"],
    "files-demon": ["delete-files", "draft-only", "curiosity-hole"],
}


def main():
    fleet = Fleet()
    for name, ids in PARTS.items():
        fleet.add(name, [BY_ID[i] for i in ids])
    results = fleet.run_all()
    for name, r in results.items():
        led = r["ledger"]
        print(f"{name}: decisions {led['decisions']} | tokens {led['tokens_in']}/{led['tokens_retained']}/{led['tokens_discarded']} | held ${led['money_held_by_gate_usd']:.2f}")
    agg = fleet.aggregate(results)
    print(f"\nAggregate (read-only): {agg['decisions']} | tokens {agg['tokens_in']}/{agg['tokens_retained']}/{agg['tokens_discarded']} | held ${agg['money_held_by_gate_usd']:.2f}")
    assert agg["decisions"] == {"release": 1, "hold": 2, "wrap": 3, "escalate": 2}
    assert (agg["tokens_in"], agg["tokens_retained"], agg["tokens_discarded"]) == (800, 400, 400)
    assert agg["money_held_by_gate_usd"] == 1090.0
    print("Fleet golden check PASSED: three demons, same total, separate ledgers.")


if __name__ == "__main__":
    main()
