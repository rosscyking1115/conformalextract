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
6. **Certification preflight** (§3.2) — `certification_preflight.py`, seven label-free
   assertions (identical document sets across arms; manifest match; group disjointness from
   train/development; grid+tie-order committed; α/δ/floor match the ADR 0007 freeze; synthetic
   coverage passed; final/shift structurally unreachable — no parameter accepts them). **DONE**
   (`test_certification_preflight.py`, commit `7d7e5ba`).
7. **Analysis-version lock** (§13.2) — `analysis_version.py`, binds prediction manifests,
   data/group/split hashes, evaluator/loss/score hash, candidate grid, cert config + delta
   ledger, Git commit and env hash into one `analysis_id`; any input change → new id. **DONE**
   (`test_analysis_version.py`, commit `99113bb`).
8. **Threshold grid builder** (§5.4) — `threshold_grid.py` + `build-grid` command
   (development-only), per-system quantile grids of the frozen `minimum` candidate plus
   boundary policies, theorem-sized (9 certifiable candidates at n=1396/δ=0.05/floor=0.20),
   deterministic, hashed. **DONE** (`test_threshold_grid.py`, commit `d5a170d`; real grids in
   `evidence/plan2/threshold_grids.json`).

## Gate-0 freeze (now decided — ADR 0007)

`alpha=0.20`, `delta=0.05`, acceptance floor `0.20`, material `CA` gain `0.05`, bootstrap
`2,000`, and primary confidence candidate **`minimum`** are frozen in
`docs/adr/0007-plan3-certification-parameters-frozen.md`, exercised against real
development-split evidence. Grid size is theorem-derived (feasibility, not performance). The
`certification.FROZEN_*` constants are the single source of truth. The **shift definition**
(§3.4) remains the one Gate-0 item still open — needed only for `evaluate-shift`, after
certification and final.

## Still open before `certify` can run

- §5.5 global multiplicity / delta allocation across the three system families — the
  theorem-to-code note must show the failure budget covers adaptive selection across
  `{ZS,FS,QA} × thresholds`. If the conservative construction allocates δ/3, the grids must be
  rebuilt at that δ (theorem max drops from 9 to 3); the analysis-version lock will catch the
  change. **This is a theorem/allocation decision, not invented here.**
- The `certify`/`evaluate-final`/`evaluate-shift`/`render-report` commands (still `_not_ready`
  stubs) — `certify` opens the sealed certification split for the first time.

## Hard rules carried from the plan

- No certification/final/shift label access outside the ordered, hash-gated commands.
- No GPU and no paid job in Plan 3 (§13.4: certification/scoring/bootstrap/report are CPU).
- Out-of-order or hash-mismatched execution must record an invalid attempt, never overwrite.
