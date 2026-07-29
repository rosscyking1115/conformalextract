# Items carried into Plan 3 by Plan 2's close — status of each

- Source: [`../../evidence/plan2/reviewer_record.plan2-close.json`](../../evidence/plan2/reviewer_record.plan2-close.json)
  → `what_this_close_does_and_does_not_authorise.carried_into_plan_3`
- Created 2026-07-29, retrospectively, after finding **O3**

## Why this document exists

Plan 2's close carried four items into Plan 3. **One of them was silently dropped for eight days**
and was found only when an independent reviewer refused to close Plan 3 and went looking for it.

The mechanism is worth stating precisely, because it defeats every automated check in this
repository. `CX-SERVING-01` inherited both of the probe's *reassuring* limitations and dropped the
one that cut against the result. Every surviving sentence was **individually true**, so
claim-fidelity, forbidden-wording, citation and evidence-resolution checks all passed. **A
limitations list that is individually true and collectively flattering is invisible to all of
them.**

The countermeasure is this document, and specifically **where it lives**. The items were already
listed — in the review that raised them. That was not enough: a later reviewer had to find the
source record to discover that something was missing. **A carried-forward list belongs in the
receiving document**, so the obligation travels with the work rather than with the review.

> **Standing rule, recorded in [`../../REVIEW.md`](../../REVIEW.md):** when a review carries items
> forward, the receiving plan's directory gets a register like this one, and each item is ticked
> off **by name**. A close may not be issued while any item is untracked.

## The four items

| # | Item | Status |
|---|---|---|
| 1 | Re-report divergence at the realised operating point before any stability claim | **discharged, late** |
| 2 | C3 — empty frames reported as a separate first-class column; FS acceptance never a single conflated number | **discharged** |
| 3 | C6 — H1/H2 rest on grounding and certified acceptance, not structural validity | **discharged** |
| 4 | The abstain/extract flip finding: two of four flips survive into the accepted set | **DROPPED, then discharged 2026-07-29** |

### 1. Probe condition 1 — re-report divergence at the realised operating point

**Discharged.** The condition was that the near-zero top-quartile divergence result is
operating-point-dependent and must not be carried forward as though it applied at whatever
acceptance calibration selected. Certification returned **Infeasible for all three systems**, so no
operating point was ever realised — the condition could not fire in the form written. It is now
carried explicitly as a limitation on `CX-SERVING-01` (added 2026-07-29) rather than left as a
condition nobody could discharge: at top-90% acceptance divergence is 12.59%, barely below the
13.67% raw rate.

### 2. C3 — empty frames as a first-class column

**Discharged.** `evidence/plan2/prediction_parse_summary.json` and
[`certification-result.md`](certification-result.md) both report `valid but contentless` as its own
channel — FS 31.4% against ZS 0.5% — and the four-channel decomposition in ADR 0011 makes it
structural rather than a footnote. FS acceptance is never reported as a single conflated number.

### 3. C6 — H1/H2 rest on grounding and certified acceptance

**Discharged.** Both hypotheses are evaluated on certified acceptance and return
`both_infeasible`. Structural validity is explicitly recorded as the axis that *failed* to
discriminate (FS 9,105 ≥ QA 9,085 > ZS 8,959), which is the point C6 was protecting.

### 4. The abstain/extract flip finding — the one that was dropped

**Dropped for eight days. Discharged 2026-07-29 as finding O3.**

Plan 2's close directed it into "Plan 4 limitations and any model/report card". It reached
neither. `CX-SERVING-01` holds the `report` and `model_card` surfaces — the exact two named — and
carried the two reassuring limitations without it.

The finding: the abstain/extract decision itself flips between serving stacks at **1.3–1.8% of
frames at plausible operating points**, and two of the four empty-versus-nonempty flips sit just
above the median confidence percentile, so they **survive into the accepted set** rather than being
abstained away. The flip rate can therefore exceed the 1.3% raw rate. The abstention mechanism is
stack-dependent at the margin.

Now carried as limitation 4 on `CX-SERVING-01`, with the operating-point dependence of its
companion reassurance as limitation 5.

## What this document does not do

It does not close Plan 3, and it does not discharge findings O1 or O2. It records the status of the
four Plan 2 items only, so that the next close review can check them by name instead of
reconstructing them from a prior record.
