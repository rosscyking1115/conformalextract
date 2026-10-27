# UncertaiNLP 2026 short paper — status, provenance and remaining work

> **The paper itself is [`uncertainlp-2026-short.tex`](uncertainlp-2026-short.tex), and that file
> is authoritative.** This companion carries the things that belong in the repository but not in a
> submission: gate status, where each external number came from, and what is left to do.
>
> **This file used to contain a full Markdown copy of the paper. That copy has been deleted, not
> updated** — it still asserted the claim the 2026-08-02 review refuted, and a second copy of a
> rewritten argument is exactly the drift this repository has already been bitten by once this
> week. One source. (Prior content is recoverable from git and from a `safe_ops` snapshot.)

- **Status: DRAFT, updated 2026-08-09. Not submitted, not under review, not submittable yet.** The
  gate below is six steps from a Plan 3 close, five of which cannot be self-issued. The honest
  external label is **"in preparation for UncertaiNLP 2026 (3rd Workshop on Uncertainty-Aware NLP,
  EMNLP 2026)"** — never "submitted", "under review" or "accepted", and "certified" appears nowhere
  until step 6 issues a PASS.
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

## Gate status — the real chain, not the two packets

> **This section used to list two REVISE packets and stop there.** That was true and it was not the
> gate. The actual blocker is that **Plan 3 has never closed**: its close was *refused*, and the two
> packets are two steps of six on the path back to a close. A reader taking the old table as the
> remaining work would have seen **two of the six steps** — and not the one that governs them, the
> refused close — in the direction that says the paper is nearly shippable. (Two-of-six is a count
> of steps, not of effort: the omitted steps include the two heaviest, and no estimate of their cost
> is asserted here.) **A status surface that understates its own gate is an attestation
> that flatters** — the defect this repository exists to name, committed by the document whose only
> job is to state the gate. Corrected 2026-08-09. The canonical machine-readable state is
> [`../../evidence/gate_state.json`](../../evidence/gate_state.json); reconcile against that, not
> against this prose.

**Where the gate actually stands.** Plan 1 closed; Plan 2 closed (independent reviewer PASS,
2026-07-21). **Plan 3 is executed and independently reviewed but NOT closed** — its close record is
[`reviewer_record.plan3-close.json`](../../evidence/plan3/reviewer_record.plan3-close.json), whose
`review_kind` is `plan_close_refused` and whose verdict is *"Plan 3 may NOT be closed"*, blocking on
findings O1, O2 and O3. **Plan 4 is PAUSED**, open only by owner override of the gated sequence.

**The chain, step by step.** Every step's implementer work is *already applied*; what is outstanding
is review. Steps marked 🔒 **may not be self-issued** — no seat may review its own work, and per
`CLAUDE.md` a change to evaluation, label access, certification or release policy requires an
independent review.

