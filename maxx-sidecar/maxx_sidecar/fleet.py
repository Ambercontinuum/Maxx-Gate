"""Fleet — every agent + harness gets its own demon.

Each harness spawns its OWN sidecar process, with its OWN permit store,
its OWN ledger, and its OWN budgets. Ledgers are never merged into one
mutable record; Fleet.aggregate() is a read-only sum for reporting.

That is the scale story, built, not just described: one trio per
harness, same gate logic everywhere, isolation by process. A permit
issued by one demon fails verification in every other demon — see tests.
"""
from .client import SidecarClient
from .harness import Harness


class Fleet:
    def __init__(self):
        self.harnesses = {}  # name -> (client, harness, queue)

    def add(self, name, queue, money_budget=None, token_budget=None,
            attention_budget=None, ledger_path=None, executor=None):
        client = SidecarClient(name=name, money_budget=money_budget,
                               token_budget=token_budget, attention_budget=attention_budget,
                               ledger_path=ledger_path)
        self.harnesses[name] = (client, Harness(client, executor), queue)
        return client

    def run_all(self):
        results = {}
        try:
            for name, (client, harness, queue) in self.harnesses.items():
                receipts = harness.run(queue)
                results[name] = {"receipts": receipts, "ledger": harness.ledger()}
        finally:
            self.close()
        return results

    def aggregate(self, results):
        decisions = {"release": 0, "hold": 0, "wrap": 0, "escalate": 0}
        tokens_in = tokens_retained = tokens_discarded = 0
        money_held = money_at_risk = 0.0
        for r in results.values():
            led = r["ledger"]
            for k in decisions:
                decisions[k] += led["decisions"][k]
            tokens_in += led["tokens_in"]
            tokens_retained += led["tokens_retained"]
            tokens_discarded += led["tokens_discarded"]
            money_held += led["money_held_by_gate_usd"]
            money_at_risk += led["money_at_risk_baseline_usd"]
        return {"decisions": decisions, "tokens_in": tokens_in,
                "tokens_retained": tokens_retained, "tokens_discarded": tokens_discarded,
                "money_at_risk_baseline_usd": money_at_risk,
                "money_held_by_gate_usd": money_held,
                "sidecars": list(results.keys())}

    def close(self):
        for client, _harness, _queue in self.harnesses.values():
            try:
                client.close()
            except Exception:
                pass
