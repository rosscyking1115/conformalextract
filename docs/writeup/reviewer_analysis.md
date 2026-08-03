# Reviewer Analysis — UncertaiNLP 2026 short paper

Produced 2026-08-02 with the `ai-research-writing-skill` reviewer-diagnosis and submission-audit
routes. Author-facing: a diagnosis for the owner to act on, not a set of edits already made.

> **DISPOSITION, 2026-08-02.** The owner ruled on this document the same day. R1 was verified
> through `scorc_certificate` itself (result **0.0000**, confirming the ad hoc figure and its
> reason) and all six items were then applied to the paper. This file is retained as the diagnosis
> of record; the risks below are **addressed**, not outstanding. What remains outstanding is the
> re-review of both §11.3 and claim-narrowing packets.

Subject: [`uncertainlp-2026-short.tex`](uncertainlp-2026-short.tex) at commit `61b7846`.

## Executive Summary

- **Current likely reviewer stance:** borderline, leaning positive at a workshop on uncertainty.
  The core observation is genuinely interesting and the evidence discipline is unusually strong.
  Two unstated methodological facts are what would sink it.
- **Strongest part:** the three-mechanism decomposition, and the fact that every number resolves to
  a committed artifact with a reproduction command.
- **Highest rejection risk:** **the "certified" row of Table 1 is computed with the conservative
  audit's Hoeffding bound, not the primary certifier's empirical-Bernstein construction, and the
  paper does not say so.** At a venue about uncertainty this is the first question a reviewer asks.
- **Recommended next decision:** treat R1 and R2 as submission-blocking. Both are documentation
  fixes, not experiments; neither needs new data or spend.

## Strengths

- **Strength:** the ranking/certification divergence is a real, crisply stated finding.
  **Evidence:** AUROC 0.796 with 0.0000 certified acceptance, same population, same artifact.
  **Why reviewers may value it:** it is directly actionable for anyone reporting AUROC as evidence
  of selective-prediction fitness, which is most of the field.
- **Strength:** the three mechanisms are separated rather than merged.
  **Evidence:** Table 1 rows (1)-(3) with per-system figures; ZS and FS die at mechanism 1, QA at
  2 and 3. **Why:** most negative results report "it failed"; this one localises the failure.
- **Strength:** priority disclosure is first, unprompted, and quantified ("roughly 80% replication").
  **Why:** removes the single most common reviewer irritation with a replication-adjacent paper.
- **Strength:** the Limitations section reports the authors making the paper's own error twice.
  **Why:** it is the thesis demonstrated on the authors, which is rare and, at this venue,
  probably a differentiator rather than a liability.

## Major Risks

| Risk | Why reviewers may care | Evidence status | Severity | Recommended action |
|---|---|---|---|---|
| **R1.** "Certified" uses the **conservative audit's Hoeffding** bound, not the primary SCoRC **empirical-Bernstein** construction. The paper's caption says "Hoeffding" but never says this is the *audit* rather than the *certificate*. | An uncertainty audience knows Hoeffding is loose on low-variance data, and a loss-optimal prefix is nearly all zero-loss — exactly where Bernstein wins. The obvious objection is "your mechanism 3 is an artefact of picking the loosest bound". | **Refuted, in the paper's favour** — indicative recompute of the primary EB construction gives **0.0000**, worse than Hoeffding's 0.1139. The answer is good; it is simply absent. | **HIGH** | State which construction each figure uses. Report the EB number. **Verify the recompute first** — it was done ad hoc here, not through `scorc_certificate`. |
| **R2.** Mechanism 3 is partly a statement about **corpus size**, and the paper does not say so. | A reviewer will observe that the Hoeffding radius shrinks as 1/√k and ask whether the finding survives more data. | **Quantified:** at the floor the prefix mean is 0.174 and the radius budget is 0.026, needing ~3,600 accepted groups — about **18,000 groups total, 12.9× RAMS's certification split**. Below that, mechanism 3 holds. | **HIGH** | One sentence in §3 or Limitations: mechanism 3 is real at this corpus size and would dissolve at roughly an order of magnitude more data. Better to own it than be told it. |
| **R3.** Mechanism 3 is observed in **exactly one system**. | "You found a phenomenon in n=1" is a fair reading; ZS and FS cannot exhibit it because they die at mechanism 1. | True and stated in Limitations, but the Abstract presents it as a contribution. | MEDIUM | Keep the contribution claim, add "in the one system where it is observable" to the Abstract. Cheap, and pre-empts the objection. |
| **R4.** QA's AUROC 0.796 rests on **90 non-failing groups** of 1,392. | An AUROC on 90 positives has a wide interval; the paper quotes three decimals. | Counts are in the artifact; no interval is reported. | MEDIUM | Report a bootstrap CI, or quote two decimals and state the positive count inline. |
| **R5.** The Kotte AUROC comparison is disclaimed as not like-for-like, then leaned on. | "Ours is 0.796, theirs 0.793" carries argumentative weight while a parenthesis says the comparison is only indicative. | Honest but structurally weak. | MEDIUM | Either demote to "the same broad range" or justify why instance- and group-level AUROC are comparable here. |
| **R6.** No venue checklist artifact. | *ACL venues require a responsible-NLP checklist at submission. | `camera_ready_check.py` flags it; not yet written. | LOW (blocking at submission) | Produce at submission time. |

