"""6. Interface — one screen, plain language. No extra screens."""
from .gate import GateDecision
from .intake import Action
from .stability import Stability
from .temperature import Temperature


def render(action: Action, temp: Temperature, stability: Stability | None, decision: GateDecision) -> str:
    lines = [
        f"--- {action.id}: {action.description} ---",
        f"Type: {action.type} | Trace: {', '.join(action.trace) or 'none'} | Reversible: {temp.reversible}",
        f"Temperature: {temp.temperature:.0f} degrees | Bearer: operator | Recipient: {action.recipient or '—'} | Money at risk: ${temp.money_usd:.2f}",
        f"Stability: {stability.source if stability else 'OFF'}"
        + (f" | K={stability.k} | flip_rate={stability.flip_rate} | advice={stability.advice}" if stability and stability.k is not None else ""),
        f"Decision: {decision.decision.upper()} | Permit: {decision.permit_id or 'none'}",
        f"Reason: {decision.reason_plain}",
    ]
    if decision.wrapped_version:
        lines.append(f"Wrapped version: {decision.wrapped_version}")
    return "\n".join(lines)
