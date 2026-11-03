"""5. Ledger / Budget — the conserved quantity, vs. a no-gate baseline."""
from dataclasses import dataclass, field

from .gate import GateDecision
from .intake import Action
from .temperature import Temperature


@dataclass
class Ledger:
    tokens_in: int = 0
    tokens_retained: int = 0
    tokens_discarded: int = 0
    attention_required: int = 0
    attention_saved_vs_baseline: int = 0
    money_held_usd: float = 0.0
    money_at_risk_baseline_usd: float = 0.0
    irreversible_released: int = 0
    irreversible_released_baseline: int = 0
    decisions: dict = field(default_factory=lambda: {"release": 0, "hold": 0, "wrap": 0, "escalate": 0})
    entries: list = field(default_factory=list)
    receipts: list = field(default_factory=list)

    def record(self, action: Action, temp: Temperature, decision: GateDecision, receipt=None, stability=None):
        self.tokens_in += 100
        if decision.decision in ("release", "wrap"):
            self.tokens_retained += 100
        else:
            self.tokens_discarded += 100
        self.attention_required += 1
        self.money_at_risk_baseline_usd += action.amount_usd
        if not action.reversible:
            self.irreversible_released_baseline += 1
        if decision.decision in ("hold", "wrap", "escalate"):
            self.money_held_usd += action.amount_usd
        if decision.decision == "release" and not action.reversible:
            self.irreversible_released += 1
        self.decisions[decision.decision] += 1
        entry = {
            "id": action.id, "type": action.type, "temperature": temp.temperature,
            "cost_bearer": temp.cost_bearer, "decision": decision.decision,
            "permit_id": decision.permit_id, "reason": decision.reason_plain,
            # Record everything: action, stability, wrap, and mock execution.
            "amount_usd": action.amount_usd, "reversible": action.reversible,
            "trace": list(action.trace), "recipient": action.recipient,
            "proposed_text": action.proposed_text, "description": action.description,
            "wrapped_version": decision.wrapped_version,
            "stability_k": getattr(stability, "k", None),
            "stability_flip_rate": getattr(stability, "flip_rate", None),
            "stability_advice": getattr(stability, "advice", None),
            "stability_source": getattr(stability, "source", None),
            "mock_tool": getattr(receipt, "tool", None),
            "mock_status": getattr(receipt, "status", None),
            "mock_executed": getattr(receipt, "executed", None),
            "mock_receipt_id": getattr(receipt, "receipt_id", None),
            "mock_executed_content": getattr(receipt, "executed_content", None),
            "mock_simulated_effect": getattr(receipt, "simulated_effect", None),
            "mock_real_world_effect": getattr(receipt, "real_world_effect", None),
        }
        self.entries.append(entry)
        if receipt is not None:
            self.receipts.append({
                "action_id": receipt.action_id, "tool": receipt.tool,
                "executed": receipt.executed, "status": receipt.status,
                "receipt_id": receipt.receipt_id,
                "executed_content": receipt.executed_content,
                "simulated_effect": receipt.simulated_effect,
                "real_world_effect": receipt.real_world_effect,
            })

    def check_identities(self) -> None:
        """Exact identities. Any break is a bug — stop, do not demo around it."""
        assert self.tokens_in == self.tokens_retained + self.tokens_discarded, "tokens identity broken"
        assert sum(self.decisions.values()) == len(self.entries), "decision count identity broken"
        assert self.decisions["release"] == sum(
            1 for e in self.entries if e["decision"] == "release"
        ), "permit/release identity broken"
        if self.receipts:
            assert len(self.receipts) == len(self.entries), "receipt/entry identity broken"
            assert all(
                e["mock_receipt_id"] == r["receipt_id"] and e["id"] == r["action_id"]
                for e, r in zip(self.entries, self.receipts)
            ), "receipt/entry linkage broken"
            assert all(
                not r["executed"] for e, r in zip(self.entries, self.receipts)
                if e["decision"] in ("hold", "escalate")
            ), "held/escalated action executed identity broken"

    def baseline_comparison(self) -> dict:
        """No-gate baseline: every action processed in full, every action needs a human check."""
        total = len(self.entries)
        gated_attention = self.decisions["hold"] + self.decisions["wrap"] + self.decisions["escalate"]
        return {
            "actions": total,
            "attention_baseline": total,
            "attention_gated": gated_attention,
            "attention_saved": total - gated_attention,
            "money_at_risk_baseline_usd": self.money_at_risk_baseline_usd,
            "money_held_by_gate_usd": self.money_held_usd,
            "irreversible_released_baseline": self.irreversible_released_baseline,
            "irreversible_released_gated": self.irreversible_released,
        }
