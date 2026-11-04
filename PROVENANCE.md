# Provenance — what is new, what is pre-existing, what is labelled

Submission rule (Meta Global AI Developer Hackathon, Participant Guide):
presented work must have been built during the event, the demo must only
highlight Hackathon-built work, and original contributions must be clearly
identified. Submission repo must be public. This repo, `Ambercontinuum/Maxx-Gate`,
is core-only by design: it holds the gate, the sorter, and the sidecar
from the Oct 26–Nov 4 window, and intentionally does NOT hold the Maxx
Lab, partition, council, or energy work that landed on the old
`Ambercontinuum/Maxx` branch on 2026-11-02. As of its first push on
2026-11-03 it is still private, NOT flipped public, and NOT submitted —
flipping and submitting are Amber's alone, and neither has happened.
Gate hold reasons in this repo use the Nov 2 reputation wording:
"Verify before money moves, files are lost, or an irreversible action
goes out" — reputation is not measured anywhere here.

## How it was built
Designed and directed by Amber Anson. The code was written by Maxx, her
Muse agent (Meta Muse), in her Muse workspace. Codex was also used,
in her IDE, as a developer-augmentation tool — for verification runs
and IDE-side execution under her orchestration.
Authorship of the design, the code of record, and every claim here is
the author's and her Muse's; Codex's role was verification and
execution support, and one of its runs is labelled as such in
`analysis/live-meta-run-2026-11-03.md`.

## New work in this codebase (Oct 26–Nov 4, 2026 window)
- The Maxx gate package (`maxx/`): intake, stated-arithmetic temperature,
  gate/permit enforcer, conserved ledger, mock tools, fixed-rule arm,
  Spark proposal with seeded fallback, advice-only stability stub.
  Bearer redefinition (2026-11-01): cost_bearer = "operator" for all actions,
  recipient recorded separately in the ledger.
- The demon sorter (`sorter/`): frozen-table gate, counts, chamber means,
  entropies, KL/JS, mutual information, flip rates, tau sweep,
  shuffled-gate control, binning sensitivity — all in bits/counts.
- The integrated run (`run_all.py`), this README, this provenance file,
  and the combined report it generates.
- Glimmer sweep analysis and K geometry analysis (in `analysis/` as
  appendix only): Nov 1 in-window runs, but K was never wired to the gate
  and no K claim travels from them into gate decisions.

## Pre-existing input, labelled as such, never presented as new results
- UCI Adult dataset (Becker/Kohavi 1996, UCI ML Repository, DOI
  10.24432/C5XW20): pre-existing census data. Full files verified:
  adult.data 3,974,305 bytes, SHA-256
  5b00264637dbfec36bdeaab5676b0b309ff9eb788d63554ca0a249491c86603d;
  adult.test 2,003,153 bytes, SHA-256
  a2a9044bc167a35b2361efbabec64e89d69ce82d9790d2980119aac5fd7e9c05.
  UCI page lists CC BY 4.0 (attribution required); a secondary catalog
  lists CC0 — CC BY 4.0 is quoted here, not CC0. Templates in `datasets/`
  are gathering artefacts (first 2,000 rows), not results.
- AgentAbstain dataset (Liu et al., arXiv 2607.10059): pre-existing benchmark.
  Code MIT (Copyright (c) 2026 The AgentAbstain Authors); dataset CC BY 4.0
  (repo README + Hugging Face card, verified 2026-11-01). File
  agentabstain-tasks.jsonl, 526 rows, SHA-256
  165f021e7bb8b3a1ba103cef291eb522ff219769e8e7727f1a669364a225fb63.
  Not yet converted to a frozen table in this codebase.
- CIFAR-10 (Krizhevsky, Nair, Hinton, University of Toronto): pre-existing
  dataset. File cifar-10-python.tar.gz, 170,498,071 bytes, SHA-256
  6d958be074577803d12ecdefd02955f39262c83c16fe9348329d7fe0b5c001ce,
  MD5 c58f30108f718f92721af3b95e74349a (matches the official page).
  Official page states NO licence and asks for citation to Krizhevsky 2009;
  secondary licence claims conflict (CC BY 4.0 vs CC BY-NC-SA 4.0) and are
  NOT quoted as official here.
- Synthetic validation table: SYNTHETIC ONLY, seed 12345, 2,000 rows,
  label 0 score ~N(0.35, 0.15), label 1 ~N(0.65, 0.15). Never real data,
  never a model result.
- PDOT drive equation form E = (I + PW - D) / 3: cited reproduced formalism
  from pre-existing PDOT work, candidate only. PDOT's own I/PW/D semantics
  were NOT verified against PDOT code, and no PDOT mapping is used in the
  gate or the sorter. PDOT work was stopped at Amber's instruction and is
  not part of this submission's claims.
- NHAM / SERAPH / prior papers and data: background and pre-existing input
  only, per the Nov 1 old-work clarification. Old results are never
  presented as new results. Former framing was removed under the Nov 1
  framing reset; only what was built inside this project, through the
  Principal Architect invariants, travels forward.
- The author's older `Ambercontinuum/Maxx` branch (Lab, partition,
  council, and energy work) is a separate body of work and is
  intentionally NOT in this repo. Codex verified commit `eb7e24c…` on
  that branch on 2026-11-01; that verification does not cover this
  repo, and the later combined-budgets change on that branch
  (`43396a2b…`) was not Codex-verified.
- The demo video was produced on 2026-11-03 from the final v2
  storyboard and is published at the link in the README. Earlier
  script drafts and their approval states are internal production
  history, not part of this submission.

## Data-freshness rule
No 2025 data is used in submission/interface copy in this codebase, per
Amber's Nov 1 rule. Scope of that rule (current product/competitor/incident
claims only vs stricter all-claims) is still to be clarified before
submission text is finalised, and no 2025-only material (e.g. Replit) is
included here.

## What is NOT in this codebase
- No live Spark run is claimed. The gate demo uses the seeded queue by
  default in `run_all.py`; Spark proposal code is present with a labelled
  seeded fallback, key from env only, never in chat/files.
- No demo video. No hosted site. No enterprise admin UI.
- No real integrations, no real money, sends, shares, bookings, posts,
  or deletions.
