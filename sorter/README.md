# Maxwell's-demon isomorph sorter — backend

Local only. Nothing in this directory is pushed to any git repo,
flipped public, or submitted. Built 2026-11-01, in-window, from
the spec in the task: a frozen logged table in, chamber counts /
means / entropies / divergences / flip rates out.

## What this is, in one paragraph

A "particle" is one logged row. Its "speed" is the scalar score
already in the table, in that score's own units. The "door" is a
threshold rule at a stated, frozen tau. The "chambers" are the
admitted / held partitions of a frozen logged stream. The demon's
memory is the log itself. There are no joules, no kelvin, no
token-energy conversion, no Petermann K, and no physics budget
anywhere in this module.

## Inputs

A frozen logged table, CSV, with columns:

    id, score, label, score_source, chamber, split

`chamber` is EMPTY at input and is filled only by the gate at the
stated tau. `label` must be independent of the score and the gate
rule — see "Non-circularity" below. `split` is stated per row and
frozen before gating; train and test are never pooled into one claim.

Runs in this directory:

| Run | Input | tau | n | split |
| --- | ----- | --- | - | ----- |
| synthetic | `../maxx-isomorph-datasets/synthetic-validation-2000.csv` | 0.50 | 2000 | synthetic |
| adult-train | `../maxx-isomorph-datasets/adult-template-2000.csv` | 0.50 | 2000 | train |
| adult-test | `../maxx-isomorph-datasets/adult-test-template-2000.csv` | 0.50 | 2000 | test |

Tau 0.50 is the same for all three runs: a round, pre-stated value,
not tuned to maximise label separation (label separation in fact
keeps rising past 0.50 in the Adult sweep — see results).

## Gate

    chamber = admitted if score >= tau else held

Identity check, enforced loudly: N_admitted + N_held must equal
N_in, or the run raises. All three runs pass it.

## Adult score — transparent, NOT a fitted model

Computed in-backend with numpy only (scikit-learn is not installed
and is not imported), from age / education-num / hours-per-week:

    score = clip(0.40 * education_num/16
                 + 0.35 * min(age, 80)/80
                 + 0.25 * min(hours_per_week, 80)/80, 0, 1)

Score source recorded in every output: `adult-linear-2026-11-01`.
This is a stated linear combination, not a trained classifier and
not a claimed model result. Adult income labels are mapped
<=50K -> 0, >50K -> 1 after stripping whitespace and any trailing
period (the test file carries a trailing period; the train file
does not — stripping is what makes the held-out comparison valid).

Adult score range in these templates is about 0.22–0.88, so the
outer [0, 1] bins are empty. That is why the Adult runs carry a
sparse-bin warning (see below); it is a binning-coverage note, not
a chamber failure.

## Outputs and units

Per run, in `results/`:

- `<run>.json` — full output
- `<run>.csv` — long-form metric rows, each carrying tau, n_in,
  split, score_source, metric, value, binning, and note

Metrics, all in bits or counts (never joules/kelvin):

1. Counts per chamber + identity check.
2. Chamber mean scores (score units).
3. Chamber Shannon entropy in bits, over the score-bin alphabet.
4. KL and JS divergence between chambers in bits.
5. Mutual information I(score bin; chamber) in bits, and separately
   I(label; chamber) in bits.
6. Flip rate per stated delta (0.01, 0.03, 0.05, 0.10):
   flip_plus (held -> admitted under +delta), flip_minus
   (admitted -> held under -delta), and flip_either (|score - tau|
   < delta, i.e. would flip under a delta-sized perturbation
   toward tau).

Binning: equal-width bins over [0, 1] at 10 bins (primary), 5 bins,
and 20 bins. Max entropy is log2(n_bins) bits (3.322 for 10 bins),
before the empty-outer-bin caveat for Adult.

## Non-circularity — read this before quoting any number

Sorting on score guarantees chambers differ in score. Score-bin
KL / JS / MI are therefore CONSTRUCTIONAL and are never evidence:

- Score JS at 10 bins is 1.000 bit in all three runs at tau 0.50,
  because the admitted and held score-bin supports are disjoint
  (bins align with tau). Score KL is reported as null with
  `disjoint_support=true` — it is infinite, not a large finite
  number, and no smoothing was invented to hide that.
