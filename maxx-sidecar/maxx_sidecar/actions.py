"""Action intake — validation only, no LLM, no execution."""
from dataclasses import dataclass

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
    stability_k: float | None = None
    flip_rate: float | None = None

    def as_dict(self):
        return {
            "id": self.id, "type": self.type, "description": self.description,
            "trace": list(self.trace), "amount_usd": self.amount_usd,
            "reversible": self.reversible, "recipient": self.recipient,
            "proposed_text": self.proposed_text,
            "stability_k": self.stability_k, "flip_rate": self.flip_rate,
        }


def validate(raw: dict) -> Action:
    if not isinstance(raw, dict):
        raise ValueError("action must be an object")
    if raw.get("type") not in ALLOWED_TYPES:
        raise ValueError(f"unknown action type: {raw.get('type')!r}")
    trace = tuple(raw.get("trace") or [])
    bad = [t for t in trace if t not in ALLOWED_TRACES]
    if bad:
        raise ValueError(f"unknown trace types: {bad}")
    if not raw.get("id") or not raw.get("description"):
        raise ValueError("action needs an id and a description")
    return Action(
        id=str(raw["id"]), type=str(raw["type"]), description=str(raw["description"]),
        trace=trace, amount_usd=float(raw.get("amount_usd") or 0.0),
        reversible=bool(raw.get("reversible", True)),
        recipient=str(raw.get("recipient") or ""),
        proposed_text=str(raw.get("proposed_text") or ""),
        stability_k=raw.get("stability_k"), flip_rate=raw.get("flip_rate"),
    )