| # | Step | State | Who |
|---|---|---|---|
| 1 | **O1** — [§11/§12 disposition](../plan3/sections-11-and-12-disposition.md) + [Amendment 1](../plan3/sections-11-and-12-disposition-amendment-1.md) (`0d5100b`, `ed3693b`, `3320af9`; **REVISE** twice, plus v3/v4 rounds whose verdicts were never filed) + [Amendment 2](../plan3/sections-11-and-12-disposition-amendment-2.md) (2026-10-27: §12.1 descoped on Ross's choice, §11.2 disposed axis by axis) | the 2026-10-27 [close-chain review](../../evidence/plan3/reviewer_record.plan3-close-chain.json) returned **BLOCK** on S1-B1/S1-B2; Amendment 2 answers both; the [delta review](../../evidence/plan3/reviewer_record.plan3-close-chain-delta.json) ruled them discharged (**PASS-WITH-NITS**) and the [C1 review](../../evidence/plan3/reviewer_record.c1-2026-08-03-packets.json) passed Amendment 1 with nits; nits applied 2026-10-27, for the close review to verify | 🔒 (ruled) |
| 2 | **Ledger entries** for the §11.3 quantities that became stated claims (group AUROC, normalized AURC, Spearman ρ, the stratifications), each with its own review | written 2026-10-27 (`CX-RANKING-01`, `CX-STRATIFICATION-01`); first review **BLOCK**; [delta review](../../evidence/plan4/reviewer_record.certify-hardening-and-claims-delta.json) **PASS-WITH-NITS**, nits applied | 🔒 (ruled) |
| 3 | **The strict-failure indicator**, ruled on separately | **ruled 2026-10-27** (the cheap ruling): no predeclared strict-failure loss exists; the three indicators are exploratory; the dependent items are disposed as unavailable in Amendment 2 | 🔒 (ruled) |
| 4 | **O2/O3** — [`reviewer_record.o2-o3-claims-change.json`](../../evidence/plan4/reviewer_record.o2-o3-claims-change.json) returned **BLOCK** on 2026-07-29 | verified by the 2026-10-27 [close-chain review](../../evidence/plan3/reviewer_record.plan3-close-chain.json), which returned **BLOCK** on S4-B1/S4-B2; `44ed212` answers both and the [delta review](../../evidence/plan3/reviewer_record.plan3-close-chain-delta.json) ruled them discharged | 🔒 (ruled) |
| 5 | **Claim narrowing** — [packet](../plan3/claim-narrowing-2026-08-02.md) (`d256ca5`, `ed3693b`; **REVISE** twice, plus v3/v4 rounds whose verdicts were never filed) | the close-chain review ruled its questions (keep the identifier, no redirect; the narrowing is a separate finding, O2-S1, discharged) and returned **BLOCK** on S5-B1, since discharged; the [C1 review](../../evidence/plan3/reviewer_record.c1-2026-08-03-packets.json) then returned **BLOCK** on B1/B2 (naming the construction; the 0.1075 wording), answered 2026-10-27 and awaiting verification | 🔒 |
| 6 | **A fresh Plan 3 close record** — by an independent reviewer who did **not** implement Plan 3 and did **not** author this refusal's remedies, re-verifying the green command and the artifact hashes at its own commit | not started; may be attempted once the 2026-10-27 corrections, including C1's B1/B2, are applied | 🔒 |
| 7 | Plan 4's owner override lapses and the gate is satisfied on its merits | follows 6 | — |

**Nothing here may be submitted, posted, published or quoted until step 6 issues a PASS.** That
includes the public release of this repository: publishing the repo publishes its claims, and the
claims are in an undischarged state. Every quantitative sentence is additionally bound by
[`../plan3/certification-result.md` → "What may and may not be claimed"](../plan3/certification-result.md).

**Do not read "corrections applied" as "nearly done".** Across the review events above, the
first-pass clean rate is **zero** — REVISE twice, REVISE twice, REFUSED, BLOCK, then on 2026-10-27
three more BLOCKs (the close chain, the certify hardening, the claim-narrowing packet), with the
two packets' unfiled v3/v4 rounds not counted — and
Amendment 1 records an instance where *the correction for a defect contained that same defect*.
Budget for a further round on each step rather than assuming one passes.

## The venue route, and why no deadline applies

**Decision, 2026-08-09: the UncertaiNLP 2026 direct deadline is deliberately not targeted.** The
paper is blocked on the chain above, and submitting against this project's own gate would be the
paper refuting itself — its subject is instruments that return `ok` when they should fail.

**That cliff was the only cliff, so this is a non-event rather than a miss.** ACL Rolling Review is
*rolling*: it runs recurring ~10-week cycles, roughly five a year, and — read from
<https://aclrollingreview.org/dates> on 2026-08-09 — *"Once authors have reviews they may choose to
revise and resubmit for another round of reviews, or commit their paper and reviews to a publication
venue."* So when the gate clears, the paper enters ARR with no deadline and commits to a venue with
reviews already in hand. **There is no next window to miss**, which is what lets the review chain run
at its proper pace instead of against a clock.

(The workshop's own ARR-commitment track was never available here: it accepts only papers that
already carry ARR reviews, and this one carries none.)

## The two build artifacts

Both are produced by `scripts/build_paper.ps1` and neither is tracked.

| File | What it is |
|---|---|
| `uncertainlp-2026-short.pdf` | **Submission artifact.** `\usepackage[review]{acl}` — anonymous, line-numbered. Built by the bare script. |
| `uncertainlp-2026-short-bylined.pdf` | **Writing sample.** Bylined, no line numbers. Built by `-Bylined`, which *derives* `uncertainlp-2026-short-bylined.tex` from the submission `.tex` by substitution. It is generated, never hand-edited, and gitignored — a second copy of this paper is the drift that already cost this file its Markdown duplicate. |

The writing sample is **not gated by the chain above**, because it makes no publication claim. It
carries the status *"in preparation for UncertaiNLP 2026 (3rd Workshop on Uncertainty-Aware NLP,
EMNLP 2026)"* — pre-submission, not submitted, not under review.

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
2. **The six-step chain in "Gate status" must run to a Plan 3 close.** The only blocking item — and
   it is six steps, not the two packets this list used to name. Five of the six may not be
   self-issued. **Resumes on the owner's word, not on momentum**; it has no deadline (see "The
   venue route") and must not compete with work that does.
