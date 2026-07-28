# ADR 0012: CX-COST-01 cited a forecast; the cost claim is re-evidenced and re-worded

- Status: accepted
- Date: 2026-07-28
- Reviewed: `evidence/plan4/reviewer_record.cost-claim.json` (independent, 2026-07-28 — BLOCK on the
  first draft for publishing a total below the supported band; PASS-WITH-NITS on the discharge)
- Trigger: the independent review of the README status correction
  (`evidence/plan4/reviewer_record.readme-status.json`, 2026-07-28) found, while checking a
  different item, that `CX-COST-01`'s `evidence` array points at a **forecast** rather than at a
  record of spend. That reviewer recorded it as "a ledger defect the README inherits rather than
  creates", ruled that the README's ~$19 figure was faithful to the ledger wording and corroborated
  by `evidence/plan2/reviewer_record.plan2-close.json` and so **may stand**, raised and saw
  discharged a separate required item on cost-recording precision, and carried the ledger-citation
  defect forward for "a future claims review". This ADR is that review.

## The defect

`CX-COST-01` asserted that the programme "cost approximately $19 against a $25 ceiling" and cited
two documents: `docs/plan2/g2b-result.md` and `docs/plan2/serving-equivalence-probe-result.md`.

The first is a **cost forecast**. Its table projects $18.26 of $24.7992 at a 256-token output cap;
it records one actual figure (~$0.10, for the G2b job itself) and nothing else. The second records
two probe costs totalling $0.526. Together the cited evidence supports about **$0.63** of a **$19**
claim.

Its `method` field said "per-job durations and flavour rates recorded in each run's evidence
artifact" and its `limitations` said "individual job costs are recorded exactly". Neither was true
as stated. There is no per-job cost artifact for Plan 2, and no cost anywhere in this repository is
recorded to the cent from a billing statement.

The number itself was never wrong. It is corroborated — by
`evidence/plan2/reviewer_record.plan2-close.json` ("~$6.0 of $24.7992 remains unspent"), and by
re-summing the per-job figures. What failed is the chain from the claim to something a reader can
check, which is the only thing the ledger exists to hold.

**The corroborating reviewer record was deliberately not added to the `evidence` array.** A close
record that mentions a remaining balance is not a spend ledger, and citing it would have made the
claim look sourced while leaving the actual defect — no per-job spend record for Plan 2 — in place.
Making a citation resolve is not the same as making a claim evidenced.

## What the repository actually holds

**Gate 0 (Plan 1)** — a genuine per-job artifact,
`evidence/gate0/hf_jobs_submission_attempts.json`, ten attempts. They are **not** uniform, and the
first draft of this ADR described them as though they were: four GPU runs carry
`estimated_charge_usd` $0.05 each; four CPU preflights carry `estimated_charge_upper_bound_usd`
$0.0002 each, which are bounds rather than products (at $0.01/hr for 9s the product is $0.000025);
and two attempts were never scheduled at all, carrying no job id, no duration and
`charge_incurred_usd: 0.00`. The entries sum to **$0.2008**, which is exactly the figure
`training.REMAINING_BUDGET_USD` (24.7992) subtracts from the $25 cap. That reconciliation is the
strongest cost evidence in the repository, and the ledger did not cite it.

The rounding is upward throughout — L40S at $1.80/hr for 96s is $0.048, recorded as $0.05 — so the
direction is safe, but "price × duration" is a description of intent rather than of what the
artifact shows.

**Plan 2** — eight jobs, costs recorded as **prose** in each run's launch-brief or result document:

| Job | Document | Recorded |
|---|---|---|
| `6a5bcee6bee6ee1cf4ecfe08` R0 inference benchmark | `docs/plan2/r0-launch-plan.md` | **no cost stated** |
| `6a5d517ed216bd6f3a2021f1` R0 re-run at real distribution | `docs/plan2/r0-launch-plan.md` | ≈ $0.10 |
| `6a5d58e6d216bd6f3a2022c3` R1 QLoRA pilot | `docs/plan2/r1-launch-brief.md` | ≈ $0.40 |
| `6a5d5e98d216bd6f3a202357` R2 QLoRA full | `docs/plan2/r2-launch-brief.md` | ≈ $6.00 |
| `6a5e397ed09dc1f57c6bd562` G2b serving benchmark | `docs/plan2/g2b-result.md` | ~ $0.10 |
| `6a5e5724d09dc1f57c6bd938` prediction generation | `docs/plan2/reviewer-brief-extraction-policy.md` | ~ $11.2 |
| `6a5fa55913e6ef894d549ee7` probe v1 | `docs/plan2/serving-equivalence-probe-result.md` | $0.046 |
| `6a5fab15d09dc1f57c6bfb68` probe v2 | `docs/plan2/serving-equivalence-probe-result.md` | $0.48 |

Recorded Plan 2 subtotal **$18.33**, plus Gate 0 **$0.2008**, gives **$18.53** — plus one job whose
cost was never written down per-job.

Note where the largest single figure lives: the ~$11.2 prediction-generation cost, 60% of the
programme, is recorded in a *reviewer brief about extraction policy*. It is committed and it is
checkable, but nothing about that document's name or purpose would lead a reader to it.

**Running totals — four more actual-spend records, which the first draft of this ADR missed:**

