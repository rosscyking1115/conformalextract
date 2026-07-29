# Proposed: make the repository public

- Status: **PROPOSED. Not accepted, not acted on. The repository is PRIVATE and stays private until
  this is ruled on.**
- Date: 2026-07-29
- Author: implementer. **Requires independent review.**
- Open decision 5 in [`open-release-decisions.md`](open-release-decisions.md)

## Why this is its own request

The staged-release amendment was rejected on 2026-07-29, and the reviewer's most useful finding was
not one of its three grounds. It was this: **the seven-item minimum was never what kept this
repository private.** §1 of the accepted plan governs the public *contribution*; **visibility is not
one of the seven items.** That amendment asked "may we ship fewer than seven?" when the actual goal
is a public repository — a different question, with different gates.

So this is routed on its own, not as a scope cut and not as an amendment to §1. **The reviewer
explicitly did not rule that a bare visibility flip is permitted**, so this is a real question.

## What a visibility flip actually does

> **Corrected 2026-07-29 on independent review.** The first version of this section said 199 tracked
> files and 14 internal-audience files. Both were wrong. The count was 200 at the commit this
> document was committed in — the table described the tree *one commit earlier*, **and the single
> file it omitted was this document**. The internal-audience list was 24, not 14. A document arguing
> that a visibility flip publishes more than people expect, which itself undercounted what would be
> published and excluded itself from the count. Corrected below; the error is left recorded rather
> than quietly fixed.

**It is not a release of selected artifacts. It publishes all 200 tracked files at once**, including
every file never written for an outside reader. Enumerated rather than characterised:

| Count | Category | Written for an outside reader? |
|---:|---|---|
| 41 | evidence artifacts | yes — this is the contribution |
| 41 | tests | yes |
| 27 | other docs (ADR-adjacent, results, glossary) | mostly |
| 25 | source code (Apache-2.0) | yes |
| 14 | configs / scripts / manifests | yes |
| 12 | root files (README, REVIEW, CONTRIBUTING, AGENTS, CLAUDE, SECURITY, LICENCE…) | yes |
| 12 | ADRs | yes |
| 8 | remote job scripts | yes |
| 2 | write-up draft, no venue | **no — explicitly not a submission** |
| 6 | internal launch and reviewer briefs | **no** |
| 4 | accepted plans | **no — external planning documents, in-repo as historical record** |
| 2 | agent handoffs | **no** |
| 2 | agent tooling specs | **no** |
| 2 | frontier-check notes | **no** |
| 1 | CI | yes |

**Twenty-four files were written for an internal audience** and would go live unreviewed as public
prose:

| Group | Files |
|---|---|
| Accepted plans (external planning documents) | `docs/gate0/`, `docs/plan2/`, `docs/plan3/`, `docs/plan4/accepted-plan.md` |
| Launch and reviewer briefs | `docs/plan2/`: `r0-launch-plan`, `r1-launch-brief`, `r2-launch-brief`, `prediction-generation-launch-brief`, `reviewer-brief`, `reviewer-brief-extraction-policy` |
| Agent handoffs | `docs/plan2/claude-code-handoff.md`, `docs/plan3/HANDOFF-2026-07-22-reanalysis.md` |
| Agent tooling specs | `docs/superpowers/plans/…`, `docs/superpowers/specs/…` |
| Frontier-check notes | `docs/frontier-check/findings.md`, `pre-paid-run-gate.md` |
| **Agent instructions** | `CLAUDE.md`, `AGENTS.md` — first version of this table wrongly marked these "written for an outside reader" |
| **Process records from this week** | `docs/progress.md`, `docs/release-check-2026-07-28.md` |
| **Plan 4 deliberation, including this file** | `open-release-decisions.md`, `publishable-and-sealed.md`, `proposed-amendment-staged-release.md`, `proposed-visibility-change.md` |

Two of those deserve naming individually.

**`docs/progress.md` is a stale gate-state assertion.** It is a PMO log signed "Manager (Codex)",
frozen at 2026-07-17, closing on *"Plans 3–4 remain sequentially blocked"* — which was true then and
is not now. A public reader would meet it as a current statement of where the project stands, and
the README links to it. It is the same defect corrected in the README on 2026-07-28 and in the Plan
4 accepted plan on 2026-07-29, in a third file, still uncorrected.

**This document is on the list.** A deliberation about whether to publish becomes, on publication,
a public document. That is not an argument against publishing it — the reasoning is honest and the
project's whole position is that its records are checkable — but it is an argument for reading it as
public prose first, which has not been done.

