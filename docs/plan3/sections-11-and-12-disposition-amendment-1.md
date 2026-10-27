# Amendment 1 to the §11 and §12 disposition — three §11.3 rows reversed and executed

- Date: 2026-08-02
- Amends: [`sections-11-and-12-disposition.md`](sections-11-and-12-disposition.md) (2026-07-29)
- Raised by: the owner's publication-sprint plan of 2026-08-02, §4 (held outside this repository)
- **Status: REVISED after independent review, 2026-08-02. Not discharged.** The review returned
  **REVISE** and refuted one of this document's own findings; the correction is in
  “What it found” below. Nothing here may reach a public surface, and Plan 3 does not close on
  this document.
  - *Updated 2026-10-27.* After the unfiled v3 and v4 rounds, the fresh independent review of
    this document (`../../evidence/plan3/reviewer_record.c1-2026-08-03-packets.json`) returned **PASS-WITH-NITS**; its four nits are applied below
    by dated note. This note does not lift the public-surface restriction above: whether
    `CX-RANKING-01` may stay on the paper's abstract is an open owner decision.
- Artifact produced: [`../../evidence/plan3/calibration_diagnostics.json`](../../evidence/plan3/calibration_diagnostics.json)
  (`sha256 a69da67c5b014af71471feb834303b3bede19a8d2ef7142352719a3b83b75458` over **git-canonical
  (LF) bytes**, `git show :evidence/plan3/calibration_diagnostics.json | sha256sum`)

  > **Corrected 2026-08-03.** This line previously read
  > `4c2424457ca1212330f7a7eced0ac91c1c43e964b05ce62e11f85897a9062cfb` **with no byte convention
  > named**. That is the hash of a *Windows CRLF working copy*, so an independent verifier on any
  > LF checkout would have computed a mismatch against a document written to be verified — the
  > exact trap `certification-result.md` already records for the certification artifact, repeated
  > here. A hash without its byte convention is the same defect as an acceptance bound without its
  > δ allocation. The artifact was regenerated in the same commit (the `interpretation` string
  > carried the withdrawn "each independently forbid" wording); **every number in it is unchanged**
  > and the access chain head is unchanged at `ff5562419c…` with `final_reads: 0, shift_reads: 0`,
  > so the new hash reflects one prose line and nothing else.
- Command: `uv run conformalextract calibration-diagnostics`

## What is being reversed

The 2026-07-29 disposition descoped three of the four §11.3 sub-items:

| Sub-item | 2026-07-29 | Now |
|---|---|---|
| score–loss Spearman association | descoped | **executed** |
| AUROC/AUPRC for the strict-failure indicator | descoped | **executed with three exploratory indicators**; the plan's predeclared indicator is unavailable (ruled 2026-10-27, [Amendment 2](sections-11-and-12-disposition-amendment-2.md)) |
| binned confidence/risk diagrams with counts | descoped | **executed** (risk at fixed coverage) |
| selective-risk curves | executed | unchanged |

§11.2 subgroup reporting was descoped as "moot — empty input", with the explicit note that
*subgroup analysis of loss across all predictions is possible and is not being done*. That note is
the part now reversed: the stratifications are computed over all groups, not over an accepted set,
so the mootness reasoning is untouched and only the "not being done" is.

## Why the original ground no longer holds

The descope reason was **methodological redundancy, and it was correct on its own terms**: the
committed oracle risk–coverage curve already bounds what any threshold rule could achieve, so a
rank correlation or an AUROC could only be weaker evidence *for the same conclusion*. Nothing below
disputes that. The reversal does not claim the old reasoning was wrong.

What changed is the purpose, and it is a purpose that did not exist on 29 July:

1. **Comparability.** AUROC and normalized AURC are the units the selective-prediction and
   hallucination-detection literature reports. A null stated only in this repository's own
   quantities cannot be placed against Kotte (arXiv:2606.29054) or Farquhar et al. (Nature 630),
   and a reader cannot assess whether the score was unusually bad or entirely ordinary. The curve
   is the stronger bound; the AUROC is the one an outside reader can price.
