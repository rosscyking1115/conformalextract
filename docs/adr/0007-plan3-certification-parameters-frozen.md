# ADR 0007: Plan 3 certification parameters frozen (Gate 0)

- Status: accepted
- Date: 2026-07-21
- Trigger: Plan 2 is closed (independent reviewer PASS, `evidence/plan2/reviewer_record.plan2-close.json`).
  Plan 3 requires "target risk `alpha`, failure probability `delta`, minimum acceptance floor,
  primary confidence score... frozen by Gate 0" before certification opens sealed labels
  (accepted plan, `docs/plan3/phase-a-implementation.md`). This ADR is the freeze, produced
  before any certification/final/shift label is read.

## Decision

Freeze the following for all of Plan 3 certification:

| Parameter | Value | Source |
|---|---|---|
| `alpha` (target risk) | **0.20** | Plan 3 §21 planning default, now exercised with real evidence |
| `delta` (failure probability) | **0.05** | Plan 3 §21 planning default |
| acceptance floor | **0.20** | Plan 3 §21 planning default |
| material `CA` gain (H1/H2) | **0.05** | Plan 3 §21 planning default |
| bootstrap replicates | **2,000** | Plan 3 §21 planning default |
| **primary confidence candidate** | **`minimum`** (min transition log-probability) | Computed below — was NOT decided in advance |

All six were listed only as "planning defaults... before certification" in the accepted plan;
none were exercised against real evidence until this ADR. The confidence candidate specifically
was not a default at all — three predeclared candidates (`mean`, `tenth_percentile`, `minimum`)
existed, and which one is primary was left open pending development-split evidence.

## How the confidence candidate was chosen — and why pooled, not per-system

Command: `uv run conformalextract development-gate`. Reproducible from
`evidence/plan2/development_gate_summary.json`.

**Selection is pooled across ZS+FS+QA development documents into one choice, not selected
separately per system.** This mirrors the fairness rule ADR 0006 established for the extraction
policy: apply one rule uniformly, don't let each system pick its own best-looking definition.
The plan's own text supports this reading — "primary confidence score" is listed singular
alongside `alpha`/`delta`/floor as frozen-by-Gate-0 (plan intro), while §5.4 has each system
build its own **threshold grid** from quantiles of that *same* score. One score definition;
per-system thresholds on it.

Method: `selection.select_confidence_candidate` — lowest grouped development risk-coverage AUC
(accept high-score-first; lower AUC is better) — run once on 2,799 pooled documents (933 × 3
systems):

| Candidate | Pooled risk-coverage AUC |
|---|---|
| mean | 0.7347 |
| tenth_percentile | 0.8652 |
| **minimum** | **0.6854** (selected) |

**`minimum`** — the worst (lowest) transition log-probability among a document's generated
tokens — is the frozen primary confidence score. Intuitively: a document is only as trustworthy
as its single worst-generated token: one confidently-wrong token anywhere in the completion is
enough to make the whole answer suspect, which the minimum captures and the mean can dilute.

## Base-risk feasibility at `alpha=0.20`, floor `0.20` (real development-split evidence)

Document loss is always-answer bounded loss (`1 - micro-F1`; a structural or grounding failure
is forced to loss `1.0`, never scored on content it did not actually produce — matching
`evaluate_document`'s existing contract). 933 development documents per system.

| System | base risk (point) | base risk (Hoeffding UCB) | min forced abstention | max feasible acceptance | verdict |
|---|---|---|---|---|---|
| ZS | 0.9927 | 1.0000 | 1.0000 | **0.0000** | **near_vacuous** |
| FS | 0.9586 | 1.0000 | 1.0000 | **0.0000** | **near_vacuous** |
| **QA** | 0.5834 | 0.6279 | 0.5349 | **0.4651** | **marginal** |

**Read this precisely.** Base risk is `1 - micro-F1` — a much stricter bar than the grounding
validity reported in `docs/plan2/prediction-parse-result.md` (QA 95.7% valid). "Valid" means
parseable and grounded; it says nothing about whether the extracted *entity* is correct. Manual
inspection of high-loss valid QA documents shows the pattern clearly: the model grounds a
real, well-formed span, in the right role, but names the wrong entity —
e.g. gold `victim = "Mrs. Clinton"` vs predicted `victim = "she"`; gold `candidate = "Trump"` vs
predicted `candidate = "dictators"`. These are genuine extraction errors (coreference/entity
selection), not extraction-policy or grounding failures.

**ZS and FS are near-vacuous at this operating point: the target is structurally unanswerable.**
Even abstaining on literally every document, their base risk is high enough that the forced
minimum abstention already exceeds what the floor allows — there is no selective policy at
`alpha=0.20`/floor `0.20` that both baselines could ever satisfy, independent of sample size or
which threshold is chosen. This is a legitimate feasibility finding, not a bug: it follows
directly from the population-level always-answer decomposition (`minimum_abstention`,
arXiv 2606.29054), computed from real held-out predictions.

**QA is marginal: answerable in principle, but only under substantial abstention** (≥53.5% by
this bound). This is base-risk *feasibility* only — a population-level upper bound on what any
selective policy could achieve, not a claim that a specific finite-sample policy will hit it.
Finite-sample certification against sealed certification-split data determines that.

## What this predicts, and what it does not

If certification holds this pattern, `certification.compare_certified_acceptance`'s
`_decide_hypothesis` would record H1/H2 as `boundary_crossing` — QA feasible where a baseline is
infeasible — rather than a numeric material-gain comparison, since the framework never invents a
difference against an infeasible baseline (Plan 2 audit correction, plan §8.2). **This is a
prediction from base-risk feasibility, not a certification result.** Finite-sample noise, the
SCoRC grid, and the sealed certification split could still change any of these verdicts,
including QA's. Per the CLAUDE.md honesty boundary, an infeasibility or negative result at
certification remains a first-class publishable outcome.

## Consequences

- These six values are now frozen inputs to the certification preflight (§3.2) and the
  threshold-grid builder (§5.4). Changing any of them after certification labels open would
  itself require an independent review, per the general evaluation-change rule.
- `minimum` becomes the confidence field every `PredictionRecord` carries forward from
  `predictions.parse_arm` for certification purposes (the other two candidates remain in the
  source prediction artifacts for reference, never discarded).
- Development gold access for this freeze is logged: `label_access_head_hash
  c1b3e5a2…`, 2,799 entries, `LabelAccessPurpose.DEVELOPMENT_SELECTION`, verified.
  Certification/final/shift gold was not read.
