# ADR 0008: Confidence scores span more tokens than the parser accepts (disclosed residual)

- Status: accepted (disclosure; no code change)
- Date: 2026-07-21
- Trigger: independent reviewer Phase-A finding 1(d)
  (`evidence/plan3/reviewer_record.phase-a.json`) — raised by the reviewer, not by the
  implementer, and not on the review checklist it was asked for.

## The defect

Confidence candidates (`mean`, `tenth_percentile`, `minimum`) were computed in
`jobs/plan2_prediction_generation.py` over the transition log-probabilities of **every generated
token**. ADR 0006's extraction policy then parses only the **first balanced JSON object**. The
two spans do not coincide.

Median share of the generated text that the accepted object actually occupies (independently
measured over all valid generations):

| System | Median share | Mean share |
|---|---|---|
| QA | **1.000** | 1.000 |
| ZS | 0.630 | 0.662 |
| FS | **0.112** | 0.101 |

So roughly **89% of FS's scored tokens are the fabricated continuation the parser discards**, and
about 37% of ZS's are its instruction-echo preamble. QA is clean. This is the same missing-stop-
sequence harness bug ADR 0006 corrected for *parsing*, propagating into the *scoring* channel,
where it was not corrected.

## Why it cannot be fixed here

The generation job persisted only the three aggregate candidates, **not the per-token
log-probabilities** (`confidence_candidates` is a 3-float dict per record). Recomputing a
span-restricted score is therefore impossible from the saved artifacts; it requires re-running
generation. The original three-arm run cost ~$11 over ~14h, and FS alone was the expensive arm.
Remaining programme budget is ~$6.0 of $24.7992. **A re-run is not affordable**, and spending
essentially the entire remaining budget to re-derive a score for two systems that are
base-risk-infeasible regardless (below) would be poor judgement.

## Direction of the bias — stated plainly

This is the uncomfortable part and it must not be softened. A contaminated score is a *worse*
selective signal, so the affected system's certified acceptance is **understated**. For
H2 (`CA_QA ≥ CA_FS + δ_material`) an understated `CA_FS` makes H2 **easier to support**. The
defect therefore biases the evidence **in favour of the implementer's own hypothesis** — the
dangerous direction. The same applies more weakly to H1 via ZS.

Supporting evidence that the contamination is doing real damage: FS's best development
risk-coverage AUC is 0.9467 against a base risk of 0.9586 — the score is very close to
non-discriminative, which is what a mostly-noise signal looks like.

## What bounds the damage

**Base-risk infeasibility is score-independent.** The forced-abstention bound
`(base_risk − α)/(1 − α)` depends only on the always-answer base risk, not on the confidence
score. ZS (0.9927) and FS (0.9586) cannot reach the 0.20 acceptance floor at **any** score
quality, and ADR 0007's two-directional check confirms this holds even at the bound most
favourable to them (max acceptance 0.0647 and 0.1073). A perfect confidence score could not
rescue either baseline.

So the contamination cannot flip a feasible/infeasible verdict for either baseline, which is what
the predicted `boundary_crossing` H1/H2 pattern actually turns on. It affects *how good* a
baseline's selective policy looks, in a regime where no policy can qualify.

## Decision

1. **Disclose, do not re-run.** The residual is recorded here, in ADR 0007's consequences, and
   must appear in the Plan 4 limitations section and any model/report card.
2. **Pre-commit a claim cap.** If H2 is supported, it **may not** be reported as a clean
   QLoRA-versus-few-shot comparison. The mandatory wording is that FS's selective policy was
   handicapped by a harness artifact of known direction and unknown magnitude, so H2 support is
   **confounded** and is not evidence of the size of any QA-over-FS advantage. If H2 is *not*
   supported despite this favourable-to-QA bias, that is a strong negative result and may be
   reported as such.
3. **Any future generation run must persist per-token log-probabilities**, so a span-restricted
   score is recomputable without re-inference. Recorded as a standing requirement.

## Consequences

- No code change: nothing here is repairable from the saved artifacts.
- H2's interpretation is capped in advance, before the sealed split opens — the point of
  recording it now rather than after seeing the result.
- The reviewer found this; the implementer did not. That is recorded because the gap it exposes
  is a *class* of defect — a harness fix applied to one consumer of an artifact (the parser) and
  not to another (the scorer) — worth checking for directly next time a policy changes.