3. ~~The RoSE reference needs its full author list.~~ **Done, 2026-08-09.** It read `Huang, Guang`:
   a wrong given name *and* four missing co-authors, in a paper about citation integrity. Corrected
   from the publisher's own `citation_*` metadata to Huang, Zhang, Zhou, `{Zhang Yi}` and Xu, with
   volume, pages and DOI. The braces on `{Zhang Yi}` are load-bearing — that author publishes
   surname-first while his co-authors are listed given-name-first, and unbraced BibTeX renders him
   "Z. Yi". `external_citations.json`'s standing "author list still to be completed" note is
   discharged rather than left open. The **54.4 value itself was not re-opened** and still rests on
   the 2026-07-28 reading.
4. ~~Decide the figure's width.~~ **Done** — single-column, regenerated at 3.3×2.2in with type
   sized for it. It was a full-width `figure*` costing about seven column-inches; in one column it
   costs under two. *(That trim did bring the content inside four pages; text added afterwards took
   it back out, which item 1 records.)*
5. Author block and acknowledgements — the submission artifact stays anonymous, which is correct for
   review; the bylined writing-sample variant is generated from it by `-Bylined` and is not a second
   source. Acknowledgements remain to be written for a camera-ready that does not yet exist.
6. **The build script's two blind spots are closed, and both had shipped.** It grepped for
   *undefined* references, which is a different condition from *unsettled* ones — this paper needs a
   fourth pdflatex pass, and every build before 2026-08-09 reported "all citations and
   cross-references resolved" over a warning saying they were not. It also sent `bibtex` output to
   `Out-Null`, so a malformed entry that rendered a citation as `[hua()]` passed a check that only
   knew how to see "undefined". Both now fail the build; `-SelfTest` proves the first in **both**
   directions, asserting a cold single pass *is* detected as unsettled before asserting a settled
   build passes. Recorded here because they are the same defect class as the five in the paper's
   Limitations: a gate that returns `ok` on the wrong property.

## Build notes

- `acl.sty` is **not vendored** — the upstream repository declares no licence. See
  [`acl-template.md`](acl-template.md) for the pinned fetch; `scripts/build_paper.ps1` finds it via
  `TEXINPUTS`, so nothing unlicensed can be committed by accident.
- LaTeX build products are gitignored. `fig/*.pdf` is tracked because it is an input, generated by
  `scripts/plot_risk_coverage.py` — which refuses to draw if its recomputed curve disagrees with
  the committed `alpha_frontier.json`.