## Claim and Evidence Gaps

| Claim | Current evidence | Reviewer concern | Recommendation |
|---|---|---|---|
| "certifies **nothing at all**" (Abstract) | `acceptance_certified_score_ranked = 0.0000`, committed | Sound, and now the strongest sentence in the paper | Keep |
| "ranked by true loss, the same population certifies 11.4%" | Hoeffding audit bound | Bound choice unstated — see R1 | **Qualify or restate** |
| "AUROC 0.796 ... matching what log-probability achieves on structured generation elsewhere" | Kotte Table 5, verified | Cross-level comparison — see R5 | Weaken to "the same range" |
| "infeasibility is overdetermined" | Table 1, three mechanisms | Sound | Keep |
| "the third mechanism ... is the one we had no vocabulary for" | Single system — see R3 | Slight overreach as stated | Scope to QA |
| Grounding dissociation, ρ = −0.206 | `calibration_diagnostics.json` | Sound, correctly weakened from "orthogonal" | Keep |

## Five-Dimension Review

| Dimension | Score | Note |
|---|---|---|
| Contribution | **pass** | Contribution type is explicit (analysis/finding), and differentiated from the replication. |
| Writing clarity | **pass** | The three-mechanism spine is restatable after the Abstract. |
| Experimental strength | **needs revision** | Not for missing experiments — for the unstated bound choice (R1) and corpus-size dependence (R2). |
| Evaluation completeness | **pass** | Three systems, three confidence candidates, two splits, all reported. |
| Method soundness | **needs revision** | Same as above: the certified figure's construction must be named. |
| Responsibility | **pass** | Limitations are honest and do not contradict the central claim; sealed splits and cost are disclosed. |

## Simulated Review

```text
Summary: The paper defines a document-level selective-certification protocol for event-argument
extraction on RAMS and reports that no system certifies at alpha=0.20. Its contribution is a
decomposition of the failure into base risk, ranking quality, and finite-sample penalty, showing a
confidence score with AUROC 0.796 that certifies nothing.

Strengths: The decomposition is genuinely useful and not something I have seen stated this cleanly.
Evidence discipline is exceptional — every figure traces to a committed artifact. The priority
disclosure is exemplary. Limitations are unusually honest.

Weaknesses: (1) The certified figures use a Hoeffding bound; the authors' own framework has an
empirical-Bernstein construction, which is standard and tighter on the near-zero-variance prefixes
at issue. Without that number I cannot tell whether mechanism 3 is a property of the data or of the
bound. (2) The finite-sample mechanism is inseparable from corpus size at n=1,396 groups; the paper
does not report what n would dissolve it. (3) Mechanism 3 appears in one of three systems.

Key reason for accept/reject: Accept if (1) and (2) are addressed in the text — both are one
paragraph each. The core observation is worth the workshop's time.

Questions for authors: Why Hoeffding rather than empirical Bernstein? What n would make the
certified oracle clear the floor? Is the AUROC comparison with Kotte cross-level?

Actionable suggestions: State the bound; report the n-sensitivity; add a CI to the AUROC.

Confidence: 4/5 on methodology, 3/5 on the event-extraction literature.
```

## Author Decisions Needed

