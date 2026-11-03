"""Gate / Permit — the regulator. Exactly one decision per action.

This is REGULATION, not reporting:
  - High-cost irreversible actions escalate or hold — they do not pass.
  - Medium-cost send/share/delete actions are wrapped — only the safer
    version may execute, never the original as-is.
  - Cool irreversible actions hold — cool cost alone never permits them.
  - A missing stability signal holds irreversible actions (fail-to-hold).
  - Budget regulation (when a budget is set on the sidecar): a would-be
    release whose money cost exceeds the remaining money budget is held;
    a token budget caps total tokens processed; an attention budget caps
    actions requiring a human check, after which remaining actions hold.
    Budgets are counting limits in stated units, not physics.
  - Only a release carries a one-use permit. Wraps carry a wrapped
    version, NOT a permit. Holds/escalates carry neither.
  - No permit, no release. A permit verifies exactly once, in the
    sidecar that issued it — a permit from another sidecar fails.

Bands are the stated Maxx rule (escalate 85 / hold 70 / wrap 40),
not locked fitted thresholds.
"""
import uuid
from dataclasses import dataclass

from .actions import Action
from .cost import cost_of
from .stability import Stability, advise, is_missing

WRAP_TYPES = {"send", "share", "delete"}


@dataclass(frozen=True)
class GateDecision:
    decision: str
    permit_id: str | None
    reason_plain: str
    wrapped_version: str | None
    temperature: float
    # True only when the decision itself requires a human check.
    # Release and system budget-holds require none, so they must not
    # consume attention budget or increment attention_gated.
    attention_required: bool = False


@dataclass
class Budget:
    """Optional, per-sidecar regulation limits. None = not enforced."""
    money_usd: float | None = None
    tokens: int | None = None
    attention_checks: int | None = None


def _wrap(action: Action) -> str:
    if action.type == "send":
        return ("Corrected draft — review before sending: report draft, "
                "attachment omitted for verification — the original "
                "attachment was incorrect and is not included. "
                "Attach the correct file before sending.")
    if action.type == "share":
        return f"Limited expiring link version of: {action.description} (external share held, link expires, scope limited)"
    if action.type == "delete":
        return f"Archive instead of delete: {action.description} (move to archive, do not permanently delete)"
    return f"Wrapped version of: {action.description}"


def decide(action: Action, stability: Stability | None = None,
           budget: Budget | None = None,
           tokens_used: int = 0, attention_used: int = 0) -> GateDecision:
    cost = cost_of(action)
    temp = cost.temperature
    if stability is None:
        stability = advise(action.stability_k, action.flip_rate)
    attention_blocked = bool(
        budget and budget.attention_checks is not None
        and attention_used >= budget.attention_checks)

    def budget_hold():
        return GateDecision("hold", None,
                            f"Held — attention budget exhausted ({attention_used} checks). "
                            "Held, not executed, for later review outside this run.",
                            None, temp, attention_required=False)

    # Regulation 1: token budget — cap total information processed.
    # A token-budget hold is a system hold, not a human check.
    if budget and budget.tokens is not None and tokens_used + 100 > budget.tokens:
        return GateDecision("hold", None,
                            f"Held — token budget exhausted ({tokens_used} of {budget.tokens} used). No further information is processed.",
                            None, temp, attention_required=False)
    if action.type == "curiosity":
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None, "Parked — no physical trace, no budget spent.", None, temp, attention_required=True)
    if is_missing(stability) and not action.reversible:
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None,
                            "Held — a stability check is missing and this action cannot be undone.", None, temp, attention_required=True)
    if temp >= 85:
        if attention_blocked:
            return budget_hold()
        kind = "irreversible" if not action.reversible else "reversible"
        return GateDecision("escalate", None,
                            f"Escalated — {temp:.0f} degrees, {kind}. A human must approve this.", None, temp, attention_required=True)
    if stability.advice == "verify":
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None,
                            f"Held — {temp:.0f} degrees, stability advice is verify. Verify before money moves, files are lost, or an irreversible action goes out.", None, temp, attention_required=True)
    if temp >= 70:
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None,
                            f"Held — {temp:.0f} degrees. Verify before money moves, files are lost, or an irreversible action goes out.", None, temp, attention_required=True)
    if temp >= 40 and action.type in WRAP_TYPES:
        # Attention check BEFORE wrap: a wrap requires a human to review
        # the safer version, so a zero / exhausted attention budget must
        # not produce a wrap — and must not increment attention usage.
        if attention_blocked:
            return budget_hold()
        return GateDecision("wrap", None,
                            f"Wrapped — {temp:.0f} degrees. Here is a safer version; the original is not released.",
                            _wrap(action), temp, attention_required=True)
    if temp >= 40:
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None,
                            f"Held — {temp:.0f} degrees. A human should read this before release.", None, temp, attention_required=True)
    if not action.reversible:
        if attention_blocked:
            return budget_hold()
        return GateDecision("hold", None,
                            f"Held — {temp:.0f} degrees, irreversible. Cool temperature alone does not permit an irreversible release.", None, temp, attention_required=True)
    # Regulation 2: money budget — blocks release only, when set.
    # This hold is normally a human-review item (raise the budget /
    # review the spend), so it counts as attention-required — UNLESS
    # attention is already exhausted. Then it must use the same
    # exhausted-attention check as every other review path (Codex,
    # 2026-11-01): a system budget hold that mentions both budgets and
    # counts NO attention, so a $101 proposal against $100 money +
    # 0 attention cannot increment attention usage to 1.
    if budget and budget.money_usd is not None and action.amount_usd > budget.money_usd:
        if attention_blocked:
            return GateDecision("hold", None,
                                f"Held — ${action.amount_usd:.2f} exceeds the remaining money budget of ${budget.money_usd:.2f} "
                                f"and attention budget exhausted ({attention_used} checks). "
                                "Held, not executed, for later review outside this run.",
                                None, temp, attention_required=False)
        return GateDecision("hold", None,
                            f"Held — {temp:.0f} degrees, ${action.amount_usd:.2f} exceeds the remaining money budget of ${budget.money_usd:.2f}.", None, temp, attention_required=True)
    # Release requires no human check, so an exhausted attention budget
    # must NOT block a release — that is exactly the attention a gate saves.
    permit = f"permit-{action.id}-{uuid.uuid4().hex[:8]}"
    return GateDecision("release", permit,
                        f"Released — {temp:.0f} degrees, reversible, cost-bearer operator.", None, temp, attention_required=False)
