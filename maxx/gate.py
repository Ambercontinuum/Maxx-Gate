"""4. Gate / Permit — the enforcer. Exactly one decision per action.

PROPOSED PATCH 2026-10-28 (Bird 1, LOCAL ONLY, NOT LOCKED, NOT pushed to any repo).
Fixes, relative to the pre-patch scaffold:
  (a) Gate now READS stability advice: a "verify" advice blocks release/wrap
      (hold, or escalate if already at/above the escalate band). Before, the
      gate never read advice/K/flip_rate at all, so K could not act as a
      susceptibility signal for the gate.
  (b) Gate now accepts an OPTIONAL budget parameter. Default budget=None
      means "not consulted", so all pre-patch behaviour is preserved when
      no budget is supplied. Budget semantics below are PROPOSED, not locked.
  (c) OFF is now treated as MISSING, not as a present signal. Before,
      advise(None, None) returned proceed/OFF and the demo always passed an
      object, so fail-to-hold never ran in the demo.
  (d) Cool irreversible actions can no longer release. Before, a no-trace
      irreversible action scored 30 degrees and fell through to release.
  (e) Escalate reasons now state only true facts: "irreversible" appears
      only when the action is actually irreversible; reversible >=85
      actions say "reversible".

Bands below are SCAFFOLD VALUES, not locked thresholds, unless/until Amber
locks them. They are now injectable via GateConfig so a fitted band set can
replace them without editing this module — injectability is PROPOSED, the
values themselves are NOT locked.
"""
import uuid
from dataclasses import dataclass

from .intake import Action
from .stability import Stability
from .temperature import Temperature

WRAP_TYPES = {"send", "share", "delete"}


@dataclass(frozen=True)
class GateDecision:
    decision: str  # release | hold | wrap | escalate
    permit_id: str | None
    reason_plain: str
    wrapped_version: str | None


@dataclass(frozen=True)
class GateConfig:
    """PROPOSED, NOT LOCKED. Scaffold defaults; Amber locks any fitted values."""
    escalate_at: float = 85
    hold_at: float = 70
    wrap_at: float = 40


@dataclass(frozen=True)
class Budget:
    """PROPOSED budget semantics, NOT LOCKED.

    remaining_usd: money budget still available, in USD, in the same unit
    as Action.amount_usd. When a budget is supplied, it blocks RELEASE only:
    a would-be release whose amount exceeds the remaining budget is held
    instead. Hold/wrap/escalate decisions are unchanged by budget, because
    they do not release money. Amber must still decide: (1) whether budget
    should also block wrap/escalate, (2) whether the budget unit is money,
    tokens, or temperature degrees, and (3) how spent/remaining is updated
    across a run (this patch does NOT mutate a budget — the caller owns it).
    """
    remaining_usd: float


def _is_missing(stability: Stability | None) -> bool:
    """Missing = no object, source OFF, or both K and flip_rate None.

    OFF is a statement that telemetry is off, not a clean bill of health.
    Treating it as "proceed" was the pre-patch defect (c).
    """
    if stability is None:
        return True
    if stability.source == "OFF":
        return True
    return stability.k is None and stability.flip_rate is None


def _stability_label(stability: Stability | None) -> str:
    if stability is None:
        return "missing (no stability object)"
    parts = [f"source {stability.source}"]
    if stability.k is not None:
        parts.append(f"K={stability.k}")
    if stability.flip_rate is not None:
        parts.append(f"flip_rate={stability.flip_rate}")
    return ", ".join(parts)


def _wrap(action: Action) -> str:
    if action.type == "send":
        # Do NOT echo the original proposed text: it may name a wrong
        # attachment. A corrected draft omits the attachment entirely and
        # requires a human to attach the correct file before sending.
        # No correct filename is invented here — it is not in the queue.
        return ("Corrected draft — review before sending: report draft, "
                "attachment omitted for verification — the original "
                "attachment was incorrect and is not included. "
                "Attach the correct file before sending.")
    if action.type == "share":
        return f"Limited expiring link version of: {action.description} (external share held, link expires, scope limited)"
    if action.type == "delete":
        return f"Archive instead of delete: {action.description} (move to archive, do not permanently delete)"
    return f"Wrapped version of: {action.description}"


