# Amendment 2 to the §11 and §12 disposition — §12.1 descoped, §11.2 disposed axis by axis

- Date: 2026-10-27
- Amends: [`sections-11-and-12-disposition.md`](sections-11-and-12-disposition.md) (2026-07-29) and
  [Amendment 1](sections-11-and-12-disposition-amendment-1.md) (2026-08-02)
- Raised by: the Plan 3 close-chain review of 2026-10-27, step 1
  ([`../../evidence/plan3/reviewer_record.plan3-close-chain.json`](../../evidence/plan3/reviewer_record.plan3-close-chain.json)),
  blocking items S1-B1 and S1-B2, required items S1-R1 to S1-R4
- **The §12.1 choice was made by Ross on 2026-10-27:** "go with a, descope 12.1" — option (a) of
  S1-B1.
- **Status: proposed, pending independent review.** Plan 3 does not close on this document.
  Nothing here creates a claim; one ledger limitation and three prose surfaces change to match it
  (listed at the end).

## §12.1 Machine-coded taxonomy — **descoped from Plan 3** (S1-B1)

The 2026-07-29 disposition ruled §12.1 **to be executed**. It never ran: the 2026-07-30
certification-only scope addendum passed review but authorised no execution, set seven
preconditions and recorded that no command existed, and none has been written since. A ruling to
run that has not run is neither an execution nor a descope, and a close cannot be issued over it.
This amendment makes it a descope.

**Not descoped for cost.** It is computable at $0 — deterministic categorisation of committed
predictions against gold, with no inference, GPU or Hugging Face job — and that is said so that
nobody later reads the descope as a budget decision.

**The ground.** The 2026-07-29 refusal to descope rested on one thing: `CX-GROUNDING-ORTHOGONAL-01`
then carried an error-category attribution on README, report and abstract surfaces, and descoping
§12.1 would have stranded it. **That ground no longer exists.** O2 narrowed the claim the same day
to what the loss decomposition measures, and the close-chain review ruled the later narrowing a
separate finding (O2-S1) and discharged it (step 5). No live claim on any surface attributes QA's
loss to an error category, so the taxonomy has nothing left to substantiate. Running it now would
produce a new finding requiring its own claim and its own review — new Plan 3 work, not the closing
of an open item.

**Consequence, stated once so no surface states it differently:** *Plan 3 makes no error-category
claim.* The two measured signatures — the 637-argument false-positive excess, and the co-occurrence
of a false positive and a false negative in 2,003 of 2,515 error-bearing documents — stay recorded
as measurements. What would separate the error types they are consistent with is not run.

**The 2026-07-30 scope addendum** stays in the repository unedited — it is admitted byte-for-byte
and may not be edited — as a reviewed scope text. It is now inert: it constrained an execution that
will not happen under Plan 3. If a later plan runs the taxonomy, the addendum's preconditions are
the place to start.

**§22 checklist.** The line *"Failure taxonomy/manual audit and all result artifacts are
generated"* is **waived in its first half**: the taxonomy is descoped here and the manual audit by
§12.2 below. Its second half — all result artifacts generated — is not waived and is a matter for
the close review.

## §11.2 Subgroup reporting — each axis (S1-B2)

The base document disposed §11.2 as a whole ("moot — empty input"), and Amendment 1 reversed its
"not being done" note by executing one axis. The plan names five; each is disposed here.

| Axis (§11.2) | Disposition | Reasoning |
|---|---|---|
| event type | **descoped** | Computable on all predictions, but §11.2 makes every subgroup interval exploratory and reportable only above a displayed minimum, and no minimum was predeclared. Choosing one now, after the result, decides which event types are shown. No claim depends on a per-event-type figure, and none could change an infeasibility that holds on the whole split. |
| role | **descoped** | The certified unit is the document group and its loss is not decomposed by role; a per-role reading needs argument-level scoring by role, which is new analysis rather than reporting. The committed `argument_error_counts.json` aggregates over roles and is not offered as this item. |
| document-length quartile | **descoped** | Computable; same ground as event type. Two correlates of document complexity were executed — cross-sentence distance below, and trigger count — which bear on the question but are **not** this item and are not offered as it. |
| cross-sentence distance | **executed** | Amendment 1, stratification finding 2, over all groups rather than an accepted set. Exploratory, as §11.2 requires. |
| seen/unseen schema | **moot — split descoped** | The seen/unseen-schema distinction belongs to the shift stress test (§10), and shift is descoped and sealed by ADR 0010. The certification split has no unseen-schema stratum to report. |

**Trigger count is an addition, not a §11.2 item.** Amendment 1's first stratification finding
groups by trigger count, which §11.2 does not list. It is reported as exploratory and must not be
cited as having discharged any §11.2 axis.

## §12.2 Manual audit sample — the two computable strata (S1-R1)

