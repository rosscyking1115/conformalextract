# Project governance

This page holds the process detail that used to sit in the README: how the work was gated, where
each gate stands, and how the evidence is checked. It was moved here unchanged on 2026-10-28 so the
README could start with what the project is. The authority for gate state is
[`evidence/gate_state.json`](../evidence/gate_state.json); if this page and that file disagree, the
file wins.

Contributor and agent rules — approvals, review gates, spend — are in
[`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`AGENTS.md`](../AGENTS.md). The review standard is
[`REVIEW.md`](../REVIEW.md).

## Gate state

The repository is executed through four sequential evidence gates. Each plan opens only after an
independent reviewer PASSes the one before it.

| Plan | Scope | State |
|---|---|---|
| **Plan 1** (Gate 0) | feasibility, licences, evaluator, statistics, paid smoke tests | **complete** — gates 0A–0F pass, Gate 0 decision `go`, consolidated reviewer PASS 2026-07-17 |
| **Plan 2** | QLoRA training, prediction generation for three systems | **closed** — independent reviewer PASS 2026-07-21 (`evidence/plan2/reviewer_record.plan2-close.json`) |
| **Plan 3** | certification against the sealed split | **closed** — 2026-10-27, on an independent fresh close review and its delta ([`reviewer_record.plan3-close-fresh-delta.json`](../evidence/plan3/reviewer_record.plan3-close-fresh-delta.json), PASS-WITH-NITS at `d8d2223`), after the 2026-07-29 close was refused on findings O1–O3 ([`reviewer_record.plan3-close.json`](../evidence/plan3/reviewer_record.plan3-close.json)) |
| **Plan 4** | verification, public release, write-up | **open** — opened by owner override on 2026-07-29 and paused; the override lapsed on 2026-10-27 when Plan 3 closed, so the gate now stands on its merits ([`evidence/gate_state.json`](../evidence/gate_state.json)) |

Plan 3's certification ran once, on 2026-07-22, and returned infeasibility for all three systems.
`evaluate-final` and `evaluate-shift` are descoped ([ADR 0010](adr/0010-descope-final-and-shift.md))
because no selected policy exists to audit or transport — not for cost or effort. A subsequent $0
re-analysis ([ADR 0011](adr/0011-reanalysis-frontier-and-loss-channels.md)) was reviewed over
four independent passes, opening at BLOCK and closing with the publication condition lifted and no
blocking items.

The paper is a draft, [`docs/writeup/uncertainlp-2026-short.tex`](writeup/uncertainlp-2026-short.tex),
in preparation for UncertaiNLP 2026 and not submitted; its status and the review steps that still
gate it are in [`uncertainlp-2026-short.md`](writeup/uncertainlp-2026-short.md). The first draft
([`draft-2026-07-28.md`](writeup/draft-2026-07-28.md)) is kept as a record. What the paper may claim is
fixed by the list in [`docs/plan3/certification-result.md`](plan3/certification-result.md)
("What may and may not be claimed"), and that list is narrower than the results might suggest.

## How the evidence is held to account

The gate discipline is the substantive engineering contribution here, and it is enforced rather
than described.

- **An independent reviewer, with a real BLOCK verdict.** Review is performed by an agent that did
  not implement the work under review, against [`REVIEW.md`](../REVIEW.md), with the verdict vocabulary
  PASS · PASS-WITH-NITS · BLOCK, and it is recorded as a committed artifact
  (`evidence/*/reviewer_record*.json`). BLOCKs have been issued and have held up work — on the
  QLoRA smoke test (below) and on the ADR 0011 re-analysis, where the reviewer reproduced the
  load-bearing numbers by from-scratch reimplementation with zero mismatches and still blocked on
  six items — including a `--roles` hole that would have let a sealed split be opened while the
  artifact attested zero reads of it.
- **A bit-exact reproducibility gate on quantized model loading.** Gate 0F's paid QLoRA smoke test
  was BLOCKed on a mismatch in generated tokens between two independently quantized loads of the
  same base model. The fix aligned k-bit preparation, gradient checkpointing, cache and generation
  state across both inference paths; **exact equality was retained as a hard gate** rather than
  relaxed to a tolerance. The corrected run reproduced exact adapter and greedy-token hashes in a
  fresh process. ([`docs/gate0/decision.md`](gate0/decision.md), [`docs/progress.md`](progress.md))
- **SHA-256 matched across storage boundaries.** Remote job artifacts are hashed on the private Hub
  and against the in-Git evidence copy, and both must agree — e.g. Gate 0F at `adb61606…`, pinned to
  Hub revision `840fb41e…`. Separately, the certification artifact is pinned at `71c0de3e…` over
  git-canonical (LF) bytes; a Windows working copy is checked out CRLF and hashes differently, and
  that correction is recorded ([`docs/plan3/certification-result.md`](plan3/certification-result.md))
  rather than left as a trap for an independent verifier.
- **Per-job cost recorded for every job but one** — in a per-job evidence artifact for Gate 0
  ([`evidence/gate0/hf_jobs_submission_attempts.json`](../evidence/gate0/hf_jobs_submission_attempts.json)),
  and in each run's launch brief or result document for Plan 2 — against a hard aggregate ceiling
  enforced in code (`training.REMAINING_BUDGET_USD` = $24.7992, the $25 cap less $0.2008 of prior
  recorded spend), with a run ledger imposing R0→R1→R2 order. No single spend ledger exists and the
  figures are price×duration estimates, not billed amounts
  ([ADR 0012](adr/0012-cost-claim-evidence-correction.md)).
- **Claims cannot outrun their evidence — as far as the paths, and no further.**
  `conformalextract verify-claims` fails closed if a claim's cited evidence is missing or not
  git-tracked, and a regression tripwire refuses a claim that holds a public surface while its own
  verification literally reads as pending. **What it does not do is open the file.** It compares no
  number and sees no configuration, so `verify-claims ok` means the paths resolve, not that the
  claims check out — and a claim quoting a figure that appears nowhere in its own evidence passes
  unchanged. That gap is the mechanism behind five quoting errors this project made and records
  (`docs/plan4/open-release-decisions.md`, 2026-08-03; `docs/writeup/uncertainlp-2026-short.tex`,
  Limitations). It is named rather than closed, which is the honest state of it. What *is* enforced
  by reading files: the generated claims appendix must be byte-identical to what the ledger renders,
  and every test named in the docs must exist.
- **Sealed roles are guarded, not merely logged.** Only `development` and `certification` are
  reachable from the analysis commands; every other role raises before a file is opened. A test
  discovers the command list by introspection, so a *new* unguarded command fails rather than
  passing silently.

Typing and tests are strict: **`mypy` runs with `strict = true`** over the package (which ships
`py.typed`), `ruff` is clean, and **the suite is green — total not asserted.** It previously read
"the suite is 349 tests, all passing"; that figure was stale and, being a count nothing re-checks,
it is the same defect class as an unverified claim. Run the commands in the README's [Quick start](../README.md#quick-start) and read your own
number. The green command must pass before any hand-off.