**This is the substance of the request, and it is what makes it a real question rather than a
formality.** Every prior release decision in this project has been about *whether a particular claim
may be published*. A visibility flip bypasses that model entirely: nothing is selected, nothing is
assembled, and the claim ledger — which governs what may be *said* — has nothing to say about a file
simply becoming readable.

## Gate status of the plans themselves (required by R5, and omitted from the first version)

- **Plan 3 is not formally closed.** Five Plan 3 reviewer records exist and none carries
  `review_kind: "plan_close"`. The only close record in the repository is Plan 2's.
- **Plan 4 was opened by the owner on 2026-07-29** while that remained true. Under the gated
  doctrine — Plan N+1 opens only after Plan N's independent reviewer PASS — that is an owner
  override of the sequence, not a satisfied gate, **and this document should have said so before
  proposing anything.** It is surfaced here rather than left for a reader to infer.

## What gates it

1. **Decisions 1–3, now ruled.** Decision 1 (reviewer records publish as-is) is a **precondition**,
   not merely a bundle question, because a flip publishes those records with no assembly step.
   Satisfied. Decision 2 (description) is drafted but not yet reviewed. Decision 3 (topics)
   satisfied.
2. **§17's evidence-acceptance checklist**, headed "before public release". Twelve boxes, and the
   rejection ruling established that they bind. **They have not been walked.** One of them —
   `GitHub, Hugging Face and Kaggle drafts are cross-linked and inspected` — cannot be ticked
   without items 5 and 6, which is precisely why the staged split was refused. **This is the hardest
   gate and it is unresolved.**
3. **The operator-path gate** (`tests/test_internal_paths.py`) — passing, and its `ALLOWED` list now
   becomes a public statement rather than an internal one.
4. **The fourteen internal-audience files above**, none of which has been read as public prose.
5. **The write-up draft**, which is explicitly not a submission and would become a readable draft
   with no venue attached.

## The reviewer's ruling on separability, 2026-07-29

Recorded here because it answers the question this document asked
(`evidence/plan4/reviewer_record.visibility-and-description.json`):

**Visibility *is* separable from §17's twelve evidence-acceptance boxes** — five of them (frozen
release candidate, immutable release manifest, adapter replay, cross-linked HF/Kaggle drafts, V12
fresh-download) are unsatisfiable by construction for a bare repository, so reading §17 as gating
visibility would make visibility unreachable without the seven items, which §1 never says. **It is
not separable from §2.1's licence, privacy and link audit node.**

The gate it set, which visibility must clear:

| | Gate | Status |
|---|---|---|
| G1 | **Plan 4 open on a Plan 3 close record** | **UNSATISFIED — above everything else.** Plan 3 has none. |
| G2 | V8/V9 re-walked at the flip commit | not done |
| G3 | operator-string disclosure matching what actually ships | corrected 2026-07-29; now accurate |
| G4 | decisions 1, 2, 3 each with a review record | 2 has one; 1 and 3 are owner policy calls |
| G5 | every internal-audience file read as public prose, against a correct enumeration | not done — 24 files |
| G6 | gate-state reconciliation | `docs/progress.md` outstanding |
| G7 | recorded acknowledgement that the act has no rollback | this document, §"The risk" |

**This does not authorise a flip and does not reopen the seven-item minimum.**

## The honest position

**The implementer is not proposing that visibility be flipped now.** Gate 2 is unresolved and gate 4
has not been attempted. What is proposed is narrower:

- **Rule on whether visibility is gated on §17 in full**, or whether §17 gates the *public
  contribution* (the seven items) while visibility is a separate act with its own, smaller gate. The
  accepted plan does not obviously answer this — §17 is headed "before public release", and whether
  "release" means the seven-item contribution or the act of becoming readable is the question the
  staged-release rejection turned on without settling.
- If visibility is separable: **rule on what its gate should be**, given the fourteen files.
- If it is not separable: say so, and the repository stays private until the seven items exist.

**The risk, stated against my own preference and without theatre.** A public repository is what Ross
wants and it is the outcome this project has been built toward. The argument for waiting is not that
"a public repository has no reviewer" — that was the first version's closing line, and it is both
theatrical and against this document's own premise, since the point of publishing is that outside
readers *can* check the work.

**The real argument is irreversibility.** §11 gives R1, R2 and R3 explicit rollbacks and §9.3 gives
a correction procedure; none of them reaches a fork, a cache, or an archive. Every other release
step in this plan can be withdrawn. A visibility flip cannot. That asymmetry — not the absence of
review — is why 24 unread files matter more here than they would anywhere else in Plan 4.
