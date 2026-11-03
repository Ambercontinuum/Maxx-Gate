"""Maxx — one integrated run: gate demo + Maxwell's-demon sorter.

This is the submission codebase in one place. It does NOT push, flip, or
submit anything, and it moves no real money and executes no real action.

Part 1 — the gate (maxx/): a seeded 8-action everyday queue, gated by
Maxx, with mock tools only. Golden numbers, locked 2026-10-31:
  decisions release 1 / hold 2 / wrap 3 / escalate 2
  tokens 800 in / 400 retained / 400 discarded
  attention baseline 8 -> gated 7, money held $1,090, irreversible gated 0
  Only the single release carries a one-use permit. Wraps carry mock
  wrapped receipts, NOT permits. Holds/escalates carry none.
  Stability K in the gate is a STUB (K=1.0), advice-only, never wired
  to Glimmer telemetry.

Part 2 — the demon sorter (sorter/): the same "move information like
physics" idea, on datasets. A particle is one logged row, its "speed" is
the scalar score in its own units, the door is a threshold at frozen tau,
the chambers are admitted / held, the demon's memory is the log itself,
and the conserved bill is counting: N_admitted + N_held = N_in.
Values are in bits and counts only. No joules, no kelvin, no token-energy
conversion, no physics budget, no validated Petermann K claim.
Evidence is divergence on an INDEPENDENT label, never score-bin divergence
(which is constructional, because chamber is a deterministic function of score).

Usage:
  python3 run_all.py            # gate (seeded) + sorter, writes results/
  python3 -m unittest discover -s tests   # 49 gate tests

Sorter runs here use the included templates only (first 2,000 rows each),
not the full Adult files. Full-file hashes and licences are in datasets/.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from maxx.demo import run_with_mocks  # noqa: E402


def main():
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    # Part 1: gate, seeded so the run is reproducible without an API key.
    ledger, receipts = run_with_mocks(proposal_source="seeded")
    comp = ledger.baseline_comparison()
    gate_report = {
        "proposal_source": "seeded-queue",
        "world": "SYNTHETIC mock only; no real money, send, share, book, post, or delete",
        "tokens": {
            "in": ledger.tokens_in,
            "retained": ledger.tokens_retained,
            "discarded": ledger.tokens_discarded,
        },
        "decisions": dict(ledger.decisions),
        "attention_baseline": comp["attention_baseline"],
        "attention_gated": comp["attention_gated"],
        "attention_saved": comp["attention_saved"],
        "money_at_risk_baseline_usd": comp["money_at_risk_baseline_usd"],
        "money_held_by_gate_usd": comp["money_held_by_gate_usd"],
        "irreversible_released_baseline": comp["irreversible_released_baseline"],
        "irreversible_released_gated": comp["irreversible_released_gated"],
        "mock_executed": sum(1 for r in receipts if r.executed),
        "mock_not_executed": sum(1 for r in receipts if not r.executed),
    }

    # Part 2: sorter, frozen tau 0.50, same as the verified runs.
    sorter_runs = [
        {
            "name": "synthetic",
            "input": "datasets/synthetic-validation-2000.csv",
            "split": "synthetic",
            "adult": False,
        },
        {
            "name": "adult-train",
            "input": "datasets/adult-template-2000.csv",
            "split": "train",
            "adult": True,
        },
        {
            "name": "adult-test",
            "input": "datasets/adult-test-template-2000.csv",
            "split": "test",
            "adult": True,
        },
    ]
    sorter_reports = {}
    for run in sorter_runs:
        json_out = results_dir / f"sorter-{run['name']}.json"
        csv_out = results_dir / f"sorter-{run['name']}.csv"
        cmd = [
            sys.executable,
            str(ROOT / "sorter" / "sorter.py"),
            "--input", str(ROOT / run["input"]),
            "--tau", "0.50",
            "--split", run["split"],
            "--json", str(json_out),
            "--csv", str(csv_out),
        ]
        if run["adult"]:
            cmd.append("--adult")
        subprocess.run(cmd, check=True)
        data = json.loads(json_out.read_text())
        b10 = data["binnings"]["10"]
        sorter_reports[run["name"]] = {
            "n_in": data["n_in"],
            "counts": data["counts"],
            "identity_ok": data["identity_check"]["ok"],
            "mean_gap": data["mean_gap"],
            "label_js_bits_10bin": b10["label_js_bits"],
            "label_mi_bits_10bin": b10["mi_label_chamber_bits"],
            "label_kl_bits_10bin": b10["label_kl_admitted_vs_held_bits"],
            "shuffled_label_js_bits": [
                s["label_js_bits"] for s in data["shuffled_control"]
            ],
            "flip_either_rates": {
                str(f["delta"]): f["flip_either_rate"] for f in data["flip_rates"]
            },
            "warnings": data["warnings"],
        }

    combined = {
        "maxx_integrated_run": "gate + demon sorter, one codebase, one command",
        "gate": gate_report,
        "sorter_tau": 0.50,
        "sorter": sorter_reports,
        "limits": [
            "Gate world is SYNTHETIC and mock-only.",
            "Gate stability K is a STUB, advice-only, not Glimmer telemetry.",
            "Sorter runs here are templates only (first 2,000 rows each).",
            "Score-bin divergence is constructional and is NOT evidence; "
            "label divergence on an independent label is the evidence.",
            "No joules, no kelvin, no physics budget, no validated K claim.",
            "Analysis/ (K geometry, Adult information isomorph) is appendix "
            "analysis, NOT gate input, and Adult coherence is NOT K's "
            "geometrical coherence.",
        ],
    }
    out = results_dir / "combined-report.json"
    out.write_text(json.dumps(combined, indent=2))
    print("\n--- Integrated report written to results/combined-report.json ---")
    print(json.dumps(combined, indent=2))
    return combined


if __name__ == "__main__":
    main()
