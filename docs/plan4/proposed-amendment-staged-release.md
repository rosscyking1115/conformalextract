# Proposed Plan 4 amendment — stage the public contribution

- Status: **REJECTED, 2026-07-29.** The seven-item minimum stands and release work is built against
  `accepted-plan.md` §1 as written.
- Date proposed: 2026-07-29
- Ruling: [`evidence/plan4/reviewer_record.staged-release-amendment.json`](../../evidence/plan4/reviewer_record.staged-release-amendment.json)
- Governs: nothing. Retained as the record of a request that was made and refused.

> ### Rejection — 2026-07-29
>
> Appended, not rewritten; the proposal below stands as made so the reasoning that failed stays
> legible. **Three findings, any one sufficient:**
>
> 1. **§1 does not stand alone, and the rest of the plan settles sequencing against this split.**
>    §2.1 drafts the GitHub/HF/Kaggle candidates at *one* node with *one* licence and link audit
>    before *one* public act. §17's evidence-acceptance checklist, headed "before public release",
>    contains `[ ] GitHub, Hugging Face and Kaggle drafts are cross-linked and inspected` — **Stage
>    A cannot tick that box by construction**, and this proposal never mentions it. Meanwhile §11 R3
>    already publishes GitHub → HF → Collection → Kaggle *in that order*, so the GitHub-first
>    sequencing was already granted; what was actually requested was deferring the **building** of
>    items 5 and 6, which is a different thing and a weaker case.
> 2. **The "copy of another item" line fails on facts, not merely on principle.** §7.1 states
>    plainly that *"Kaggle will not be a redundant model mirror by default. Its distinctive
>    contribution is an accessible, CPU-compatible learning artifact."* §7.2 then imposes eleven
>    requirements — a plain-language rendering of α/δ/Infeasible, the conservative audit shown
>    beside the certifier, an educational walkthrough — none of which exists in any other item.
>    **Item 6 is the largest genuinely new work in the deferred set.** The objection this document
>    flagged as unanswerable was unanswerable because the premise underneath it was false.
> 3. **The plan already authorises two routes to a smaller release, and this proposal cited
>    neither.** §15: *"Kaggle environment cannot run method → … omit notebook until it can pass."*
>    §17's first evidence line: *"Plans 1–3 gates pass **or the release scope is reduced
>    explicitly**."* The seven are reducible — by a declared, failure-triggered reduction, not by
>    re-reading the word "minimum".
>
> **Two errors in the proposal's own reasoning, recorded because they are the point of keeping it:**
>
> - **The staleness argument was partly recruited.** "Four documented instances of a record drifting"
>   takes the *count* from `REVIEW.md`'s scope-matches-sentence gate (four instances, none of which
>   is drift) and the *description* from the gate-state gate (three instances). Exactly one — `main`
>   sitting eleven days behind — genuinely fits. **The document committed the defect class it cited,
>   one commit after the tests enforcing that class were added.** §3.2, §5.1 and §9.3 already answer
>   staleness with hashes and immutable revisions, which the proposal did not engage.
> - **It contradicted itself**: "Stage A would make the repository public" against "It does not flip
>   repository visibility."
>
> **And the finding that matters most, which reframes the request rather than refusing it:** the
> seven-item minimum was **never** what kept this repository private. §1 governs the public
> *contribution*; **visibility is not one of the seven items.** This document answered "may we ship
> fewer than seven?" when the motivating problem was "Ross wants the repository public" — a
> different question, gated by different things (the §17 checklist, the operator-path gate, open
> decisions 2 and 3, and every prose surface going live at once). The reviewer explicitly did **not**
> rule that a bare visibility flip is permitted; it needs its own routing.

---

## The proposal as made, 2026-07-29 — refused, retained for the record

## The question

§1 names seven items as the **minimum useful public contribution**:

