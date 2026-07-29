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

**It is not a release of selected artifacts. It publishes all 199 tracked files at once**, including
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

**Fourteen files in the last five rows were written for an internal audience** and would go live
unreviewed as public prose:

```
docs/gate0/accepted-plan.md          docs/plan2/r1-launch-brief.md
docs/plan2/accepted-plan.md          docs/plan2/r2-launch-brief.md
docs/plan3/accepted-plan.md          docs/plan2/reviewer-brief.md
docs/plan4/accepted-plan.md          docs/plan2/reviewer-brief-extraction-policy.md
docs/plan2/claude-code-handoff.md    docs/plan2/prediction-generation-launch-brief.md
docs/plan3/HANDOFF-2026-07-22-reanalysis.md    docs/plan2/r0-launch-plan.md
docs/superpowers/plans/2026-07-18-rams-profiles-generator.md
docs/superpowers/specs/2026-07-18-rams-profiles-generator-design.md
```

**This is the substance of the request, and it is what makes it a real question rather than a
formality.** Every prior release decision in this project has been about *whether a particular claim
may be published*. A visibility flip bypasses that model entirely: nothing is selected, nothing is
assembled, and the claim ledger — which governs what may be *said* — has nothing to say about a file
simply becoming readable.

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

**A one-line summary of the risk, stated against my own preference:** a public repository is what
Ross wants and it is the outcome this project has been built toward, but a flip made before those
fourteen files are read is a release of unreviewed prose, and this project has now produced five
documented instances of prose asserting something its own records contradict. Four of them were
found by review. A public repository has no reviewer.