- At 5 bins, score JS drops (synthetic 0.683, Adult train 0.338,
  Adult test 0.360 bits) because the 0.4–0.6 bin straddles tau.
  That spread across binnings is expected and is reported, not
  hidden.

Evidence is divergence on the INDEPENDENT label only:
label JS / KL / MI between chambers, and the label-1 rate gap.
That is the metric the shuffled control is judged on.

## Controls / falsifiers

- **Tau sweep** (0.1–0.9, 10 bins, in every JSON): chamber mean gap
  is U-shaped, smallest near the balanced tau and larger at the
  extremes — it does NOT shrink monotonically as tau is lowered.
  The literal reading "gap shrinks as tau relaxes" therefore does
  not hold as a monotonic claim; what holds is that the gap is
  smallest near the centre and the extremes become small-n
  unstable (see below). This is reported as a flagged nuance, not
  smoothed over.
- **Shuffled-gate control** (seeds 0, 1, 2, same tau): scores
  randomly permuted. Label JS must be ~0. It is: synthetic
  0.0002–0.0026, Adult train 0.00001–0.0005, Adult test
  0.0006–0.0030 bits. Score JS under shuffling is NOT expected to
  be ~0 (the shuffled gate still thresholds on the shuffled score)
  and is not judged on.
- **Binning sensitivity**: label JS is binning-invariant by
  construction (it uses only the label alphabet), so its spread
  across 5/10/20 bins is 0.000 in all runs. Score JS spread is
  0.317 (synthetic), 0.662 (Adult train), 0.640 (Adult test) bits —
  again the straddling-bin effect, reported in the JSON.
- **Small-n warnings**: any chamber with fewer than 100 rows, and
  any score bin with fewer than 5 rows in total, is flagged.
  Adult main runs: chambers are 1379/621 (train) and 1341/659
  (test), so no small-chamber warning at tau 0.50; the sparse-bin
  warning fires because outer [0, 1] bins are empty for Adult
  scores (range ~0.22–0.88). Tau-sweep extremes (e.g. Adult tau
  0.1, 0.2, 0.9) have an empty chamber: means, gaps, and JS are
  reported as null there, not as numbers.
- **Bug found and fixed during this build**: the first version
  returned JS = 0.5 bits for an empty chamber. That was an artefact
  of treating an empty distribution as a zero vector. Empty-chamber
  divergences and entropies are now null. The Adult sweep files
  were regenerated after the fix.

## How to re-run

    python3 sorter.py --input <frozen csv> --tau 0.5 --split <split> \
        --json results/<run>.json --csv results/<run>.csv

    python3 sorter.py --input <adult template csv> --tau 0.5 \
        --split train --adult \
        --json results/adult-train-run.json --csv results/adult-train-run.csv

Dependencies: stdlib + pandas / numpy / scipy only. No sklearn,
no network, no repo access. AgentAbstain and CIFAR-10 were NOT
used in this task (AgentAbstain out of scope; CIFAR still
downloading and unverified at build time).

## Headline measured numbers (see JSON/CSV for full tables)

Synthetic (SYNTHETIC ONLY, never real-world data), tau 0.50:
admitted 986 / held 1014; means 0.6730 / 0.3203; label-1 rates
0.8357 / 0.1617 (gap 0.6740); label JS 0.3585, label MI 0.3585,
label KL 1.5938 bits; shuffled label JS <= 0.0026 bits.

Adult train, tau 0.50: admitted 1379 / held 621; means 0.6010 /
0.4350; >50K rates 0.3445 / 0.0386 (gap 0.3058); label JS 0.1222,
label MI 0.0966, label KL 0.7249 bits; shuffled label JS <= 0.0005.

Adult test (held-out, same tau, same formula), tau 0.50:
admitted 1341 / held 659; means 0.6011 / 0.4337; >50K rates
0.3386 / 0.0410 (gap 0.2976); label JS 0.1159, label MI 0.0954,
label KL 0.6770 bits; shuffled label JS <= 0.0030.

Train and test agree closely (label JS 0.122 vs 0.116 bits), which
is the held-out check passing at the level this transparent score
allows. It is a sorting-arithmetic result on a stated linear
score, not a model-accuracy claim, and Adult is census data about
people — use only for the sorting test, never for claims about
individuals, and race/sex were not used as score inputs.
