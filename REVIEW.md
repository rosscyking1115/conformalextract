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
- **A bound chosen to avoid false alarms is a bound chosen to miss partial failure. A floor detects
  collapse, not narrowing.** Not specific to scanning gates — it holds of any threshold standing in
  for a correctness condition: row counts, coverage percentages, timeout margins, sample sizes.
  The instance, measured: a `len(scanned) > 30` guard on a **63-file** corpus. Removing *every
  individual subtree in turn* still passed — `docs/plan2`, `docs/adr`, **the entire repository
  root**. Only re-rooting the walk to `glob` instead of `rglob`, leaving 6 files, tripped it. The
  bound was set low to avoid churn, and low enough to tolerate losing 51% of what it guarded.
  **Raising it does not fix it.** A floor at the true count becomes a number that must be edited
  whenever the corpus grows — the stale-count defect this repository already rejects elsewhere.
  There is no correct threshold, because a threshold is the wrong instrument.
  **The right shape is a cross-check against a second source of truth**, which needs no threshold
  and nothing kept updated: `test_the_markdown_scan_matches_the_index` asserts that no git-tracked
  file is missing from the walk (catches narrowing at any scale) and that nothing gitignored is
  present (catches over-inclusion, which no probe can see). When you reach for a bound, first ask
  what independent record could be compared against instead.
- **Overstatement in the self-critical direction is still overstatement, and it attracts less
  challenge than an amplification because it reads as humility.** A separate mechanism from the
  amplification rule below, and it runs the other way: the instances there were findings made
  *stronger* than their data; this is a **retraction that exceeded its evidence.**
  The instance: the guard-the-guard convention was reported as an assessment "false in three ways".
  It was not. The three findings concern **coverage**; the rule itself was sound, and the reviewing
  record said so verbatim — *"Rule 1 is correct as a RULE; only its evidence sentence is false"* and
  *"do not weaken or remove the rule"*. Only the evidence sentence — that the convention was
  already implemented — was false.
  **Why it attracts less challenge:** the party a concession costs is the party making it, so nobody
  else has an interest in auditing it, and it reads as rigour. A retraction that goes further than
  the data can cost a sound rule, and that cost lands on whoever needed the rule later.
  **Concede exactly as much as the evidence requires, and no more — then say which part survives, in
  the same breath.**
  **Corrected 2026-07-29, and the corrections are the point.** This bullet first said "*nothing*
  checks it", which its own instance refutes — a reviewer checked it, which is why the instance
  exists. It said such a retraction "*destroys*" a sound rule; here the rule survived and was
  broadened in the same round. **Self-critical overstatement inside the rule about self-critical
  overstatement**, twice, in the first draft. It also rests on **one** instance, against the
  two-instance bar the next bullet sets — kept as a rule because its mechanism is argued rather than
  induced, and flagged so a reader can discount it accordingly.
