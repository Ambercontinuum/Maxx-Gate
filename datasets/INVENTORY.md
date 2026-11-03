# Isomorph datasets — inventory, gathered 2026-11-01

Purpose: datasets for the backend Maxwell's-demon sorting code — one frozen
logged table in, counts / mean scores / entropies (bits) / KL-JS divergence
(bits) / mutual information (bits) / flip rate per stated δ / tau sweep /
shuffled-gate control out. No joules, no kelvin, no token-energy conversion.
A dataset is usable here only if it has: (a) items, (b) a scalar score the
gate can threshold on (or features to compute one from, in the backend step),
(c) an independent label/outcome for the held-out, non-circular check,
(d) n large enough that entropy over a stated alphabet is not just small-n bias.

## VERIFIED, downloaded here

### 1. UCI Adult (Census Income) — VERIFIED
- File: `adult.data` (3,974,305 bytes, SHA-256 `5b00264637dbfec36bdeaab5676b0b309ff9eb788d63554ca0a249491c86603d`)
- Rows verified: 32,561, 15 columns. Label `income`: <=50K 24,720 / >50K 7,841.
- Missing: workclass 1,836 / occupation 1,843 / native-country 583 (marked ` ?` in source).
- Source: UCI Machine Learning Repository, Adult dataset, DOI 10.24432/C5XW20,
  creators Becker / Kohavi 1996, task: predict income > $50K/yr from census data.
- License: UCI page lists **CC BY 4.0** for this dataset (search result, UCI
  dataset page). A secondary catalog lists CC0 — do NOT quote CC0 until the
  UCI page itself is re-read; for this inventory, record CC BY 4.0 as the
  UCI-page claim, with attribution required.
- Use for isomorphs: tabular, binary label = independent outcome.
  Score to be computed in backend (e.g. a simple classifier's confidence on
  age / education-num / hours-per-week and other features), then gate at τ,
  chambers admitted vs held, divergence checked against the income label
  on held-out rows. Natural train/test split exists in the full UCI release
  (adult.test not yet downloaded — add it before any held-out claim).
- Held-out split, verified 2026-11-01: `adult.test` (2,003,153 bytes,
  SHA-256 `a2a9044bc167a35b2361efbabec64e89d69ce82d9790d2980119aac5fd7e9c05`),
  16,281 rows after skipping the first header-like line, label
  <=50K. 12,435 / >50K. 3,846. Note for backend: test labels carry a
  trailing period (`<=50K.`, `>50K.`) — strip it before comparing to
  train labels, or the held-out check will silently mismatch.
- Templates: `adult-template-2000.csv` (train, first 2,000 rows) and
  `adult-test-template-2000.csv` (test, first 2,000 rows, labels stripped
  of trailing periods) — id + 3 numeric features + income label, score
  and chamber left EMPTY for the backend gate to fill. These templates
  are gathering artefacts, not results.
- Sensitivity note: this is census data about people. Use only for the
  sorting-arithmetic test, with the label as a statistical outcome, not
  for any claim about individuals, and do not use race/sex as a gate score.

### 2. Synthetic validation table — VERIFIED, LABELLED SYNTHETIC ONLY
- File: `synthetic-validation-2000.csv`, 2,000 rows, seed 12345.
- Construction (stated, not a real model): label 0 → score ~ N(0.35, 0.15),
  label 1 → score ~ N(0.65, 0.15), clipped to [0,1]. Measured means:
  label 0 = 0.3468, label 1 = 0.6451, label mean 0.494.
- Use: ONLY to validate backend arithmetic (means, entropy, KL/JS, MI,
  tau sweep, shuffled control must behave as known). Never present as
  real-world data, never as a model result.

### 3. In-house, already gathered (not re-downloaded here)
- Maxx seeded queue: 8 actions, `~/workspace/maxx-overnight/data/queue.json`,
  SYNTHETIC, small-n flag — useful as a smoke test, NOT as an entropy
  dataset (n=8, alphabet 10 would be meaningless).
- Glimmer sweep: 955,136 rows, verified SHA, `~/workspace/glimmer-analysis/`,
  Nov 1 in-window. LIMIT: pre-RoPE q_proj/k_proj 3-token score-block proxy,
  no clean decision labels, no PDOT_E — so it is NOT a sorting log and
  cannot supply the held-out independent-label check. Do not force it
  into the backend sorter as if it were.

## DOWNLOADING / PENDING — do NOT use yet

