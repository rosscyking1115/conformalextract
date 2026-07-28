# Handoff — ADR 0011 $0 re-analysis (2026-07-22)

Dated handoff per the project doctrine. Records what was **executed** vs planned, evidence paths,
gate outcomes, spend, and the next authorised action. Append dated amendments; never rewrite.

## State

- Branch `codex/plan2-training`, HEAD **640aeb9**, working tree clean.
- Green command passing: `uv run pytest -q` (348 passed) `&& uv run ruff check .` `&& uv run mypy`.
- Total spend for all of this work: **$0**. The $25 aggregate cap is untouched.
- No new sealed-label access. `final`/`shift` remain sealed; `certification_result.json` hash
  `71c0de3e…` unchanged.

## What was executed (commits 098b7a3 → 640aeb9)

Two $0 re-analyses over already-open splits, plus honesty/discipline fixes, all behind
**ADR 0011** (`docs/adr/0011-reanalysis-frontier-and-loss-channels.md`).

1. **α-frontier** — `evidence/plan3/alpha_frontier.json` (cmd `alpha-frontier`). The 20% floor
   first becomes oracle-reachable at **α≈0.406** (QLoRA), 0.930 (FS), 0.981 (ZS). The curve is
   α-free, so the sweep is a re-reading of the committed diagnostic, not a new statistic; used
   only to rule α values *out*. Crossing is necessary, not sufficient.
2. **Grounding ⊥ certifiability** — `evidence/plan3/loss_decomposition.json` (cmd
   `loss-decomposition`). 87% of QLoRA's loss is grounded, well-formed, wrong-entity; removing
   ZS/FS's entire grounding deficit moves the frontier by 0.0000. Baselines' result carried by an
   arithmetic ceiling (`mean_loss_ceiling` = 0.84), not by the counterfactual.
3. **WikiEvents 2nd arm WITHDRAWN** — impossible at any α: SCoRC needs 1,386 groups, corpus has
   246 documents. `largest_scorc_grid`=0 at every scale. Not deferred; withdrawn (ADR 0011 §3).
4. **Honesty/discipline fixes**: 2606.29054 citation corrected (Table 3: μ band is NER+MMLU, not
   extraction; JSON-Extract μ=0.033; shift 71%/21% ACI); α=0.20 reframed as deployment threshold;
   sealed-split `--roles` allowlist (`reanalysis.assert_reanalysis_role`); `claims.py` untracked-
   evidence + pending-verification-tripwire fixes; four accepted plans brought in-repo and pinned.

## Claims added (`evidence/plan4/claim_ledger.json`, `verify-claims` ok, 14 claims / 12 publishable)

`CX-GROUNDING-ORTHOGONAL-01` (qualified), `CX-ALPHA-FRONTIER-01` (negative),
`CX-WIKIEVENTS-NCERT-01` (infeasible). Each cites `reviewer_record.reanalysis.json` in
`verified_by`.

## Independent review — `evidence/plan3/reviewer_record.reanalysis.json`

Four passes recorded, all preserved: initial **BLOCK** (6 items) → **PASS** → P1–P6 discharged →
final pass (§6.2-not-§6.3 correction, tripwire narrowing, plan pins). **Publication gate: lifted.**
Numbers were confirmed by from-scratch reimplementation, not by reading the implementation.

## Key corrections the review forced (so they are not re-litigated)

- The binding constraint is **§6.2's fourth bullet** ("do not relax α after seeing certification"),
  NOT §6.3. Do not write "the constraint was weaker than we thought". Licence for plotting the
  curve is **§9.1** (read across from the ADR-0010-descoped §9 stage; disclosed as such).
- The grounding oracle is **not** "the most generous reading" — it raises 24 FS / 21 QA group
  losses. The baselines' result rests on the arithmetic ceiling, which is **silent for QLoRA**.
- 2606.29054 evaluates no EAE/RAMS/WikiEvents; μ≈0.60 is our own measurement in a harder regime.
  It does **not** "contradict" their JSON-Extract 0.033 — different task, different metric.
- `PENDING_VERIFICATION_TRIPWIRE` is a tripwire, NOT a gate: it misses 11 of 18 genuine pending
  strings. `git ls-files` = tracked (index), which is weaker than committed-and-pushed.