- **A check reports on the set it can see, and a clean result is evidence only if the set was the
  right one.** Not local to this repository — two instances in two days, in different repositories,
  from different parties. Here, `test_withdrawn_assertions` scanned `git ls-files`, so the file the
  commit was *adding* was untracked at run time and invisible; a red suite was reported as green.
  Elsewhere the same night, a scan whose directory change failed printed zero hits, and **a zero
  meaning "examined nothing" was indistinguishable from a zero meaning "found nothing"**.
  **The corollary that catches both: any check that can return zero must also report how many items
  it examined**, so an empty scan cannot render identically to a clean one.

  **Two guards are needed, not one, and conflating them is how B2 shipped.** A *cardinality* guard
  bounds what the scan reached. A *kind* guard proves it reads the right population — for a
  filesystem walk, a live probe that plants an untracked file and asserts the scan sees it. B2 was a
  failure of kind: the cardinality guard returned 202 and passed under the broken implementation.

  **Every gate that walks the filesystem needs the kind guard.** An earlier version of this rule
  said "a gate whose scope was itself the defect needs the kind probe too" — **that clause is only
  knowable in retrospect, so before B2 it would have licensed B2.** A rule that exempts a gate until
  it has already failed is not a rule.

  **Prefer a cross-check to a floor** — see the standalone rule below, which is the general form.

  **The unit is the gate, not the module.** A first version of this rule claimed four modules were
  guarded and named four companions. There are **six scanning gates across those four modules**, and
  one companion bounded a set with *zero overlap* with the gate it was credited with guarding —
  `test_the_derivation_finds_something` bounds 18 reviewer records; the tripwire beside it walks 63
  markdown files. **A rule verified against the set its author could see is the defect the rule
  describes**, which is why the enumeration is now by gate and each companion names the set it
  bounds.

  **Copy a scope decision's verification, not just its implementation — this is the subtlest of the
  three and the one to keep closest.** `test_internal_paths.py` had carried the untracked-file probe
  since the day before. The fix for B2 copied its *walk* and not its *probe*, which left the correct
  code with **no evidence that it was correct** — a state indistinguishable from the wrong code until
  something plants an untracked file. Reverting the walk demonstrates it: the probe fails, the
  cardinality guard still passes. **When you adopt a hard-won scope decision from elsewhere, adopt
  the test that proves it is the right kind, or you have inherited the conclusion without the
  argument.**
  Second half, and the reason this recurred: `tests/test_internal_paths.py` already walked the
  filesystem rather than the index, for exactly this reason, discovered a day earlier. The newer
  check did not inherit it. **A hard-won scope decision that lives in one check's implementation
  instead of a shared rule gets rediscovered the expensive way** — which is why it is written here
  rather than only in the file that learned it.
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
- **The sharpest instance of selective carrying, because the author knew the pattern and was
  working on it.** The claim ledger's version of a finding kept the antecedent — *2,003 of 2,515
  documents show both a false positive and a false negative, consistent with substitution* — and
  both prose surfaces **dropped that sentence while keeping the one that depended on it**, leaving
  "wrong-role, boundary and coreference errors share that signature" attached to a signature they
  cannot produce. **This happened inside the fix for the selective-carrying defect**, by the author
  who had recorded the pattern one commit earlier. Knowing a failure mode is not protection against
  it; a check is.
  **Keep the falsifier, not the sentence.** `fp = predictions − tp` and `fn = gold − tp`, so
  `fp − fn = predictions − gold` **identically** — a substitution yields one false positive and one
  false negative and contributes **exactly zero** to the excess. Anyone can check that in one line,
  and it outlives the prose it corrected. **When a claim rests on a decomposition, write down the
  identity that would refute it.**
- **Retiring an obligation by relabelling is worse than leaving it open.** An open item is visible;
  a relabelled one is closed with nothing having changed. R5 required a named finding to be
  registered; a commit message described it as a *different* item that had been done, and the
  obligation left the list without ever being met. **A discharge must name the item it discharges
  and point at where it now lives**, and a discharge that only asserts completion is not one.
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
  result document six claims cite. Found by a reviewer, not the test.

  **REQUIRED MANUAL STEP — nothing automated fills this gap.** When a claim is reworded or
  withdrawn, a reviewer reads the **primary documents** end to end and searches by *meaning*, not by
  string: `README.md`, `docs/plan3/certification-result.md`, the write-up, and any document the
  ledger cites as `evidence`. Register each paraphrase found in `withdrawn_assertions.json`
  afterwards so the literal check covers *that* wording next time — but the register is a record of
  what was found, not the finding mechanism. **Do not treat a green suite as coverage here.** The
  count of affected surfaces went 3 → 5 → 7 across three reports: two hand-assembled and one from a
  check with this known limit. A hand-assembled inventory is short by construction, and a
  literal-match check inherits the same shortness against paraphrase.
- **"Carried forward" is a behaviour, not a field.** A review can express it in more than one
  place, and reading the key that looks like the list is not reading the record. Plan 2's close
  carried items in two structures; the register built to stop carried items being dropped was built
  against the one that did not contain the dropped item. **A register is only as good as its source
  enumeration, and nothing checks the enumeration** — its absence is visible, but a register built
  on an incomplete enumeration looks exactly like a complete one. Reviewer records now carry a
  top-level `carried_forward` key so new obligations have one home; that does nothing for records
  already written, or for an obligation stated in prose. Enumerating a source record is a manual
  read of the whole record.
