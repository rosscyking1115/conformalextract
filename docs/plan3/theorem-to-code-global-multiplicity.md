# Theorem-to-code note — global multiplicity across {ZS,FS,QA} × thresholds (Plan 3 §5.5)

Companion to `docs/plan3/theorem-to-code-scorc.md`. That note verified the **within-system**
certificate (Theorem 1 of arXiv 2606.08517 gives a joint guarantee over one system's threshold
grid, licensing adaptive `argmax U_LCB` selection). This note settles the **cross-system**
question §5.5 raises: the candidate family is `{ZS, FS, QA} × {their frozen thresholds}`, and
"the failure budget [must] cover adaptive selection across thresholds **and across the three
systems**."

Status: **analysis complete; the allocation choice is a Gate-0 freeze that needs review sign-off
before `certify` runs.** No sealed label is touched by anything here.

## 1. What Theorem 1 does not give us

Theorem 1 controls, with probability ≥ 1−δ, *all* candidate bounds **within a single system's
grid** simultaneously. It says nothing about running the procedure on three systems and then
comparing or selecting across them. Concretely, if we run three independent per-system
certificates each at budget δ, the event "at least one of the three certificates is invalid"
can have probability up to 3δ, not δ. The primary comparison (§8.2: `CA_QA ≥ CA_ZS + δ_material`,
and §8.3 for FS) reads three certified quantities off three certificates at once, so all three
must be simultaneously valid. A cross-system correction is therefore mandatory, exactly as §5.5
anticipates.

## 2. Construction A — union bound across systems (the "allocate δ" path)

Predeclare weights `δ_QA, δ_ZS, δ_FS ≥ 0` with `δ_QA + δ_ZS + δ_FS = δ`. Run each system's
SCoRC certificate at its own budget `δ_s` (Theorem 1 handles that system's within-grid
multiplicity at `δ_s`). Let `V_s` be the event "every bound in system s's `δ_s`-ledger holds."
Theorem 1 gives `P(V_s) ≥ 1 − δ_s`, so

> `P(V_QA ∩ V_ZS ∩ V_FS) ≥ 1 − (δ_QA + δ_ZS + δ_FS) = 1 − δ`.

On that event **every** `(system, threshold)` acceptance-LCB is a valid lower bound and **every**
selected policy's selected-risk is ≤ α. This is stronger than we need, and that strength is the
point:

- **It covers the pairwise H1/H2 comparisons** — `CA_QA`, `CA_ZS`, `CA_FS` are all simultaneously
  valid, so `CA_QA ≥ CA_ZS + δ_material` is a comparison of jointly-valid certified quantities.
- **It also covers any max-over-systems reporting** — because the guarantee is uniform over the
  whole fixed family, any post-hoc function of the certified quantities (including
  `argmax_s CA_s`) is simultaneously licensed. This is the "verified global conservative
  construction" §5.5 offers as the alternative to a bespoke procedure: a union bound over a
  *predeclared* family needs no adaptivity penalty beyond `Σδ_s = δ`.
- **`CA_s = max over that system's grid of acceptance_LCB` (§8.1) is within `δ_s`, not extra.**
  Taking the max over QA's own thresholds is covered by QA's within-system joint guarantee
  (see the SCoRC note, G1c); it does not consume additional cross-system budget.

Construction A is valid for **any** predeclared non-negative weights summing to δ. The only open
choice is the weights.

### 2.1 The weights, and what they cost in grid resolution

Grid size is bounded by the theorem's sample-size precondition at the *effective* per-system δ.
At n = 1,396 certification groups, floor 0.20 (computed via `largest_scorc_grid`):

| Allocation | δ per system | Max certifiable candidates / system |
|---|---|---|
| (no split — invalid across systems, shown for reference) | 0.05 | 9 |
| **Equal split δ/3** | 0.0167 each | **3** (ZS, FS, QA all) |
| QA-weighted δ/2 : δ/4 : δ/4 | QA 0.025; ZS/FS 0.0125 | QA **4**, ZS/FS **2** |

The finite-sample theorem is **grid-starved at this n**: even the whole δ budget on one system
buys only 9 thresholds, and splitting three ways drops each system to 3 (of which one is
always-answer). This is a real property of the sample size, not a modelling choice, and it must
be stated plainly in any results table — the acceptance sweep is coarse.

### 2.2 Recommended weights: equal δ/3

