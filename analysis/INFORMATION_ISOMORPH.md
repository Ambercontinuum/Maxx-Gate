# Information-space isomorph of the K geometry — Adult entropy grid

PDOT work was stopped at Amber's instruction (2026-11-01 ~17:54 ET) and is NOT
used here. This is a different, information-space candidate, tested with the
same geometry tests as the K map.

CORRECTION, Amber 2026-11-01 ~17:58 ET: Adult shows coherence, but NOT K's
geometrical coherence. That distinction is the point, and the file below must
not be read as claiming otherwise. K's geometrical coherence is specifically:
the (layer, head) landscape, prompt-map Spearman mean 0.479, token-split
Spearman 0.374, flat head profile, small layer bumps, no mirror symmetry,
isolated tail spikes. Adult shows a different landscape with a different
profile and different symmetry behaviour. What Adult shares with K is
coherence-as-a-property (a grid map that coheres across independent contexts
and fails shuffled/mirror checks in a structured way), NOT K's geometry itself.

## The mapping (structural, not identity)
- K cell (layer, head)  ->  Adult cell (education-num, hours-per-week bucket)
- K context (prompt)    ->  Adult context (train split / test split)
- K value (mean log10K) ->  Adult cell value: binary entropy H(income) in bits,
  and income rate p(>50K), per cell
- K prompt coherence    ->  Adult train-vs-test map coherence
- K mirror symmetry     ->  Adult reverse-education / reverse-hours symmetry
- K small-n / tracking failures -> Adult small-n cells

Census sensitivity note: Adult is census data about people. Used here ONLY
for sorting-arithmetic / geometry comparison, label as a statistical outcome,
never about individuals. Race/sex are NOT used.

## Results (full Adult files: train 32,561, test 16,281; grid 16 education x 9 hours = 142 train cells)
- Coherence, entropy map, train vs test:
  - all cells (n=138): Spearman 0.745, Pearson 0.742
  - cells with n>=30 in both (n=59): Spearman 0.955, Pearson 0.964
  - cells with n>=100 in both (n=27): Spearman 0.951, Pearson 0.983
  - rate map, all cells: Spearman 0.837; n>=30: 0.963
- Shuffled falsifier (entropy, 20 permutations): mean Spearman 0.037, SD 0.087,
  range -0.124 to 0.165. Observed 0.745–0.955 is far outside the shuffled null.
- Random-split falsifier: train split into two random halves, entropy map
  Spearman 0.734 (all cells) — consistent with train/test, not a split artefact.
- Symmetry, train entropy map:
  - reverse education: Spearman -0.299, Pearson -0.284
  - reverse hours: Spearman +0.339, Pearson +0.321
  - reverse both: Spearman -0.719, Pearson -0.759
  So: NOT symmetric, and asymmetrically structured — reversing both flips the
  map strongly, unlike K where every reversal/flip was ~0.
- Profile, train entropy by education: rises from 0.0 (edu 1) to ~0.87–0.90
  (edu 13–14), then ~0.83 (edu 15–16). Monotonic rise + plateau, unlike K's
  flat layer profile with small bumps.
- Profile, train entropy by hours: rises to a peak at bucket 6 (60–69 h,
  mean 0.739), then falls to ~0.61–0.62 — an inverted-U, not flat.
- Tail / spread: cell entropy median 0.598 bits, mean 0.508, p10 0.0, p90 0.979.
  Many pure (0-bit) cells at low education; high-entropy cells near 1 bit
  where income is near-even.
- Small-n: 60/142 train cells have n<30, 27 have n<10. All-cells coherence
  (0.745) is dragged down by those cells; n>=30 coherence (0.955) is the
  trustworthy figure. Same small-n lesson as K.

## Comparison table: K geometry vs Adult information geometry
- Grid: 52x32 (K) vs 17x9 (Adult, education values present 1–16)
- Cross-context coherence: K prompt-prompt Spearman mean 0.479 (range 0.43–0.55);
  Adult train-test entropy Spearman 0.745 all cells, 0.955 n>=30
- Shuffled null: K ~0.005; Adult ~0.037 — both far below observed
- Symmetry: K ~0 on every reversal/flip; Adult strongly negative on reverse-both
  (-0.72), mixed on single reversals (-0.30 / +0.34)
- Profile: K flat with small bumps; Adult monotonic rise (education) and
  inverted-U (hours)
- Tail: K isolated spikes to 245, Poisson-like high cells; Adult 0-bit pure
  cells and near-1-bit mixed cells

## What this is and is not
- IS: an information-space system (bits per cell, over a 2D grid) that passes
  the same geometry tests — cross-context coherence, asymmetry, falsifier,
  small-n discipline — with a measurable map, not a metaphor.
- IS NOT: K's geometrical coherence. Adult does not reproduce K's (layer, head)
  landscape, its profile, or its symmetry behaviour, and must not be cited
  as evidence for them. It is not a claim that Adult IS Glimmer K, or that
  K IS income, or that the magnitudes match. Coherence is stronger in Adult
  (0.95 at n>=30) than in K (0.48), and Adult asymmetry is directional where
  K asymmetry is flat. The shared thing is coherence-as-a-property and the
  grid-in-bits test form, not the geometry itself.

Files: `information_isomorph.py`, `information_isomorph.json` in this directory.
K geometry files: `geometry.py`, `geometry.json`, `NOTES.md`.