## Still open / deliberately not done

- **The write-up itself** — not started. This is the next unit of work. Target:
  Insights-from-Negative-Results as-is → Findings with the two additions. Positioning =
  science-of-evaluations ("grounding ⊥ certifiability for grounded EAE; here is a $0 diagnostic").
  Do NOT frame as discovering CRC-extraction-infeasibility (that is 2606.29054's).
- **`claims.py` structural fix** (typed `verified_by` = reviewer-record path + verdict) — would
  re-classify existing claims, so needs its own review. Recorded in ADR 0011 §6.

## NOT authorised without explicit Ross approval

Spend / paid execution, opening `final` or `shift`, starting Plan 4, or any public claim beyond the
recorded claim boundaries in `docs/plan3/certification-result.md` ("What may and may not be
claimed"). Every eval/certification/claims change still goes through independent review.

---

## Amendment — 2026-07-28: README gate state and the CX-COST-01 correction

Appended, not rewritten. Everything above stands.

**Executed** (commits `0982a6a` → `4d80ecd`, all pushed, $0, no sealed access, no gate advanced):

1. **README gate state corrected.** It said "Plan 1 is active" while the records said Plan 1
   complete, Plan 2 closed, Plan 3 executed and independently reviewed, Plan 4 not started. Plan 3
   is stated as **"executed and independently reviewed; not formally closed"** — five Plan 3
   reviewer records exist and none carries `review_kind: "plan_close"`. Result section takes each
   claim verbatim from the ledger with its limitations; only the six claims surfaced to README
   appear. Independent review: `evidence/plan4/reviewer_record.readme-status.json`
   (PASS-WITH-NITS → PASS on discharge).
2. **`CX-COST-01` re-evidenced and re-worded** — ADR 0012, independent review
   `evidence/plan4/reviewer_record.cost-claim.json` (**BLOCK** → PASS-WITH-NITS on discharge). It
   cited a forecast; the total is now the band **$18.7–$18.9** with both readings of the running
   totals stated, and the Gate 0 per-job artifact is cited for the first time.

**Added to the open list below:** the Plan 2 spend artifact (new). The write-up and the `claims.py`
structural fix are unchanged and still open.

### Open — a committed per-job spend artifact for Plan 2

`TrainingRunLedger` exists in `src/conformalextract/training.py` with an `actual_cost_usd` field and
`spent_usd`, and is **never serialised anywhere**. Gate 0 has the artifact this would produce
(`evidence/gate0/hf_jobs_submission_attempts.json`, ten attempts, summing to the $0.2008 that
`REMAINING_BUDGET_USD` subtracts). Plan 2 has nothing equivalent — its costs are prose across six
documents, and the single largest figure (~$11.2, 60% of the programme) sits in a reviewer brief
about extraction policy.

**Forward-looking only.** It cannot retroactively record what was never written down: one job has
no per-job figure at all, and the attempt inventory is a floor rather than a count — the R0 launch
plan records fixes discoverable only by a job that reached GPU execution and was billed, with no id
or cost anywhere. New engineering, its own independent review, not this round. Do **not** treat
writing the artifact as licence to backfill numbers by inference and record them as measured; the
$0.15–$0.35 recovery in ADR 0012 is explicitly an inference and is labelled as one.

### Two lessons worth carrying, both bought at cost

- **After re-citing, re-derive the number from the new citations.** The first draft of ADR 0012
  fixed `CX-COST-01`'s citations and still published a total that omitted a figure recoverable from
  two documents *it had just added to the evidence array* — landing below the supported band, and
  below the number it replaced. Understatement is the flattering direction for a spend claim
  against a fixed ceiling.
- **Derive a pattern from its source of truth, never restate it.** The first version of
  `test_every_claim_id_cited_in_public_prose_is_surfaced_there` invented a claim-ID regex ending
  `-\d+`, silently skipping `CX-H1-PRIMARY` and `CX-H2-SECONDARY` — the only two IDs not ending in
  digits, and exactly the pair the review had flagged. A mutation probe caught it; reading the
  pattern did not. Same shape as ADR 0011 §6's pending tripwire: a substance-blind rule must be
  measured on realistic inputs before it is trusted.