1. the tested extraction evaluator and certification library
2. an immutable, licence-safe evidence bundle with manifests, aggregate results and claim status
3. a CPU-compatible notebook reproducing the certificate, tables and figures from released evidence
4. a versioned GitHub research release
5. a Hugging Face evidence Dataset repository and Collection
6. a Kaggle evidence dataset plus reproducibility notebook
7. a paper-shaped technical report and outcome-conditional portfolio narrative

Ross wants the repository public. All seven before anything is visible is a long road. Staging is
defensible on its own terms — but **the plan says "minimum", and quietly reinterpreting a word like
that is precisely what this repository exists to prevent.** So the reinterpretation is proposed in
the open, with the argument against it stated as strongly as the argument for.

## Proposal

Split §1's seven items into two stages, with **no change to the total** and **no item dropped**.

**Stage A — repository visibility.** Items 1, 2, 3, 4 and a first-draft of 7.
**Stage B — external mirrors.** Items 5, 6 and the finished 7.

Stage A would make the repository public. Stage B would follow, gated on its own review.

## The case for it

- **Items 5 and 6 are distribution, not contribution.** A Hugging Face Dataset and a Kaggle dataset
  are *copies* of the item-2 evidence bundle on other hosts. They widen reach; they add no
  checkable content that item 2 does not already carry. If item 2 is sound, a reader can verify
  every claim from the GitHub release alone.
- **They are the items most likely to go stale.** This repository has now produced four documented
  instances of a record drifting from what it describes. A mirror on a third-party host is a fifth
  opportunity, on infrastructure with no test suite and no reviewer.
- **Item 6 has an unresolved dependency.** A Kaggle dataset requires deciding what ships in the
  public bundle — which is open decision 1 in `open-release-decisions.md` and is explicitly not
  being settled here. Stage B keeps items 5 and 6 behind that decision instead of forcing it.
- **Staging surfaces defects earlier.** A public repository gets read. Anything item 2 or 3 gets
  wrong is better found before it is mirrored twice.

## The case against it, stated fairly

- **"Minimum" is unambiguous, and this proposal reinterprets it.** §1 does not say "in stages" or
  "at least". A reader of the accepted plan would understand seven items as the floor. The honest
  description of this proposal is that it lowers the floor for a first release, not that it
  reorders work.
- **The staging argument is available for any item.** Nothing in the reasoning above is specific to
  5 and 6; "distribution, not contribution" could be argued about item 4, and a plan that yields to
  that argument once has no principled stopping point. This is the strongest objection and it is
  not fully answered — the reply is that 5 and 6 are the only two items whose *entire content* is a
  copy of another item, which is a bright line, but it is a line drawn after the fact.
- **Stage B may never happen.** Deferred release items in a portfolio have a poor completion record
  generally, and the plan's own §2.1 principle — evidence before narrative — is weakened if the
  evidence trail is "GitHub plus two promises".
- **§1's list may be load-bearing in a way the implementer cannot see.** It was accepted as a unit.
  The reviewer has the accepted plan and this repository's history; the implementer proposing to
  cut it is the party with the incentive.

## What this amendment does not do

- **It settles none of the three open decisions** in
  [`open-release-decisions.md`](open-release-decisions.md). It must not be read as deciding, by
  implication, that reviewer records ship (decision 1) — Stage A includes item 2, and what item 2
  *contains* is exactly decision 1, so **Stage A cannot be executed until decision 1 is answered by
  Ross.** That dependency is stated here so the amendment cannot quietly resolve it.
- It does not flip repository visibility. That is Ross's action, not this plan's.
- It does not change any claim, boundary, or the honesty doctrine.
- It does not create a Hugging Face or Kaggle artifact.

## Requested ruling

1. **Accept, reject, or amend the A/B split.** Rejection returns the seven-item minimum, which is a
   complete and workable answer.
2. If accepted, rule on whether Stage A's item 7 may be the **existing first draft**
   (`docs/writeup/draft-2026-07-28.md`, independently reviewed) or must be finished first.
3. Rule on the objection the implementer could not answer: **why 5 and 6 and not 4** — whether the
   copy-of-another-item line is principled or convenient.
