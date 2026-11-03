"""Maxwell's-demon isomorph sorter — backend, bits/counts only.

No joules, no kelvin, no token-energy conversion, no Petermann K,
no physics budget. A "particle" is one logged row. Its "speed" is the
scalar score already in the table, in that score's own units. The
"door" is a threshold rule at a stated, frozen tau. The "chambers"
are the admitted / held partitions of a frozen logged stream.
The demon's memory is the log itself.

Inputs: a frozen logged table, CSV, with columns
    id, score, label, score_source, chamber (empty at input), split
Gate: chamber = admitted if score >= tau else held.
      tau is recorded with every output. Identity check:
      N_admitted + N_held must equal N_in, or the run fails loudly.

Outputs per run:
  (1) counts per chamber + identity check
  (2) chamber mean scores
  (3) chamber Shannon entropy in bits, over a stated score-bin alphabet
  (4) KL / JS divergence between chambers in bits
  (5) mutual information I(score bin; chamber) in bits
  (6) flip rate per stated delta
Plus, required and kept separate from the constructional metrics:
  - label divergence (KL / JS / MI between chambers over the
    INDEPENDENT label alphabet). This is the only non-circular
    evidence: sorting on score guarantees chambers differ in
    score, so score-bin divergence is NOT evidence.
  - tau sweep, shuffled-gate control, binning sensitivity, warnings.

Constructional warning, stated once and applied everywhere:
  Chamber is a deterministic function of score, so score-bin
  KL/JS/MI are expected to be large (JS up to 1 bit for a binary
  chamber split, KL infinite when bin supports are disjoint)
  BY CONSTRUCTION. They are reported for completeness and must
  never be presented as evidence that the gate "works".
  Evidence is divergence on a label independent of score and gate.

Score-bin KL with disjoint support is reported as null with
disjoint_support=true, not as a large finite number invented
by smoothing.

Dependencies: stdlib + pandas / numpy / scipy only. No sklearn.
Adult score (see README and --compute-adult-score): a transparent
linear combination, NOT a fitted model result:
    score = clip(0.40 * education_num/16
                 + 0.35 * min(age, 80)/80
                 + 0.25 * min(hours_per_week, 80)/80, 0, 1)
Adult income labels are mapped <=50K -> 0, >50K -> 1 after
stripping whitespace and any trailing period (the test file
carries a trailing period; the train file does not).
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ADULT_SCORE_FORMULA = (
    "clip(0.40*education_num/16 + 0.35*min(age,80)/80 "
    "+ 0.25*min(hours_per_week,80)/80, 0, 1)"
)


def entropy_bits(counts):
    """Shannon entropy in bits from raw counts."""
    counts = np.asarray(counts, dtype=float)
    total = counts.sum()
    if total <= 0:
        return 0.0
    p = counts[counts > 0] / total
    return float(-np.sum(p * np.log2(p)))


def kl_bits(p_counts, q_counts):
    """KL(P||Q) in bits. Returns (value_or_None, disjoint_flag).

    None + disjoint=True when Q has zero mass where P has mass:
    the KL is infinite, and inventing a finite value by smoothing
    would hide that fact. None also when either distribution is
    empty (undefined, not zero).
    """
    p = np.asarray(p_counts, dtype=float)
    q = np.asarray(q_counts, dtype=float)
    if p.sum() <= 0 or q.sum() <= 0:
        return None, True
    p = p / p.sum()
    q = q / q.sum()
    mask = p > 0
    if np.any(mask & (q == 0)):
        return None, True
    return float(np.sum(p[mask] * np.log2(p[mask] / q[mask]))), False


def js_bits(p_counts, q_counts):
    """Jensen-Shannon divergence in bits (0..1 for two distributions).

    Returns None when either distribution is empty: JS is undefined
    then, and the previous implementation silently returned 0.5 bits
    for an empty chamber (a bug found on the Adult tau sweep).
    """
    p = np.asarray(p_counts, dtype=float)
    q = np.asarray(q_counts, dtype=float)
    if p.sum() <= 0 or q.sum() <= 0:
        return None
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask]))) if np.any(mask) else 0.0
    return float(0.5 * _kl(p, m) + 0.5 * _kl(q, m))


def mi_bits(joint_counts):
    """Mutual information in bits from a joint count table."""
    joint = np.asarray(joint_counts, dtype=float)
    total = joint.sum()
    if total <= 0:
        return 0.0
    pxy = joint / total
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    mask = pxy > 0
    return float(np.sum(pxy[mask] * np.log2(pxy[mask] / (px * py)[mask])))


def bin_scores(scores, n_bins):
    """Equal-width bins over [0, 1]; returns bin index per score."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(scores, edges[1:-1]), 0, n_bins - 1)
    return idx, edges


