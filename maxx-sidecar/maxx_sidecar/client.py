"""Sidecar client — spawns one demon per harness. Use as context manager.

    with SidecarClient(name="billing-demon", money_budget=1000.0) as sc:
        gated = sc.gate(action_dict)
        if gated["decision"] == "release":
            ok = sc.verify_permit(action["id"], gated["permit_id"])["ok"]

The client holds no permit store and no ledger. Both live in the
sidecar process it spawns. Closing the client shuts that sidecar down.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


class SidecarClient:
    def __init__(self, name="demon", money_budget=None, token_budget=None,
                 attention_budget=None, ledger_path=None):
        self.name = name
        cmd = [sys.executable, "-m", "maxx_sidecar.sidecar", "--name", name]
        if money_budget is not None:
            cmd += ["--money-budget", str(money_budget)]
        if token_budget is not None:
            cmd += ["--token-budget", str(token_budget)]
        if attention_budget is not None:
            cmd += ["--attention-budget", str(attention_budget)]
        if ledger_path is not None:
            cmd += ["--ledger-path", str(ledger_path)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, cwd=str(HERE))

    def _call(self, req):
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def ping(self):
        return self._call({"op": "ping"})

    def gate(self, action):
        raw = action.as_dict() if hasattr(action, "as_dict") else action
        return self._call({"op": "gate", "action": raw})

    def verify_permit(self, action_id, permit_id):
        return self._call({"op": "verify_permit", "action_id": action_id, "permit_id": permit_id})

    def cancel_permit(self, action_id, permit_id):
        """Return an unused permit's money reservation to the budget."""
        return self._call({"op": "cancel_permit", "action_id": action_id, "permit_id": permit_id})

    def ledger(self):
        return self._call({"op": "ledger"})

    def cost(self):
        return self._call({"op": "cost"})

    def close(self):
        try:
            self._call({"op": "shutdown"})
        except Exception:
            pass
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait(timeout=5)
        try:
            self.proc.stdout.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
