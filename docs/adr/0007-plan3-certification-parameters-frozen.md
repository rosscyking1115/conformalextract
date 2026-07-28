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
| **primary confidence candidate** | **per system: ZS `mean`, FS `tenth_percentile`, QA `mean`** | Computed below — was NOT decided in advance |

> **Amended 2026-07-21 after independent review** (`evidence/plan3/reviewer_record.phase-a.json`,
> ruling 1a = REVISE). The first version of this ADR froze a single **pooled** candidate
> (`minimum`). That was wrong and is superseded; see §"Why per-system, not pooled" below.

All six were listed only as "planning defaults... before certification" in the accepted plan;
none were exercised against real evidence until this ADR. The confidence candidate specifically
was not a default at all — three predeclared candidates (`mean`, `tenth_percentile`, `minimum`)
existed, and which one is primary was left open pending development-split evidence.

## How the confidence candidate was chosen — and why per-system, not pooled

Command: `uv run conformalextract development-gate`. Reproducible from
`evidence/plan2/development_gate_summary.json`.

Method: `selection.select_confidence_candidate` — lowest development risk-coverage AUC (accept
high-score-first; lower AUC is better) — run **separately for each system** on its own 933
development documents:

| System | mean | tenth_percentile | minimum | **frozen** |
|---|---|---|---|---|
| ZS | **0.9888** | 0.9889 | 0.9920 | `mean` |
| FS | 0.9531 | **0.9467** | 0.9524 | `tenth_percentile` |
| QA | **0.4401** | 0.4508 | 0.4663 | `mean` |

### Why per-system, not pooled (supersedes the original decision)

The first version of this ADR pooled all 2,799 development documents into one AUC and froze
`minimum` (pooled AUC 0.6854). Independent review ruled that **REVISE**, and the reasoning is
correct:

- **Pooling imposed a strictly worse score on the only system that can certify.** QA's own AUC
  for `minimum` is 0.4663 against 0.4401 for `mean` — the pooled choice handicaps QA. The
  direction is toward the null (it makes H1/H2 *harder*, not easier), so this was a power loss
  rather than a bias, but it is still a defect.
- **The pooled object is not well-defined.** It ranks documents from three systems in a single
  risk-coverage curve using raw log-probabilities whose scales differ materially between systems
  (medians for `minimum`: QA −0.73, ZS −0.99, FS −3.18 — a ~2.4-nat spread). The pooled ranking
  therefore partly sorts by *which system produced the document*, and corresponds to no policy
  any single system could deploy.
- **The ADR 0006 analogy was misapplied.** ADR 0006's uniformity governs a **harness**
  transformation, where letting each arm choose its own parser would hand one arm a parsing
  advantage. The confidence score is not harness — it is a component of each system's own
  selective policy, exactly like its threshold.
- **§5.3 does not compel pooling.** "Use exactly the score frozen by Gate 0 … candidate score
  invention ends before certification" compels *freezing* and a tested *orientation*; a
  per-system choice frozen at Gate 0 satisfies it identically.

Each system's score is frozen here, before any certification label opens, and its §5.4 threshold
grid is built from quantiles of the score it actually deploys.

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

### Two-directional robustness (added at reviewer request)

The verdicts above use the Hoeffding **upper** bound on base risk. That inflates risk, which makes
`near_vacuous` **more** likely — the *anti-conservative* direction for declaring two systems
hopeless. So the check is re-run in the direction most favourable to each system (the lower
bound, `base_risk − radius`), recorded as `favourable_bound_check` in the gate summary:

| System | base risk (point) | max acceptance at the *favourable* bound | floor 0.20 reachable? |
|---|---|---|---|
| ZS | 0.9927 | 0.0647 | **no** |
| FS | 0.9586 | 0.1073 | **no** |
| QA | 0.5834 | 0.5763 | yes |

**ZS and FS remain below the acceptance floor even under the reading most generous to them**, so
the near-vacuous verdict is stable under point, lower and upper bounds. This matters because the
verdict is load-bearing for the predicted H1/H2 shape; it is not an artefact of choosing a
conservative bound.

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
- Each system carries forward **its own** frozen candidate (ZS `mean`, FS `tenth_percentile`,
  QA `mean`) from `predictions.parse_arm` for certification purposes; the other candidates remain
  in the source prediction artifacts for reference, never discarded. `build-grid` reads the
  frozen candidate per system from the development-gate summary and refuses to run if that
  summary does not record `selection_scope: per_system`.
- **The confidence scores are computed over a wider token span than the parser accepts** — see
  `docs/adr/0008-confidence-span-mismatch.md`. That is a disclosed, unfixable-at-this-budget
  residual, and it bounds what H2 may claim.
- Development gold access for this freeze is logged: `label_access_head_hash
  c1b3e5a2…`, 2,799 entries, `LabelAccessPurpose.DEVELOPMENT_SELECTION`, verified.
  Certification/final/shift gold was not read.
