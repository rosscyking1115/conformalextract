# Plan 3 — Phase A implementation notes (CPU, no labels, no GPU)

Source of truth: the accepted plan at
`C:\dev\_pmo\assistant\plans\conformalextract\conformalextract-plan3-certification-and-schema-shift-experiments.md`.
This file only tracks the *implementation* of the unblocked Phase-A scaffolding.

## Gate status at start (2026-07-18)

- Plan 2 has an independent **contracts** PASS at `8e5a2c8`. Plan 2's paid execution
  (R0→R2, QA checkpoint, ZS/FS/QA label-free prediction manifests) has **not** run, so
  Plan 3 Phases B–E (certify / evaluate-final / evaluate-shift) are **blocked**: they need
  those prediction artifacts and open sealed certification/final/shift labels, and require
  explicit GPU-spend authorization + prepaid HF credit.
- The certifier core is already implemented and tested (Gate 0D):
  `scorc_certificate` (preferred joint finite-grid SCoRC) and `conservative_certificate`
  (Hoeffding + Clopper-Pearson + Bonferroni audit) in `src/conformalextract/certification.py`.
- The five Plan 3 commands are registered as `_not_ready` stubs in `cli.py`:
  `build-grid`, `certify`, `evaluate-final`, `evaluate-shift`, `render-report`.

## What is buildable now (Phase A, §13.1 / §13.2 / §3.2)

Ordered, immutable, hash-gated reproducibility scaffolding — pure and synthetic-testable:

1. **Ordered-pipeline gating** (§13.1) — five ordered stages
   (build_grid → certify → evaluate_final → evaluate_shift → render_report), each requiring
   the prior stage's immutable artifact hash, refusing out-of-order execution, all bound to
   one analysis version. **DONE** (`analysis_pipeline.py`, `test_analysis_pipeline.py`).
2. **Certifier verification** (frontier-check gate G1b/c). Theorem-to-code note confirms
   `scorc_certificate` correctly implements Algorithm 1 of arXiv 2606.08517 (U3/U4 are proof-only,
   not a gap). **DONE** (`docs/plan3/theorem-to-code-scorc.md`).
3. **Base-risk feasibility diagnostic** (§6.1 / gate G1a). `base_risk_feasibility`,
   `minimum_abstention`, `max_feasible_acceptance` in `certification.py`. **DONE**
   (`test_base_risk_feasibility.py`); α=0.20 answerable for RAMS band; finalize with real dev losses.
4. **Certifier coverage validation** (§13.3 / gate G1d). Monte-Carlo valid + deliberately-invalid
   regimes + negative control. **DONE** (`test_scorc_coverage.py`).
5. **CA_s / H1 / H2 decision logic** (§8). `certified_acceptance`, `compare_certified_acceptance`
   in `certification.py`. **DONE** (`test_hypotheses.py`).
6. **Certification preflight** (§3.2) — label-free assertions (ZS/FS/QA predictions exist for
   identical group IDs; hashes match frozen manifests; no group overlap with train/development;
   grid + tie order committed; α/δ/floor/ledger committed; final/shift manifests inaccessible to
   the calibration command). *(remaining — needs prediction manifests to exist)*
7. **Analysis-version lock** (§13.2) binding prediction manifests, data/group/split hashes,
   evaluator/loss/score hashes, grids, cert config + delta ledger, Git commit and env lock.
   `AnalysisLock` already exists in `contracts.py`. *(remaining)*

## Not invented here (Gate-0 / development-freeze decisions)

Grid size, `alpha`, `delta`, acceptance floor, material `CA` gain, bootstrap replicates, and
the shift definition are frozen decisions (plan §21). Phase-A scaffolding encodes the
*mechanism* (hash-gating, ordering, refusal) without hardcoding those values as if decided.

## Hard rules carried from the plan

- No certification/final/shift label access outside the ordered, hash-gated commands.
- No GPU and no paid job in Plan 3 (§13.4: certification/scoring/bootstrap/report are CPU).
- Out-of-order or hash-mismatched execution must record an invalid attempt, never overwrite.
