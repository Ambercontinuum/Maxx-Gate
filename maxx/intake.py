"""1. Intake — the action, nothing more. No LLM here."""
import math
from dataclasses import dataclass, field

ALLOWED_TYPES = {"pay", "send", "share", "book", "post", "delete", "draft", "curiosity"}
ALLOWED_TRACES = {"money", "schedule", "device", "person", "contract"}


@dataclass(frozen=True)
class Action:
    id: str
    type: str
    description: str
    trace: tuple = ()
    amount_usd: float = 0.0
    reversible: bool = True
    recipient: str = ""
    proposed_text: str = ""
    # Stub telemetry only for the scaffold demo, labeled STUB in output.
    # Glimmer telemetry plugs in here; it is never required for a gate decision.
    stability_k: float | None = None
    flip_rate: float | None = None


def validate(raw: dict) -> Action:
    """Validate one action record, or raise ValueError. Nothing else is accepted."""
    if not isinstance(raw, dict):
        raise ValueError("action must be an object")
    action_type = raw.get("type")
    if action_type not in ALLOWED_TYPES:
        raise ValueError(f"unknown action type: {action_type!r}")
    trace = tuple(raw.get("trace") or [])
    bad = [t for t in trace if t not in ALLOWED_TRACES]
    if bad:
        raise ValueError(f"unknown trace types: {bad}")
    if not raw.get("id") or not raw.get("description"):
        raise ValueError("action needs an id and a description")
    # Strict field types (verification fix, 2026-11-04): a string "false"
    # must never coerce to True — irreversibility misread is a release
    # risk — and an amount must be a finite, non-negative number, because
    # a negative amount would inflate a money budget instead of spending it.
    amount_raw = raw.get("amount_usd") or 0.0
    if isinstance(amount_raw, bool):
        raise ValueError(f"amount_usd must be a number: {amount_raw!r}")
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        raise ValueError(f"amount_usd must be a number: {amount_raw!r}") from None
    if not math.isfinite(amount) or amount < 0:
        raise ValueError(f"amount_usd must be finite and non-negative: {amount_raw!r}")
    reversible = raw.get("reversible", True)
    if not isinstance(reversible, bool):
        raise ValueError(f"reversible must be a boolean: {reversible!r}")
    return Action(
        id=str(raw["id"]),
        type=action_type,
        description=str(raw["description"]),
        trace=trace,
        amount_usd=amount,
        reversible=reversible,
        recipient=str(raw.get("recipient") or ""),
        proposed_text=str(raw.get("proposed_text") or ""),
        stability_k=raw.get("stability_k"),
        flip_rate=raw.get("flip_rate"),
    )
