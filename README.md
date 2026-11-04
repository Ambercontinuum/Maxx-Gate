# Maxx — a Maxwell's-demon gate that moves information like physics

**Demo video (3 minutes): https://youtu.be/Xuv3uOgpjss**

**A submission to the Meta Global AI Developer Hackathon**, built
during the event (October 26 – November 4, 2026). Everything claimed
below was built in that window unless a section labels it background.

Maxx is a deterministic gate between an AI agent and tool execution.

A proposed action is declared in a fixed schema:

- **Type** — what kind of action it is.
- **Trace** — what it touches.
- **Amount** — how much money moves.
- **Reversibility** — whether it can be undone.

The gate scores the declared action with stated arithmetic:

`floor 15 + trace weights + 15 if irreversible`, capped at `98`.

It then decides:

- **Release** — a one-use permit is issued.
- **Wrap** — a corrected version is substituted.
- **Hold** — nothing executes.
- **Escalate** — nothing executes; the human decides.

Enforcement is a separate sidecar process. It owns the permits and
the ledger, and the ledger counts must reconcile.

The gate itself calls no model. In the documented live run, Muse
Spark 1.3 proposed the actions and Muse Wonder 1.0 reviewed them
through the Meta Model API; the gate decided.

Seeded run — 8 actions:

- Decisions: release 1 / wrap 3 / hold 2 / escalate 2.
- Irreversible executions: 6 → 0 against the ungated baseline.
- Held for human decision: $1,090.
- Operator attention: 8 → 7.
- Tokens: 800 = 400 retained + 400 discarded.

Limits and checks:

- All tools behind the gate are mocks; no real action is taken in
  any run.
- A sorter backend tests whether trace-based sorting is informative
  on a held-out variable, with falsifiers stated in advance.
- The Petermann-K analysis on Muse Glimmer 30B activations did not
  beat conventional baselines.
- The gate's stability input is a constant stub.
- Test suites: 61 + 25 passing; the demo commands below print their
  own golden checks.

---

## Maxx, in one line
Maxx is the intent, the sidecar is the enforcement. Maxx states what
should happen to each proposed action — release, wrap, hold, or
escalate, with one plain reason — and the sidecar, a separate process
outside the agent, enforces that decision: it issues a one-use permit
only for a release and keeps the ledger the agent cannot rewrite.
The agent proposes; Maxx decides the intent; the sidecar enforces it.

## What "intent" means
"Intent" is not what the agent proposed. A proposal is a claim about
what to do, written by the system that wants to do it. Intent is what
*should* happen — determined on the operator's side of the gate, in
the operator's terms. Maxx determines it in four moves:

1. **The proposal is stripped to its intent-bearing facts**: what kind
   of action it is, what it touches (money, a person, a contract, a
   schedule, a device), how much money moves, and whether it can be
   undone. The agent's prose — its framing, its confidence, its
   reasons — is never scored.
2. **Those facts are scored by stated arithmetic** the operator can
   read, dispute, and change. The rules are the operator's priorities
   written as policy, not a model's judgment.
3. **The gate states the intent as one decision with one plain
   reason.** Release it as proposed. Wrap it: execute the safer
   version that matches what the operator actually meant — the email
   goes out as a corrected draft with the wrong attachment omitted,
   because the intent was the message, not the attachment. Hold it.
   Or escalate it to the human, because some actions are the human's
   to intend, not the gate's.
4. **The sidecar makes the stated intent binding.** No permit, no
   execution; a wrap executes the wrapped version, never the original
   (against mock tools in this prototype); the ledger records what
   was decided and what ran, in counts that must reconcile.

Proposal, intent, and enforcement in three different hands — the
agent's, Maxx's, and the sidecar's. That separation is the whole
architecture.

## Models and Meta products used
- **Muse Spark 1.3** (`muse-spark-1.3`), via the **Meta Model API** —
  proposed the actions in the documented live run
  (`analysis/live-meta-run-2026-11-03.md`).
- **Muse Wonder 1.0** (`muse-wonder-1.0`), via the **Meta Model API** —
  reviewed the live run's proposals and the saved sorter results.
  The review never decides; the gate decides.
