# Theorem-to-code note — SCoRC certifier vs arXiv 2606.08517 (gate G1b/G1c)

Verifies `src/conformalextract/certification.py::scorc_certificate` against the preferred
method, "A Joint Finite-Sample Certificate for Adaptive Selective Conformal Risk Control"
(arXiv 2606.08517, Theorem 1 / Algorithm 1 / Table 2 δ-ledger). Source fetched 2026-07-18
(`https://arxiv.org/html/2606.08517v1`). The paper is a 2026 preprint — treat theorem/line
numbers as version-specific.

## Verdict

**One genuine gap that blocks an unqualified "certified via Theorem 1" claim: the certifier
omits the two Chernoff bounds on the accepted count (U3, U4).** Every other component matches
the paper exactly. Resolve before any "certified" wording (not before the generation run, since
the certifier is CPU and runs after predictions — but a run is only worth paying for if it can
end in a valid certificate).

## Component-by-component

Paper Table 2 (δ-ledger), per candidate pair over a grid of size `m`:

| Event | Bound | Per-pair δ | Our code | Status |
|---|---|---|---|---|
| U1 | Two-sided Maurer–Pontil / empirical-Bernstein on `Z=A(L−α)` | δ/(16m) | `risk_log=log(64m/δ)`; `eb = Z̄ + √(2σ̂²·risk_log/n) + 7·risk_log/(3(n−1))` | **match** (log-arg `64m/δ` = the paper's two-sided M-P at δ/(32m) per tail) |
| U2 | Clopper–Pearson acceptance coverage | δ/(16m) | `beta.ppf(δ/(16m), count, n−count+1)` | **match** |
| U3 | **Chernoff lower-tail on accepted count** `{s ≥ (3/4)·n·p_acc}`, over eligible set ℋ | δ/(16m) | **absent** | **MISSING** |
| U4 | **Chernoff upper-tail on accepted count** `{s ≤ (3/2)·n·p_acc}`, over ℋ | δ/(16m) | **absent** | **MISSING** |
| U6 | Two-sided Maurer–Pontil on deployment utility | δ/(2m) | `utility_log=log(8m/δ)`; symmetric M-P lower bound | **match** |
| — | Sample size (Assumption 5) `n ≥ 32·log(32m/δ)/π_min` | — | `scorc_minimum_n = ceil(32·log(32m/δ)/floor)` | **match** |
| — | Selector `argmax_{Ĝ} U_LCB` (Alg. 1 L9–14) | — | `max(feasible, key=(utility_lower, −index))` | **match** |

Paper total failure budget `U1+U2+U3+U4+U6 = δ/16+δ/16+δ/16+δ/16+δ/2 = 3δ/4 ≤ δ`.
Our code's realised budget `U1+U2+U6 = δ/16+δ/16+δ/2 = 5δ/8` — it *under-spends* δ, but that is
not the issue: it omits the U3/U4 **correctness** events, which the paper states are "required
for correctness, not for budget savings" and which make the ratio denominator `E[A]` concentrate
so the reported conditional risk (`risk_upper = α + eb/acceptance_LCB`, our line ~216) is valid.

## G1b — the U3/U4 gap (OPEN, blocks "certified")

- **Fact:** `scorc_certificate` never bounds the accepted count `s` against `(3/4)·n·p_acc` /
  `(3/2)·n·p_acc`. Feasibility is decided by `eb ≤ 0 ∧ acceptance_LCB ≥ floor` only.
- **Why it may still be *partly* sound:** the feasibility test `eb ≤ 0` bounds `E[Z]=E[A(L−α)]`
  directly (Z is bounded in `[−α, 1−α]`), which already implies selected risk `E[AL]/E[A] ≤ α`
  when `E[A]>0`. So the *feasibility decision* for risk may not need U3/U4.
- **Why it is still a gap:** the paper's **joint** guarantee and the **reported** conditional
  `risk_upper` (which divides by the acceptance LCB) rely on the denominator concentration that
  U3/U4 provide. Reproducing "the paper's Theorem 1 certificate" requires them; omitting them
  means our object is a *related* certificate whose exact validity must be re-proven for the
  specialization, not the paper's.
- **Fix path (needs Algorithm 1 lines 5–8, not on the fetched page):** either (a) add U3/U4 as
  Chernoff bounds on `accepted_counts` at δ/(16m) each, restricted to the eligible set
  `ℋ={acceptance_LCB ≥ floor}`, and wire them into the reported risk_upper per the paper's
  algorithm; then re-validate with Monte Carlo (valid + deliberately-invalid regimes); OR
  (b) write a proof that the fixed-output-policy specialization's `eb ≤ 0` feasibility plus the
  Clopper–Pearson acceptance LCB is self-sufficient and drop the denominator-based `risk_upper`
  in favour of the directly-bounded quantity. **Do not ship a "certified" claim until (a) or (b).**

## G1c — selector reconciliation (documentation fix)

- **Code and paper agree:** deploy `argmax U_LCB` over `Ĝ`. No code change needed.
- **Plan wording is the mismatch.** Plan §7.3/§8.1 says "select the feasible candidate with the
  largest acceptance LCB" and defines `CA_s = max acceptance_LCB`. Reconcile as:
  - **Deployed policy** = `argmax U_LCB` (paper/code).
  - **Headline comparison object** `CA_s` = `max` over `Ĝ` of `acceptance_LCB` is **also valid**
    because the guarantee holds *uniformly* over `Ĝ` (every pair's acceptance LCB is simultaneously
    covered), so reporting the best certified acceptance across `Ĝ` is licensed.
  - **But** the current code returns only the utility-selected pair's `acceptance_lower`, not the
    max over `Ĝ`. If §8.1's `CA_s` (max acceptance-LCB) is the headline, the certifier must also
    expose `max_{Ĝ} acceptance_LCB`. Decide and make plan ↔ code ↔ reported-number consistent.

## Recommended validation additions (from the frontier check)

Mirror 2606.29054 / 2512.12844 practice: Monte Carlo over resplits in a VALID (`μ<α`) and a
deliberately-INVALID (`μ>α`) regime, reporting test-violation counts vs the δ budget; and a
**negative control** — naive max-raw-acceptance threshold selection violates `α` while the
certified selector does not.