2. **A distinction the curve cannot draw.** The curve reports the acceptance a score reached. It
   does not report the acceptance the population *permitted*, and **three** bounds answer that,
   in increasing strictness. Which one is quoted decides whether a claim is honest:
   - the **arithmetic** bound, `1 - (mu - alpha)/(1 - alpha)` = 0.4911 for QA, which assumes the
     population's goodness can be concentrated arbitrarily and therefore **overstates** what was
     available;
   - the **empirical oracle** = 0.2357, which ranks this exact population by its actual loss and
     reads the same height, holding the population fixed and varying only the ranking. This is the
     only one a **score-discrimination** claim may use, because the measured 0.0201 it is compared
     against is empirical too;
   - the **certified oracle** = 0.1139 at delta/3, the same perfect ranking required to keep its
     Hoeffding upper bound within alpha. **This is the only one that licenses the word
     "certified"**, and it is below the 0.20 floor.

   An earlier version of this document listed only the first two and then read the second as
   though it were the third. That is the error the review caught; see "What it found".

## Why this is not the post-hoc rescue §8.5 forbids

Every guard the original disposition relied on still binds, and the artifact carries them on its
face (`diagnostic_only`, `certifies_nothing`, `reverses_disposition`):

- **No threshold is selected and no certificate is issued** at any alpha, on any split.
- **The frozen target is untouched.** α = 0.20, δ = 0.05, floor 0.20, and the headline stays
  infeasible for all three systems.
- **Nothing here can rescue the hypothesis.** Every statistic is bounded above by the oracle curve
  that already returned infeasible. The reversal makes the null *more specific*, never weaker —
  §8.5 forbids reporting an alternative score or a re-scoring as a rescue, and no alternative score
  and no re-scoring appears here.
- **No new label access.** The access chain head hash is
  `ff5562419c7ddd543e06fdf656114a26cf79cdbf12063e906002b1024b423d9f` — byte-identical to the one
  carried by `alpha_frontier.json`, `loss_decomposition.json` and **`certification_result.json`**.
  Same single opening of 3,152 documents; `final_reads: 0`, `shift_reads: 0`, `verified: true`.

  > **Corrected 2026-08-02.** An earlier version of this bullet, and the routing packet that
  > carried it, named `risk_coverage_diagnostic.json` as the third hash-carrier. **It carries no
  > access block at all.** The third carrier is the certification result. The claim being made —
  > one chain, one opening — is unaffected, but it was stated against a file that could not
  > support it. `tests/test_reanalysis_artifacts.py` now asserts both halves.
- **$0.** No inference, no GPU, no Hugging Face job. The $25 cap is untouched.

Three values reproduce the committed artifacts exactly rather than approximately, which is the
check that the new command and the certifier agree about what a loss is:

| Quantity | `risk_coverage_diagnostic.json` | this artifact |
|---|---|---|
| QA max acceptance within α | 0.02005730659025788 | 0.02005730659025788 |
| QA risk at floor acceptance | 0.4053806110257721 | 0.4053806110257721 |
| FS risk at floor acceptance | 0.9299880525686979 | 0.9299880525686979 |

## What was NOT reversed

- §11.1's four descoped rows and §12.2's audit sample stay descoped on their original grounds.
- The strict-failure indicator remains **undefined**. Plan 1 §6.1 (its line 237) froze only that such a loss
  *would* be frozen before calibration; the exact definition never was. Rather than invent one now
  and call it predeclared, the artifact reports three named indicators (`above_alpha`, `any_error`,
  `not_all_valid`) and describes none of them as predeclared. **This is a Plan 1 defect this
  amendment surfaces but does not repair**, and a reviewer should treat it as its own finding.
  *(Ruled 2026-10-27: unavailable, not repairable after calibration; item by item in
  [Amendment 2](sections-11-and-12-disposition-amendment-2.md).)*

