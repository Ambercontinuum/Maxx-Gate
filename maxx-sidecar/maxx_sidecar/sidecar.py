"""Sidecar server — one demon per harness, in its own process.

Run: python3 -m maxx_sidecar.sidecar [--ledger-path FILE]
       [--money-budget USD] [--token-budget N] [--attention-budget N]
       [--name NAME]

Protocol: JSON lines over stdin/stdout.
  {"op": "ping"} -> {"ok": true, "name": ...}
  {"op": "gate", "action": {...}} -> decision + permit (release only)
  {"op": "verify_permit", "action_id": ..., "permit_id": ...} -> {"ok": bool}
      A permit verifies exactly once, in THIS sidecar only.
      Money budget regulation (Codex fix, 2026-11-01): at gate time a
      release RESERVES its amount against the remaining money budget,
      so a second outstanding permit cannot be issued over budget.
      At verify time the reservation is consumed (money_released +=
      amount, budget already reduced at gate). For any permit without a
      reservation, verify atomically rechecks amount <= remaining and
      fails (consuming the permit) rather than letting the budget go
      negative. {"op": "cancel_permit", ...} returns a reservation.
  {"op": "ledger"} -> sidecar-owned ledger + cost + remaining budgets
  {"op": "cost"} -> current cost regulation summary
  {"op": "shutdown"} -> write ledger file (if set), exit 0

The permit store and ledger live ONLY here. The agent process never
sees them; the harness only receives decisions, permit tokens, and
ledger reports by protocol. That is what makes this more than a skills
doc: a doc can be ignored by the agent it guides; a sidecar permit
cannot be forged, and a tool call without one does not run.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from maxx_sidecar.actions import validate  # noqa: E402
from maxx_sidecar.gate import Budget, decide  # noqa: E402
from maxx_sidecar.stability import advise  # noqa: E402


class Sidecar:
    def __init__(self, name="demon", budget=None, ledger_path=None):
        self.name = name
        self.budget = budget or Budget()
        self.ledger_path = ledger_path
        self.permits = {}
        self.entries = []
        self.decisions = {"release": 0, "hold": 0, "wrap": 0, "escalate": 0}
        self.tokens_in = 0
        self.tokens_retained = 0
        self.tokens_discarded = 0
        self.tokens_est_total = 0
        self.money_held = 0.0
        self.money_at_risk = 0.0
        self.money_released = 0.0
        self.irreversible_baseline = 0
        self.irreversible_gated = 0
        self.attention_gated = 0

    def gate(self, raw):
        action = validate(raw)
        stability = advise(action.stability_k, action.flip_rate)
        decision = decide(action, stability, self.budget,
                          tokens_used=self.tokens_in,
                          attention_used=self.attention_gated)
        if decision.permit_id:
            # Reserve money at gate time: prevents two outstanding
            # $60 permits against a $100 budget both verifying.
            amount = action.amount_usd
            if self.budget.money_usd is not None:
                self.budget.money_usd -= amount
            self.permits[decision.permit_id] = {
                "action_id": action.id, "amount_usd": amount,
                # True iff this permit's amount was already subtracted
                # from the money budget at gate time.
                "money_reserved": self.budget.money_usd is not None,
            }
        self.decisions[decision.decision] += 1
        self.tokens_in += 100
        self.tokens_est_total += 100 + int(decision.temperature)
        if decision.decision in ("release", "wrap"):
            self.tokens_retained += 100
        else:
            self.tokens_discarded += 100
        if decision.attention_required:
            self.attention_gated += 1
        self.money_at_risk += action.amount_usd
        if not action.reversible:
            self.irreversible_baseline += 1
        if decision.decision in ("hold", "wrap", "escalate"):
            self.money_held += action.amount_usd
        if decision.decision == "release" and not action.reversible:
            self.irreversible_gated += 1
        entry = {"id": action.id, "type": action.type, "temperature": decision.temperature,
                 "cost_bearer": "operator", "recipient": action.recipient,
                 "decision": decision.decision, "permit_id": decision.permit_id,
                 "reason": decision.reason_plain, "wrapped_version": decision.wrapped_version,
                 "amount_usd": action.amount_usd, "reversible": action.reversible,
                 "attention_required": decision.attention_required}
        self.entries.append(entry)
        return {"decision": decision.decision, "permit_id": decision.permit_id,
                "reason": decision.reason_plain, "wrapped_version": decision.wrapped_version,
                "temperature": decision.temperature,
                "attention_required": decision.attention_required}

    def verify(self, action_id, permit_id):
        entry_permit = self.permits.get(permit_id) if permit_id else None
        if not entry_permit or entry_permit["action_id"] != action_id:
            return {"ok": False}
        amount = entry_permit["amount_usd"]
        # Atomic recheck for permits without a money reservation:
        # fail (and consume the permit) rather than go negative.
        if not entry_permit.get("money_reserved", False) and self.budget.money_usd is not None:
            if amount > self.budget.money_usd:
                del self.permits[permit_id]
                return {"ok": False}
            self.budget.money_usd -= amount
        # Reserved permits: budget was already reduced at gate time,
        # so verify only consumes the reservation and records release.
        del self.permits[permit_id]
        self.money_released += amount
        return {"ok": True}

    def cancel_permit(self, action_id, permit_id):
        entry_permit = self.permits.get(permit_id) if permit_id else None
        if not entry_permit or entry_permit["action_id"] != action_id:
            return {"ok": False}
        if entry_permit.get("money_reserved", False) and self.budget.money_usd is not None:
            self.budget.money_usd += entry_permit["amount_usd"]
        del self.permits[permit_id]
        return {"ok": True}

    def ledger(self):
        assert self.tokens_in == self.tokens_retained + self.tokens_discarded
        assert sum(self.decisions.values()) == len(self.entries)
        return {
            "sidecar": self.name,
            "tokens_in": self.tokens_in, "tokens_retained": self.tokens_retained,
            "tokens_discarded": self.tokens_discarded,
            "tokens_est_total": self.tokens_est_total,
            "decisions": self.decisions,
            "attention_baseline": len(self.entries),
            "attention_gated": self.attention_gated,
            "attention_saved": len(self.entries) - self.attention_gated,
            "money_at_risk_baseline_usd": self.money_at_risk,
            "money_held_by_gate_usd": self.money_held,
            "money_released_usd": self.money_released,
            "money_budget_remaining_usd": self.budget.money_usd,
            "token_budget": self.budget.tokens,
            "attention_budget": self.budget.attention_checks,
            "irreversible_released_baseline": self.irreversible_baseline,
            "irreversible_released_gated": self.irreversible_gated,
            "entries": self.entries,
        }

    def save(self):
        if self.ledger_path:
            Path(self.ledger_path).write_text(json.dumps(self.ledger(), indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger-path", default=None)
    parser.add_argument("--money-budget", type=float, default=None)
    parser.add_argument("--token-budget", type=int, default=None)
    parser.add_argument("--attention-budget", type=int, default=None)
    parser.add_argument("--name", default="demon")
    args = parser.parse_args()
    sidecar = Sidecar(name=args.name,
                      budget=Budget(money_usd=args.money_budget, tokens=args.token_budget,
                                    attention_checks=args.attention_budget),
                      ledger_path=args.ledger_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"error": "bad json"}), flush=True)
            continue
        op = req.get("op")
        if op == "ping":
            print(json.dumps({"ok": True, "name": sidecar.name}), flush=True)
        elif op == "gate":
            print(json.dumps(sidecar.gate(req["action"])), flush=True)
        elif op == "verify_permit":
            print(json.dumps(sidecar.verify(req.get("action_id"), req.get("permit_id"))), flush=True)
        elif op == "cancel_permit":
            print(json.dumps(sidecar.cancel_permit(req.get("action_id"), req.get("permit_id"))), flush=True)
        elif op == "ledger":
            print(json.dumps(sidecar.ledger()), flush=True)
        elif op == "cost":
            led = sidecar.ledger()
            print(json.dumps({k: led[k] for k in (
                "tokens_in", "tokens_retained", "tokens_discarded", "tokens_est_total",
                "attention_gated", "attention_saved", "money_held_by_gate_usd",
                "money_released_usd", "money_budget_remaining_usd",
                "irreversible_released_gated")}), flush=True)
        elif op == "shutdown":
            sidecar.save()
            print(json.dumps({"ok": True}), flush=True)
            break
        else:
            print(json.dumps({"error": f"unknown op {op!r}"}), flush=True)


if __name__ == "__main__":
    main()
