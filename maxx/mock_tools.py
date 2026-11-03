"""7. Mock tools — SIMULATED external side effects, ADOPTED 2026-10-28.

ADOPTED / SYNTHETIC ONLY. Pushed to Ambercontinuum/Maxx (private) 2026-10-28 at Amber's instruction.

What is real here: the gate decision that precedes every call. What is
simulated here: the world the action would touch. These tools NEVER call
Stripe, Gmail, Drive, a travel provider, or a social platform. They make
no network call of any kind — this module imports no http, socket, or
urllib code, by design — and they move no real money.

Rules enforced by this layer, not by the caller:
  - hold / escalate -> NOTHING executes. No receipt, no content.
  - wrap -> ONLY the wrapped version executes. The original is never
    released as-is (e.g. never sent as a send). The send wrap does NOT
    echo the original text: a corrected draft omits the (incorrect)
    attachment and requires a human to attach the correct file.
  - release -> executes only with a one-use permit. No permit, no release.
  - draft -> a draft object is created in memory. It is NEVER sent.
  - curiosity / parked -> nothing executes (the gate returns hold).

Every receipt says, in plain text, that its effect is NONE in the real
world. Demo captions must carry: SYNTHETIC, NO REAL MONEY, NO REAL
SEND / SHARE / BOOK / POST / DELETE.
"""
import hashlib
from dataclasses import dataclass

from .gate import GateDecision
from .intake import Action

TOOL_NAMES = {
    "pay": "mock-pay",
    "send": "mock-send",
    "share": "mock-share",
    "book": "mock-book",
    "post": "mock-post",
    "delete": "mock-delete",
    "draft": "mock-draft-create",
    "curiosity": "mock-no-op",
}

NO_REAL_EFFECT = "NONE — SYNTHETIC ONLY: no real money moved, nothing sent, shared, booked, posted, or deleted."


@dataclass(frozen=True)
class MockReceipt:
    action_id: str
    tool: str
    executed: bool
    status: str  # mock-executed | mock-wrapped-executed | mock-not-executed
    receipt_id: str | None
    executed_content: str | None
    simulated_effect: str
    real_world_effect: str = NO_REAL_EFFECT


def _receipt_id(action_id: str, permit_id: str | None, content: str | None) -> str:
    """Deterministic mock receipt id (same inputs -> same id, no randomness)."""
    raw = f"{action_id}|{permit_id or ''}|{content or ''}".encode()
    return "mock-" + hashlib.sha256(raw).hexdigest()[:12]


def execute(action: Action, decision: GateDecision) -> MockReceipt:
    """Execute the gated action through a simulated tool, or execute nothing.

    This is the only entry point the demo should use. It never reaches
    the network and never touches a real account, by construction.
    """
    tool = TOOL_NAMES.get(action.type, "mock-unknown")

    if decision.decision in ("hold", "escalate"):
        return MockReceipt(
            action_id=action.id,
            tool=tool,
            executed=False,
            status="mock-not-executed",
            receipt_id=None,
            executed_content=None,
            simulated_effect=(
                f"Nothing executed for {action.id}: gate decision was "
                f"{decision.decision.upper()}. The original action was NOT "
                "paid, sent, shared, booked, posted, or deleted."
            ),
        )

    if decision.decision == "wrap":
        if not decision.wrapped_version:
            # Fail safe: a wrap without a wrapped version executes nothing.
            return MockReceipt(
                action_id=action.id,
                tool=tool,
                executed=False,
                status="mock-not-executed",
                receipt_id=None,
                executed_content=None,
                simulated_effect=(
                    f"Nothing executed for {action.id}: wrap had no wrapped "
                    "version, so the original was not released."
                ),
            )
        return MockReceipt(
            action_id=action.id,
            tool=tool,
            executed=True,
            status="mock-wrapped-executed",
            receipt_id=_receipt_id(action.id, decision.permit_id, decision.wrapped_version),
            executed_content=decision.wrapped_version,
            simulated_effect=(
                f"Simulated wrapped execution only for {action.id}: "
                f"{decision.wrapped_version}"
            ),
        )

    if decision.decision == "release":
        if not decision.permit_id:
            # Fail safe: no permit, no release, even if the gate said release.
            return MockReceipt(
                action_id=action.id,
                tool=tool,
                executed=False,
                status="mock-not-executed",
                receipt_id=None,
                executed_content=None,
                simulated_effect=(
                    f"Nothing executed for {action.id}: release had no permit."
                ),
            )
        if action.type == "draft":
            content = f"DRAFT (not sent): {action.proposed_text or action.description}"
            effect = (
                f"Simulated draft created in memory for {action.id}. "
                "It was NOT sent to anyone."
            )
        else:
            content = action.proposed_text or action.description
            effect = f"Simulated execution only for {action.id}: {content}"
        return MockReceipt(
            action_id=action.id,
            tool=tool,
            executed=True,
            status="mock-executed",
            receipt_id=_receipt_id(action.id, decision.permit_id, content),
            executed_content=content,
            simulated_effect=effect,
        )

    # Unknown decision string: fail safe, execute nothing.
    return MockReceipt(
        action_id=action.id,
        tool=tool,
        executed=False,
        status="mock-not-executed",
        receipt_id=None,
        executed_content=None,
        simulated_effect=f"Nothing executed for {action.id}: unknown decision {decision.decision!r}.",
    )


# Thin per-tool wrappers. Each checks the action type matches the tool,
# then delegates to execute(), so the fail-safe rules live in one place.
def _typed(expected_type: str, action: Action, decision: GateDecision) -> MockReceipt:
    if action.type != expected_type:
        raise ValueError(f"{expected_type} tool called with {action.type!r} action")
    return execute(action, decision)


def mock_pay(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("pay", action, decision)


def mock_send(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("send", action, decision)


def mock_share(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("share", action, decision)


def mock_book(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("book", action, decision)


def mock_post(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("post", action, decision)


def mock_delete(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("delete", action, decision)


def mock_draft(action: Action, decision: GateDecision) -> MockReceipt:
    return _typed("draft", action, decision)