Recommend **equal δ/3**. Rationale, in order of weight:

1. **Symmetric and assumption-free.** No system is advantaged by the budget; the allocation
   cannot be read as tuned to help QA clear H1/H2. Under the honesty boundary this is the
   unimpeachable default.
2. **The QA-weighted gain is marginal.** δ/2 buys QA 4 candidates vs 3 — one extra abstention
   threshold. That is unlikely to change a feasible/infeasible verdict, and it costs the
   symmetric defensibility in (1).
3. **A QA-weighted split is nonetheless *valid* and *available*** if Gate 0 judges the
   development base-risk prediction (ZS/FS near-vacuous, QA marginal — ADR 0007) strong enough
   to justify concentrating resolution where a feasible certificate is possible. Grid resolution
   only helps a *feasible* system; a coarse grid detects infeasibility just as well. If chosen,
   it must be frozen here, before labels open, with that rationale recorded. **This note does not
   pre-empt that call — it recommends δ/3 and flags the weighted option for review.**

## 3. Construction B — global conservative Bonferroni (finer grid, looser bounds)

The plan already ships a second certifier, `conservative_certificate` (Hoeffding + Clopper–
Pearson + Bonferroni). It takes a `family_size` and has **no `scorc_minimum_n` sample-size
floor**, so it can certify an arbitrarily fine grid — the cost is only a `log(family_size)`
term in the Hoeffding radius. Set `family_size = 3 × (thresholds per system)` to cover the whole
`{ZS,FS,QA} × thresholds` family in one budget δ. Illustrative Hoeffding half-widths (n_accepted
= 500, δ = 0.05):

| Thresholds/system | family_size | Hoeffding half-width |
|---|---|---|
| 3 | 9 | 0.0767 |
| 9 | 27 | 0.0836 |
| 20 | 60 | 0.0882 |

The half-width grows only ~0.007 going from 9 to 60 candidates — **Construction B is nearly
insensitive to grid size**, so it can afford the fine grid Construction A cannot. Its per-candidate
bound is looser than SCoRC's empirical-Bernstein for a given (n, δ), but SCoRC's advantage is
data-dependent (it wins when accepted-loss variance is low), and we cannot know that before the
sealed split opens.

Which wins for QA's certified acceptance is therefore **genuinely undetermined pre-data**: A has
tighter bounds on a coarse grid; B has looser bounds on a fine grid. A feasible operating point
that A's 3-point grid steps over, B's 9-point grid may hit.

## 4. Why not combine them

Running both and reporting the better `CA_s` is a selection over two methods and needs its own
factor-2 correction. So **do not** take `max(A, B)` for the headline. Instead predeclare one as
primary and the other as a secondary descriptive robustness check — the same discipline §6.3
applies to the risk-target sweep (single confirmatory α; the sweep is descriptive).

## 5. Recommendation (for Gate-0 freeze / review)

1. **Primary, headline:** Construction A (per-system SCoRC), **equal δ/3 split**. SCoRC is the
   plan's preferred method; the δ/3 split is symmetric and covers H1/H2 and any max-over-systems
   claim. Headline `CA_s` come from here.
2. **Secondary, descriptive:** Construction B (global conservative Bonferroni) at a finer grid
   (e.g. 9 thresholds/system, `family_size = 27`), reported alongside as a grid-rich robustness
   view — **not** combined into the headline.
3. Both are predeclared and frozen now, before certification labels open. The higher-resolution
   B view guards against the real risk that A's coarse 3-point grid is too crude to locate QA's
   feasible frontier.

## 6. Code and configuration consequences

- **Grid rebuild at the effective δ.** `evidence/plan2/threshold_grids.json` was built at
  δ = 0.05 (9 candidates/system). Under δ/3 the SCoRC grids must be rebuilt at δ = 0.0167 →
  3 candidates/system: `conformalextract build-grid --delta 0.0166666667`. The δ = 0.05 grid is
  retained for Construction B. `build_threshold_grid`'s `n_groups`/`delta` guard already refuses
  an over-sized grid, so a wrong δ fails loudly rather than silently over-certifying.
- **`certify` runs three per-system SCoRC calls at `δ_s`**, not one call at δ. Each call's
  `candidate_count` is that system's certifiable grid size; the paper's within-grid ledger is
  already implemented (SCoRC note). The command must also run Construction B over the pooled
  family for the secondary view.