- **Decision:** whether to verify the empirical-Bernstein recompute through `scorc_certificate`
  before quoting it.
  **Options:** (a) verify and quote 0.0000; (b) state the bound choice without the EB number;
  (c) leave as is.
  **Trade-off:** (a) is strongest and closes R1 completely, but is a new computation on an opened
  split and would need its own record; (b) is honest and cheap but leaves the obvious question
  half-answered; (c) is a live rejection risk.
  **Recommendation:** **(a)**, routed as a correction to the existing §11.3 packet rather than as
  new work — it uses the certifier already in the repository and changes no committed artifact.

- **Decision:** whether R2's corpus-size sentence goes in §3 or Limitations.
  **Recommendation:** §3, immediately after mechanism 3. In Limitations it reads as a concession;
  in §3 it reads as precision.

## Revision Priorities

1. **Must fix before submission:** R1 (name the construction; report the EB figure), R2 (corpus-size
   sensitivity).
2. **Should fix if time allows:** R3 (scope mechanism 3 to QA in the Abstract), R4 (AUROC interval),
   R5 (weaken the Kotte comparison).
3. **Safe to leave as limitation:** single seed, single stack, in-domain only, post-hoc diagnostics
   — all already stated.

## Submission Readiness

> **Corrected 2026-08-03. This line read `UncertaiNLP 2026 (short, 4 pages)` and that number was
> never traced to the call.** It was an assumption written here and then carried forward by every
> later session as though it were the venue's rule. **Three factual defects came out of compressing
> to it**, and the compression was the highest-risk edit available in this document each time.
>
> **The call's own wording, read from source on 2026-08-03** at
> <https://uncertainlp.github.io/> (Third Workshop on Uncertainty-Aware NLP @ EMNLP 2026):
> short papers **"up to 4 pages"**, full papers **"up to 8 pages"**, both archival and
> non-archival, and non-archival submissions "go through the same review process as archival ones".
> Formatting follows the EMNLP 2026 / ARR guidelines using the official ACL style templates.
> Under those guidelines (<https://2026.eacl.org/calls/papers/>, read the same day) references and
> appendices are **unlimited**, and the Limitations and ethics sections **do not count** toward the
> limit. No separate appendix limit is specified.
>
> **Owner's decision, 2026-08-03: target the FULL-PAPER format, up to 8 pages, same review
> process.** The reasoning, recorded so it can be argued with rather than around: after every
> legitimate structural lever the residual overflow was still 10 lines, measured from a build; the
> paper grew *as it became more correct*, through scoping, definitions and qualifiers; compression
> introduced a factual defect three times out of three; and at four pages the Limitations section
> needed explicit protection all session, which at eight it does not.

```text
Target venue:            UncertaiNLP 2026 (FULL paper, up to 8 pages; short is 4)
Template:                ACL, acl.sty, unvendored (no upstream licence), pinned fetch recorded
Main tex:                docs/writeup/uncertainlp-2026-short.tex
Build status:            PASS — 5 pages, content ends 85% down page 4, 0 errors, 0 overfull,
                         0 undefined refs/citations, 0 missing files (parse_build_log.py)
Citation check:          PASS — no missing or duplicate keys (check_citations.py)
TODO/placeholder check:  PASS — no markers (check_todos.py)
Checklist status:        MISSING — *ACL responsible-NLP checklist not yet written (R6)
Limitations status:      PASS — present, honest, non-contradictory
Reproducibility status:  PASS — every figure resolves to a committed artifact
Figure/source status:    PASS — vector PDF, generator script, refuses to draw on artifact mismatch,
                         greyscale-verified
Known reviewer risks:    R1, R2 high; R3-R5 medium
Known packaging risks:   R6 only. Camera-ready check reports three fails (author metadata,
                         acknowledgments, checklist) — the first two are CORRECT for anonymous
                         review and are a tool-mode mismatch, not defects.
Next actions:            R1 and R2 before any re-submission; both packets still need re-review
```

## Final Self-Review Statement

```text
The paper is currently strongest on the three-mechanism decomposition and on evidence traceability.
The highest remaining reviewer risk is that the certified figures use the conservative audit's
Hoeffding bound while the framework's primary construction is empirical Bernstein, and the paper
does not name either.
The main evidence supporting the central claim is evidence/plan3/calibration_diagnostics.json,
reproducible with `uv run conformalextract calibration-diagnostics`.
Claims intentionally weakened or removed: "a perfect ranking would clear the floor" (refuted on
review, removed); "grounding and certifiability are orthogonal" (narrowed to a dissociation).
Submission-blocking issues: R1, R2, and both outstanding review packets.
```