- **Muse Glimmer 30B** (open-weight) — the spectral sweep behind the
  appendix analysis (955,136 rows; `analysis/`, `datasets/INVENTORY.md`).
  Its Petermann-K checks did not beat the conventional baselines, and
  nothing in the gate consumes its output: the gate's stability input
  is a labelled stub.
- **Built with Meta Muse** — the code in this repo was written by Maxx,
  the author's Muse agent, under the author's direction and sign-off.
  AmberContinuum is human-led by design: research direction,
  experimental design, interpretation, and claims stay with the author.
  One more tool, disclosed in full in `PROVENANCE.md`: Codex, used in
  the author's IDE for verification runs and IDE-side execution under
  her orchestration.
- **The gate itself calls no model.** It is deterministic arithmetic
  and runs offline on the seeded queue. Models propose and review;
  only the gate decides.
- **Not used:** Muse Image, Voice Transcribe, and SAM 3.1 are named in
  the hackathon guide and were never run in this project.

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

## How it works — one action through the gate
1. The agent proposes an action. Intake reads its trace: what it touches
   (money, a contract, a person, a schedule, a device) and whether it is
   irreversible.
2. The gate scores the action with stated arithmetic — a floor of 15,
   plus the trace weights, plus 15 if irreversible, capped at 98. That
   score is the action's temperature. Nothing about it is learned or
   hidden; the same inputs always give the same score.
3. The gate decides by its ladder: release, wrap, hold, or escalate,
   with one plain reason. In the seeded run, paying the $240 bill scores
   90 and escalates to the human; drafting a reply scores 15 and releases.
4. The sidecar enforces the decision. A release gets a one-use permit,
   which the harness verifies before anything runs. A wrap runs a
   corrected, safer version of the action instead (a draft with the wrong
   attachment omitted, a limited expiring link, an archive instead of a
   delete) and carries a mock receipt, not a permit. A hold or an
   escalate executes nothing.
5. Every decision is written to the ledger with its cost-bearer, and the
   ledger's counts must reconcile — tokens in = kept + discarded,
   decisions = entries — or the run fails its own checks.

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
- Whole sets are gated, and the operator gets one plain-reason card
  per action. (Earlier drafts listed rehearsal as a release criterion;
  no rehearsal step exists in this codebase or in the demo, so that
  claim is removed, not shown.)
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

## What the demo video shows — and does not show

