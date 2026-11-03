"""Harness — the only path from an agent to tools, via its own sidecar.

Agent proposes -> Harness asks Sidecar -> Sidecar regulates (decide,
permit, budget, ledger) -> Harness executes a tool ONLY as gated.

ENFORCEMENT LIVES IN THE HARNESS, NOT IN THE EXECUTOR (Codex fix,
2026-11-01). A custom executor is NEVER called for:
  - hold / escalate decisions — nothing executes, no matter what the
    executor would do;
  - a release whose permit verification failed — no verified permit,
    no execution, even if the executor claims it can run;
  - a wrap with no wrapped version — the original must never run;
  - an unknown decision string.
For a wrap, the harness passes the executor a sanitized action whose
proposed_text IS the wrapped version, so even a naive executor that
ignores the wrapped_version argument cannot execute the original text.
The default executor is the mock tool set (simulated only).
"""
from dataclasses import replace

from .actions import validate
from .mock_tools import execute as mock_execute


class Harness:
    def __init__(self, client, executor=None):
        self.client = client
        self.executor = executor or self._mock_executor

    @staticmethod
    def _mock_executor(action, decision, wrapped_version, permit_verified):
        receipt = mock_execute(action, decision, wrapped_version, permit_verified)
        return receipt.executed, receipt.status, receipt.executed_content

    def run(self, raw_actions):
        receipts = []
        for raw in raw_actions:
            action = validate(raw)
            gated = self.client.gate(action)
            decision = gated["decision"]
            # --- Harness enforcement: decide whether ANY executor runs ---
            if decision in ("hold", "escalate"):
                receipts.append({"action_id": action.id, "decision": decision,
                                 "permit_verified": False, "executed": False,
                                 "status": "harness-blocked-not-executed", "content": None,
                                 "reason": gated["reason"],
                                 "temperature": gated["temperature"]})
                continue
            if decision not in ("release", "wrap"):
                receipts.append({"action_id": action.id, "decision": decision,
                                 "permit_verified": False, "executed": False,
                                 "status": "harness-blocked-unknown-decision", "content": None,
                                 "reason": gated["reason"],
                                 "temperature": gated["temperature"]})
                continue
            verified = False
            if decision == "release":
                verified = self.client.verify_permit(action.id, gated["permit_id"])["ok"]
                if not verified:
                    receipts.append({"action_id": action.id, "decision": decision,
                                     "permit_verified": False, "executed": False,
                                     "status": "harness-blocked-no-permit", "content": None,
                                     "reason": gated["reason"],
                                     "temperature": gated["temperature"]})
                    continue
                exec_action = action
            else:  # wrap
                wrapped = gated.get("wrapped_version")
                if not wrapped:
                    receipts.append({"action_id": action.id, "decision": decision,
                                     "permit_verified": False, "executed": False,
                                     "status": "harness-blocked-no-wrapped-version", "content": None,
                                     "reason": gated["reason"],
                                     "temperature": gated["temperature"]})
                    continue
                # Sanitized action: a custom executor that reads
                # proposed_text can only ever see the wrapped version.
                exec_action = replace(action, proposed_text=wrapped)
            executed, status, content = self.executor(
                exec_action, decision, gated.get("wrapped_version"), verified)
            # Defense in depth: if an executor claims it executed a
            # decision the harness blocked above, that path never reaches
            # here — blocked decisions return before this call.
            receipts.append({"action_id": action.id, "decision": decision,
                             "permit_verified": verified, "executed": executed,
                             "status": status, "content": content,
                             "reason": gated["reason"],
                             "temperature": gated["temperature"]})
        return receipts

    def ledger(self):
        return self.client.ledger()
