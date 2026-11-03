# Maxx — a Maxwell's-demon gate that moves information like physics

## Maxx, in one line
Maxx is the intent, the sidecar is the enforcement. Maxx states what
should happen to each proposed action — release, wrap, hold, or
escalate, with one plain reason — and the sidecar, a separate process
outside the agent, enforces that decision: it issues a one-use permit
only for a release and keeps the ledger the agent cannot rewrite.
The agent proposes; Maxx decides the intent; the sidecar enforces it.

## Why
An AI assistant acting on an everyday consequential action — paying a bill,
sending to the wrong person, sharing a folder, booking a nonrefundable trip,
posting publicly, deleting files — can move money or files, or send an
irreversible action out, before the operator notices it got it wrong,
and operators drown in decisions. What is at stake is probable cost,
inferred from the trace — money at risk, files lost, irreversible
exposure — not a reputation score, which is subjective and is not
measured anywhere in this codebase.
Maxx puts one gate in that moment: it holds, wraps, or releases the action,
and the human stays governor. Safety and attention come from the same gate.

The science question underneath it: can a demon-like sorter separate a logged
stream by a measured trace in a way that is actually informative — that is,
does the separation show up on a held-out independent variable, not just on
the score it sorted on? Sorting on X and then reporting that chambers differ
in X is circular and proves nothing. This codebase exists to catch that.

## What is the innovation
Not any single piece — per-action approval, budgets, reversibility grading,
and rehearsal each exist elsewhere. The innovation is their combination in
one gate for everyday actions, plus a backend that tests the sorting idea
in bits and counts with falsifiers built in:

- The gate sits outside the agent, between proposal and execution.
- It issues one-use permits only for releases. Wraps carry mock wrapped
  receipts, not permits. Holds and escalates carry none.
- It keeps a conserved ledger in the counting sense — counts reconcile,
  the agent cannot rewrite it.
- Cost is weighted by reversibility, with a named cost-bearer (operator)
  and recipient recorded separately.
- Rehearsal is a release criterion, whole sets are gated, and the operator
  gets one plain-reason card per action.
- The sorter moves information "like" physics: a particle is one logged row,
  its "speed" is the scalar score in its own units, the door is a threshold
  at a frozen tau, the chambers are admitted / held, the demon's memory is
  the log itself, and the conserved bill is counting:
  N_admitted + N_held = N_in. Values are in bits and counts only.

## What this is not
- Not a per-action gate alone (a language model could prompt one out).
- Not a pretty interface.
- Not Petermann K. K in the gate is a stub (K=1.0), advice-only, never wired
  to Glimmer telemetry, and no K threshold is claimed from any run here.
- Not joules, kelvin, or a physics budget. No energy claim is made anywhere.

## Run it
```
python3 run_all.py
python3 -m unittest discover -s tests
```

`run_all.py` runs, in one command:
1. The gate demo on a seeded 8-action synthetic queue (mock tools only).
2. The sorter at frozen tau 0.50 on the synthetic validation table and on
   Adult train/test templates (first 2,000 rows each).
3. A combined report in `results/combined-report.json`.

Golden gate numbers (locked, seeded run):
decisions release 1 / hold 2 / wrap 3 / escalate 2; tokens 800 / 400 / 400;
attention baseline 8 -> gated 7; money held $1,090; irreversible gated 0.

## Sidecar demo (video hero)
The demo video hero is the single-agent sidecar: Agent proposes ->
Harness -> Demon sidecar (separate process, owns permits + ledger) ->
mock tools. The reproducible equivalent in this repo is
`maxx-sidecar/examples/single_agent_demo.py` (same golden
numbers, 15 sidecar tests). The fleet example in that package is a repo
example only, not a video beat. The separate local prototype
`~/workspace/maxx-sidecar-demo/run_demo.py` is NOT in this repo, so
do not cite it as a repo path. Video status, stated plainly: the video
script for the single-sidecar form was approved by Amber as written on
2026-11-02, then edited the same day for the reputation wording
(432 words) and is NOT approved as written after that edit — it needs
her re-approval before recording. The video itself is not yet recorded,
and no freeze has been declared. Repo status: `Ambercontinuum/Maxx-Gate`,
main branch, core-only first push 2026-11-03, still private, not
flipped public, not submitted. The Maxx Lab, partition, council, and
energy work from the old `Ambercontinuum/Maxx` branch is intentionally
NOT in this repo. Codex verified `eb7e24c…` on the old branch; do not
claim Codex verified the later combined-budgets change (`43396a2b…`)
until a reply arrives — that change is covered here by the local
15 sidecar tests, not by a Codex reply.

Sorter evidence, templates only, tau 0.50 (label divergence, 10 bins):
synthetic label JS 0.359 bits vs shuffled ~0; Adult train label JS 0.122 bits,
test 0.116 bits, shuffled ~0, train/test agreement on held-out labels.
Score-bin divergence is constructional and is never presented as evidence.

## Layout
- `maxx/` — the gate: intake, temperature (stated arithmetic), gate/permit
  enforcer, ledger, mock tools, Spark proposal with seeded fallback, stability
  (advice-only stub).
- `maxx-sidecar/` — the reusable sidecar package: sidecar server process,
  client, harness, fleet, mock tools, and `examples/single_agent_demo.py`
  (same golden numbers) and `examples/fleet_demo.py` (repo example only).
  See `maxx-sidecar/README.md` and `maxx-sidecar/CONNECTION.md`.
- `data/queue.json` — the seeded 8-action synthetic queue.
- `sorter/` — the Maxwell's-demon isomorph sorter (bits/counts only).
- `datasets/` — synthetic validation table, Adult templates, and the full
  dataset inventory with hashes and licences. Full Adult/CIFAR files are
  referenced by hash, not duplicated here (CIFAR alone is 170 MB).
- `analysis/` — appendix analysis only, NOT gate input: K geometry notes
  and the Adult information isomorph. Adult coherence is NOT K's
  geometrical coherence — see `analysis/INFORMATION_ISOMORPH.md`.
- `tests/` — 51 tests (gate + sorter, including the empty-chamber sorter
  tests). Verified 2026-11-02: 51 pass locally.
- `results/` — generated by `run_all.py`; do not hand-edit.

## Limits, stated plainly
- The gate world is synthetic and mock-only. No real money, send, share,
  book, post, or delete happens in any run here.
- Sorter runs here are templates only. Full Adult (32,561 / 16,281 rows),
  AgentAbstain conversion, and a CIFAR classifier run are not in this
  codebase's generated results yet.
- The tau-sweep expectation ("gap shrinks as tau relaxes") does NOT hold
  monotonically in the sorter runs — the gap is U-shaped, smallest near
  tau 0.50. Do not claim that pattern.
- Adult scores cluster near tau 0.50, so at delta 0.10 about 63% of Adult
  train rows flip chamber, vs 32% synthetic. That is sensitivity of this
  score/tau pair, not robustness.
- K coherence, on the Glimmer analysis, is a static-slice result. The
  motion view — K lives in the motion of telemetry, and a slice decays —
  requires a decoding-time tracking run that is NOT in this codebase.
