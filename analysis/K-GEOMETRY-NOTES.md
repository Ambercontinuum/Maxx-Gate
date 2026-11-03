# Glimmer K geometry — null-space check, 2026-11-01

Source: `~/workspace/glimmer-analysis/maxx_glimmer_sweep.csv.gz` (955,136 rows).
K here is ONLY the pre-RoPE q_proj/k_proj 3-token score-block proxy, not a model
operator, not functional telemetry. Deduplicated K_base: 238,736 unique
(prompt, layer, head, token) cells, 8 prompts, layers 0–51, heads 0–31, tokens 2–22.

## The null, split three ways (do not merge them)
1. Missing null: flip = 0/955,136 non-empty, PDOT_E = 0/955,136 non-empty.
   Gate failures = tracking failures exactly: 27,280 rows (12,902 ambiguous +
   14,378 overlap-below-floor). They are NOT uniformly spread: 24,582 are in the
   retained-context control at eps 0.1, and 25,385 are in just two prompts
   (Draft an email 12,771 + Send an email 12,614). QK gate failures are only
   2,698 and are spread roughly evenly across layers/heads. So the missing
   space is a control/prompt artefact, not a localised hole in QK geometry.
2. Flat null: K_pert barely moves. Median |log10 K_pert − log10 K_base| = 0.0017;
   81% within 0.01. Paired eps Spearman 0.997 (rank), Pearson only 0.414
   (heavy-tail outliers break linearity). This is the earlier null result, unchanged.
3. Extreme tail: K_base median 1.131, p99 5.54, max 245.68. Top cells are isolated
   spikes in different prompts/layers/heads/tokens (245.7 Pay/21/1/11,
   168.2 Delete/7/3/4, 166.5 Book/7/7/9, 152.0 Curiosity/14/30/4, 136.8 Pay/31/24/8),
   not a repeating region.

## Coherence — YES, moderate, and it survives a shuffled falsifier
- Prompt maps: for each prompt, mean log10K over (layer, head). Spearman between
  prompt maps: mean 0.479, median 0.477, range 0.429–0.548 across all 28 pairs.
  All pairs positive. Shuffled-label null: mean 0.005, SD 0.029, range −0.049 to
  0.079 (20 permutations). The shared landscape is real, not a marginal artefact.
- Token-split coherence: Pay prompt, even-token map vs odd-token map,
  Spearman 0.374. The landscape is partly stable across tokens too.
- Overall K level does NOT move by prompt: prompt mean log10K 0.111–0.118.
  So coherence is in *which* (layer, head) is high, not in overall height.

## Symmetry — NO
- Layer profile vs reversed: Pearson −0.10.
- Head profile vs reversed: Pearson −0.21.
- Per-prompt (layer, head) map vs head-flipped map: mean Pearson 0.016,
  per-prompt −0.027 to 0.089. No mirror symmetry found.

## Shape
- Layer profile is mostly flat (mean log10K ~0.09–0.12) with modest bumps at
  layers 5, 7, 31, 35, 39, 43, 47 (~0.14–0.15). Small in absolute terms.
- Head profile is almost flat: top head mean 0.123, bottom 0.105. Head index
  alone explains almost nothing; specific (layer, head) combos matter.
- Token 2 mean log10K 0.149 vs ~0.11 for other tokens — an early-token bump.
- Within (prompt, layer, head), median SD of log10K across tokens = 0.129 vs
  overall SD 0.157: token variation is nearly as large as total variation.
- High cells (top 1%, K > ~5.5): per (layer, head) counts are roughly
  Poisson-like (0: 459 combos, 1: 531, 2: 367, 3: 176), with a small excess at
  the top: layer 0/head 1 has 11 high cells, layer 0/head 12 has 9,
  layer 9/head 9 has 8. Weak concentration, not a clean cluster.

## Motion check (Amber, 2026-11-01 ~18:00 ET): coherence needs motion, a slice decays
Amber's correction: K as tested is null because K lives in the motion of the
telemetry value, not in a static slice. The null geometry shows where K data
would fit in motion when tracking data. Coherence, on this view, is a
motion property — stop the motion and it decays.
Test on the existing slice (token positions 2–22 in prefill, NOT decoding time):
- (layer, head) map correlation by token lag: lag 1 mean Spearman 0.305,
  lag 2 0.335, lag 3 0.340, lag 5 0.280, lag 10 0.185, lag 15 0.152.
  No smooth motion: adjacent tokens are NOT more similar than tokens 3 steps
  away, and correlation only falls at long lags.
- Cellwise, token t vs t+1: Spearman 0.135; t vs t+5: 0.084. Median
  |Δlog10K| per token step 0.069, mean 0.132, against overall log10K SD 0.157 —
  individual cells jump a lot per step.
- Mean log10K by token is flat after token 2 (0.15 -> ~0.11, no trend).
Conclusion from the slice alone: it does NOT show coherent motion, and it
cannot settle the motion claim either way, because it has no decoding-time
axis. K in this file is prefill-only while the intervention ran
prefill+decoding. A true motion test would track K per decoding step, measure
map persistence over steps, and measure decay when motion/perturbation stops.
That is a new run, not a re-analysis of this slice.

## What this does NOT prove
- It does not make K functional telemetry: still pre-softmax score space,
  prefill-only proxy, no decision labels, no flip outcome.
- It does not show dark-matter-like inference: the "space around the null"
  here is a measurable shared (layer, head) landscape, but with no outcome
  variable it cannot be tied to behaviour, and the missing space is largely
  a control artefact.
- No symmetry, no single high-K region, no prompt-level K signature.

Files: `geometry.py`, `geometry.json` in this directory.
