# Amendment 1 to the §11 and §12 disposition — three §11.3 rows reversed and executed

- Date: 2026-08-02
- Amends: [`sections-11-and-12-disposition.md`](sections-11-and-12-disposition.md) (2026-07-29)
- Raised by: the owner's publication-sprint plan of 2026-08-02, §4 (held outside this repository)
- **Status: proposed. Pending independent review. Nothing here may reach a public surface, and
  Plan 3 does not close on this document.**
- Artifact produced: [`../../evidence/plan3/calibration_diagnostics.json`](../../evidence/plan3/calibration_diagnostics.json)
  (`sha256 cde30bba46ebc8e4da74dc60889a50d2f44026ab8476db586663ab18f813732a`)
- Command: `uv run conformalextract calibration-diagnostics`

## What is being reversed

The 2026-07-29 disposition descoped three of the four §11.3 sub-items:

| Sub-item | 2026-07-29 | Now |
|---|---|---|
| score–loss Spearman association | descoped | **executed** |
| AUROC/AUPRC for the strict-failure indicator | descoped | **executed** |
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
   does not report the acceptance the population *permitted*. Two bounds answer that, and they
   are far apart, so which one is quoted decides whether a claim is honest:
   - the **arithmetic** bound, `1 - (mu - alpha)/(1 - alpha)`, which assumes the population's
     goodness can be concentrated arbitrarily and therefore **overstates** what was available;
   - the **loss-optimal oracle**, which ranks this exact population by its actual loss and reads
     the same height, holding the population fixed and varying only the ranking.

   Only the second may carry a score-discrimination claim. On QA the two differ by more than a
   factor of two (49.1% against 23.6%), so the distinction is not academic — see below.

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
  carried by `alpha_frontier.json`, `loss_decomposition.json` and `risk_coverage_diagnostic.json`.
  Same single opening of 3,152 documents; `final_reads: 0`, `shift_reads: 0`, `verified: true`.
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
- The strict-failure indicator remains **undefined**. Plan 1 §237 froze only that such a loss
  *would* be frozen before calibration; the exact definition never was. Rather than invent one now
  and call it predeclared, the artifact reports three named indicators (`above_alpha`, `any_error`,
  `not_all_valid`) and describes none of them as predeclared. **This is a Plan 1 defect this
  amendment surfaces but does not repair**, and a reviewer should treat it as its own finding.

## What it found

Certification split, α = 0.20, acceptance floor 0.20, group level:

| System | base risk | arithmetic bound | **loss-optimal oracle** | delivered | AUROC (any error) | normalized AURC | Spearman ρ |
|---|---|---|---|---|---|---|---|
| QA | 0.6071 | 0.4911 | **0.2357** | 0.0201 | 0.796 | 0.531 | −0.403 |
| FS | 0.9580 | 0.0525 | **0.0244** | 0.0000 | 0.727 | 0.920 | +0.073 |
| ZS | 0.9923 | 0.0096 | **0.0036** | 0.0000 | 0.344 | 0.926 | −0.027 |

(QA and ZS read at `mean`, FS at `tenth_percentile` — the candidates the development gate
selected. All nine system × candidate combinations are in the artifact.)

**Two findings, and they must not be merged.**

**QA — score discrimination, and the floor really was reachable.** A perfect ranking of this exact
population reaches **23.6%** acceptance, which clears the 20% floor. The score delivered 2.0%. So
the target was not arithmetically excluded and not excluded by the population either; it was lost
in the ranking, by an order of magnitude and with only a narrow margin to spare. What makes this
worth publishing is that the score is **not weak by the field's standard measures** — AUROC 0.796,
ρ = −0.403 at p ≈ 1e-55, replicated on the development split (0.834, ρ = −0.313, oracle 24.4%,
delivered 3.0%). A score can be clearly informative and still certify almost nothing, because risk
control needs the *top* of the ranking to be nearly clean rather than the whole ranking to be
ordered: QA's best-scoring 5% of groups still average 0.274 loss, above α.

**ZS and FS — capability, definitively.** Their loss-optimal oracles are 0.36% and 2.44%, an order
of magnitude below the floor. **No score whatever could have certified them.** This is now proved
against the tight oracle rather than only against the loose arithmetic bound.

**A correction this supersedes.** The owner's sprint plan §2 states the QA gap as "base risk
permitted up to 49.1% acceptance; the run achieved 2.0%". 49.1% is the arithmetic bound, and this
population does not supply it — the attainable figure is 23.6%. The gap is **21.6 points, not 47**.
The finding survives the correction and is arguably cleaner for it, because 23.6% against a 20%
floor says the target was *barely* reachable, which is a more precise claim than a loose bound can
support. Any paper text must use 23.6%.

**Three stratification findings**, QA at `mean`, over all groups rather than an accepted set:

- **The document unit is doing much of the damage.** Mean group loss barely moves with trigger
  count (0.589 → 0.634 from 1 trigger to 4–5), but the share of groups within α collapses from
  17.3% to 0.7%, and 23 of the 28 oracle-accepted groups are single-trigger (lift 1.68). Groups
  with 3+ triggers contribute **zero** acceptances. Averaging frame loss across a whole document
  and scoring the group by its weakest member makes acceptance fall away with document complexity
  even where mean loss is flat.
- **Cross-sentence distance behaves the same way.** 16.1% of groups with no cross-sentence argument
  are within α (25 of 28 acceptances); groups with 3+ cross-sentence arguments contribute none.
- **Grounding is necessary and nowhere near sufficient.** Group grounded-share against group loss
  gives ρ = −0.206 (p ≈ 8e-15) — a real association, so "orthogonal" was wrong — but the 1,266
  fully-grounded QA groups still average **0.589** loss, roughly 3× α. This is direct group-level
  support for the §3.2 replacement wording and it is stronger than the aggregate percentages were.

## Required before this leaves the repository

1. Independent review of this reversal, to the standard ADR 0010 and ADR 0011 §3 met.
2. A claim-ledger entry for anything above that becomes a stated claim, with its own review.
3. The undefined strict-failure indicator ruled on separately.
