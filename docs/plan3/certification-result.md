# Plan 3 certification — result (2026-07-22)

Command: `uv run conformalextract certify --i-have-reviewer-approval`
Artifact: `evidence/plan3/certification_result.json` (immutable, sha256
`71c0de3e953d758684b9bf88bef0f15ec5baa02967ac442f578f33a7f35af30f`)

> **Hash canonicalisation (correction C3).** That sha256 is over the **LF-normalised,
> git-canonical** bytes. A Windows working copy is checked out CRLF and hashes to
> `55237e5a…`. Both are the same artifact; verify with `git show HEAD:evidence/plan3/certification_result.json | sha256sum`
> rather than hashing the working-copy file, or an independent verifier on Windows will
> wrongly conclude it was altered.
Sealed certification split opened once: **3,152 documents / 1,396 groups**, access chain verified,
`final_reads: 0`, `shift_reads: 0`. Cost: $0.

## Headline

> **All three systems are Infeasible at α = 0.20, δ = 0.05, acceptance floor 0.20.
> H1 and H2 both return `both_infeasible`. No certified acceptance is claimed for any system.**

| System | status | reason | unweighted group loss | never-acceptable groups | ceiling |
|---|---|---|---|---|---|
| QA | **infeasible** | `no_jointly_feasible_candidate` | 0.6071 | 130 / 1,396 | 0.907 |
| ZS | **infeasible** | `no_jointly_feasible_candidate` | 0.9923 | 1,020 / 1,396 | 0.269 |
| FS | **infeasible** | `no_jointly_feasible_candidate` | 0.9580 | 684 / 1,396 | 0.510 |

The conservative Bonferroni audit (Construction B) agrees: infeasible for all three. QA's audit is
the closest any system came — 296 groups accepted, acceptance LCB 0.1825 (just under the 0.20
floor) with risk UCB 0.5157 (far over α = 0.20).

## The failure is a capability gap, not a methodological artifact

This is the important question, and the answer is unambiguous. Reproduce with:

```bash
uv run conformalextract risk-coverage-diagnostic
```

emitting `evidence/plan3/risk_coverage_diagnostic.json`. The diagnostic runs through the same
`certification_run.aggregate_to_groups` the certifier uses, so unit, eligibility, loss and score
are identical by construction; **no threshold is selected or certified** (plan §7.2 forbids
picking the empirically best point and calling it certified).

| System | empirical risk at 20% acceptance | max acceptance with **empirical** risk ≤ 0.20 |
|---|---|---|
| **QA** | **0.405** | **0.0201** |
| ZS | 0.983 | 0.0000 |
| FS | 0.930 | 0.0000 |

Read the QA row carefully. **With an infinitely fine grid, zero finite-sample penalty, and oracle
threshold selection, QA could accept at most 2.0% of documents at 20% error.** The floor demands
20%. The gap is an order of magnitude.

So the infeasibility is **not** caused by:

- the coarse 3-point grid (an unpenalised continuous sweep does no better);
- the δ/3 three-way split (the empirical curve carries no δ at all);
- the loose finite-sample bounds (these figures are pre-bound);
- a distribution difference between splits (QA's certification group loss 0.6071 vs development
  0.5898 — close, and in the expected direction).

The confidence score simply cannot isolate a 20%-sized subset of documents on which the model is
80% correct. At 20% acceptance QA's error is 0.405 — **twice the target**.

## What this means, stated honestly

**QLoRA produced a large, real improvement that did not reach the certification bar.** Plan 2
established QA's grounding advantage: 95.7% parseable-and-grounded against ZS 39.4% and FS 68.1%,
with ungrounded spans at 340 versus 5,355 — a ~16× separation. That is a genuine effect and it
survives. It is simply not sufficient for a *certified selective* guarantee at this target: being
well-formed and grounded is a much weaker property than being *correct*, and the certificate
scores correctness.

### Grounding improved sharply and certifiability not at all — measured, not asserted

> **Narrowed 2026-08-02.** This section was headed "Grounding and certifiability are orthogonal
> here". One intervention observed across three systems cannot establish that two properties are
> independent, and "orthogonal" asserted exactly that. What is measured is a **dissociation**: a
> large gain in the first produced almost none in the second. The numbers below are unchanged.