The base document called *10 QA improvements over both baselines* and *10 QA regressions* moot as
"defined relative to an accepted set". **That is not in the plan text**, which defines neither by
acceptance (`accepted-plan.md` §12.2), and the refusal record listed both as computable. The
mootness claim is withdrawn and the five strata are re-disposed:

- *10 QA improvements over both baselines*, *10 QA regressions* — **computable, descoped.** The
  audit "explains failure mechanisms"; its output is attribution of the kind §12.3 limits, and with
  §12.1 descoped there is no category vocabulary to sample "all categories" across and no
  error-category claim for it to explain. A ten-case sample would add examples without adding a
  finding the plan could state.
- *10 high-confidence/high-loss accepted cases* — moot: nothing is accepted.
- *10 abstained low-loss cases* — moot: no threshold was selected, so nothing is abstained.
- *10 shift-only failures* — moot: shift is descoped and sealed (ADR 0010).

Three strata are empty and two are descoped, so the frozen stratified sample is not constructed.
The base document's "five of six strata" miscounted: §12.2 lists five strata and one sampling rule.

## §11.3 — two things Amendment 1 did not state (S1-R2, S1-R3)

- **The split deviates from the plan.** §11.3 says "use development/final data". The diagnostics
  were computed on **certification**, with a development replication; final is sealed by ADR 0010
  and was not read. The certification split was already open from the single 2026-07-22 opening, so
  no new label access occurred, but it is a deviation and is recorded as one. ECE, which §11.3 makes
  optional, was not shown.
- **The empirical-Bernstein verification**, completing v2 F-G. The `empirical_bernstein_probe` in
  `certification_sensitivity.json` runs a single pre-chosen oracle candidate through
  `scorc_certificate` at the full δ with no multiplicity. It returns **infeasible at every coverage
  tested** (k = 139, 279, 329 and 559), so the certified acceptance is 0.0000 throughout. The probe
  is one-sided by construction: a perfect ranking, one candidate and no δ split all favour the
  system, so it can only overstate what a real policy could certify — and it still certifies
  nothing.

## The strict-failure indicator — the step 3 ruling, item by item (S1-R4)

The close-chain review took the cheap ruling: **there is no predeclared strict-failure loss in this
programme.** Plan 1 §237 required its exact definition to be frozen before calibration; it never
was, and calibration ran on 2026-07-22. A definition written now would be chosen after the labels
opened and after three indicators' AUROCs were committed, which §8.5 forbids. It is a Plan 1 defect,
not repairable after calibration, and the dependent Plan 3 items are disposed accordingly:

| Plan 3 item | Disposition |
|---|---|
| §5.2 secondary strict-loss certificate | **unavailable** — no predeclared loss to certify |
| §11.1 row 3, binary strict-failure certificate/interval | **unavailable** — the base document's "moot — empty input" is a second, also-true ground; this is the first |
| §11.3 AUROC/AUPRC for the predeclared strict-failure indicator | **unavailable** — Amendment 1's three indicators (`above_alpha`, `any_error`, `not_all_valid`) are **exploratory and not predeclared**, and none may be called the strict-failure indicator |
| §9 strict failure rate | **unavailable**, and moot in any case: final evaluation is descoped (ADR 0010) |

The `CX-RANKING-01` limitation recording that its AUROC uses an exploratory indicator was added in
`44ed212`. Amendment 1's "What was NOT reversed" now points here.

## What changes to match this amendment

- `evidence/plan4/claim_ledger.json`, `CX-GROUNDING-ORTHOGONAL-01`: the limitation saying §12.1
  "has not been run" now states the descope; the generated claims appendix is regenerated.
- [`certification-result.md`](certification-result.md): the sentence saying §12.1 "is ruled for
  execution … but has not been run" gets a dated note recording the descope.
- [`../writeup/draft-2026-07-28.md`](../writeup/draft-2026-07-28.md): the "open decision" sentence
  is closed by dated note.
- [`accepted-plan.md`](accepted-plan.md) §12.1, §12.2 and §22: an appended, dated note pointing
  here, with the pin in `tests/test_doc_references.py` moved in the same commit. Plan 1 §237
  ([`../gate0/accepted-plan.md`](../gate0/accepted-plan.md)) gets a dated note recording the
  strict-failure defect, likewise re-pinned.
- The base disposition's §12.1 heading and Amendment 1's "What was NOT reversed" gain pointers here.

## What this document does not do

- It does not close Plan 3. Steps 2, 4 and 5 have their own open items, C1 (the two 2026-08-03
  packets whose verdicts were never filed) is not addressed here, and step 6 has not started.
- It does not run anything. Every disposition above is a ruling on existing evidence; no number in
  it is new.
- It does not descope on cost. Every descoped item is $0 to compute, and each carries the
  methodological reason it is not computed.
