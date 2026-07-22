# Plan 3 certification — result (2026-07-22)

Command: `uv run conformalextract certify --i-have-reviewer-approval`
Artifact: `evidence/plan3/certification_result.json` (immutable, sha256 `71c0de3e…`)
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

This is the important question, and the answer is unambiguous. Diagnostic on the certification
split, **with no threshold selected or certified** (plan §7.2 forbids picking the empirically
best point and calling it certified):

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

**The pre-registered prediction was directionally right and quantitatively wrong, in an
instructive way.** ADR 0007 predicted QA `marginal` (base risk 0.5834 → max feasible acceptance
0.465) and both baselines `near_vacuous`. The baselines behaved exactly as predicted. QA did not:
the base-risk bound `(1−r)/(1−α)` is a *population* bound that assumes an **oracle** confidence
score, so it is necessary but nowhere near sufficient. QA's real score delivers 2.0% where the
oracle bound allowed 46.5%. **Base-risk feasibility should not be read as a forecast of
certifiability** — a lesson worth carrying into any future plan.

**H1 and H2 are `both_infeasible`, and the collapse pre-registration applies.** No numerical
difference is invented against an infeasible baseline (§8.2), and the two hypotheses must not be
reported as two independent confirmatory comparisons. There is one finding, not two.

## Caveats that remain attached

- **The certificate bounds average within-group error** (ADR 0009), not absence of error.
- **ADR 0008's confidence-span contamination stands**, but note its effect here: it biased *toward*
  H2 support, and H2 was **not** supported. Per ADR 0008's pre-registered cap, that makes this a
  **clean negative** — the contamination cannot explain a null it was pushing against.
- Unweighted vs size-weighted group loss agree to within 0.0002–0.0011 on the certification split,
  so the document-level reading a reader will naturally take is not misleading here (amendment A2).
- Scoped to the frozen vLLM 4-bit serving stack; portability is not established (probe: 86.3%
  parsed-output parity).
- α = 0.20 with a 20% floor is one operating point. This result says nothing about whether a
  laxer target would certify — and per §6.3 the headline target **must not** be relaxed after
  seeing this.

## Status

This is a **first-class publishable negative result** under the `CLAUDE.md` honesty boundary:
infeasibility was a pre-declared possible outcome, the procedure was built to be able to return
it, and it did. No certified-acceptance claim may be made for any system. The result requires
independent review before any claim derived from it is published.
