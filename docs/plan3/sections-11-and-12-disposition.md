# Plan 3 §11 and §12 — disposition of every sub-item

- Date: 2026-07-29
- Raised as **O1** by the independent review that refused to close Plan 3
  ([`../../evidence/plan3/reviewer_record.plan3-close.json`](../../evidence/plan3/reviewer_record.plan3-close.json))
- Ruled by Ross. **Status: proposed dispositions, pending independent review.** Plan 3 does not
  close on this document alone.

## The defect this addresses

§11 and §12 were **neither executed nor descoped**. ADR 0010 descopes only `evaluate-final`,
`evaluate-shift` and `render-report`, and its stated reason — no selected policy exists to audit or
transport — does not reach every item here.

**The defect is not that items were skipped. It is that mootness was assumed rather than ruled.**
A bare list of dispositions would reproduce that in a tidier form, so every sub-item below carries
its reasoning, and where an item is moot the reason it is moot is stated rather than implied.

The recurring reason is worth stating once. The certification returned **Infeasible for all three
systems**, so there is **no accepted set** — no system has a certified operating point, and no
threshold was selected. Any analysis whose unit is "the accepted outputs" has an empty input. That
is a real mootness, but it is a *consequence of the result*, not a licence to skip work, and it does
not reach analyses that run on all predictions regardless of acceptance.

---

## §11.1 Predeclared analyses

| Sub-item | Disposition | Reasoning |
|---|---|---|
| mean vs maximum-frame document loss | **NOT executed — descoped, on a corrected ground** | **Corrected twice on review.** R3: the first version marked it *executed*, which was wrong — amendment A2 delivered *unweighted vs size-weighted group* loss, a comparison across groups, where §4.1's item is *maximum frame loss per document*, within a document. Different quantity, different level; nothing matching `max_frame` exists. R6: the second version descoped it on a **§8.5 post-hoc-rescue ground, which the plan contradicts** — §4.1 *predeclares* max-frame loss, so it is not post-hoc, and it is a strictly **harsher** loss, so it cannot rescue a failed hypothesis. Descoped instead on the honest ground: it is a sensitivity analysis on a result that is infeasible under the *lenient* loss, so the harsher one cannot change the conclusion, and running it would add a number without adding a finding. **Not descoped for cost** — it is $0 — and if Plan 3's close review wants it, it is cheap to run. |
| exact vs normalized grounded-span matching | **descoped** | Span matching is frozen by the Plan 1 task contract and ADR 0006's extraction policy; changing it after seeing the result would re-score the certified object. §8.5 forbids exactly this class of post-hoc re-scoring. Descoped on that ground, not for effort. |
| binary strict-failure certificate/interval | **moot — empty input** | §5.2 defines the strict loss as a *secondary* certificate. A certificate requires a feasible candidate; none exists for any system. Running it would return `infeasible` three times and add nothing to a null already established on the primary loss. |
| primary score vs completion-mean-NLL score | **descoped** | Descriptive-only by the item's own terms unless jointly corrected. The primary score has already been shown incapable of isolating a 20%-loss subset at any acceptance (`CX-CAPGAP-01`, 2.0% oracle acceptance). A second score would be measured against the same oracle ceiling, and §8.5 forbids reporting an alternative score as a rescue of a failed hypothesis. |
| accepted-output quality by cross-sentence distance and argument count | **moot — empty input** | The unit is *accepted* outputs. Nothing is accepted. |
| deterministic constrained decoding | **moot — precondition unmet** | The item is conditional on Plan 1 having admitted constrained decoding as a structural-validity ablation. It did not; ADR 0002 descoped training ablations to a single seed. The condition never fired. |

## §11.2 Subgroup reporting

**Moot — empty input.** Subgroup reporting is scoped to accepted outputs and to intervals that are
exploratory unless separately predeclared. With no accepted set there are no subgroup outcomes to
report. **Note what is *not* claimed here:** subgroup analysis of *loss* across all predictions is
possible and is not being done — it is descoped as out of scope for a null, not impossible.

> **Superseded 2026-10-27.** Disposed axis by axis in [Amendment 2](sections-11-and-12-disposition-amendment-2.md).

## §11.3 Calibration diagnostics

