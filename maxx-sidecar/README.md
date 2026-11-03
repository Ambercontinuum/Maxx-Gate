# Maxx sidecar — a demon per harness, built to regulate cost

New code, written 2026-11-01 in the hackathon window. First pushed 2026-11-01 to
the old `Ambercontinuum/Maxx` branch `submission-integrated-2026-11-01`, and
re-pushed core-only to `Ambercontinuum/Maxx-Gate` main on 2026-11-03.
This repo is still private, not flipped public, nothing submitted.
Codex verification status, stated plainly: Codex verified `eb7e24c…`
on the old branch (64 tests at that time); do NOT claim Codex verified
the later combined-budgets change (`43396a2b…`) — no reply to that
push is in the conversation yet. Local verification 2026-11-02 and
2026-11-03: 15 sidecar tests pass, single-agent demo prints
"Golden check PASSED."
No SERAPH code is imported or copied. This is executable code, not a skills
doc: a skills doc can be ignored or rewritten by the agent it guides; a
sidecar permit cannot be forged, and a tool call without one does not run.

## The idea, in one line
Maxx is the intent, the sidecar is the enforcement. Every agent +
harness gets its own demon sidecar — a separate process that regulates
the thermodynamic cost of the information that harness processes, in
accounting units, not joules. Maxx states what should happen to each
proposed action; the sidecar enforces it with a one-use permit and a
ledger the agent cannot rewrite.

## Connection to the sorter — read this first
See `CONNECTION.md` for the intended connection, stated before further
features: the sorter is the experimental foundation (threshold rule
separating a frozen logged stream, non-circular label divergence on a
held-out label), the sidecar is the deployment of that same door form
to live actions (threshold bands, executed vs not-executed chambers,
conserved counting ledger, enforced by permits and budgets). The
connection does NOT prove the sidecar's temperature score predicts
real-world harm — that held-out outcome has not been measured yet —
and it does NOT validate Petermann K, which remains stub, null, and
flat in the Glimmer sweep (see CONNECTION.md for the full limits).

```
Agent proposes -> Harness -> Demon sidecar (separate process) -> Tools
                      ^                |
                      |   gate, permit, budget, ledger (sidecar-owned)
                      +---- execute only as gated ----+
```

## What "regulate" means here — not just measure
The sidecar does not just report cost. It enforces it:
- **Gate by cost:** temperature (stated arithmetic, degrees as a score,
  not kelvin) + irreversibility + stability advice decide release / hold /
  wrap / escalate. High-cost irreversible actions escalate or hold; they
  do not pass. Medium-cost send/share/delete actions are wrapped — only
  the safer version may execute, never the original.
- **Budgets, when set:** money budget is RESERVED at gate time and
  consumed at verified execution, so two outstanding $60 permits
  against a $100 budget cannot both verify (second gate holds, budget
  never goes negative; unreserved permits are atomically rechecked at
  verify and fail rather than overspend); token budget caps information
  processed, after which actions hold; attention budget caps human
  checks — a zero-check budget blocks wraps and counts no attention,
  while releases (which need no check) still proceed. If a money hold
  arrives when attention is already exhausted, it becomes a system
  hold mentioning both budgets and counting no attention. Budgets are
  counting limits in stated units. No conserved physics budget, no
  joules, no kelvin is claimed.
- **Permits:** only a release carries a one-use permit, issued by that
  sidecar, verified exactly once, in that sidecar only. A permit from
  another demon fails. A release claimed without a verified permit
  executes nothing.
- **Harness enforcement:** the harness, not the executor, decides
  whether any tool runs. Custom executors are never called for
  held/escalated actions, for releases whose permit verification
  failed, for wraps with no wrapped version, or for unknown decisions;
  for wraps, the executor receives a sanitized action whose proposed
  text IS the wrapped version, so it cannot execute the original.
- **Ledger:** sidecar-owned, agent cannot rewrite it. Identities checked:
  tokens in = retained + discarded; decision counts = entries; held /
  escalated actions never executed.

## Cost, in stated units
Per action: temperature, tokens estimate (100 + temperature), attention
items (1), money at risk, reversibility, cost-bearer always "operator"
(recipient recorded separately). Per sidecar ledger: tokens 100/action
in / retained / discarded (the golden 800 / 400 / 400), attention
baseline / gated / saved, money at risk / held / released, irreversible
releases baseline / gated.

## Use it
```python
from maxx_sidecar import SidecarClient, Harness

with SidecarClient(name="billing-demon", money_budget=1000.0) as client:
    receipts = Harness(client).run(my_actions)  # list of action dicts
    ledger = client.ledger()
```

Fleet — one demon per harness:
```python
from maxx_sidecar import Fleet
fleet = Fleet()
fleet.add("billing-demon", billing_actions)
fleet.add("comms-demon", comms_actions)
results = fleet.run_all()          # each sidecar separate, ledgers separate
agg = fleet.aggregate(results)     # read-only sum, never a merged ledger
```

## Run it
```
python3 examples/single_agent_demo.py   # golden 1/2/3/2, 800/400/400, $1,090
python3 examples/fleet_demo.py          # 3 demons, same aggregate total
python3 -m unittest discover -s tests  # 15 tests, including Codex regression tests
```

## Video hero
The single-agent demo (`examples/single_agent_demo.py`) is the video
hero form: the video script for the single-sidecar form was approved by
Amber as written on 2026-11-02, then edited the same day for the
reputation wording and is NOT approved as written after that edit —
it needs her re-approval before recording. The video itself is not yet
recorded, and no freeze has been declared. The fleet demo
(`examples/fleet_demo.py`) stays a repo example only, not a video beat.

## What is simulated, what is real
Real: gate decisions, permits, budgets, ledger identities, process
isolation. Simulated: the world — mock tools only, SYNTHETIC, NO REAL
MONEY, NO REAL SEND/SHARE/BOOK/POST/DELETE. Seeded queue only; no live
model run is claimed. Stability is STUB advice unless real telemetry is
supplied; the gate works if it is off, flat, or missing.

## Provenance
New 2026-11-01 code in `maxx_sidecar/`. Seeded queue copied from the
integrated demo's queue (same 8 actions, same golden numbers). This
folder is in `Ambercontinuum/Maxx-Gate` main, core-only, pushed
2026-11-03; not flipped public, not submitted. The separate local
prototype `~/workspace/maxx-sidecar-demo/` is NOT in this repo — see
its own README for the video-script source.