That last sentence was an interpretation when this document was first written. It is now a
measurement: `uv run conformalextract loss-decomposition` →
`evidence/plan3/loss_decomposition.json` (ADR 0011, $0, no new sealed access). Document loss splits
into four channels; the group-level contributions sum exactly to the certified quantity in the
table above, so this decomposes the certificate itself rather than a proxy for it.

| Certification split | QA | FS | ZS |
|---|---|---|---|
| structural failure (forced loss 1.0) | 0.7% | 0.4% | 2.3% |
| grounding failure (forced loss 1.0) | 4.1% | 32.3% | 58.0% |
| valid but contentless | 4.9% | 31.4% | 0.5% |
| **valid and content-bearing** | **90.3%** | **35.9%** | **39.3%** |
| mean loss *within* the content-bearing channel | **0.579** | 0.947 | 0.986 |
| group-level loss contributed by that channel | **0.530** / 0.607 | 0.354 / 0.958 | 0.404 / 0.992 |

The ~16× separation in ungrounded spans lives in the first three rows. The certificate scores the
fourth. **87% of QA's remaining loss (0.530 of 0.607) is grounded, well-formed, content-bearing
output that is simply wrong.**

> **Corrected 2026-07-29.** That sentence continued "— the coreference and entity-selection errors
> ADR 0007 catalogued (`victim = "she"` for `"Mrs. Clinton"`)". The appositive attributed the 87% to
> two named §12.1 error categories on the strength of an unquantified inspection of two development
> examples, which §12.3 forbids. It was a **stronger** form of the attribution withdrawn from
> `CX-GROUNDING-ORTHOGONAL-01` the same day, and it survived that correction because the search was
> for the retired phrasing and this is a paraphrase — the O2 mechanism reappearing inside the fix
> for O2.
>
> **The decomposition locates loss by channel and identifies no error category.** Two separate
> measurements point elsewhere, and they must not be run together — an earlier version of this note
> conflated them and stated a falsehood as a result.
>
> **Signature one, the excess.** False positives exceed false negatives by 637 arguments (4,434
> against 3,797): the system predicts more arguments than the gold contains. Both baselines run the
> other way, so it is QA-specific rather than a metric artefact. Note what this signature *cannot*
> show: `fp = predictions − tp` and `fn = gold − tp`, so `fp − fn = predictions − gold` identically,
> and **a substitution — wrong role, wrong boundary, wrong entity via coreference — produces one
> false positive and one false negative and contributes exactly zero.** The 637 is over-generation
> and nothing else.
>
> **Signature two, the co-occurrence.** 2,003 of 2,515 error-bearing documents show both a false
> positive and a false negative, which *is* consistent with substitution and rules out "mostly
> missing arguments". Wrong-role, boundary and coreference errors share **this** signature — not the
> one above.
>
> §12.1's machine-coded taxonomy is what would separate them and is ruled for execution
> ([`sections-11-and-12-disposition.md`](sections-11-and-12-disposition.md)) but has not been run.

The counterfactual states it directly. Give each system a **grounding oracle** — drop every
document outside the content-bearing channel, so the system is scored as though it never emitted
a structural failure, an ungrounded span or an empty frame, and measure coverage against that
restricted population:

| System | max acceptance at α = 0.20 | under the grounding oracle | movement | restricted mean loss |
|---|---|---|---|---|
| QA | 0.0201 | 0.0374 | +0.017 | 0.582 |
| FS | 0.0000 | 0.0000 | **+0.0000** | **0.951** |
| ZS | 0.0000 | 0.0000 | **+0.0000** | **0.984** |

**Removing 58% of ZS's documents' worth of grounding failure, and 32% of FS's, moves the
certifiable frontier by exactly nothing.** QA's frontier moves by 1.7 points and remains 5× short
of the 0.20 floor.

**The baselines' result does not depend on the counterfactual being fair, and it should not be
argued that way.** The restriction is *not* uniformly generous — dropping a low-loss member raises
a group's mean loss, and 24 FS groups and 21 QA groups do score worse under it — and a different
counterfactual (a correctness oracle) would move the baselines off zero. What carries the claim is
arithmetic. With losses in [0,1], accepting a fraction `c` at risk `α` requires a population mean
loss of at most `α·c + (1−c)` = **0.84** at `c = α = 0.20`, because the best achievable mean over
the best `c` fraction is `(μ − (1−c))/c`. ZS (0.984) and FS (0.951) exceed that ceiling on their
restricted populations, so **no selection rule of any kind** — oracle, certified, or otherwise —
reaches the floor for them. QA sits below the ceiling at 0.582, so for QA the ceiling is silent
and the measured curve is what leaves it short. Both readings are recorded as
`excluded_by_ceiling` and `groups_worsened_by_restriction` in the artifact.