Shown, and checkable against the run below: the seeded 8-action
synthetic queue sorted by the gate, presented as a two-room interface
visualisation of the verified run — one decision per action with its
stated-arithmetic temperature and one plain reason, mock execution
only for the 3 wraps and the 1 release, no execution for the 2 holds and
2 escalates, and the closing ledger (tokens 800 / 400 / 400, attention
8 -> 7, $1,090 held, irreversible baseline 6 -> gated 0, "Golden check
PASSED."). The one-use permit for the release is enforced inside the
harness (a release with no verified permit executes nothing, covered by
the sidecar tests); the demo output does not print a permit ID, so the
video states the permit in narration/captions and shows its effect —
the release runs, the others do not.
Also shown, as short proof beats recorded from real runs: the
information sorter computing on held-out templates (admitted and held
counts reconcile exactly; label separation about a tenth of a bit
against a near-zero shuffled control; the flip rate under nudges is
reported as sensitivity, not strength), the three-sidecar fleet example
reconciling to the same totals, and the test suite passing (51 gate and
sorter tests, 15 sidecar tests). Not shown in the video: any full Adult
dataset run or CIFAR run, any K or Glimmer telemetry (stability in the
demo is a stub, advice-only, and no K value is printed by the demo run),
Spark/Wonder live proposals, and any real tool, payment, send, share,
booking, post, or delete. Those are repo-only or appendix material
below, not demo claims. A labelled live Meta run does
exist as a document in `analysis/live-meta-run-2026-11-03.md`; it is not
the video run, and its decisions and token split differ from the seeded
golden numbers above — do not mix the two.

## Get started in under a minute
Needs Python 3 and two packages the sorter uses (numpy, pandas);
everything else is the standard library. No accounts, no API keys.

```
git clone https://github.com/Ambercontinuum/Maxx-Gate.git
cd Maxx-Gate
pip install numpy pandas
python3 run_all.py
```

Then the pieces on their own:

```
python3 maxx-sidecar/examples/single_agent_demo.py
python3 -m unittest discover -s tests
cd maxx-sidecar && python3 -m unittest discover -s tests
```

The sidecar demo is the video hero's run — it prints the golden numbers
below and "Golden check PASSED." The two test commands run 61 gate and
sorter tests and 25 sidecar tests. And `demo/maxx-gate-hero.html` is the
hero page from the video: open it in any browser, no server needed.

`run_all.py` runs, in one command:
1. The gate demo on a seeded 8-action synthetic queue (mock tools only).
2. The sorter at frozen tau 0.50 on the synthetic validation table and on
   Adult train/test templates (first 2,000 rows each).
3. A combined report in `results/combined-report.json`.

Golden gate numbers (locked, seeded run):
decisions release 1 / hold 2 / wrap 3 / escalate 2; tokens 800 / 400 / 400;
attention baseline 8 -> gated 7; money held $1,090; irreversible gated 0.

## Sidecar demo (video hero)

The demo video's hero is the single-agent sidecar — the enforcement
half of Maxx, running as its own process:

- **See it:** the [demo video](https://youtu.be/Xuv3uOgpjss)
  (3 minutes) and the [interactive hero page](demo/maxx-gate-hero.html)
  — the page animates the same run and carries a live in-browser port
  of the gate; with GitHub Pages enabled it is served at
  https://ambercontinuum.github.io/Maxx-Gate/.
- **The loop:** Agent proposes → Harness → Demon sidecar (separate
  process; owns the permits and the ledger) → mock tools. Nothing
  executes without the sidecar's permit.
- **Run it yourself:** `python3 maxx-sidecar/examples/single_agent_demo.py`
  reproduces the run in this repo with the same golden numbers above;
  the sidecar package carries 25 tests.
- **What the video shows:** a rendered, paced presentation of that
  verified run, made for editing — not a raw terminal recording. Run
  the command to see the raw output, which prints in plain text in
  seconds. What the video shows and does not show is itemised in its
  own section above.
- **Scope:** the demo's subject is the single sidecar. The fleet
  example in the same package appears in the video only as a short
  proof beat; in scope it is a repo example.

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
  (same golden numbers) and `examples/fleet_demo.py` (repo example; its
  run is the video's short fleet proof beat).
  See `maxx-sidecar/README.md` and `maxx-sidecar/CONNECTION.md`.
- `data/queue.json` — the seeded 8-action synthetic queue.
- `demo/` — the two-room hero page from the video (`maxx-gate-hero.html`):
  a self-contained page that animates the seeded run and carries the full
  run as plain text underneath it, with pause/replay controls,
  fit-to-screen scaling, and a reduced-motion path that shows the closed
  ledger immediately. Under the text sits a live port of the gate itself
  — the sidecar's arithmetic and decision ladder in JavaScript, verified
  output-identical to the Python sidecar on the seeded queue (temperatures,
  decisions, reasons, wrapped versions, ledger totals). Run the queue, or
  build your own action and watch it decide. The repo root `index.html`
  redirects here, so a GitHub Pages deployment lands visitors on it.
- `sorter/` — the Maxwell's-demon isomorph sorter (bits/counts only).
- `datasets/` — synthetic validation table, Adult templates, and the full
  dataset inventory with hashes and licences. Full Adult/CIFAR files are
  referenced by hash, not duplicated here (CIFAR alone is 170 MB).
- `analysis/` — appendix analysis only, NOT gate input: K geometry notes
  and the Adult information isomorph. Adult coherence is NOT K's
  geometrical coherence — see `analysis/INFORMATION_ISOMORPH.md`.
- `tests/` — 61 tests (gate + sorter, including the empty-chamber sorter
  tests and the 2026-11-04 intake-validation regressions).
  Verified 2026-11-04: 61 pass locally.
- `results/` — generated by `run_all.py`; do not hand-edit.

## The open problems — what this gate exists to work on
None of what follows is solved — here, or anywhere in the published
record we know of. These are the live problems of AI governance, and
they are the research program, not an apology. Maxx's claim is narrower
and stronger than a solution: before a problem can be solved it has to
be measurable, and a checkpoint that scores every proposed action with
stated arithmetic, enforces with one-use permits, and reconciles every
count in a ledger the agent cannot rewrite is the instrument that makes
these problems measurable — one logged action at a time, at the moment
of action, where they actually happen. The gate does not solve them
yet. The gate is how they get worked on.

**Where the threat actually lives.** Not at the checkpoint — in three
places around it:
- **Upstream, in perception.** The gate scores the proposer's *declared*
  trace; it never inspects the proposed text. A well-typed lie — a
  payment declared as a reversible draft — passes intake and scores low.
  The 2026-11-04 fix closes *malformed* declarations (a string `"false"`
  is no longer read as true; a negative amount can no longer inflate a
  budget). It does not, and cannot, close *dishonest* ones. Perception
  is bracketed, not solved.
- **At the band edges, in calibration.** The weights and bands are
  stated scaffold values, not fitted thresholds, and a predictable
  ladder invites a proposer to phrase actions just under a band. Only
  comparable ledgers at scale — and the held-out AgentAbstain test —
  can show whether that bunching is happening.
- **Downstream, in production trust.** Permits are in-memory bearer
  tokens bound to an action id, not to a payload hash; they carry no
  expiry and no signature. The sidecar channel is unauthenticated
  beyond process isolation. The ledger asserts its own consistency
  but has no hash chain, and it reaches disk only on shutdown. None
  of that matters in a mocked demo; all of it matters before a real
  tool is wired in.
- **Live tools.** Every execution path ends at a mock tool. Wiring the
  gate to a real tool, account, or payment rail is future work, left out
  deliberately: the gate had to be provable before it could be trusted
  with anything real.
- **The AgentAbstain held-out test.** The dataset is in the inventory
  with its licence verified, but the conversion to the frozen table and
  the pre-registered held-out test have not been run.
- **Full-dataset sorter runs.** Adult runs here are templates only (the
  first 2,000 rows); the full 32,561 / 16,281-row runs are not done.
  CIFAR-10 is verified by hash only — no classifier, no run.
- **K in motion.** The gate's stability input is an advice-only stub.
  Tracking Petermann K across decoding steps — the run the Glimmer slice
  analysis points to — is not built.
- **Live proposals as a repo command.** One live Meta-model run is
  documented in `analysis/live-meta-run-2026-11-03.md`; it is a record of
  a run, not a reproducible command in this repo.
- **Production hardening.** No persistence, accounts, permissions UI, or
  deployment packaging. This is a research prototype with a conserved
  ledger, not a shipped product.

The shape also extends past one agent — the same stated arithmetic can
run as a fleet, and the fleet example in `maxx-sidecar/` is the seed of
that — because a fleet's comparable ledgers are where these problems
turn statistical. That direction is noted, not developed: today's
subject is the one gate, doing its one job, on the record.

Maxx is one local use of a broader constraint architecture — a layer
outside the agent that governs execution through permits, invariants,
and a ledger the agent cannot rewrite. The research direction is the
architecture itself, at larger scales; this gate is what it looks like
at the scale of one person's everyday actions.

**Verification, on the record.** An independent verification pass over
this repo on 2026-11-04 (at head `99424df5`) reproduced two intake
defects — the string-boolean misread and the negative-amount budget
inflation described above — before approving anything else: 66 tests,
the golden demo, the full pipeline, and 1,544 JavaScript/Python parity
cases passed, and credential scans of the files and the git history
were clean. Both defects are fixed, with regression tests in both
packages, in commit `621a2778`; the suites now run 61 + 25 tests. That
loop — propose, verify, find the hole, fix it, pin it with a test — is
the working method this project claims, and this paragraph is part of
its evidence.

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
