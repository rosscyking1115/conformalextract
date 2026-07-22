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
- α = 0.20 with a 20% floor is one operating point. This result says nothing about whether a
  laxer target would certify — and per §6.3 the headline target **must not** be relaxed after
  seeing this.

## What may and may not be claimed (fixed at review)

**Permitted:**

- Report the Plan 2 grounding result (95.7% vs ZS 39.4% / FS 68.1%) **in the same document and the
  same passage as the null** — suppressing it would be its own distortion — framed as: a large,
  real improvement in grounding fidelity that **did not translate into a certified selective
  guarantee**, because well-formed-and-grounded is a much weaker property than correct, and the
  certificate scores correctness.
- **One** finding, not two (H1/H2 collapsed).
- The oracle risk–coverage diagnostic, as evidence the failure is capability rather than method.

**Forbidden — in both directions:**

| Overclaiming the null | Overclaiming the positive |
|---|---|
| "QLoRA doesn't work" | 95.7% in an abstract, CV line or slide that can be quoted **without the null attached** |
| Any hint that a laxer α would certify | Any QA-over-baseline **certified margin** (none exists) |
| Generalising past the frozen vLLM 4-bit stack (86.3% parity) or past in-domain RAMS | Calling grounding validity "accuracy" |

## Status

A **first-class publishable negative result** under the `CLAUDE.md` honesty boundary:
infeasibility was a pre-declared possible outcome, the procedure was built to be able to return
it, and it did. No certified-acceptance claim may be made for any system.

Independent post-execution review: **PASS** (`evidence/plan3/reviewer_record.certification.json`)
— the result is what it says it is, verified by re-deriving the risk–coverage curve through the
implementer's own aggregation. Four corrections (C1–C4) are incorporated above. Publication of any
derived claim remains gated on those corrections and on the reviewer's stated claim boundaries.

`evaluate-final` and `evaluate-shift` are **descoped** — see `docs/adr/0010-descope-final-and-shift.md`.