So the QLoRA adapter's principal learned behaviour — grounding fidelity — **did not make low-risk
documents identifiable by the confidence score the certificate uses**. A 16× grounding gain left
certified acceptance where it was. This is the finding that does not appear in the prior work:
2606.29054 tests neither event-argument extraction nor the grounding/correctness distinction. Its
one extraction task (JSON-Extract, μ = 0.033) is a much easier regime than this one — a different
task under a different metric, so the comparison marks out a new operating regime rather than
contradicting their measurement.

**This is a dissociation, not an orthogonality result, and the difference is not pedantic.**
Orthogonality asserts independence, which one intervention across three systems cannot establish
and which nothing here tested. The measured statement is narrower and is all the evidence carries:
the gain in grounding was large and the change in certifiability was not.

**Nor is it a task-wide impossibility.** On the datasets 2606.29054 reports,
`(μ−α)/(1−α)` **forbids nothing** at μ = 0.033 and permits up to 80.5% acceptance at μ = 0.356
(`docs/frontier-check/findings.md`, re-verified 2026-07-22), so a 20% target is **not excluded** on
structured extraction at those base risks.

> **Corrected 2026-08-02 (review finding F1).** This paragraph said "demonstrably reachable". It is
> not: the impossibility bound is a **necessary** condition, and not being forbidden by it is not
> achievability — the same ruling-in direction this document forbids for the 0.406 frontier point
> three sections above. 2606.29054 in fact reports certification becoming practical only at
> α = 0.30–0.40 on its own tasks. "Not excluded" is what the evidence carries.

What is established here is that **this** model with **this** score on **this** task could not —
a model-and-score-specific result, not a statement about the task or the field. Any sentence that
reads otherwise is an overclaim of the kind finding O2 was raised about.

Caveats that travel with this: conditional coverage under the grounding oracle is **not** a
deployable acceptance rate — the restricted population differs per system, so those numbers are
not comparable across systems and support only the within-system question "does closing the
grounding gap reach the floor?". The decomposition selects no threshold and certifies nothing.

### The process failure: this was predictable at Phase A, for $0 (correction C2)

**The pre-registered prediction was directionally right and quantitatively wrong**, and the reason
matters more than the miss. ADR 0007 predicted QA `marginal` (base risk 0.5834 → max feasible
acceptance 0.465). The base-risk bound `(1−r)/(1−α)` is a *population* bound that assumes an
**oracle** confidence score, so it is necessary but nowhere near sufficient.

The same oracle diagnostic run on **development** — no sealed access, $0, available throughout
Phase A — already gave the answer:

| Split | QA risk at 20% acceptance | QA max acceptance at empirical risk ≤ 0.20 |
|---|---|---|
| **development** | **0.3826** | **3.02%** |
| certification | 0.4054 | 2.01% |

**Development already showed 3% against a 20% floor.** The infeasibility was fully knowable before
the sealed split was ever opened, and nobody ran the check — not the implementer, and not the
reviewer.

The ceiling was used as a *forecast* at three gates, and it was wrong at all three:

1. ADR 0007 calling QA `marginal`;
2. the Phase-A review endorsing that reading;
3. most concretely, the ADR 0009 review calling QA's 33.4%-acceptance threshold "inside the
   feasible region" **solely because 0.334 ≤ 0.465**, without checking the empirical risk at that
   acceptance — where it is ~0.40, twice α.

This is recorded as a joint failure because a lesson naming one party does not transfer. **The
durable form: the empirical risk–coverage curve on development settles selective feasibility, costs
nothing, and requires no sealed data. The base-risk ceiling does not — it bounds what an oracle
score could do, not what the actual score does.** `conformalextract risk-coverage-diagnostic` now
exists so this check is a command, not a habit; it should be run on development *before* any
certification is attempted.

**H1 and H2 are `both_infeasible`, and the collapse pre-registration applies.** No numerical
difference is invented against an infeasible baseline (§8.2), and the two hypotheses must not be
reported as two independent confirmatory comparisons. There is one finding, not two.

