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

## Why it is not fixed here

The generation job persisted only the three aggregate candidates, **not the per-token
log-probabilities** (`confidence_candidates` is a 3-float dict per record). Recomputing a
span-restricted score is therefore impossible from the saved artifacts; it requires re-inference.

**The reason not to re-run is that it would buy nothing, not that it is unaffordable.** The
decision rests on the score-independence argument below: neither baseline can reach the
acceptance floor at *any* score quality, so a clean score cannot change either system's
feasibility verdict — the quantity H1/H2 actually turn on. A re-run would purchase a better
score for two systems that remain infeasible with it.

*(An earlier version of this ADR led with affordability — "~$11 against ~$6.0 remaining." That
framing was imprecise and is corrected at the reviewer's instruction: the ~$11 prices the full
three-arm run, whereas a targeted re-run of the baselines purely to persist per-token
log-probabilities was never costed. Cost is not the load-bearing reason and should not be
presented as one.)*

## Direction of the bias — stated plainly

This is the uncomfortable part and it must not be softened. A contaminated score is a *worse*
selective signal, so the affected system's certified acceptance is **understated**. For
H2 (`CA_QA ≥ CA_FS + δ_material`) an understated `CA_FS` makes H2 **easier to support**. The
defect therefore biases the evidence **in favour of the implementer's own hypothesis** — the
dangerous direction. The same applies more weakly to H1 via ZS.

**The magnitude of the damage is unknown and must not be asserted.** An earlier version of this
ADR offered FS's near-zero discrimination gap (best development AUC 0.9467 against base risk
0.9586) as evidence that contamination was doing real damage. That inference does not hold, and
the correction is recorded here rather than quietly dropped:

| System | discarded share of generation | best AUC | base risk | discrimination gap |
|---|---|---|---|---|
| ZS | 37% | 0.9888 | 0.9927 | 0.0039 |
| FS | **89%** | 0.9467 | 0.9586 | 0.0120 |
| QA | 0% | 0.4401 | 0.5834 | 0.1433 |

If contamination drove non-discrimination, ZS at 37% should show a *larger* gap than FS at 89%.
It shows a **smaller** one. Both baselines are near-non-discriminative irrespective of
contamination level, which is at least as well explained by base risks of 0.96–0.99 leaving
almost no signal for any score to find. The direction of the bias (below) is established by
reasoning about the mechanism; its **size is not measurable from these artifacts** and no
estimate of it may be reported.

## What bounds the damage

**Base-risk infeasibility is score-independent.** The forced-abstention bound
`(base_risk − α)/(1 − α)` depends only on the always-answer base risk, not on the confidence
score — the score sets the *ordering* of documents, not the base rate. ZS (0.9927) and FS
(0.9586) cannot reach the 0.20 acceptance floor at **any** score quality, including an oracle
score, and ADR 0007's two-directional check confirms this holds even at the bound most favourable
to them (max acceptance 0.0647 and 0.1073). A perfect confidence score could not rescue either
baseline.

So the contamination cannot flip a feasible/infeasible verdict for either baseline, which is what
the predicted `boundary_crossing` H1/H2 pattern actually turns on. It affects *how good* a
baseline's selective policy looks, in a regime where no policy can qualify.

**What this argument does NOT cover** (independently confirmed at review):

1. **The magnitude of any QA-over-FS advantage.** Conceded in the claim cap below.
2. **Any score-dependent descriptive claim about a baseline.** Risk–coverage curves, AUC values,
   calibration statements, "FS's confidence is uninformative", or any comparison of selective
   *behaviour* between systems are contaminated for ZS and FS and are **not** protected by
   score-independence. FS's development AUC of 0.9467 must not be reported as a property of
   few-shot prompting; it is a property of few-shot prompting *as scored over a span that is 89%
   discarded text*.

## Decision

1. **Disclose, do not re-run.** The residual is recorded here, in ADR 0007's consequences, and
   must appear in the Plan 4 limitations section and any model/report card.
2. **Pre-commit a claim cap, in three parts.**
   - **H2 support is confounded.** If H2 is supported it **may not** be reported as a clean
     QLoRA-versus-few-shot comparison. The mandatory wording is that FS's selective policy was
     handicapped by a harness artifact of known direction and unknown magnitude, so H2 support is
     not evidence of the *size* of any QA-over-FS advantage.
   - **H2 is retained as a falsification opportunity, not a confirmation.** Its evidential value
     now lies almost entirely in its null. Because the defect biases *toward* H2, a failure to
     support H2 despite that bias is a strong, clean negative result and may be reported as such
     without this caveat. H2 is kept for exactly that reason rather than withdrawn.
   - **No score-dependent descriptive claim about ZS or FS.** Per "What this argument does NOT
     cover" above, contaminated selective-behaviour statistics for the baselines are not reported
     as properties of zero-shot or few-shot prompting.
3. **Any future generation run must persist per-token log-probabilities**, so a span-restricted
   score is recomputable without re-inference. Recorded as a standing requirement.

## Consequences

- No code change: nothing here is repairable from the saved artifacts.
- H2's interpretation is capped in advance, before the sealed split opens — the point of
  recording it now rather than after seeing the result.
- The reviewer found this; the implementer did not. That is recorded because the gap it exposes
  is a *class* of defect — a harness fix applied to one consumer of an artifact (the parser) and
  not to another (the scorer) — worth checking for directly next time a policy changes.
