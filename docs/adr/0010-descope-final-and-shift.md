# ADR 0010: Descope `evaluate-final` and `evaluate-shift` — the precondition does not exist

- Status: accepted (independent reviewer instruction, post-execution certification review,
  `evidence/plan3/reviewer_record.certification.json`)
- Date: 2026-07-22
- Trigger: the certification run returned **Infeasible for all three systems**
  (`docs/plan3/certification-result.md`). Both remaining Plan 3 stages take a *selected policy*
  as input. There is no selected policy.

## Decision

**Do not open the final in-domain split. Do not open the shift split.** Both remain sealed and
unopened. `evaluate-final`, `evaluate-shift` and `render-report` stay `_not_ready` stubs.

## Why — the precondition, not the cost

This is **not** a budget or effort decision, and must never be described as one. **Both commands
are $0 and require no GPU** (plan §13.4). Framing a principled stop as an abandoned one would
misrepresent it.

The reason is that the input does not exist:

- **`evaluate-final` audits transport of a selected policy** from certification to a fresh
  in-domain sample (§3.3: "exactly one policy per system is selected or marked infeasible" — the
  precondition is satisfied, all three are marked infeasible). But `selected_candidate` is `null`
  and `n_accepted` is `0` for every system in `evidence/plan3/certification_result.json`. There is
  no threshold to transport and no accepted set to audit. The command could only emit a vacuous
  artifact.
- **`evaluate-shift` tests whether an in-domain guarantee survives distribution shift.** There is
  no in-domain guarantee to carry. Plan §2.4 already forbids labelling any transferred point
  "certified"; with nothing certified in-domain, the stage has no object at all.

## Why opening them anyway would be worse than useless

Each split is a **one-shot resource**: once opened it can never again serve as a clean held-out
sample for this corpus. Opening final would spend that resource to answer no new question, and
the question it might have answered — does the null reproduce out of sample? — **is already
answered**: the oracle diagnostic gives QA 3.02% max acceptance on development against 2.01% on
certification, the same conclusion on two independent splits.

Keeping both sealed preserves them for future work at a different target, with a better score, or
with a different model — which is the outcome most likely to need them.

## Consequences

- Plan 3 ends at certification. Its deliverable is the negative result, not a report over
  final/shift evidence.
- The label-access position is unchanged and verifiable: `final_reads: 0`, `shift_reads: 0` in the
  certification artifact, and `certification_run.build_certification_access_log` raises
  `SealedRoleError` on `final` and `shift` by construction, so neither can be reached from the
  certification path.
- Any future work that wants these splits must re-open this ADR and state what question the
  opening answers — the bar being that the question cannot be answered on development.
- **Per plan §6.3, α is not relaxed.** Nothing here proposes, computes or hints at a softer target
  to obtain a positive result; a laxer α after seeing this outcome would invalidate the finding.