- **The allocation must be bound into the analysis version.** `analysis_version.certification_config_hash`
  currently hashes α/δ/floor/material_gain/bootstrap/candidate. It must be extended to include the
  **allocation scheme** (weights + which construction is primary), so a change of allocation
  produces a new `analysis_id` and can never be silently swapped after the fact.
- No change to `scorc_certificate` or `conservative_certificate` themselves — both already
  implement what each construction needs. This is a wiring-and-freeze decision, not new theory.

## 7. Reviewer ruling and binding conditions (2026-07-21)

Ruled **ADOPT with conditions** (`evidence/plan3/reviewer_record.phase-a.json`). The reviewer
independently reproduced all four grid claims (9 / 4 / 3 / 2 at n=1396), endorsed δ/3 after
building and rejecting the case against it (QA-weighted buys one extra threshold while creating
an allocation readable as tuned to help QA; certifying QA alone at full δ was also rejected
because the baselines' certification-split certificates carry evidentiary value a development
extrapolation does not), and confirmed the union-bound argument. Binding conditions:

1. **The union bound licenses comparing certified *bounds*, not a certified *difference*.**
   H1/H2 must be phrased as a comparison of jointly-valid certified acceptances — not as a
   confidence statement about `CA_QA − CA_ZS`. No interval on the difference is claimed.
2. **Construction A is fixed before running.** The primary construction and the δ/3 allocation
   are frozen here and bound into `analysis_id` via
   `analysis_version.certification_config_hash(delta_allocation=..., primary_construction=...)`.
3. **Both constructions are reported unconditionally**, whatever they show. B is never used to
   support a claim A does not support; A is never quietly dropped if B looks better.
4. **A coarse null is not a model result.** If certification returns infeasible or no material
   gain, it may **not** be reported as "QLoRA did not certify" without stating the true grid
   resolution. **Corrected at re-review — the original wording ("~two usable thresholds per
   system") understated the problem.** Measured against each system's feasible region on
   development data:

   | System | thresholds | inside the feasible region |
   |---|---|---|
   | QA | −inf (acc 0.955), −0.0695 (acc 0.641), **−0.0453 (acc 0.330)** | **exactly 1** |
   | ZS | acc 0.389 / 0.285 / 0.127 | 0 (max feasible acceptance is 0) |
   | FS | acc 0.659 / 0.475 / 0.244 | 0 (max feasible acceptance is 0) |

   **QA has exactly one usable operating point** — the minimum for a non-vacuous certificate.
   Grid starvation at n=1396 is a property of the design, not of the model, and this is the
   number that must be stated.

## 7a. Pre-registered: H1 and H2 collapse to a single test

Recorded **before** the sealed split opens, so it is not discovered afterwards.

Base-risk feasibility (ADR 0007) puts `CA_ZS = CA_FS = Infeasible`, and the grid measurement
above shows no ZS or FS threshold lands in a feasible region. If that holds on the certification
split, then `CA_ZS = CA_FS = 0` **by construction**, and both hypotheses reduce to the same
statement:

> `CA_QA ≥ 0.05`

H1 and H2 are then **one single-system threshold test stated twice** — the baselines contribute
only a zero. Consequences, binding:

- They **must not** be reported as two independent confirmatory comparisons; doing so would
  overstate the evidence by counting one test twice.
- The `boundary_crossing` outcome that `compare_certified_acceptance` will emit is the correct
  and honest encoding (§8.2 forbids inventing a numerical difference against an infeasible
  baseline) — but the write-up must say plainly that the comparison degenerated, not present a
  crossing as though a contested margin had been won.
- Given QA's single usable threshold, the achievable claim is narrow and its shape is known in
  advance: *at one frozen threshold, QA accepts ≈33% of documents with certified risk ≤ α at
  1−δ confidence, where neither baseline can certify at any threshold.* That is worth
  establishing on sealed data, and it is all that is on offer.

## 8. Still a decision, not invented here

The **weights** (δ/3 vs QA-weighted) and **which construction is primary** are Gate-0 freezes
that change the headline guarantee, so they require the same independent review as any evaluation
change (`CLAUDE.md`). This note verifies that each option is *valid* and quantifies its grid
cost; it recommends δ/3-primary + conservative-secondary but does not unilaterally freeze it.
Nothing here reads a certification, final, or shift label.
