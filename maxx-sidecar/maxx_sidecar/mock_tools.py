"""Mock tools — SIMULATED only, by design. No network, no real accounts.

Rules enforced here, not by the caller:
  - hold / escalate -> nothing executes, no receipt, no content.
  - wrap -> only the wrapped version executes, never the original.
  - release -> executes only with a verified (sidecar-consumed) permit.
  - draft -> a draft object in memory, never sent.
Every receipt states its real-world effect is NONE.
"""
import hashlib
from dataclasses import dataclass

TOOL_NAMES = {"pay": "mock-pay", "send": "mock-send", "share": "mock-share",
              "book": "mock-book", "post": "mock-post", "delete": "mock-delete",
              "draft": "mock-draft-create", "curiosity": "mock-no-op"}
NO_REAL_EFFECT = "NONE — SYNTHETIC ONLY: no real money moved, nothing sent, shared, booked, posted, or deleted."


@dataclass(frozen=True)
class MockReceipt:
    action_id: str
    tool: str
    executed: bool
    status: str
    receipt_id: str | None
    executed_content: str | None
    simulated_effect: str
    real_world_effect: str = NO_REAL_EFFECT


def _receipt_id(action_id, permit_id, content):
    raw = f"{action_id}|{permit_id or ''}|{content or ''}".encode()
    return "mock-" + hashlib.sha256(raw).hexdigest()[:12]


def execute(action, decision, wrapped_version=None, permit_verified=False):
    tool = TOOL_NAMES.get(action.type, "mock-unknown")
    if decision in ("hold", "escalate"):
        return MockReceipt(action.id, tool, False, "mock-not-executed", None, None,
                           f"Nothing executed for {action.id}: gate decision was {decision.upper()}.")
    if decision == "wrap":
        if not wrapped_version:
            return MockReceipt(action.id, tool, False, "mock-not-executed", None, None,
                               f"Nothing executed for {action.id}: wrap had no wrapped version.")
        return MockReceipt(action.id, tool, True, "mock-wrapped-executed",
                           _receipt_id(action.id, None, wrapped_version), wrapped_version,
                           f"Simulated wrapped execution only for {action.id}: {wrapped_version}")
    if decision == "release":
        if not permit_verified:
            return MockReceipt(action.id, tool, False, "mock-not-executed", None, None,
                               f"Nothing executed for {action.id}: release had no verified permit.")
        if action.type == "draft":
            content = f"DRAFT (not sent): {action.proposed_text or action.description}"
            effect = f"Simulated draft created in memory for {action.id}. It was NOT sent."
        else:
            content = action.proposed_text or action.description
            effect = f"Simulated execution only for {action.id}: {content}"
        return MockReceipt(action.id, tool, True, "mock-executed",
                           _receipt_id(action.id, "verified", content), content, effect)
    return MockReceipt(action.id, tool, False, "mock-not-executed", None, None,
                       f"Nothing executed for {action.id}: unknown decision {decision!r}.")
