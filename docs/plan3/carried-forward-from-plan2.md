# Items carried forward by Plan 2's close — status of each

- Source: [`../../evidence/plan2/reviewer_record.plan2-close.json`](../../evidence/plan2/reviewer_record.plan2-close.json)
- Created 2026-07-29, retrospectively, after finding **O3**; extended the same day after **R4**

> ### This register covered the wrong list first
>
> Plan 2's close carries items forward in **two** places, and the first version of this document
> registered only one of them:
>
> - `what_this_close_does_and_does_not_authorise.carried_into_plan_3` — four items (§A below)
> - `ruling_2_serving_equivalence_probe.standing_limitation` — six elements (§B below)
>
> **The second list is the one O3 came from.** It is the sentence that says "Carry into Plan 4
> limitations and any model/report card", so a register built to prevent O3 recurring was built
> against the list that did not contain it. Extending it found **two more elements that never
> arrived**, by the same asymmetry: both are qualifiers on reassurances that did travel.
>
> The generalisable point: **"carried forward" is not a field, it is a behaviour**, and a review can
> express it in more than one place. Read the whole record, not the key that looks like the list.

## §A — `carried_into_plan_3`, four items

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

## §B — `standing_limitation`, six elements

Directed to "Plan 4 limitations and any model/report card, scoped to the exact serving stack".
`CX-SERVING-01` holds `report` and `model_card`, so it is the receiving artifact for all six.

| # | Element | Status |
|---|---|---|
| B1 | 13.67% raw divergence | **arrived** — the claim's headline is its complement, 86.3% agreement |
| B2 | 1.3–1.8% abstain/extract flip rate at plausible operating points | **dropped, discharged 2026-07-29 as O3** |
| B3 | quality-neutrality | **arrived** — limitation 2 |
| B4 | confidence-concentration **with its 4.80% upper bound in the top quartile** | **half-arrived — the bound never came** |
| B5 | probe frames are train-split only | **arrived** — limitation 1 |
| B6 | cause is not isolated to a specific kernel | **never arrived** |

### B4 — the reassurance travelled, its bound did not

Limitation 2 says divergence "concentrates in low-confidence frames". The source attaches a
qualifier to that reassurance: the top-quartile result is **0 of 75**, which carries a two-sided
Clopper–Pearson 95% upper bound of **4.80%** — not zero. The reassurance arrived; the number
bounding how reassuring it is did not.

**This is the O3 asymmetry a third time**, and B6 makes it a fourth. Each dropped element is a
qualifier on something that survived. Nothing that flattered the result was lost.

### B6 — cause is not isolated

The probe established *that* the stacks diverge, not *why*. No kernel, quantisation path or sampler
was identified as responsible, so nothing about the divergence can be assumed fixed by changing any
one of them. Absent from the claim entirely.

Both are now added to `CX-SERVING-01` as limitations 6 and 7.

## §C — the finding: omissions all pointed one way

Six items across the two lists failed to arrive or arrived incomplete. **Every one qualifies a
reassurance that did travel.** Recording the direction is the point, because the direction is the
signal:

| Item | Direction | Travelled? | What it qualified |
|---|---|---|---|
| A1 probe condition 1 | qualifies a reassurance | late | the near-zero top-quartile result, which holds only under aggressive abstention |
| A4 / B2 abstain-extract flip | states a risk | **no** (8 days) | — |
| B4 4.80% Clopper–Pearson bound | qualifies a reassurance | **no** | "concentrates in low-confidence frames" — 0 of 75 is not zero |
| B6 cause not isolated | states a risk | **no** | — |
| B1 13.67% raw divergence | states a risk | yes (as its complement, 86.3%) | — |
| B3 quality-neutrality | reassurance | yes | — |

**No counter-example exists in this set.** Nothing that flattered the result was ever dropped, and
no dropped item was a reassurance. That is a **directional bias, not attrition**, and it is
invisible to every automated check here because each surviving sentence is individually true.

**The countermeasure is the `direction` column, not vigilance.** Recording whether each carried item
*qualifies a reassurance* or *states a risk* makes a one-way omission set detectable as a signal —
without needing to establish intent, which is neither knowable nor the point. A carried set whose
omissions all point one way is a finding on its own, whatever caused it.

`REVIEW.md` now requires the direction to be recorded when items are carried forward, and reviewer
records carry a `carried_forward` key with a direction per item.

## §D — the register was built against the wrong source, and nothing checks that

A separate mechanism from §C, and separately unrecorded.

This register was built against `carried_into_plan_3`. The dropped item came from
`standing_limitation`. **A register whose entire purpose is to prevent dropped obligations was built
against the one of two structures that did not contain the dropped obligation** — so it would have
reported four-of-four complete while the thing it existed to catch sat unregistered in the same
source record.

**A register is only as good as its source enumeration, and nothing checks the enumeration.** The
absence of a register is visible; a register built against an incomplete enumeration looks exactly
like a complete one. This will recur wherever a structured record can express an obligation in more
than one place — and reviewer records are free-form JSON, so there is no schema constraining where
a future reviewer puts one.

Partial mitigation, recorded honestly as partial: reviewer records now carry a top-level
`carried_forward` key, so *new* obligations have one conventional home. That does nothing for
records already written, and nothing for a reviewer who states an obligation in prose instead.
**Enumerating a source record's obligations remains a manual read of the whole record.**

## What this document does not do

It does not close Plan 3, and it does not discharge findings O1 or O2. It records the status of the
four Plan 2 items only, so that the next close review can check them by name instead of
reconstructing them from a prior record.
