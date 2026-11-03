"""Fixed-rule baseline arm — an adjacent comparison module, NOT the Maxx gate.

SYNTHETIC data only. No network, no API keys, standard library only.
Stability K is STUB and is NOT consulted here. This baseline is a
CANDIDATE comparison arm, not a validated result.

Purpose: give the demo a third arm to quote alongside the no-gate
baseline and the gated run, so the comparison is not only "gate vs.
nothing". A fixed-rule / prompt-only baseline is what a simple setup
looks like: each action is judged on its own, by a few surface rules,
with no whole-set view.

Exact rules (the complete rule set — nothing else is checked):
  1. One action at a time. No whole-set gate, no shared budget, no
     running total across actions. Each call sees one action only.
  2. No temperature check. Trace, temperature degrees, and cost-bearer
     are never read.
  3. No stability check. stability_k, flip_rate, and any K / advice
     value are never read.
  4. No budget check. No remaining-budget limit is applied, and the
     amount of one action never affects another action.
  5. Irreversibility alone does NOT block. An irreversible action
     passes exactly like a reversible one unless rule 6 or 7 fires.
  6. Blocked-phrase hold: if the action's description or proposed
     text (lowercased) contains one of BLOCKED_PHRASES, the decision
     is "hold" and nothing is released. None of the 8 seeded queue
     actions contains a blocked phrase.
  7. Amount cap hold: if amount_usd is greater than MAX_AMOUNT_USD
     (10,000), the decision is "hold" and nothing is released. The
     largest queue amount is $850, so no queue action hits this cap.
  8. Otherwise the decision is "release", unchanged: the released
     text is exactly the action's original proposed_text, the wrapped
     version is None (a fixed-rule release never wraps), and no gate
     permit is issued (permit_id is None — a baseline pass-through
     is not a Maxx permit).

Consequence for the seeded SYNTHETIC queue (data/queue.json, 8 actions):
every queue action passes rules 6 and 7, so the fixed-rule arm releases
all 8 unchanged — including the $240 pay, the $850 nonrefundable trip,
and, critically, the send with the wrong attachment, released with its
original text and wrong attachment intact, NOT wrapped to a corrected
draft. That is the point of the baseline: a surface rule cannot see
that the attachment is wrong, that the trip is nonrefundable, or that
the set as a whole spends a shared budget.

Attention accounting (documented so the three-arm totals are comparable):
  - no-gate arm: attention_checks = all actions (8). Nothing was
    triaged, so a human must still check every action.
  - fixed-rule arm: attention_checks = all actions (8). The surface
    rules triage nothing in this queue, so a human must still check
    every action. Attention saved vs. no-gate = 0.
  - gated arm: attention_checks = hold + wrap + escalate (7), exactly
    as Ledger.baseline_comparison() defines it: the 1 permitted
    release needs no further check, the other 7 need human attention.
    Attention saved vs. no-gate = 1.
Money accounting: money_at_risk_usd = sum of amount_usd over released
actions; money_held_usd = sum over non-released actions. Irreversible
releases = released actions where reversible is False. The gated arm
is computed with the real gate code (temperature.assign, stability.advise,
gate.decide), never hardcoded, so it stays honest if the queue changes.
"""

import json
import pathlib
from dataclasses import dataclass

from .gate import decide as _gated_decide
from .intake import Action, validate
from .stability import advise as _advise
from .temperature import assign as _assign

QUEUE = pathlib.Path(__file__).resolve().parent.parent / "data" / "queue.json"

# Rule 6: narrow, explicit phrases only. This is a surface keyword list,
# not a safety classifier, and it is the only content check in the arm.
BLOCKED_PHRASES = (
    "make a bomb",
    "build a weapon",
    "steal credentials",
    "exfiltrate passwords",
)

# Rule 7: single-action amount cap. No shared budget is tracked.
MAX_AMOUNT_USD = 10000.0


@dataclass(frozen=True)
class FixedRuleDecision:
    decision: str  # "release" | "hold"
    reason_plain: str
    released_text: str | None  # original proposed_text when released, else None
    wrapped_version: str | None = None  # always None: this arm never wraps
    permit_id: str | None = None  # always None: a pass-through is not a permit


def decide_fixed_rule(action: Action) -> FixedRuleDecision:
    """Judge one action by the fixed rules above, and nothing else.

    Deliberately unread here: action.trace, action.reversible,
    action.stability_k, action.flip_rate, temperature, budget, and
    every other action in the queue.
    """
    text = f"{action.description} {action.proposed_text}".lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in text:
            return FixedRuleDecision(
                "hold",
                f"Held by fixed rule — blocked phrase present: {phrase!r}.",
                None,
            )
    if action.amount_usd > MAX_AMOUNT_USD:
        return FixedRuleDecision(
            "hold",
            f"Held by fixed rule — ${action.amount_usd:.2f} exceeds the "
            f"single-action cap of ${MAX_AMOUNT_USD:.2f}.",
            None,
        )
    return FixedRuleDecision(
        "release",
        "Released by fixed rule — no blocked phrase, under the amount cap. "
        "No temperature, stability, budget, or reversibility check was applied.",
        action.proposed_text,
    )