| Document | Recorded |
|---|---|
| `docs/plan2/r1-launch-brief.md:50` | "~$0.45 spent so far" |
| `docs/plan2/r2-launch-brief.md:61` | "Programme spend to date ≈ $6.85 of $24.7992" |
| `docs/plan2/g2b-result.md:17` | "spend-to-date ~$7.00" |
| `docs/plan2/prediction-generation-launch-brief.md:54` | "remaining budget $17.80 of $24.7992" |

**Missing them is what made the first draft's total too low**, and the correction is the
substantive one this review produced. The first R0 benchmark's cost is not unrecoverable: it falls
out of the running totals by subtraction. From the R1 brief, $0.45 − $0.2008 − $0.10 = **$0.149**;
from the R2 brief, $6.85 − $0.2008 − $0.10 − $0.40 − $6.00 = **$0.149**. Two independently written
documents agree to the tenth of a cent.

That reading assumes the running totals include Gate 0. They admit a second reading — "of $24.7992"
is the post-Gate-0 remaining budget, so a total measured against it may exclude Gate 0's $0.2008,
which puts the R0 benchmark at **$0.35** instead. Both readings are internally consistent across
both documents and nothing in the repository settles which was meant.

Total is therefore **$18.68 under the first reading and $18.88 under the second**, and it is
published as that band. Picking either endpoint would be choosing the convenient one, and the low
endpoint is the convenient one here.

**"18 attempts" is a floor, not a count** (found at discharge review). `docs/plan2/r0-launch-plan.md`
lines 19–22 record fixes that were needed "to make it run" — the slim uv image lacking `nvcc`, the
flashinfer sampler, vLLM 0.25.x's positional token-prompt format. Those are discoverable only by a
job that reached GPU execution, and a job that reached GPU execution was billed. No id and no cost
exists for it anywhere. So the recovered $0.15–$0.35 bounds **all** unrecorded pre-R1 spend rather
than isolating one job.

This does not move the published figure, and the reason is worth stating: the running totals record
money, not attempts, so they capture unrecorded jobs whether or not anyone counted them. It is a
further argument for the band — a point estimate would have implied a completeness the attempt
inventory does not have.

## Decision

**Both available remedies apply, because the defect is both a mis-citation and an over-claim.**

1. **Fix the citations.** `evidence` now lists the eight documents that actually record a job's cost
   or a running total, Gate 0's artifact first.
2. **Re-word the claim to what those documents support.** "Cost approximately $19" implied a
   measured total. It is now "recorded job by job and sums to between about $18.7 and $18.9 …
   each figure derived from the instance's hourly price and the job's measured duration rather than
   from a billing statement".
3. **State the five limits** that were previously absent or wrong: these are operator estimates and
   not billed amounts; no single spend ledger exists and the total is assembled by a reader across
   six documents; one paid job has no per-job figure and is recovered by inference from two running
   totals; the individual figures are themselves rounded, so the total is stated to one decimal
   place and not to the cent; and free-tier and local compute are excluded.

The figure moves from a point to a **band** because a band is what the records support. "$19" was
never wrong — it sits above the band, and rounding up is the safe direction for a spend claim.
What was wrong was that it could not be reproduced from the cited documents.

**The first draft of this ADR published "about $18.5", and that was the error worth recording
here.** It did not merely fail to find the figure — it **asserted unrecoverability as a positive
statement**, in its own "What this ADR does not do" section, and then omitted the job on that
basis. That put the published total *below* the supported band, and below the "$19" it replaced. For a cost claim measured against a fixed ceiling, understatement is the unsafe
direction: it flatters the project's budget discipline and overstates its remaining headroom. This
document stated that rule in the paragraph above and then broke it two paragraphs later. It was
caught by the independent review (`evidence/plan4/reviewer_record.cost-claim.json`, BLOCK), which
found the recovery by following citations *this change had itself just added*.

## What this ADR does not do

- **It does not create a spend ledger.** The right fix is a committed per-job artifact for Plan 2
  in the shape Gate 0 already has, ideally emitted by `TrainingRunLedger`, which exists in
  `training.py` with an `actual_cost_usd` field and is **never serialised anywhere**. That is new
  engineering and it would need its own review. It would not retroactively produce a per-job
  *record* for the first R0 benchmark — though the figure itself is recoverable at $0.15–$0.35 by
  differencing the running totals above, which is how the total is completed. Recorded here as open
  rather than done.
- **It does not reconcile against billing.** Nobody has compared any figure to a Hugging Face
  invoice. Until someone does, "cost" in this repository means price × duration.
- **It changes no other claim.** `verify-claims` reports 14 claims / 12 publishable before and
  after.

## Lesson

The pattern is the one ADR 0011 §6 records for the pending tripwire, in a new place: a check that
*runs* is not a check that *bites*. `verify-claims` confirmed `CX-COST-01`'s evidence paths existed
and were git-tracked, and both conditions were true — of the wrong documents. Existence and
tracking are checkable mechanically; **whether a cited document supports the sentence pointing at
it is not**, and no amount of green output substitutes for a reader opening the file.

This one was found by a reviewer who had been asked about something else and followed a citation
anyway.

**The second lesson is sharper, because this ADR's own first draft supplied it.** Adding citations
is not the same as reading them. The two documents that recover the "unrecoverable" figure were
added to the `evidence` array *by this change*, and the draft that added them still published a
total that omitted the figure they contain. It is possible to fix a citation defect and inherit its
consequence in the same commit. The durable form: after re-citing, re-derive the number **from the
new citations**, not from the arithmetic that was already in hand.