## Caveats that remain attached

- **The certificate bounds average within-group error** (ADR 0009), not absence of error.
- **ADR 0008's confidence-span contamination is not merely outweighed here — it is irrelevant to
  this outcome** (sharpened at review, correction C1). Its only channel was depressing `CA_FS`,
  i.e. making the *baseline* look worse. H2 did not fail on the baseline side; it failed on the
  **QA** side, because QA itself is infeasible. The confound was therefore **bypassed by the
  failure mode**, not tested and found immaterial. "Clean negative" is right but understates it:
  no correction to FS's score could change `both_infeasible`, because `CA_QA` is null regardless
  of what FS does.
- Unweighted vs size-weighted group loss agree to within 0.0002–0.0011 on the certification split,
  so the document-level reading a reader will naturally take is not misleading here (amendment A2).
- Scoped to the frozen vLLM 4-bit serving stack; portability is not established (probe: 86.3%
  parsed-output parity).
- **α = 0.20 with a 20% floor is a deployment threshold, not a natural constant** — it is the
  operating point this project committed to before opening any sealed label (ADR 0007), and it
  stays the headline target, and [§6.2 of the accepted plan](accepted-plan.md) binds tightly here:
  for the "all systems far above `alpha`" branch — this one — it says *do not relax `alpha` after
  seeing certification*. Nothing below relaxes it. What licenses publishing the curve is §9.1:
  *"An infeasible system remains infeasible; its descriptive risk–coverage curve may be plotted but
  no test threshold is selected."* All three are infeasible and no threshold is selected. (§9.1 sits
  under the final-evaluation stage ADR 0010 descoped, so this is a read-across; the conditions are
  met literally but the section's own stage was never run.) The whole
  frontier is now published rather than described: `evidence/plan3/alpha_frontier.json`
  (`uv run conformalextract alpha-frontier`, ADR 0011) reports the oracle risk–coverage curve
  read at every α, and no certificate is issued at any of them.

  | System | **empirical oracle frontier point** — α at which the 20% floor first becomes oracle-reachable (certification split) |
  |---|---|
  | **QA** | **0.406** |
  | FS | 0.930 |
  | ZS | 0.981 |

  **These are empirical oracle frontier points, not thresholds.** They were computed *after* the
  certification split was opened, from that split's own labels, so each describes where this
  measured population's curve crosses the floor and nothing more. No threshold was selected at
  0.406 or anywhere else, and no certificate was issued at any of them. Calling 0.406 a threshold
  would imply a certificate that does not exist.

  Read that as the answer to "you picked the one α where it fails": you did not need to pick.
  The curve is an oracle **upper** bound on what any threshold rule could achieve, so below
  α ≈ 0.406 **no** certificate at any threshold could have cleared the floor for the best system —
  the entire range is ruled out without a certificate being computed anywhere in it.

  **The crossing is a necessary condition, not a sufficient one, and must never be read as an α
  that would work.** It carries no finite-sample penalty, no grid and no multiplicity correction.
  A certificate at α ≈ 0.406 would still not issue: at the ~280 groups a 20% acceptance implies,
  the Hoeffding radius alone is 0.086 at the per-system allocation δ/3 and 0.103 under the
  family-wide Bonferroni δ/(2·9), so the risk upper bound would land at roughly 0.49–0.51 — over
  the target it was being measured against, before any other bound is applied. The curve rules
  operating points **out**. It never rules one in, and no claim from this project may use it in
  that direction.

## What may and may not be claimed (fixed at review)

**Permitted:**

- Report the Plan 2 grounding result (95.7% vs ZS 39.4% / FS 68.1%) **in the same document and the
  same passage as the null** — suppressing it would be its own distortion — framed as: a large,
  real improvement in grounding fidelity that **did not translate into a certified selective
  guarantee**, because well-formed-and-grounded is a much weaker property than correct, and the
  certificate scores correctness.
- **One** finding, not two (H1/H2 collapsed).
- The oracle risk–coverage diagnostic, as evidence the failure is capability rather than method.
- **(ADR 0011)** The α-frontier, stated as: below α ≈ 0.406 no certificate at any threshold could
  have cleared the 20% floor for the best system. It is an oracle upper bound and may only be used
  in that ruling-out direction — never to suggest what *would* certify above it. 0.406 is an
  **empirical oracle frontier point, never a threshold**.
