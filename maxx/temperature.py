"""2. Temperature — deterministic, no LLM. Cost is accounting, never sentiment.

Rules (scaffold defaults, documented here, NOT locked thresholds):
- Temperature only from a real trace. No trace -> 15 degrees (cool floor).
- Trace weights: money 40, contract 25, person 20, schedule 15, device 10.
- Irreversible actions get +15 by rule, not by vibe.
- Capped at 98 degrees.
Amber sets any LOCKED threshold; this module must not be read as one.
"""
from dataclasses import dataclass

from .intake import Action

COOL_FLOOR = 15
CAP = 98
TRACE_WEIGHTS = {"money": 40, "contract": 25, "person": 20, "schedule": 15, "device": 10}
IRREVERSIBLE_BONUS = 15


@dataclass(frozen=True)
class Temperature:
    temperature: float
    trace: tuple
    cost_bearer: str
    reversible: bool
    tokens_est: int
    attention_items: int
    money_usd: float


def assign(action: Action) -> Temperature:
    temp = COOL_FLOOR + sum(TRACE_WEIGHTS[t] for t in action.trace)
    if not action.reversible:
        temp += IRREVERSIBLE_BONUS
    temp = min(temp, CAP)
    # Cost-bearer, locked pick 4 (Amber, 2026-10-31; redefined 2026-11-01):
    # bearer is the operator who pays, never the recipient. The recipient
    # stays on the action itself (action.recipient) and is recorded
    # separately in the ledger entry, so bearer and recipient are never
    # conflated. Never "costly in general".
    bearer = "operator"
    return Temperature(
        temperature=temp,
        trace=action.trace,
        cost_bearer=bearer,
        reversible=action.reversible,
        # Demo accounting units only: 100 tokens per action, scaled by heat.
        tokens_est=100 + int(temp),
        attention_items=1,
        money_usd=action.amount_usd,
    )