def gate(scores, tau):
    """admitted if score >= tau else held."""
    return np.where(np.asarray(scores) >= tau, "admitted", "held")


def chamber_metrics(df, chambers, n_bins):
    """Metrics for one binning, given a chamber assignment."""
    scores = df["score"].to_numpy(dtype=float)
    labels = df["label"].to_numpy()
    bin_idx, _edges = bin_scores(scores, n_bins)
    out = {"n_bins": int(n_bins), "bin_width": float(1.0 / n_bins)}
    for chamber in ("admitted", "held"):
        sel = chambers == chamber
        out[f"{chamber}_n"] = int(sel.sum())
        out[f"{chamber}_mean_score"] = float(scores[sel].mean()) if sel.any() else None
        out[f"{chamber}_score_entropy_bits"] = (
            entropy_bits(np.bincount(bin_idx[sel], minlength=n_bins)) if sel.any() else None
        )
        # Label alphabet: the distinct label values present in the whole table.
        label_values = sorted(set(labels.tolist()))
        lab_counts = [int(np.sum(labels[sel] == v)) for v in label_values]
        out[f"{chamber}_label_counts"] = dict(zip([str(v) for v in label_values], lab_counts))
        out[f"{chamber}_label_entropy_bits"] = entropy_bits(lab_counts) if sel.any() else None
    # Score-bin distributions per chamber (constructional — see module docstring).
    adm_counts = np.bincount(bin_idx[chambers == "admitted"], minlength=n_bins)
    held_counts = np.bincount(bin_idx[chambers == "held"], minlength=n_bins)
    kl, disjoint = kl_bits(adm_counts, held_counts)
    out["score_kl_admitted_vs_held_bits"] = kl
    out["score_kl_disjoint_support"] = bool(disjoint)
    out["score_js_bits"] = js_bits(adm_counts, held_counts)
    # Joint score-bin x chamber -> MI(score bin; chamber), constructional.
    joint = np.zeros((n_bins, 2))
    joint[:, 0] = adm_counts
    joint[:, 1] = held_counts
    out["mi_score_bin_chamber_bits"] = mi_bits(joint)
    # Label distributions per chamber (non-circular evidence).
    label_values = sorted(set(labels.tolist()))
    adm_lab = np.array([np.sum(labels[chambers == "admitted"] == v) for v in label_values], dtype=float)
    held_lab = np.array([np.sum(labels[chambers == "held"] == v) for v in label_values], dtype=float)
    kl_lab, disjoint_lab = kl_bits(adm_lab, held_lab)
    out["label_kl_admitted_vs_held_bits"] = kl_lab
    out["label_kl_disjoint_support"] = bool(disjoint_lab)
    out["label_js_bits"] = js_bits(adm_lab, held_lab)
    joint_lab = np.zeros((len(label_values), 2))
    joint_lab[:, 0] = adm_lab
    joint_lab[:, 1] = held_lab
    out["mi_label_chamber_bits"] = mi_bits(joint_lab)
    # Label-1 rate gap, only meaningful for binary 0/1 labels.
    if set(label_values) == {0, 1} or set(label_values) == {0.0, 1.0}:
        adm_sel = chambers == "admitted"
        held_sel = chambers == "held"
        out["admitted_label1_rate"] = float(np.mean(labels[adm_sel] == 1)) if adm_sel.any() else None
        out["held_label1_rate"] = float(np.mean(labels[held_sel] == 1)) if held_sel.any() else None
        if out["admitted_label1_rate"] is not None and out["held_label1_rate"] is not None:
            out["label1_rate_gap"] = float(out["admitted_label1_rate"] - out["held_label1_rate"])
    out["small_n_warning"] = bool(min(out["admitted_n"], out["held_n"]) < 100)
    # Sparse-bin warning is on TOTAL bin counts, not per-chamber counts:
    # per-chamber counts are zero by construction for bins on the far
    # side of tau, so a per-chamber threshold would always fire.
    out["sparse_bin_warning"] = bool(np.any(adm_counts + held_counts < 5))
    return out


