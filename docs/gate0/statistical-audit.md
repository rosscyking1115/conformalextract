# Gate 0 statistical reproduction and audit

## Headline method

The preferred implementation follows the joint finite-grid SCoRC construction from arXiv
2606.08517. A row is one independent duplicate/source group. A candidate is a frozen
system/confidence/threshold policy. With document loss `L`, acceptance `A`, and target `alpha`, the
implementation bounds `Z = A(L - alpha)` simultaneously across the finite grid, applies a one-sided
Clopper–Pearson acceptance lower bound, and maximizes the lower confidence bound on acceptance only
within the jointly feasible set. Empty feasible sets return `Infeasible`.

The theorem precondition is:

```text
n >= ceil(32 * log(32 * m / delta) / acceptance_floor)
```

The actual RAMS inventory contains 3,988 independent groups. A 10% certification allocation gives
only 398 groups and cannot support even one candidate (minimum 1,034). The revised 35% allocation
provides at least 1,395 groups; nine global candidates require 1,386. This nine-group margin must be
rechecked after weighted deterministic split assignment.

## Conservative audit

The audit certifies a policy selected only on development data. Accepted bounded losses use a
one-sided Hoeffding UCB; the acceptance probability uses a one-sided Clopper–Pearson LCB. Failure
probability is Bonferroni-allocated across every family and both bounds. Zero accepted documents can
never certify. No feasible candidate is an explicit negative result.

## Paper findings

- Conformal Risk Control (arXiv 2208.02814) is an expectation guarantee under monotonicity; it is not
  substituted for the required one-sided selective certificate.
- The non-monotonic CRC preprint (arXiv 2604.01502) has a displayed finite-sample expression whose
  worked table could not be reconciled directly. Its result is not used as the headline method until
  this discrepancy is resolved against source code.
- The structured-generation limits preprint (arXiv 2606.29054) is retained as a feasibility warning.
  Universal Bernstein-vs-Hoeffding nesting is false at small sample sizes because of the additive
  finite-sample term. The repository tests only computed, regime-specific nesting.
- Adaptive testing of multiple thresholds at full `delta` is rejected. Development chooses the score
  and constructs the grid; the joint theorem or an explicit multiplicity ledger handles certification.

All cited papers are recent preprints. Code-level worked examples and Monte Carlo coverage, not
authority, determine Gate 0D.

