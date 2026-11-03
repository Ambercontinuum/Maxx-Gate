"""Cost of an action — accounting, not feeling, not joules.

Temperature is stated arithmetic, in degrees as a score (not kelvin):
floor 15 + trace weights (money 40, contract 25, person 20, schedule 15,
device 10) + 15 if irreversible, capped at 98. Cost-bearer is always
"operator"; recipient is recorded separately, never conflated.

Regulation uses these costs, it does not just display them: the gate
holds/escalates high-cost irreversible actions, wraps medium-cost
send/share/delete actions, and enforces budgets (see gate.py).
"""
from dataclasses import dataclass

from .actions import Action

TRACE_WEIGHTS = {"money": 40, "contract": 25, "person": 20, "schedule": 15, "device": 10}


@dataclass(frozen=True)
class Cost:
    temperature: float
    tokens_est: int  # per-action estimate, 100 + temperature; see ledger note
    attention_items: int
    money_usd: float
    reversible: bool
    cost_bearer: str = "operator"


def cost_of(action: Action) -> Cost:
    temp = 15 + sum(TRACE_WEIGHTS[t] for t in action.trace)
    if not action.reversible:
        temp += 15
    temp = min(temp, 98)
    return Cost(temperature=temp, tokens_est=100 + int(temp),
                attention_items=1, money_usd=action.amount_usd,
                reversible=action.reversible)
