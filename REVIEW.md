# REVIEW.md — ConformalExtract

Projects the org reviewer rubric into this repo so a repo-local agent can self-review with zero extra
context.

**Green command (external signal — must pass before any hand-off):**
```bash
uv run pytest -q && uv run ruff check . && uv run mypy
```

## The 6-point rubric
1. **Correctness** — does it do what the plan/gate/ADR says? Edge cases, off-by-ones, bad refs. For
   statistical code, verify against the paper (theorem-to-code), not just that tests pass.
2. **External signal** — the green command passes; CI green. No stub/placeholder tests; assertions must
   assert something real.
3. **Scope** — inside the current gate/plan (`docs/plan2/`, `docs/plan3/`); no scope creep; descopes
   recorded in an ADR (e.g. `docs/adr/0002` single-seed, `0003` context ladder).
4. **Safety / reversibility** — no secrets committed; no destructive ops; **raw text, sealed labels,
   checkpoints, and predictions-with-recoverable-text are gitignored/private, never tracked.**
5. **Fit** — matches `CLAUDE.md` conventions, the gated doctrine, and prior ADRs.
6. **Learning** — a genuine mistake gets a recorded lesson (ADR or evidence note), not just a fix.

## Repo-specific gates (this project's non-negotiables)
- **Claims-vs-reality:** every metric in the README/report/cards traces to a committed evidence artifact
  + the command that produced it. "certified" appears only behind an independent reviewer PASS.
- **Honesty boundary:** synthetic/random-token benchmarks ≠ measurements of real extraction quality;
  infeasibility/negative/shift-failure are reported as first-class results; in-domain guarantees are not
  claimed under shift; not "production-grade".
- **Label isolation:** training/scoring never read `certification`/`final`/`shift` gold; expect
  `sealed_reads: 0` in run evidence; the label-access hash chain must verify.
- **Paid-run discipline:** any HF-Jobs spend has explicit Ross approval and fits the \$25 aggregate cap;
  the run's cost is recorded; ephemeral downloads are checksum-verified and raw is deleted before model
  load.
- **Licence/provenance:** RAMS/WikiEvents raw text is non-redistributable — recorded and enforced.
- **No-secrets sweep:** `.env` gitignored; no tokens/keys in tracked files.
- **Scope-matches-sentence:** **A check's scope and its sentence must match. Before writing a
  verdict, say which command produced it and what that command cannot see.** `git grep` and
  `git ls-files` cannot see untracked files; a tracked scan is not a repository scan; a sample is
  not a census; and a correction inherits the defect class it corrects unless you re-derive the
  claim from the new evidence rather than the arithmetic already in hand. Four instances on
  2026-07-28 — a cost total that omitted a figure recoverable from citations the same change had
  just added; a draft asserting a citation count that a later fix made stale; a hygiene report that
  introduced the paths it existed to remove, unseen by its own `git grep`; and the reviewer record
  diagnosing all three, which asserted a repository-wide zero on the strength of a scan it had not
  run. **The seat tasked with the human check is the one that failed it**, which is why the
  operator-path half is now `tests/test_internal_paths.py` and carries a named exclusion list
  instead of a count.
- **No operator paths in prose:** enforced by `tests/test_internal_paths.py` over tracked **and
  untracked** files. Exceptions are named in `ALLOWED` with the reason each cannot do its job
  without the string, and an exception that stops matching fails the suite.
- **A document that asserts a gate state must be reconciled before it is used, not after.**
  Three instances now: the README said "Plan 1 is active" through Plan 3 (fixed 2026-07-28);
  `main` sat eleven days behind the branch that corrected it, so the only story a reader could
  reach was the wrong one; and `docs/plan4/accepted-plan.md` opened Plan 4 still saying Plans 1–3
  were "not implemented" (amended 2026-07-29). The last is the worst, because that document
  *governs the release* and every artifact built from it would have inherited the error. **Gate
  state is asserted in prose and checked nowhere** — `verify-claims` checks claim citations,
  `test_doc_references` checks identifiers resolve, and neither reads a status line. Until that is
  mechanical, reconciling a status line against `docs/gate0/decision.md` and the reviewer records
  is a manual step at the *start* of using any planning document.

**Verdict vocabulary:** PASS · PASS-WITH-NITS · BLOCK. A BLOCK escalates to the human Reviewer seat.
For Plan 2 specifically, the independent reviewer basis is `docs/plan2/reviewer-brief.md`.

## Why scope-matches-sentence is a gate and not a lesson

It sits above because it fires at the *start* of a review. A lesson in a retrospective fires never.

The sibling repo `redteam-foundry` reached the same gap independently in the same week, from the
other direction: six metrics there were satisfied by the *absence* of the thing they measured, so
each metric's scope did not cover what its **name** claimed. Here a check's scope did not cover what
its **sentence** claimed. Same failure one level up — measurement versus report rather than
measurement versus name — and in both cases the artifact passed every mechanical check it had.

Its six instances are catalogued in that repo at
`docs/findings/what-does-this-metric-return-when-nothing-happened.md`. **That document holds the
instances; this gate holds the mechanism.** Read them together — either alone understates the
problem, because the catalogue reads as six bugs in one harness and the gate reads as one habit in
one seat, when it is a single failure mode that neither repository's mechanical checks could see.
The reciprocal pointer from that catalogue back to here has not been made: that repo is closed and
this is not the place to commit to it.

Two repositories arriving at it independently is the argument that it is a real pattern rather than
a local habit, and the reason it is written as a standing check rather than a war story. The
general form: **a name, a metric and a verdict are all claims about scope, and none of them is
checked by the thing they describe.**
