# Intended connection: sorter measurements ↔ sidecar regulation

This document exists before any further features are added, as Codex
asked: state the connection, state how it can be tested, and state
what it does NOT prove. The sorter and the sidecar remain separate
modules. Neither is validated by the other.

## The connection, in one sentence
The sorter is the experimental foundation: a demon-like threshold rule
can separate a frozen logged stream by a measured score, with
non-circular divergence on a held-out independent label. The sidecar
is the deployment of that same rule FORM to live agent actions: a
threshold door, admitted vs held chambers, and a conserved counting
ledger — enforced with permits and budgets, not merely reported.

## Correspondence table — testable, and where it differs

| Sorter (experiment) | Sidecar (regulation) | Difference, stated plainly |
|---|---|---|
| Particle = one logged row | Particle = one proposed action | Same form, different object |
| Speed/score = dataset score, own units | Score = temperature cost, stated arithmetic (floor 15 + trace weights + 15 if irreversible, cap 98) | Scales differ; no conversion is claimed |
| Door = frozen tau 0.50, admitted iff score >= tau | Door = gate bands escalate 85 / hold 70 / wrap 40, plus reversibility and stability rules | Sidecar door is a banded rule, not a single tau; bands are scaffold values, not fitted thresholds |
| Chambers = admitted / held | Chambers = executed (release + wrap) / not executed (hold + escalate) | Sidecar wrap is a transformed execution, not a pure admission |
| Demon memory = the log itself | Demon memory = sidecar-owned ledger | Same role, separate implementation |
| Conserved bill = counting identity N_admitted + N_held = N_in | Conserved bill = counting identities tokens in = retained + discarded, decisions sum = entries, held/escalated never executed | Counting only. No joules, no energy, no physics budget is claimed |
| Non-circular evidence = label JS / MI on a label independent of score and gate, on a held-out split, vs shuffled control ~0 | Non-circular evidence for the sidecar = NOT YET MEASURED | This is the gap. See below |

## Testable claims — and their falsifiers
1. **Door form is monotonic.** As sidecar temperature rises with other
   factors fixed, the decision never becomes more permissive:
   release → wrap → hold → escalate. Test:
   `tests/test_sidecar.py::test_gate_is_threshold_door_monotonic`.
   Falsifier: a higher-temperature action releasing while a
   lower-temperature twin wraps or holds, all else equal.
2. **Counting identities hold.** Sorter: admitted + held = N_in.
   Sidecar: tokens in = retained + discarded; decisions = entries.
   Falsifier: any run where an identity assertion fails — the run
   must fail loudly, not demo around it.
3. **Sorter separation is non-circular.** Synthetic label JS 0.359 bits,
   Adult templates 0.122 train / 0.116 held-out test, shuffled controls
   near zero. Score JS 1.000 bit is constructional and is NOT evidence.
   Tau-sweep gap is U-shaped (smallest near 0.50), not monotonic —
   kept as a falsifier, not hidden. Adult flips ~63% at delta 0.10 vs
   32% synthetic — sensitivity, not robustness.
4. **Sidecar enforcement is real.** Permits are one-use and isolated
   per sidecar; custom executors are never called for held/escalated
   or failed-permit releases; budgets never go negative (reserve at
   gate, atomic recheck at verify); zero attention budget blocks wraps
   and counts no attention. Tests in `tests/test_sidecar.py`.

## What the connection does NOT prove
- The sorter does NOT prove the sidecar's temperature score predicts
  real-world harm, cost, or success. The sidecar's independent outcome
  — did held actions actually cause harm, did released actions succeed
  without incident — has not been measured on a held-out set. Until
  that measurement exists, sidecar regulation is an enforced mechanism
  with tested code, not a validated predictor. Any submission text
  claiming otherwise would be circular: it would use the score that
  sorted the actions as evidence the sorting was right.
- The sidecar does NOT validate the sorter, and the sorter does NOT
  validate Petermann K. They share a door form, not a validation chain.
- No claim is made that this is Maxwell's demon in a physical system,
  that Landauer's limit is measured, or that a physical bill is
  conserved. The correspondence is information-theoretic, in bits and
  counts, in software.

## Distinguished from established results
Established, not claimed as new here: Maxwell's demon (thought
experiment), Landauer's principle (1 bit ↔ k_B T ln 2 for a system
coupled to a heat bath), Shannon entropy / KL / JS / mutual
information, and Petermann's eigenvector-conditioning factor K.
New here, and only here: (a) the measured sorter numbers above, with
their falsifiers, in the frozen tables listed in the integrated
submission's inventory; (b) the sidecar code that enforces a threshold
door with permits, budgets, and a sidecar-owned ledger, with the tests
above. Everything else is background, labelled as such.

## Glimmer findings and limitations — preserved, not softened
- Full Glimmer QK sweep, 955,136 rows: K median 1.131, p99 ~5.54, max
  245.68; graded-epsilon prediction FAILS; K predicts shift FAILS;
  K predicts divergence FAILS; baselines (spectral radius / operator
  norm ~0.43 / 0.39) beat K on shift.
- Flip and PDOT_E are MISSING (0 non-empty in all rows), not zero.
- K null-space: no symmetry, no single high-K region; shared partly
  prompt-invariant landscape, prompt-to-prompt Spearman mean 0.48 vs
  shuffled 0.005; even/odd-token 0.37 in Pay prompt.
- Measurement space: pre-RoPE q_proj/k_proj 3-token score block,
  unmasked proxy, pre-softmax, prefill-only — NOT functional telemetry,
  NOT a model operator.
- No outcome variable in that data, so K cannot be tied to behaviour.
- K in motion (Amber, 2026-11-01): K as tested is null because K is
  found in the motion of the telemetry value; a static slice cannot
  test motion, and a decoding-step tracking run has NOT been run.
  Adult entropy coherence (0.955 at n≥30) is coherence-as-a-property,
  NOT K's geometrical coherence, and must not be cited as evidence
  for K's geometry.
- Consequence for the sidecar: K is STUB advice only, never required
  for a gate decision, never wired as load-bearing telemetry. The
  gate works if K is off, flat, or inconclusive — and it does, in
  the seeded demo, where stability is stub.