def flip_rates(scores, tau, deltas):
    """Flip fraction per delta.

    flip_plus: score in [tau-delta, tau) flips held -> admitted under +delta.
    flip_minus: score in [tau, tau+delta) flips admitted -> held under -delta.
    flip_either: |score - tau| < delta, i.e. would flip under a
    delta-sized perturbation in the direction toward tau.
    """
    scores = np.asarray(scores, dtype=float)
    n = len(scores)
    rows = []
    for delta in deltas:
        plus = int(np.sum((scores >= tau - delta) & (scores < tau)))
        minus = int(np.sum((scores >= tau) & (scores < tau + delta)))
        either = int(np.sum(np.abs(scores - tau) < delta))
        rows.append({
            "delta": float(delta),
            "flip_plus_n": plus,
            "flip_plus_rate": plus / n if n else 0.0,
            "flip_minus_n": minus,
            "flip_minus_rate": minus / n if n else 0.0,
            "flip_either_n": either,
            "flip_either_rate": either / n if n else 0.0,
        })
    return rows


def tau_sweep(df, taus, n_bins=10):
    """Chamber gap / label gap / divergences across tau."""
    scores = df["score"].to_numpy(dtype=float)
    rows = []
    for tau in taus:
        chambers = gate(scores, tau)
        m = chamber_metrics(df, chambers, n_bins)
        rows.append({
            "tau": float(tau),
            "admitted_n": m["admitted_n"],
            "held_n": m["held_n"],
            "admitted_mean_score": m["admitted_mean_score"],
            "held_mean_score": m["held_mean_score"],
            "mean_gap": (
                float(m["admitted_mean_score"] - m["held_mean_score"])
                if m["admitted_mean_score"] is not None and m["held_mean_score"] is not None
                else None
            ),
            "admitted_label1_rate": m.get("admitted_label1_rate"),
            "held_label1_rate": m.get("held_label1_rate"),
            "label1_rate_gap": m.get("label1_rate_gap"),
            "score_js_bits": m["score_js_bits"],
            "label_js_bits": m["label_js_bits"],
            "mi_label_chamber_bits": m["mi_label_chamber_bits"],
            "small_n_warning": m["small_n_warning"],
        })
    return rows


def shuffled_control(df, tau, seeds, n_bins=10):
    """Same tau, scores randomly permuted: label divergence should be ~0.

    Score-bin divergence will NOT be ~0 (the shuffled gate still
    thresholds on the shuffled score), and must not be read as evidence.
    """
    scores = df["score"].to_numpy(dtype=float)
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        shuffled = rng.permutation(scores)
        tmp = df.copy()
        tmp["score"] = shuffled
        # chamber_metrics uses df["score"] for binning; pass tmp so the
        # shuffled score, not the original, defines the bins.
        chambers = gate(shuffled, tau)
        m = chamber_metrics(tmp, chambers, n_bins)
        rows.append({
            "seed": int(seed),
            "admitted_n": m["admitted_n"],
            "held_n": m["held_n"],
            "label_js_bits": m["label_js_bits"],
            "mi_label_chamber_bits": m["mi_label_chamber_bits"],
            "label1_rate_gap": m.get("label1_rate_gap"),
            "score_js_bits": m["score_js_bits"],
        })
    return rows