| Sub-item | Disposition | Reasoning |
|---|---|---|
| score–loss Spearman association | **descoped** | Not run. The question it answers — does the score rank loss usefully — is answered more directly and more conservatively by the oracle risk–coverage curve already committed, which bounds what *any* threshold rule could achieve. A rank correlation could only be weaker evidence for the same conclusion. |
| AUROC/AUPRC for the strict-failure indicator | **descoped** | Same ground. Gate 0E reported a confidence AUC on a 20-group smoke and explicitly marked it provisional and not frozen; extending it now would be a new statistic on an already-open split, after the result. |
| binned confidence/risk diagrams with counts | **descoped** | Descriptive presentation of the same object the risk–coverage curve carries. `docs/plan3/certification-result.md` and `evidence/plan3/alpha_frontier.json` already publish the whole curve. |
| selective-risk curves | **executed** | This is `risk-coverage-diagnostic` and `alpha-frontier`, both committed with immutable artifacts. |

## §11.4 Multiplicity

**Executed, and observed throughout.** H1 and H2 are the only confirmatory comparisons and collapse
to one finding; threshold adaptivity is handled inside the certification procedure (SCoRC); the
α-frontier is labelled `diagnostic_only` and `certifies_nothing`; no subgroup claim exists to carry
an uncorrected p-value. ADR 0011 §1 engages §8.5 explicitly on the sweep.

---

## §12.1 Machine-coded taxonomy — **TO BE EXECUTED**

> **Superseded 2026-10-27.** This ruling never ran. [Amendment 2](sections-11-and-12-disposition-amendment-2.md) descopes §12.1
> from Plan 3, disposes §11.2 axis by axis, and re-disposes §12.2's two computable strata.
> The text below is kept as the record of the 2026-07-29 ruling.

**Ruled: execute.** It runs against committed prediction artifacts and RAMS gold, needs no accepted
policy set, and is the only route to substantiating an error-category claim.

**Cost verified before starting, as required: $0.** All three prediction files
(`data/private/plan2/predictions/{zs,fs,qa}.v1.jsonl`) and RAMS gold are present locally. The
taxonomy is deterministic categorisation of existing predictions against gold — **no model
inference, no GPU, no Hugging Face job.** The $25 cap is untouched.

**Why descoping it was refused:** `CX-GROUNDING-ORTHOGONAL-01` carried an error-category attribution
on README, report and abstract surfaces. Descoping §12.1 would have stranded that claim permanently
— it could never be substantiated afterwards, only reworded downward.

**Ordering, which is deliberate.** The claim was **reworded first** (finding O2, same day) to state
only what the decomposition measures. §12.1 runs against the reworded claim, so its output cannot be
read as confirming the wording it was run to test. If the taxonomy supports a stronger statement,
that is a new claim requiring its own review.

## §12.2 Manual audit sample

**Moot in part, descoped in part** — and the parts differ, so they are ruled separately.

- *10 QA improvements over both baselines / 10 QA regressions / 10 abstained low-loss cases* —
  **moot**: three of the six strata are defined relative to an accepted set that does not exist.
- *10 high-confidence/high-loss accepted cases* — **moot**: no accepted cases.
- *10 shift-only failures* — **moot**: shift is descoped and sealed (ADR 0010).
- The remaining audit — **descoped**. With five of six strata empty, the frozen stratified sample
  the section requires cannot be constructed as specified, and constructing a different sample after
  seeing the result is precisely what "frozen before reading examples" exists to prevent.

> **Superseded 2026-10-27.** [Amendment 2](sections-11-and-12-disposition-amendment-2.md) re-disposes the two computable strata. The
> counts above are also wrong: §12.2 lists five strata and one sampling rule, not six strata.

## §12.3 Error attribution limits

**Executed as a binding constraint, and it bound.** This section is the authority under which O2 was
raised: it forbids claiming a failure type from a few examples without a designed causal test, and
the withdrawn "names the wrong entity" attribution rested on two development examples. §12.3 did its
job; what failed was that nobody applied it when the claim was written.

---

## What this document does not do

- It does not close Plan 3. O2 and O3 are routed separately, and §12.1 has not yet run.
- It does not descope anything on grounds of cost or effort. Every descope above is on a
  methodological ground, and where the ground is "the result made this empty", that is said plainly.
- It does not create new claims. Any finding from §12.1 will need its own ledger entry and review.