## What it found

Certification split, α = 0.20, acceptance floor 0.20, group level:

| System | base risk | arithmetic bound | oracle, **empirical** | oracle, **certified** (δ/3) | delivered, empirical | delivered, certified | AUROC | *(non-failing groups)* | norm. AURC | Spearman ρ |
|---|---|---|---|---|---|---|---|---|---|---|
| QA | 0.6071 | 0.4911 | 0.2357 | **0.1139** | 0.0201 | **0.0000** | 0.796 | *90 of 1,392* | 0.531 | −0.403 |
| FS | 0.9580 | 0.0525 | 0.0244 | **0.0000** | 0.0000 | **0.0000** | 0.727 | *18 of 1,392* | 0.920 | +0.073 |
| ZS | 0.9923 | 0.0096 | 0.0036 | **0.0000** | 0.0000 | **0.0000** | 0.344 | ***3 of 1,392*** | 0.926 | −0.027 |

**Read the AUROC column against the count beside it.** ZS's 0.344 rests on three non-failing
groups and FS's 0.727 on eighteen; neither is a stable estimate and neither should be quoted
without its count. Only QA's is worth interpreting, and its 95% bootstrap interval is
[0.737, 0.850] — recorded, with its seed and resample count, in
[`../../evidence/plan3/certification_sensitivity.json`](../../evidence/plan3/certification_sensitivity.json).

The two oracle columns are the correction below. **Not one figure in the certified columns reaches
the 0.20 floor**, and the acceptance floor is 0.20 for every row.

(QA and ZS read at `mean`, FS at `tenth_percentile` — the candidates the development gate
selected. All nine system × candidate combinations are in the artifact.)