def run_sort(df, tau, split, score_source, deltas=(0.01, 0.03, 0.05, 0.10),
             binnings=(10, 5, 20), seeds=(0, 1, 2),
             sweep_taus=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """Full run on one frozen table. Raises on identity failure."""
    df = df.copy()
    scores = df["score"].to_numpy(dtype=float)
    if np.isnan(scores).any():
        raise ValueError("score column contains NaN; frozen table must be complete")
    chambers = gate(scores, tau)
    n_in = len(df)
    n_adm = int(np.sum(chambers == "admitted"))
    n_held = int(np.sum(chambers == "held"))
    if n_adm + n_held != n_in:
        raise AssertionError(
            f"IDENTITY FAILURE: admitted {n_adm} + held {n_held} != N_in {n_in}"
        )
    result = {
        "tau": float(tau),
        "n_in": int(n_in),
        "split": split,
        "score_source": score_source,
        "counts": {"admitted": n_adm, "held": n_held},
        "identity_check": {"admitted_plus_held": n_adm + n_held, "n_in": n_in, "ok": True},
        "binnings": {str(b): chamber_metrics(df, chambers, b) for b in binnings},
        "flip_rates": flip_rates(scores, tau, deltas),
        "tau_sweep": tau_sweep(df, sweep_taus, n_bins=10),
        "shuffled_control": shuffled_control(df, tau, seeds, n_bins=10),
        "warnings": [],
    }
    primary = result["binnings"]["10"]
    result["mean_gap"] = (
        float(primary["admitted_mean_score"] - primary["held_mean_score"])
        if primary["admitted_mean_score"] is not None and primary["held_mean_score"] is not None
        else None
    )
    if primary["small_n_warning"]:
        result["warnings"].append("small-n: one chamber has fewer than 100 rows")
    if primary["sparse_bin_warning"]:
        result["warnings"].append("sparse bins: at least one score bin has fewer than 5 rows in total")
    # Binning sensitivity: label JS is binning-invariant by construction
    # (it uses only the label alphabet, not score bins), so its spread
    # is expected to be 0. Score JS DOES vary with binning, in
    # particular when a wide bin straddles tau; that spread is
    # reported, not hidden, and is not a stability failure.
    label_js = {b: result["binnings"][str(b)]["label_js_bits"] for b in binnings}
    score_js = {b: result["binnings"][str(b)]["score_js_bits"] for b in binnings}
    # Empty-chamber fix (Codex, 2026-11-01): chamber divergences are
    # None when a chamber is empty (JS undefined, not zero), so max/min
    # over None values crashed run_sort. Filter Nones; if none remain,
    # sensitivity is undefined, not 0, and not stable.
    label_vals = [v for v in label_js.values() if v is not None]
    score_vals = [v for v in score_js.values() if v is not None]
    label_spread = float(max(label_vals) - min(label_vals)) if label_vals else None
    score_spread = float(max(score_vals) - min(score_vals)) if score_vals else None
    stable = bool(label_spread is not None and label_spread < 0.05)
    result["binning_sensitivity"] = {
        "label_js_bits_by_binning": label_js,
        "label_js_spread_bits": label_spread,
        "score_js_bits_by_binning": score_js,
        "score_js_spread_bits": score_spread,
        "stable": stable,
        "note": "label JS is binning-invariant by construction; score JS varies when a bin straddles tau; spreads are null when a chamber is empty (divergence undefined)",
    }
    if label_spread is None:
        result["warnings"].append(
            "binning sensitivity undefined: empty chamber, label/score JS is null, not zero"
        )
    elif not stable:
        result["warnings"].append(
            f"binning instability: label JS spread {label_spread:.4f} bits across binnings >= 0.05"
        )
    return result


def compute_adult_score(df):
    """Transparent linear Adult score (see module docstring)."""
    age = df["age"].to_numpy(dtype=float)
    edu = df["education-num"].to_numpy(dtype=float)
    hrs = df["hours-per-week"].to_numpy(dtype=float)
    return np.clip(
        0.40 * edu / 16.0 + 0.35 * np.minimum(age, 80) / 80.0 + 0.25 * np.minimum(hrs, 80) / 80.0,
        0.0, 1.0,
    )


def load_adult_template(path):
    """Adult template -> frozen table: score computed, label 0/1, period stripped."""
    df = pd.read_csv(path)
    df["score"] = compute_adult_score(df)
    raw = df["income"].astype(str).str.strip().str.rstrip(".")
    mapping = {"<=50K": 0, ">50K": 1}
    if not raw.isin(mapping).all():
        bad = sorted(set(raw[~raw.isin(mapping)]))
        raise ValueError(f"unmapped income values: {bad}")
    df["label"] = raw.map(mapping).astype(int)
    df["score_source"] = "adult-linear-2026-11-01"
    df["chamber"] = ""
    return df[["id", "score", "label", "score_source", "chamber", "split"]]


def load_frozen_csv(path):
    """Generic frozen table: id, score, label, score_source, chamber, split."""
    df = pd.read_csv(path)
    df["score"] = df["score"].astype(float)
    return df


def write_outputs(result, json_path, csv_path):
    """One JSON (full) + one CSV (long-form metric rows) per run."""
    json_path = Path(json_path)
    csv_path = Path(csv_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    rows = []
    base = {
        "tau": result["tau"], "n_in": result["n_in"], "split": result["split"],
        "score_source": result["score_source"],
    }
    rows.append({**base, "metric": "admitted_n", "value": result["counts"]["admitted"], "binning": "", "note": "counts"})
    rows.append({**base, "metric": "held_n", "value": result["counts"]["held"], "binning": "", "note": "counts"})
    rows.append({**base, "metric": "identity_ok", "value": int(result["identity_check"]["ok"]), "binning": "", "note": "admitted+held must equal n_in"})
    rows.append({**base, "metric": "mean_gap", "value": result["mean_gap"], "binning": "", "note": "admitted mean minus held mean, score units"})
    for b, m in result["binnings"].items():
        for key in (
            "admitted_mean_score", "held_mean_score",
            "admitted_score_entropy_bits", "held_score_entropy_bits",
            "admitted_label_entropy_bits", "held_label_entropy_bits",
            "score_kl_admitted_vs_held_bits", "score_js_bits",
            "mi_score_bin_chamber_bits",
            "label_kl_admitted_vs_held_bits", "label_js_bits",
            "mi_label_chamber_bits", "admitted_label1_rate",
            "held_label1_rate", "label1_rate_gap",
        ):
            rows.append({**base, "metric": key, "value": m.get(key), "binning": b,
                         "note": "constructional if score_*; evidence if label_*"})
    for fr in result["flip_rates"]:
        rows.append({**base, "metric": "flip_either_rate", "value": fr["flip_either_rate"],
                     "binning": "", "note": f"delta={fr['delta']}"})
        rows.append({**base, "metric": "flip_plus_rate", "value": fr["flip_plus_rate"],
                     "binning": "", "note": f"delta={fr['delta']}"})
        rows.append({**base, "metric": "flip_minus_rate", "value": fr["flip_minus_rate"],
                     "binning": "", "note": f"delta={fr['delta']}"})
    for sw in result["tau_sweep"]:
        rows.append({**base, "metric": "tau_sweep_label_js_bits", "value": sw["label_js_bits"],
                     "binning": "10", "note": f"sweep_tau={sw['tau']}"})
        rows.append({**base, "metric": "tau_sweep_mean_gap", "value": sw["mean_gap"],
                     "binning": "10", "note": f"sweep_tau={sw['tau']}"})
        rows.append({**base, "metric": "tau_sweep_label1_rate_gap", "value": sw["label1_rate_gap"],
                     "binning": "10", "note": f"sweep_tau={sw['tau']}"})
    for sh in result["shuffled_control"]:
        rows.append({**base, "metric": "shuffled_label_js_bits", "value": sh["label_js_bits"],
                     "binning": "10", "note": f"seed={sh['seed']}"})
        rows.append({**base, "metric": "shuffled_mi_label_chamber_bits", "value": sh["mi_label_chamber_bits"],
                     "binning": "10", "note": f"seed={sh['seed']}"})
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tau", "n_in", "split", "score_source", "metric", "value", "binning", "note"])
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Maxwell's-demon isomorph sorter")
    parser.add_argument("--input", required=True, help="CSV frozen table or Adult template")
    parser.add_argument("--tau", type=float, required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--adult", action="store_true", help="compute Adult score in-backend, map income to 0/1")
    parser.add_argument("--json", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args(argv)
    if args.adult:
        df = load_adult_template(args.input)
        score_source = "adult-linear-2026-11-01"
    else:
        df = load_frozen_csv(args.input)
        score_source = str(df["score_source"].iloc[0]) if "score_source" in df else "unknown"
    result = run_sort(df, args.tau, args.split, score_source)
    write_outputs(result, args.json, args.csv)
    print(f"tau={args.tau} n={result['n_in']} split={args.split} "
          f"admitted={result['counts']['admitted']} held={result['counts']['held']} "
          f"identity_ok={result['identity_check']['ok']}")
    print(f"wrote {args.json} and {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