def load_actions(queue_path=QUEUE) -> list[Action]:
    """Load and validate the SYNTHETIC queue. No network, file only."""
    raw = json.loads(pathlib.Path(queue_path).read_text())
    return [validate(item) for item in raw]


def run_fixed_rule(actions: list[Action]) -> list[FixedRuleDecision]:
    """Run the fixed-rule arm, one action at a time, in queue order."""
    return [decide_fixed_rule(action) for action in actions]


def run_gated(actions: list[Action]) -> list:
    """Run the real gated arm (temperature + stability advice + gate).

    This mirrors maxx.demo.run_with_mocks without printing and without
    mock-tool execution: same assign / advise / decide calls, no budget
    argument, so the gated totals here match the demo ledger exactly.
    """
    decisions = []
    for action in actions:
        temp = _assign(action)
        stability = _advise(action.stability_k, action.flip_rate)
        decisions.append(_gated_decide(action, temp, stability))
    return decisions


def _arm_totals(name: str, actions, decisions, attention_checks: int) -> dict:
    released = [a for a, d in zip(actions, decisions) if d.decision == "release"]
    counts = {"release": 0, "hold": 0, "wrap": 0, "escalate": 0}
    for d in decisions:
        counts[d.decision] += 1
    total_money = sum(a.amount_usd for a in actions)
    return {
        "arm": name,
        "actions": len(actions),
        "decisions": counts,
        "releases": len(released),
        "money_at_risk_usd": sum(a.amount_usd for a in released),
        "money_held_usd": total_money - sum(a.amount_usd for a in released),
        "money_total_usd": total_money,
        "irreversible_released": sum(1 for a in released if not a.reversible),
        "irreversible_total": sum(1 for a in actions if not a.reversible),
        "attention_checks": attention_checks,
        "attention_saved_vs_no_gate": len(actions) - attention_checks,
    }


def summarize_arms(actions=None, queue_path=QUEUE) -> dict:
    """Measured three-arm totals for one queue (default: the seeded queue).

    Returns a plain dict with one entry per arm plus a per-action table,
    so the demo can quote the numbers without re-running any arm:
      - "no_gate": every action released unchanged.
      - "fixed_rule": decide_fixed_rule per action, individually.
      - "gated": the real gate code, via run_gated.
    All three arms are computed from the same action list in this call;
    no total below is hardcoded.
    """
    if actions is None:
        actions = load_actions(queue_path)
    total = len(actions)
    no_gate_decisions = [FixedRuleDecision("release", "No gate — released unchanged.", a.proposed_text)
                         for a in actions]
    fixed_decisions = run_fixed_rule(actions)
    gated_decisions = run_gated(actions)
    per_action = []
    for action, no_gate, fixed, gated in zip(actions, no_gate_decisions, fixed_decisions, gated_decisions):
        per_action.append({
            "id": action.id,
            "description": action.description,
            "amount_usd": action.amount_usd,
            "reversible": action.reversible,
            "no_gate": no_gate.decision,
            "fixed_rule": fixed.decision,
            "fixed_rule_released_text": fixed.released_text,
            "fixed_rule_wrapped_version": fixed.wrapped_version,
            "gated": gated.decision,
        })
    gated_attention = sum(1 for d in gated_decisions if d.decision in ("hold", "wrap", "escalate"))
    return {
        "label": "SYNTHETIC three-arm comparison (no real money, no real sends)",
        "no_gate": _arm_totals("no_gate", actions, no_gate_decisions, total),
        "fixed_rule": _arm_totals("fixed_rule", actions, fixed_decisions, total),
        "gated": _arm_totals("gated", actions, gated_decisions, gated_attention),
        "per_action": per_action,
    }


def _table_row(arm: dict) -> str:
    return (f"| {arm['arm']} | {arm['releases']}/{arm['actions']} | "
            f"${arm['money_at_risk_usd']:.0f} | ${arm['money_held_usd']:.0f} | "
            f"{arm['irreversible_released']}/{arm['irreversible_total']} | "
            f"{arm['attention_checks']} | {arm['attention_saved_vs_no_gate']} |")


if __name__ == "__main__":
    summary = summarize_arms()
    print("--- Maxx three-arm comparison (SYNTHETIC, NO REAL MONEY) ---")
    print("| arm | released | money at risk | money held | irreversible released | attention checks | attention saved |")
    print("|---|---|---|---|---|---|---|")
    for key in ("no_gate", "fixed_rule", "gated"):
        print(_table_row(summary[key]))
    print()
    print("Fixed-rule send-wrong-attachment: released unchanged, NOT wrapped —")
    for row in summary["per_action"]:
        if row["id"] == "send-wrong-attachment":
            print(f"  fixed_rule={row['fixed_rule']}, released_text={row['fixed_rule_released_text']!r}, "
                  f"wrapped_version={row['fixed_rule_wrapped_version']!r}, gated={row['gated']}")