def decide(
    action: Action,
    temp: Temperature,
    stability: Stability | None,
    budget: Budget | None = None,
    config: GateConfig | None = None,
) -> GateDecision:
    """Deterministic gate. No permit, no release. Missing signal holds irreversible actions.

    Decision order (PROPOSED):
      0. Curiosity -> parked (unchanged from pre-patch; curiosity-with-trace
         handling is still an open Amber decision, see patch notes).
      1. Missing stability + irreversible -> hold (fail-to-hold).
      2. Temperature >= escalate band -> escalate, with a true reason.
      3. Stability advice == "verify" -> hold (verify blocks release/wrap).
      4. Temperature >= hold band -> hold.
      5. Temperature >= wrap band and type is wrap-able -> wrap.
      6. Temperature >= wrap band, other types -> hold.
      7. Cool but irreversible -> hold (fix for defect (d)).
      8. Budget supplied and amount exceeds remaining -> hold (release only).
      9. Otherwise -> release with a one-use permit.
    Missing + reversible actions are NOT held by step 1: they proceed on
    temperature alone, but a release reason then states the signal is
    missing, so the gap is visible rather than silent.
    """
    cfg = config or GateConfig()
    # Curiosity with no physical trace is parked, never budgeted.
    if action.type == "curiosity":
        return GateDecision("hold", None, "Parked — no physical trace, no budget spent.", None)
    # Fail-to-hold: a missing stability signal must not pass an irreversible action.
    if _is_missing(stability) and not temp.reversible:
        return GateDecision(
            "hold", None,
            f"Held — a stability check is missing ({_stability_label(stability)}) and this action cannot be undone.",
            None,
        )
    if temp.temperature >= cfg.escalate_at:
        reversibility = "irreversible" if not temp.reversible else "reversible"
        verify_note = ""
        if stability is not None and stability.advice == "verify":
            verify_note = f", stability advice is verify ({_stability_label(stability)})"
        return GateDecision(
            "escalate", None,
            f"Escalated — {temp.temperature:.0f} degrees, {reversibility}{verify_note}. A human must approve this.",
            None,
        )
    # Verify blocks release/wrap: the gate now reads stability advice (defect (a)).
    if stability is not None and stability.advice == "verify":
        return GateDecision(
            "hold", None,
            f"Held — {temp.temperature:.0f} degrees, stability advice is verify ({_stability_label(stability)}). Verify before money moves, files are lost, or an irreversible action goes out.",
            None,
        )
    if temp.temperature >= cfg.hold_at:
        return GateDecision(
            "hold", None,
            f"Held — {temp.temperature:.0f} degrees. Verify before money moves, files are lost, or an irreversible action goes out.",
            None,
        )
    if temp.temperature >= cfg.wrap_at and action.type in WRAP_TYPES:
        return GateDecision(
            "wrap", None,
            f"Wrapped — {temp.temperature:.0f} degrees. Here is a safer version; the original is not released.",
            _wrap(action),
        )
    if temp.temperature >= cfg.wrap_at:
        return GateDecision(
            "hold", None,
            f"Held — {temp.temperature:.0f} degrees. A human should read this before release.",
            None,
        )
    # Cool irreversible: temperature alone must not permit an irreversible release.
    if not temp.reversible:
        return GateDecision(
            "hold", None,
            f"Held — {temp.temperature:.0f} degrees, irreversible. Cool temperature alone does not permit an irreversible release.",
            None,
        )
    # Budget (PROPOSED semantics): blocks release only, when supplied.
    if budget is not None and action.amount_usd > 0 and action.amount_usd > budget.remaining_usd:
        return GateDecision(
            "hold", None,
            f"Held — {temp.temperature:.0f} degrees, ${action.amount_usd:.2f} exceeds the remaining budget of ${budget.remaining_usd:.2f}.",
            None,
        )
    # Cool and reversible: release with a one-use permit tied to this action.
    missing_note = ""
    if _is_missing(stability):
        missing_note = f" Stability signal missing ({_stability_label(stability)}); released on temperature alone."
    return GateDecision(
        "release", f"permit-{action.id}-{uuid.uuid4().hex[:8]}",
        f"Released — {temp.temperature:.0f} degrees, reversible, cost-bearer {temp.cost_bearer}.{missing_note}",
        None,
    )
