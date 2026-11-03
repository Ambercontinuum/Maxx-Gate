"""Maxx sidecar package — executable code, not a skills doc.

A demon sidecar is a separate process attached to one agent harness.
It REGULATES the cost of the information that harness processes: it
does not merely report cost, it decides which actions pass, which are
transformed, and which are held — and it enforces budgets and one-use
permits so the agent cannot execute around it.

Cost here is accounting in stated units, never joules or kelvin:
tokens (in / retained / discarded), attention checks required,
money at risk / held, reversibility, and stability advice.
No conserved physics budget is claimed.
"""
from .actions import validate
from .client import SidecarClient
from .cost import Cost, cost_of
from .fleet import Fleet
from .gate import decide
from .harness import Harness

__all__ = ["validate", "SidecarClient", "Cost", "cost_of", "Fleet", "decide", "Harness"]
