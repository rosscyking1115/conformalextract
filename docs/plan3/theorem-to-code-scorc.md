# Theorem-to-code note — SCoRC certifier vs arXiv 2606.08517 (gate G1b/G1c)

Verifies `src/conformalextract/certification.py::scorc_certificate` against the preferred
method, "A Joint Finite-Sample Certificate for Adaptive Selective Conformal Risk Control"
(arXiv 2606.08517, Theorem 1 / Algorithm 1 / Table 2 δ-ledger). Source fetched 2026-07-18
(`https://arxiv.org/html/2606.08517v1`). The paper is a 2026 preprint — treat theorem/line
numbers as version-specific.

## Verdict (corrected 2026-07-18 after fetching Algorithm 1 in full)

**Our `scorc_certificate` implements Algorithm 1 correctly and completely — there is NO
missing-bound implementation gap.** An earlier draft of this note flagged the two Chernoff
accepted-count bounds (U3, U4) as "missing / blocks certified." That was wrong, and this
correction records why: **U3/U4 are proof-only devices — Algorithm 1 never computes them.**
The implementable algorithm is exactly Line 5 (empirical-Bernstein `EB`), Line 6 (Clopper–Pearson
`p_LCB`), Line 7 (utility `U_LCB`), Line 9 feasibility (`EB≤0 ∧ p_LCB≥π_min`), then
`argmax_{Ĝ} U_LCB`. Our code matches every line. The eligible set `ℋ={p_acc≥π_min}` and the
Chernoff events E3/E4 depend on the unknown population `p_acc` and appear only in the proof's
union bound (Table 2 δ-ledger), not in the computed certificate. So U3/U4 must NOT be added to
the code — doing so would diverge from the paper's algorithm.

**The remaining genuine items are (a) one reporting faithfulness point and (b) empirical
validation** — neither blocks the algorithm's validity, but both should be settled before any
"certified" wording.

## Component-by-component

Paper Table 2 (δ-ledger), per candidate pair over a grid of size `m`:

| Event | Bound | Per-pair δ | Our code | Status |
|---|---|---|---|---|
| U1 | Two-sided Maurer–Pontil / empirical-Bernstein on `Z=A(L−α)` | δ/(16m) | `risk_log=log(64m/δ)`; `eb = Z̄ + √(2σ̂²·risk_log/n) + 7·risk_log/(3(n−1))` | **match** (log-arg `64m/δ` = the paper's two-sided M-P at δ/(32m) per tail) |
| U2 | Clopper–Pearson acceptance coverage | δ/(16m) | `beta.ppf(δ/(16m), count, n−count+1)` | **match** |
| U3 | Chernoff lower-tail on accepted count `{s ≥ (3/4)·n·p_acc}`, over eligible set ℋ | δ/(16m) | not computed | **correct** — proof-only (depends on unknown `p_acc`); Algorithm 1 never computes it |
| U4 | Chernoff upper-tail on accepted count `{s ≤ (3/2)·n·p_acc}`, over ℋ | δ/(16m) | not computed | **correct** — proof-only |
| U6 | Two-sided Maurer–Pontil on deployment utility `U_LCB` (v=1, c=0 → utility = acceptance) | δ/(2m) | `utility_log=log(8m/δ)`; symmetric M-P lower bound on the accept indicator | **match** |
| — | Sample size (Assumption 5) `n ≥ 32·log(32m/δ)/π_min` | — | `scorc_minimum_n = ceil(32·log(32m/δ)/floor)` | **match** |
| — | Selector `argmax_{Ĝ} U_LCB` (Alg. 1 L9–14) | — | `max(feasible, key=(utility_lower, −index))` | **match** |

Paper total failure budget `U1+U2+U3+U4+U6 = δ/16+δ/16+δ/16+δ/16+δ/2 = 3δ/4 ≤ δ`. Algorithm 1
consumes this budget **in the proof**; the code computes only the U1/U2/U6 quantities because
U3/U4 are population-restricted proof events, not computed outputs. The δ/16 shares for U3/U4 are
"spent" analytically to license the risk guarantee, not by any runtime check — so the correct
implementation does exactly what our code does.

## G1b — reporting faithfulness (was mis-flagged as a gap; now: minor, verify)

- **No missing bound.** Algorithm 1's feasibility (`EB ≤ 0 ∧ p_LCB ≥ π_min`) is fully implemented.
- **The one real reporting item:** Algorithm 1 does **not** output a numeric selected-risk upper
  bound — Theorem 1 proves `R_sel ≤ α` for any returned (feasible) pair, so the **certified upper
  bound is α**. Our code additionally returns `risk_upper = α + eb/acceptance_LCB` (line ~216),
  a self-derived quantity not in the algorithm. It is `≤ α` for feasible pairs and is a *valid
  conservative* ratio upper bound when both `E[Z] ≤ eb` (U1) and `E[A] ≥ acceptance_LCB` (U2)
  hold — since for `eb ≤ 0`, `sup_{E[A]∈[p_LCB,1]} eb/E[A] = eb/p_LCB`. So it is not wrong, but it
  goes beyond what Theorem 1 states. **Recommendation:** report the certified bound as `α`
  (Theorem-1-exact) and expose `α + eb/p_LCB` as a clearly-labeled *conservative diagnostic*, not
  as "the certified bound"; the empirical selected risk is already reported separately. This is a
  reporting/wording choice for Gate 0, not an algorithm change; the existing test only asserts
  `risk_upper ≤ 0.2`, which either representation satisfies.
- **What actually needs doing before a "certified" claim:** the empirical **coverage validation**
  below (this, not U3/U4, is what proves the certifier controls risk).

## G1c — selector reconciliation (documentation fix)

- **Code and paper agree:** deploy `argmax U_LCB` over `Ĝ`. No code change needed.
- **The mismatch is smaller than it looked.** Our utility uses `v=1, c=0`, so `u_dep = A` (the
  accept indicator) and `U_LCB` is a **Maurer–Pontil lower bound on the acceptance rate**. The code's
  `argmax U_LCB` therefore already maximizes an acceptance-based lower bound — close to the plan's
  intent. The subtlety: the feasibility/reported acceptance bound is **Clopper–Pearson** (`p_LCB`)
  while the *selector* uses the **M-P** acceptance lower bound (`U_LCB`); two different valid lower
  bounds on the same quantity. Plan §7.3/§8.1 says "select by max acceptance_LCB" and defines
  `CA_s = max acceptance_LCB`. Reconcile as:
  - **Deployed policy** = `argmax U_LCB` (paper/code).
  - **Headline comparison object** `CA_s` = `max` over `Ĝ` of `acceptance_LCB` is **also valid**
    because the guarantee holds *uniformly* over `Ĝ` (every pair's acceptance LCB is simultaneously
    covered), so reporting the best certified acceptance across `Ĝ` is licensed.
  - **But** the current code returns only the utility-selected pair's `acceptance_lower`, not the
    max over `Ĝ`. If §8.1's `CA_s` (max acceptance-LCB) is the headline, the certifier must also
    expose `max_{Ĝ} acceptance_LCB`. Decide and make plan ↔ code ↔ reported-number consistent.

## Exchangeability vs independence for a size-dependent group aggregate (ADR 0009, A3)

Settled here at the reviewer's instruction, because ADR 0009's group score is a **minimum over a
variable-size cluster** and is therefore size-dependent. Measured on development:
`corr(size, min-score) = −0.3527`, monotone in size (median min-score −0.0574 at size 1 →
−0.1079 at size 7+). A minimum over more draws is stochastically lower, so a uniform threshold
preferentially accepts small groups.

**What the theorem actually requires.** Algorithm 1's three computed bounds are empirical-Bernstein
(Maurer–Pontil) on `Z = A(L−α)`, Clopper–Pearson on the accepted count, and Maurer–Pontil on
utility. Each is stated for **i.i.d. draws** of bounded variables — Clopper–Pearson in particular
needs the accepted count to be Binomial, which fails under per-unit heterogeneous accept
probabilities (it would be Poisson-binomial).

**Why the size-dependence does not violate this.** The i.i.d. requirement is over *draws of
groups from the population of source-document clusters*. Group size is an **attribute of the
draw**, not a source of cross-unit heterogeneity: each certification row is one i.i.d. draw of a
cluster, carrying whatever size that cluster has. Accept is a deterministic function of the draw,
so the accept indicators are i.i.d. Bernoulli(`p_acc`) with `p_acc` the acceptance probability
**marginalised over the population size distribution** — Binomial, and Clopper–Pearson is exact.
Likewise `Z_i` are i.i.d. as deterministic functions of i.i.d. draws, so Maurer–Pontil applies.
The size-conditional variation is population structure, not a sampling violation.

**Conclusion: independence + bounded loss + identical marginal distribution over draws is what is
needed, and it holds.** A size-dependent aggregate is inside scope.

**Two consequences that must nonetheless be reported** (they are scope statements, not defects):

1. **The accepted set skews small-group.** The certificate is still valid, but the accepted
   population is not a uniform sample of the group population. The artifact emits the accepted
   set's size distribution so this is visible rather than inferred.
2. **The guarantee is scoped to the natural group-size mixture of this corpus.** It is a statement
   about exchangeable deployment units drawn from a population with *this* clustering structure.
   A deployment whose near-duplicate structure differs — more or fewer large clusters — is outside
   the scope, in the same way as any other distribution shift.

## Recommended validation additions (from the frontier check)

Mirror 2606.29054 / 2512.12844 practice: Monte Carlo over resplits in a VALID (`μ<α`) and a
deliberately-INVALID (`μ>α`) regime, reporting test-violation counts vs the δ budget; and a
**negative control** — naive max-raw-acceptance threshold selection violates `α` while the
certified selector does not.