**Refuted on review, and the correction is the finding.** This document originally read
“QA — score discrimination, and the floor really was reachable”, on the strength of the 0.2357
empirical oracle. **That was wrong.** 0.2357 carries no finite-sample penalty. Under the
Hoeffding diagnostic (`hoeffding_upper`, neither certifier's construction; *named 2026-10-27*), the same perfect ranking certifies **0.1139** at δ/3 and
**0.0838** family-wide — both below the 0.20 floor; at the floor itself (280 groups) empirical risk
is 0.175 against an upper bound of 0.267 at δ/3 (`derived_quantities.json`,
`at_the_acceptance_floor`; *corrected 2026-10-27* from "279 groups … 0.174 … 0.267–0.283": 279
groups is one short of the floor, and the 0.283 family-wide figure is carried by no artifact). This is the identical category error the amendment
makes such a point of avoiding for the 0.406 frontier point, three sections above, and it ran in
the flattering direction.

**Infeasibility is OVERDETERMINED, and that is the corrected result.** Every system is forbidden
by at least one of three mechanisms and QA by two, so no single repair rescues any of them. They
are *not* all active everywhere — saying they **each** forbid the target is false, as bullet 1
below says in the next breath — and a claim naming only one of them is wrong:

1. **Base risk.** Forbids the floor outright for ZS (permits 0.96%) and FS (5.25%). Does **not**
   forbid it for QA, which is permitted 49.1% — so attributing QA's null to μ alone is the
   base-risk-as-forecast error `CX-FEASIBILITY-LESSON-01` records.
2. **Ranking.** QA's score reaches 2.0% where a perfect ranking of the same population reaches
   23.6%. Both are empirical and no-penalty, so this comparison is like-for-like and the
   **21.6-point gap survives the correction intact**. It remains the score-discrimination finding.
3. **Finite-sample penalty.** The perfect ranking's 23.6% becomes 11.4% certified; QA's measured
   score certifies **0.0%**. This mechanism is visible only on QA — ZS and FS are already dead at
   (1) — and it is the one this repository had never separated out.

**What survives unchanged:** QA's score is not weak by the field's standard measures (AUROC 0.796,
ρ = −0.403 at p ≈ 1e-55, replicated on development at 0.834 / −0.313), and it still buys almost
nothing. **What is withdrawn:** every sentence of the form “the target was reachable” or “the floor
would have been cleared”. Nothing could have certified this system — not a better score, not a
perfect one.

### Added 2026-08-03 — what the R7 reconciliation found

These belong here rather than only in the write-up, because they are §11.3 findings.

- **Three population sizes, not one.** 1,396 rows are passed to the certifier and the precondition
  is checked against that count; 1,392 can be scored and ranked; 1,266 are eligible for acceptance
  under QA. The four-group difference is groups containing a document that produced no generation
  at all — the same four in every system, so a corpus property. **They remain rows**, so no number
  of further unscorable groups reduces the n the precondition sees. An earlier draft claimed seven
  more would make the certificate inadmissible; that is false against the code and is withdrawn.
- **Grid capacity is the honest statement of "at the edge".** At δ/3 the theorem admits at most a
  **three**-candidate grid on this corpus — three need 1,386 groups against 1,396, a fourth needs
  1,432 — and the frozen configuration is exactly three. This replaces the margin-in-groups
  framing, which was ambiguous between the row count and the rankable count.
- **At the frozen allocation both constraints fail.** The oracle prefix's acceptance lower bound is
  **0.1984**, below the 0.20 floor, and the risk test fails independently. An earlier draft quoted
  0.2017 — the same bound without the per-system δ/3 division — and concluded that only risk bound.
  Every allocation is now tabulated with its own δ, candidate count and n in
  `certification_sensitivity.json`.
- **The "each forbid" correction was itself incomplete, and the commit that made it said
  otherwise.** It was applied to five prose surfaces and the commit message claimed all of them.
  A surface map run on 2026-08-03 found **three more**: the `calibration.py` module docstring, the
  `interpretation` string that module bakes into its artifact, and the committed artifact carrying
  that string. Eight, not five. The prose surfaces were found by grepping the write-up; the code
  and the generated artifact were not in the search path, which is how a correction can be
  *verified complete* against the wrong population — the same shape as checking that a claim's
  evidence path exists without opening the file.

**Three stratification findings**, QA at `mean`, over all groups rather than an accepted set:

- **The document unit is doing much of the damage.** Mean group loss barely moves with trigger
  count (**0.606** → 0.634 from 1 trigger to 4–5), but the share of groups within α collapses from
  17.3% to 0.7%, and 23 of the 28 groups the score's best within-α prefix accepts (cut-off chosen
  with labels; not the loss-optimal oracle above — *wording corrected 2026-10-27*) are
  single-trigger (lift 1.68). Groups
  with 3+ triggers contribute **zero** acceptances. Averaging frame loss across a whole document
  and scoring the group by its weakest member makes acceptance fall away with document complexity
  even where mean loss is flat.

  > **Corrected 2026-08-02.** This read “0.589 → 0.634”. The 1-trigger stratum's mean loss is
  > **0.6064**; 0.589 is the all-valid / fully-grounded figure from a different row of the same
  > artifact, spliced in by mistake. It made the stratum look flatter than it is.
- **Cross-sentence distance behaves the same way.** 16.1% of groups with no cross-sentence argument
  are within α (25 of those same 28 acceptances); groups with 3+ cross-sentence arguments contribute none.
- **Grounding is necessary and nowhere near sufficient.** Group grounded-share against group loss
  gives ρ = −0.206 (p ≈ 8e-15) — a real association, so "orthogonal" was wrong — but the 1,266
  fully-grounded QA groups still average **0.589** loss, roughly 3× α. This is direct group-level
  support for the §3.2 replacement wording and it is stronger than the aggregate percentages were.

## Required before this leaves the repository

1. Independent review of this reversal, to the standard ADR 0010 and ADR 0011 §3 met.
2. A claim-ledger entry for anything above that becomes a stated claim, with its own review.
3. The undefined strict-failure indicator ruled on separately.
