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
  **Known uncovered class, by design, not oversight:** the patterns match the *shape* of a path and
  deliberately hardcode no username, since a test containing the operator's account name would be
  the leak it exists to prevent. The consequence is that a **bare account name** — not inside a path
  — is not covered. Measured 2026-07-29: it appears in 19 tracked lines across two files, and the
  private-planning-directory name in 31 occurrences across three. Decision 1 in
  `docs/plan4/open-release-decisions.md` accepts this knowingly. Do not "fix" it by hardcoding the
  name.
- **Check what a limitations list DROPPED, not just whether what it kept is true.** When a finding
  is carried forward, carry the uncomfortable half. `CX-SERVING-01` inherited both *reassuring*
  probe limitations — divergence is quality-neutral, and concentrates in low-confidence frames —
  and dropped the one that cut against the result: the abstain/extract decision itself flips
  between stacks at 1.3–1.8% at plausible operating points, with two of four flips surviving into
  the accepted set. Plan 2's close had directed that finding into "Plan 4 limitations and any
  model/report card". It reached neither, for eight days, and no check noticed.
  **This is a distinct mechanism and it defeats every other gate here.** Elsewhere the defect has
  been a claim outrunning its evidence, or a check that could not fail — both detectable by reading
  the artifact. Selective carrying-forward leaves every surviving sentence *individually true*, so
  claim-fidelity, forbidden-wording and citation checks all pass. **A limitations list that is
  individually true and collectively flattering is invisible to all of them.** The only way to
  catch it is to diff against the source that raised the findings and ask which ones did not make
  the journey — so when a review carries items forward, list them and tick them off by name.
  **The list must live in the RECEIVING document, not only in the review that raised the items.**
  Plan 2's four carried items *were* listed — in Plan 2's close record — and a later reviewer still
  had to find that record to discover one was missing. The obligation has to travel with the work.
  Pattern: `docs/plan3/carried-forward-from-plan2.md`. **A close may not be issued while any
  carried item is untracked.**
- **A withdrawn claim lives wherever it was copied, and the ledger is not the inventory.** When
  `CX-GROUNDING-ORTHOGONAL-01` was narrowed, the retired attribution was still live in three
  publication surfaces the ledger knows nothing about, and `verify-claims` was green throughout.
  `evidence/withdrawn_assertions.json` plus `tests/test_withdrawn_assertions.py` now search tracked
  prose for the **phrasing**, not the claim ID, because a copy carries the words and drops the
  identifier. It found two further surfaces on its first run — one of them regenerated minutes
  earlier by the author enumerating the list. **An inventory assembled from memory is short.**
  **Limit, and it cost something immediately: a paraphrase defeats a phrase search.** Two surfaces
  carried the same attribution in other words and passed the new check clean — including
  `certification-result.md`, in a *stronger* form naming two taxonomy categories, on the primary
  result document six claims cite. Found by a reviewer, not the test. **When a claim is reworded,
  read its copies; do not delegate that to the search.**
- **"Carried forward" is a behaviour, not a field.** A review can express it in more than one
  place, and reading the key that looks like the list is not reading the record. Plan 2's close
  carried items in two structures; the register built to stop carried items being dropped was built
  against the one that did not contain the dropped item, and extending it found two more elements
  that never arrived. **Every one of the four droppings was a qualifier on a reassurance that did
  travel.** Nothing flattering was ever lost. Check the whole record, and check what the surviving
  items were qualifying.
- **Cite one source per figure. A count and its description must come from the same place.** The
  staged-release amendment argued from "four documented instances of a record drifting" — taking the
  **count** from the scope-matches-sentence gate above (four instances, none of which is drift) and
  the **description** from the gate-state gate below (three instances, which are). Exactly one of
  the four fits. It reads as an evidenced claim and is a splice of two. **It was written one commit
  after `tests/test_internal_paths.py` landed to enforce this class**, by the author who had just
  written the enforcing test — so proximity to the lesson is not protection. When a sentence cites a
  number and a phenomenon, check they came from one source before checking whether either is right.
  **This gate missed its author's first violation.** It was added on 2026-07-28; on 2026-07-29 the
  same author quoted "~16×" from `CX-GROUNDING-ORTHOGONAL-01` while citing `CX-GROUNDING-01`, in a
  commit three files away from the gate forbidding exactly that — and the figure was also mis-stated
  (~16× is the reduction in ungrounded spans, not the grounding rate, which moved 2.4×). It was
  caught by a reviewer, not by the gate. Recorded because **a gate that misses its own author's
  first violation needs to know that**: this one is a check a reader performs, not a check the suite
  runs, so writing it down did not make it fire.
- **Gate state now has one derived home.** `evidence/gate_state.json` summarises it and
  `tests/test_gate_state.py` holds that summary to the reviewer records — a real gate. The
  superseded-assertion list in the same file is a **tripwire**: it catches known-stale phrasings
  returning and cannot detect a gate-state error phrased any other way. Its first version missed the
  very file that provoked it, because the phrase was wrapped across two lines. **Reconciling a new
  document's prose against the records remains manual**, which is why the check below stays.
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