- **Record each carried item's DIRECTION: does it qualify a reassurance, or state a risk?** Across
  Plan 2's two lists, four items failed to arrive and **every reassurance survived**. That is the
  supported statement, and it is a real one-way asymmetry: nothing that flattered the result was
  lost. It is invisible to every check here because each surviving sentence is individually true.
  Recording the direction makes the asymmetry detectable **as a signal, without needing to establish
  intent** — which is neither knowable nor the point.
  **State it in the supported form.** The first version of this gate said "every omission qualified
  a reassurance"; that is false — two omissions were free-standing risk statements, and one
  qualifier travelled. An overclaim about overclaiming, in the gate recording the countermeasure.
  The bias is in **what survives**, not in what is lost.
- **A characterisation handed down from a reviewing seat gets less scrutiny than one derived
  locally.** A finding that arrives already looking like a conclusion skips the step that would have
  caught it. **Check a supplied characterisation against the data with the same effort you would
  spend deriving it**, and record where it came from, so a later reader can tell whether it was
  tested or inherited.

  **Three instances, same day, same source — which is why this is a rule and not an anecdote.**
  The heading first read "Two instances" above a three-item list, which is the stale-count defect
  described two bullets down.

  **Provenance caveat, and it applies to all three.** Each is attributed to the owner seat on the
  basis of conversation that leaves no trace in this repository, and **the sole source for that
  attribution is the seat the attribution favours** — this one. By the self-critical-overstatement
  rule above, the mirror holds: nobody has an interest in auditing an attribution that shifts blame
  away from the attributor. A reader should treat the *mechanisms* as the durable content and the
  *allocation* as unverified.
  1. The directional claim "every omission qualified a reassurance, nothing flattering was ever
     lost" was *supplied* and transcribed; its counter-example sat one row away in a table the
     transcriber already owned.
  2. The claim that the guard-the-guard convention was **already implemented** — that all four
     scanning modules carried a companion asserting the scan reached a plausible number of items.
     That is a factual claim and it is **false in three measured ways**: one companion bounded a set
     with zero overlap with the gate it was credited with guarding, the companion named as B2's
     countermeasure passed under the broken implementation, and the enumeration counted modules
     where the unit is gates.

  3. **The retrospective clause.** "A gate whose scope was itself the defect needs the kind guard"
     was supplied and accepted rather than derived — and it **would have licensed B2 before B2
     happened**, since a gate's scope being the defect is only knowable after the failure. A
     different failure shape from the first two: not an overstated finding but an *under-specified
     rule*, accepted because it sounded like a scoping principle. Replaced with: every gate that
     walks the filesystem needs the kind guard.

  All three were taken **on their shape rather than their data**: each looked like a conclusion or a
  principle and was written up without being tested. Every test was cheap — comparing two sets,
  running one assertion against the reverted implementation, asking when the clause's condition
  becomes knowable. **The cost of checking a handed-down finding is almost always lower than the
  cost of carrying it**, and the same holds for a finding you are *reporting about* someone else,
  where stating it more strongly than the data does costs nothing locally.
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

## A completeness claim must state the population it searched

**Required, not advisory.** A reviewer rejects any claim of the form "all N surfaces are
corrected", "the map is complete", or "no artifact carries this" that does not state, *before* the
result, **which universe was searched** — prose, the paper, source, generated strings, committed
artifacts, tests, routing packets, companion records, registry entries. Name the file suffixes and
the count.

**"I found none" is not a finding until "I looked in X, Y, Z" is stated beside it.** Three times in
this project the query was correct and the population was wrong, and each ended in a verdict:

| The search | Population used | What it missed | The verdict it produced |
|---|---|---|---|
| surfaces carrying "each forbid the target" | the write-up | source, generated strings, artifacts | "all five surfaces" — it was eight |
| surfaces carrying the capability attribution | prose, source, artifacts, tests | required companion records | "the map is complete" — the withdrawn-assertions registry was not in it |
| artifacts backing six programme figures | `evidence/*.json` | committed **Markdown** | "six figures are untraceable" — all six were recoverable |

**The error is invisible from inside the search**, which is why re-running one never helps and why
the population has to be declared rather than assumed. It is the same shape as a metric satisfied
by absence, one level up: absence was never measured against a stated universe.

**This lives here rather than in a routing packet** because an obligation recorded only in the
document that raised it does not travel — the rule this file already applies to review findings,
applied to itself.

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