- **(ADR 0011)** The grounding **dissociation**: a ~16× grounding gain moved the certifiable
  frontier by +0.017 for QA and by 0.000 for both baselines, with 87% of QA's residual loss in
  grounded, content-bearing output. Reported with the restricted-population caveat attached.
- That the null is **model-and-score-specific**: a 20% target is **not excluded** on structured
  extraction at the base risks prior work reports (μ = 0.033, μ = 0.356). **What put it out of
  reach here is not μ alone** — at μ = 0.6071 the bound still permits 49.1% acceptance, far above
  the floor. Infeasibility here is **overdetermined**, and all three parts must be stated together:
  (i) base risk, which alone forbids the floor for ZS and FS but *not* for QA; (ii) **ranking** —
  the score reached 2.0% where a perfect ranking of the same population reaches 23.6%; and
  (iii) the **finite-sample penalty** — that same perfect ranking certifies only 11.4% at δ/3
  (8.4% family-wide), still below the floor, and the measured score certifies 0.0%.

  > **Corrected 2026-08-02 (review finding F1).** This bullet read "this system's μ = 0.6071 is
  > what put it out of reach here". That is false on this repository's own bound and re-commits
  > exactly the base-risk-as-forecast error `CX-FEASIBILITY-LESSON-01` exists to record — the
  > ceiling bounds what an ORACLE score could do and is not a forecast of certifiability.

**Forbidden — in both directions:**

| Overclaiming the null | Overclaiming the positive |
|---|---|
| "QLoRA doesn't work" | 95.7% in an abstract, CV line or slide that can be quoted **without the null attached** |
| Any hint that a laxer α would certify — the frontier rules α values **out**, it never rules one in | Any QA-over-baseline **certified margin** (none exists) |
| Generalising past the frozen vLLM 4-bit stack (86.3% parity) or past in-domain RAMS | Calling grounding validity "accuracy" |
| Presenting the α-frontier or the grounding oracle as a certificate — both are oracle diagnostics that select no threshold | Quoting grounding-oracle coverage as a deployable acceptance rate, or comparing it across systems |
| Claiming we discovered that CRC cannot certify extraction — that is 2606.29054's result, not ours | Claiming μ ≈ 0.60 replicates their extraction base risk, or that it refutes it — their JSON-Extract 0.033 is a different task under a different metric, so ours marks out a harder regime and settles nothing about their number |
| Any **task-wide or field-wide** impossibility reading. α ≤ 0.20 is **not excluded** on structured extraction at the base risks prior work reports — not the same as reachable — and this is a model-and-score-specific result *(added 2026-08-02; "is reachable" corrected to "not excluded" 2026-08-03, finding F1)* | — |
| Calling **0.406** a threshold, a certified operating point, or anything other than an empirical oracle frontier point measured on an already-opened split *(added 2026-08-02)* | — |
| Describing grounding and certifiability as **orthogonal**, **independent**, or **unrelated**. The measured relation is a dissociation; independence was never tested *(added 2026-08-02)* | — |
| Attributing the null to base risk **alone**. At μ = 0.6071 the bound permits 49.1%; infeasibility is overdetermined by base risk, ranking AND the finite-sample penalty *(added 2026-08-02)* | — |
| Reading the **empirical** oracle acceptance (0.2357) as something that could have been certified, or saying the floor "was reachable". Certified, that oracle is 0.1139 at δ/3 — below the floor. Only `acceptance_certified_loss_optimal` licenses the word "certified" *(added 2026-08-02)* | — |

## Status

A **first-class publishable negative result** under the `CLAUDE.md` honesty boundary:
infeasibility was a pre-declared possible outcome, the procedure was built to be able to return
it, and it did. No certified-acceptance claim may be made for any system.

Independent post-execution review: **PASS** (`evidence/plan3/reviewer_record.certification.json`)
— the result is what it says it is, verified by re-deriving the risk–coverage curve through the
implementer's own aggregation. Four corrections (C1–C4) are incorporated above. Publication of any
derived claim remains gated on those corrections and on the reviewer's stated claim boundaries.

`evaluate-final` and `evaluate-shift` are **descoped** — see `docs/adr/0010-descope-final-and-shift.md`.
