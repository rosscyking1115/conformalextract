# UncertaiNLP 2026 short paper — status, provenance and remaining work

> **The paper itself is [`uncertainlp-2026-short.tex`](uncertainlp-2026-short.tex), and that file
> is authoritative.** This companion carries the things that belong in the repository but not in a
> submission: gate status, where each external number came from, and what is left to do.
>
> **This file used to contain a full Markdown copy of the paper. That copy has been deleted, not
> updated** — it still asserted the claim the 2026-08-02 review refuted, and a second copy of a
> rewritten argument is exactly the drift this repository has already been bitten by once this
> week. One source. (Prior content is recoverable from git and from a `safe_ops` snapshot.)

- **Status: DRAFT, 2026-08-03. Not submitted. Not submittable yet.**
- Build: `pwsh -File scripts/build_paper.ps1` → all citations and cross-references resolve.
- **Targeting the FULL-PAPER format, up to 8 pages** (owner's decision, 2026-08-03). The venue's own
  call — <https://uncertainlp.github.io/>, read from source that day — offers short "up to 4 pages"
  and full "up to 8 pages", both archival and non-archival, **same review process**. Limitations,
  References and appendices do not count. The provenance and the reasoning are in
  [`reviewer_analysis.md`](reviewer_analysis.md) under Submission Readiness.
- **Content: 4 pages plus part of page 5, measured from a build.** Comfortably inside 8. Re-measure
  from a build before drawing any conclusion from this line — a stored measurement is what produced
  instance six.
- **Why the format changed, in one line:** after every legitimate structural lever the residual
  overflow at 4 pages was still 10 lines, the paper grew *as it became more correct*, and
  compression introduced a factual defect three times out of three.
- **It was ten lines over, and the fix was structural rather than a compression pass.** Two levers,
  no prose compressed: the trigger-count and cross-sentence stratification moved to
  `Appendix A: The aggregation unit` (ACL appendices follow References and do not count), leaving a
  one-line pointer in §3; and the finite-sample argument was de-duplicated — C1's rewrite and the
  0.0925/0.1075 addition had left the paper saying "the corpus is too small" three times in three
  units, so the penalty statement absorbed the "18,000 groups" restatement instead of sitting
  beside it.

  > **This line previously read "content ends 82% down page 4, so within the 4-page ACL limit", and
  > that was instance SIX of the defect class the paper's Limitations section is about.** The 82%
  > figure was measured before the C1 and C3 corrections added text, and every status report after
  > those commits repeated it from this file instead of from a build. It cites an artifact that
  > exists — the PDF — and states a number the artifact does not contain, in the direction that
  > flatters compliance, inside the one line whose whole job is to assert compliance. It was found
  > by rebuilding, not by any guard.
  >
  > **The paper still says five, and that is a judgement call, not an oversight.** The class it
  > names is *quoting a quantity that resembles a certified one and is not*; a page-position figure
  > is the same mechanism — cite a document instead of the artifact, in the flattering direction —
  > but not the same subject, and an ACL Limitations section is not the place to report a build
  > measurement. Recorded here for the owner to overrule if he wants the count to read six.
  >
  > **Resolved by relocation, not compression.** A compression pass was the highest-risk edit
  > available here — it had already introduced a factual defect twice in this document — so
  > structural levers were surveyed first and two were sufficient. The full instance list, and what
  > makes instance six worse than the other five, is in
  > [`../plan4/open-release-decisions.md`](../plan4/open-release-decisions.md).

## Gate status — both packets returned REVISE, neither is discharged

| Packet | Commit reviewed | Verdict |
|---|---|---|
| [§11.3 calibration diagnostics](../plan3/sections-11-and-12-disposition-amendment-1.md) | `0d5100b`, `ed3693b`, `3320af9` | **REVISE**, twice |
| [claim narrowing](../plan3/claim-narrowing-2026-08-02.md) | `d256ca5`, `ed3693b` | **REVISE**, twice |

Both packets were reissued after their first REVISE and both returned REVISE again. The second
round's corrections are applied and recorded in each packet; a third review has not been run.
**Nothing here may be submitted, posted or quoted until both are re-reviewed and pass.** Every
quantitative sentence is bound by
[`../plan3/certification-result.md` → "What may and may not be claimed"](../plan3/certification-result.md).

## The correction that rewrote the paper

The first draft's central sentence — *"a perfect ranking would clear the 20% floor"* — was
**false**, and the review caught it. 23.6% is an *empirical* oracle acceptance carrying no
finite-sample penalty; under the certifier's own `hoeffding_upper` the same perfect ranking
certifies **0.1139** at δ/3 and **0.0838** family-wide, both below the 0.20 floor. At the floor
itself (279 groups) empirical risk is 0.174 against an upper bound of 0.267–0.283.

That was the same category error the paper takes care to avoid for the α\* = 0.406 frontier point,
committed one section later, and it ran in the flattering direction. The paper now argues the
stronger thing the arithmetic supports: **infeasibility is overdetermined** — base risk, ranking
and the finite-sample penalty are three separate barriers, no one of which could be removed to rescue the result (they do not all bind on every system: base risk settles the baselines and not QA) — and it says so in its
Limitations, because that is the paper's own thesis happening to its authors.

The 2.0% vs 23.6% comparison survives unchanged: both sides are empirical, so it is like-for-like
and the 21.6-point gap is still attributable to the ranking.

## Provenance of every external number

Every figure about *our* systems resolves to a committed artifact. External comparanda reached this
project through a research summary rather than from source, so each was read from source before use
and recorded in [`../frontier-check/findings.md`](../frontier-check/findings.md) (addendum,
2026-08-02).

| Figure | Status |
|---|---|
| Kotte NLL AUROC 0.485–0.604 (NER/QA/CLS) and **0.793 on JSON** | **Verified** from Table 5. The relayed band omitted the JSON cell, so an earlier draft's "above the band Kotte reports" was **false**. |
| Kotte self-consistency 0.600–0.816 | **Verified**, all eight datasets. |
| Kotte semantic entropy 0.496–0.677 | **Verified**. |
| Kotte base risks μ = 0.033, 0.356 | **Verified**; re-verified 2026-07-22. |
| Farquhar et al. mean AUROC 0.790 | **Not verifiable** — Nature is behind authentication, the earlier arXiv abstract states no AUROC, the authors' blog gives none. **Dropped**, and the reference with it. |
| Kotte CoNLL/Ministral-8B, 37% acceptance at risk 0.13 | **Not in this repository. Not used.** §6 argues from the committed base risks instead. |

**The rule, kept:** no external number appears in the paper unless it has been verified against a
primary source and recorded here.

## Remaining work

1. ~~Trim ~10 lines of counted prose.~~ **Done** — see the build note above. Any future addition
   must be re-measured from a build, not from this file; that is how the overflow went unnoticed.
2. **Both packets must be re-reviewed and pass.** The only blocking item.
3. The RoSE reference needs its full author list.
4. ~~Decide the figure's width.~~ **Done** — single-column, regenerated at 3.3×2.2in with type
   sized for it. It was a full-width `figure*` costing about seven column-inches; in one column it
   costs under two. *(That trim did bring the content inside four pages; text added afterwards took
   it back out, which item 1 records.)*
5. Author block and acknowledgements — currently anonymous, which is correct for review.

## Build notes

- `acl.sty` is **not vendored** — the upstream repository declares no licence. See
  [`acl-template.md`](acl-template.md) for the pinned fetch; `scripts/build_paper.ps1` finds it via
  `TEXINPUTS`, so nothing unlicensed can be committed by accident.
- LaTeX build products are gitignored. `fig/*.pdf` is tracked because it is an input, generated by
  `scripts/plot_risk_coverage.py` — which refuses to draw if its recomputed curve disagrees with
  the committed `alpha_frontier.json`.