### 4. CIFAR-10 — VERIFIED (file), licence NOT stated on official page
- File: `cifar-10-python.tar.gz` — download completed 2026-11-01 ~17:31 ET
  after a resumed download (`curl -C -`, started ~17:04 ET; first run had
  timed out at 20,360,000 bytes). Final file, verified 2026-11-01:
  170,498,071 bytes exactly, SHA-256
  `6d958be074577803d12ecdefd02955f39262c83c16fe9348329d7fe0b5c001ce`,
  MD5 `c58f30108f718f92721af3b95e74349a` — **the MD5 matches the
  official Toronto page exactly** (page lists CIFAR-10 python version,
  163 MB, md5 `c58f30108f718f92721af3b95e74349a`).
- Contents verified by reading the archive (not just listing it):
  9 members, 5 train batches × 10,000 = 50,000 train (5,000 per class),
  test batch 10,000 (1,000 per class), 10 classes: airplane, automobile,
  bird, cat, deer, dog, frog, horse, ship, truck. 60,000 32×32 colour
  images total, matching the official page description.
- Source: official Toronto page https://www.cs.toronto.edu/~kriz/cifar.html
  (Krizhevsky, Nair, Hinton), read 2026-11-01. The page asks users to
  cite the tech report (Krizhevsky 2009, "Learning Multiple Layers of
  Features from Tiny Images") and **states no licence**.
- License: NOT settled as an official term. Secondary sources conflict
  (one claims CC BY 4.0, another CC BY-NC-SA 4.0, another "academic and
  non-commercial research"). Do NOT quote any of these as the official
  licence. Record as: "official page states no licence; use with
  citation to Krizhevsky 2009; secondary licence claims conflict and
  are unverified."
- Use: image classification, 10-class alphabet for entropy, classifier
  confidence as gate score, label as independent outcome. Requires a
  classifier in the backend step — no score exists in the raw download.

### 5. AgentAbstain — VERIFIED, downloaded 2026-11-01
- What it is: 263 paired tasks (526 tasks) in 42 executable MCP sandbox
  environments, 8 abstention scenarios, each pair = should-act + should-
  abstain variant differing by one controlled perturbation. Best reported
  paired accuracy 59.5% (Gemini 3.1 Pro, paper). This is the closest
  gate-native dataset to Maxx: act vs abstain is exactly admitted vs held.
- Code licence, verified 2026-11-01 from the repo itself
  (`agentabstain-sparse/LICENSE`, sparse clone): **MIT License,
  Copyright (c) 2026 The AgentAbstain Authors**, full text on file.
- Dataset licence, verified 2026-11-01 from BOTH the repo README
  ("The dataset is released under CC BY 4.0") and the Hugging Face
  dataset API (`antiquality/agentabstain`, cardData license
  `cc-by-4.0`, tags include `license:cc-by-4.0`): **CC BY 4.0,
  attribution required.** The earlier unverified status is now settled.
- File: `agentabstain-tasks.jsonl` (1.2M bytes, SHA-256
  `165f021e7bb8b3a1ba103cef291eb522ff219769e8e7727f1a669364a225fb63`),
  526 rows = 263 pairs, verified by row count and field check:
  task_type act 263 / abstain 263, category 8 values, phase
  pre_execution 332 / runtime 194. Fields include pair_id, category,
  task_id, task_type, phase, instruction, abstention_trigger.
- Note: full git clone timed out on 2026-11-01 (~120s, empty directory);
  sparse clone succeeded for LICENSE + README only. The dataset itself
  came from the Hugging Face resolve URL, not the git clone.
- Next step to use it: convert tasks to a frozen table (task id,
  scenario, should-act/abstain label, score to be computed by a gate in
  the backend step). No score exists in the file itself.

## Still missing for a full backend test
- A text dataset with labels (for a non-image, non-tabular check) — candidate
  to gather next, with licence verified first, not assumed.
- Any dataset where a score already exists in the file (model confidence,
  not just features) — that would let the backend sorter run without a
  classifier step, and would test sorting on a real gate score.
- CIFAR file verification done (size, MD5, batch counts); official licence still not stated — see §4.
- AgentAbstain frozen-table conversion (licence + download now verified, above).

## Frozen logged-table format (all datasets, backend input)
`id, score, label, score_source, chamber, split`
- score: the scalar the gate thresholds on, in its own units (confidence
  0–1, surprisal nats, etc.) — never joules, never kelvin.
- label: independent outcome, never derived from the score or the gate rule.
- chamber: EMPTY at gathering time; filled only by the backend gate rule
  at a stated, frozen τ.
- split: train / test / held-out, stated per row, frozen before gating.
