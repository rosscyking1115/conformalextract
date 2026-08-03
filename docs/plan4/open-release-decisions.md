# Open release-policy decisions for Plan 4

Decisions that must be made **before** anything is published, recorded here so Plan 4 finds them
rather than rediscovering them. Each item needs the owner's approval, and any item that changes a
public claim needs an independent review as well.

> **Amended 2026-07-29.** This paragraph read "Nothing here is decided. Plan 4 has not opened" —
> false at this commit on both counts. Four decisions were ruled on 2026-07-29 and Plan 4 was opened
> the same day. The standing of each ruling is stated per item: decisions 1, 3 and 4 are the owner's
> calls on questions of policy and carry no separate review record; decision 2 changes a public
> claim and its wording was independently reviewed (**BLOCK**, then re-worded — see
> `evidence/plan4/reviewer_record.visibility-and-description.json`). Recorded rather than silently
> corrected: a live list whose header contradicts its own table is the defect this repository has
> spent two days removing from other documents.

This file is a live list: items are added when found and struck when decided. It is deliberately not
a dated record — see `docs/release-check-2026-07-28.md` for the check that surfaced the first item.

> ## Plan 4 is PAUSED as of 2026-07-29 — not cancelled
>
> The owner's override kept Plan 4 open on the hypothesis that only Plan 3's paperwork was missing.
> The independent close review **refuted** that hypothesis
> ([`../../evidence/plan3/reviewer_record.plan3-close.json`](../../evidence/plan3/reviewer_record.plan3-close.json)).
> Plan 4 is the release plan, and finding **O2** was a live overclaim on README, report and abstract
> surfaces — so continuing would have built release artifacts on a claim that was about to change.
>
> **Resumes when O1, O2 and O3 are discharged and Plan 3 closes on its merits.** Nothing below is
> withdrawn, and the Plan 4 work already done stands: the gate-state derivation, the privacy review,
> the link audit, decisions 1–4, and the rejection of the staged-release amendment.

> ### Known exposure, recorded and deliberately not addressed: unnamed conventions
>
> Several conventions in this repository exist **only in their implementations**, with no rule
> naming them: the reviewer-record shape (`schema_version`, `review_kind`, `verdict`, per-question
> sections), the dated-amendment form used to correct an accepted plan or ADR without rewriting it,
> and the `permitted_in`/`ALLOWED`-with-reasons pattern for mention-not-use exemptions.
>
> **This is the exact mechanism that produced B2.** The guard-the-guard convention was real,
> consistent across four modules, and unnamed — so the fifth scanning check shipped without it and
> nothing noticed until it hid a red suite. **A convention that lives in N implementations and no
> rule is one new file away from being broken**, and each of the three above is currently in that
> state.
>
> **A fourth, measured and still latent:** the three filesystem walks in the test suite carry
> **three different skip lists**, and the newest carries the narrowest. Divergence from `.gitignore`
> is currently zero — 203 files against 202, differing only by a reviewer's probe — so nothing is
> wrong today.
>
> **The live consequence, in one line: the suite's scope now depends on what happens to be on the
> machine, and one of the three walks is guarded against that while two are not.**
> `test_the_markdown_scan_matches_the_index` closes it for the markdown walk by asserting nothing
> gitignored is included; `test_internal_paths.py` and `test_withdrawn_assertions.py` are unguarded.
>
> **Two of the three walks still carry a floor, and it is worse than the one that was replaced.**
> `test_internal_paths.py` and `test_withdrawn_assertions.py` bound at `> 50` against **202** files —
> **75% headroom**, against the 51% the floor rule was derived from. Each of the three walks now has
> exactly one of the two guards; **none has both.**
>
> **The deferral rule, stated because "Plan 4 is paused" does not distinguish these from what has
> been changed.** Three commits of test changes have landed during the pause, so the pause alone is
> not the criterion. The criterion actually being applied: **blocking findings are fixed in the round
> that raises them; non-blocking findings are recorded and deferred.** That fits every commit in this
> sequence, and it is why the Q1 kind-probe was added immediately and these two floors were not.
> Recorded here so it is a known exposure rather than a discovery waiting to happen, and so whoever
> resumes Plan 4 finds it already enumerated.

> ### Known exposure, recorded 2026-08-03 and deliberately not closed: the claims guard never opens the file
>
> `claims.verify_ledger` checks three things about a claim's cited evidence: that the **paths
> exist**, that they are **git-tracked**, and that tracking is determinable. It never opens a file,
> never compares a number against one, and never sees the configuration — the δ allocation, the
> candidate count, the sample size — that produced either the number in the file or the number in
> the prose. **A claim quoting a figure that appears nowhere in its own evidence passes unchanged,
> because the metric is satisfied by absence.**
>
> **`verify-claims ok` therefore means the paths resolve.** It was reported as a green signal in
> every status line of the 2026-08-03 session, and reading it as "the claims check out" — as that
> seat did — is reading information that is not there. That reading is the exposure; the tool is
> doing what it says, under a name that suggests more.
>
> **This is the mechanism behind the five quoting errors** recorded in the write-up's limitations,
> not five separate lapses of attention. It also explains their direction: nothing was ever pushing
> back, so the only filter on a wrong number was whether it looked plausible, and a number that
> flatters the result looks plausible to the person who wants it. Contrast
> `test_doc_references.py::test_every_test_named_in_the_docs_exists`, which *does* open the file and
> compare — it caught a stale test name in the very commit that renamed it.
>
> **Attestation is not checking.** `evidence/plan3/certification_sensitivity.json` now stamps each
> quoted quantity with its δ, allocation, candidate count and n. That narrows the four quantities it
> covers and closes nothing: **nothing compares the prose against it.** The stamp is a place to look
> up the right answer, not a gate that notices the wrong one.
>
> **The instance list. The paper carries five; this repository carries six.** The paper's five are
> scoped to the claims it reports, and it now says so in the sentence rather than leaving the scope
> implied. The sixth is not a reported claim and does not belong in an ACL Limitations section,
> where it would dilute the five that bear on the result.
>
> | # | The quantity | Where it was quoted | Caught by |
> |---|---|---|---|
> | i | $\alpha$-frontier point 0.406, as a threshold | claim wording | claim-wording audit |
> | ii | empirical oracle 0.2357, as clearing the floor | write-up | independent review |
> | iii | 11.4%, as "certified" without naming the construction | write-up | pre-submission audit |
> | iv | a narrowing applied to a derived doc, not the ledger | ledger → appendix | review |
> | v | acceptance LCB 0.2017, at an allocation not used | write-up | review |
> | **vi** | **"content ends 82% down page 4, within the limit"** | **every status line** | **a rebuild** |
>
> **Instance vi is the purest example in the set.** It cites an artifact that exists — the built
> PDF — states a number that artifact does not contain, flatters compliance, and sits in the one
> line whose entire job is to assert compliance. No guard could have caught it, and none did.
>
> **And it propagated further than any of the others.** It was repeated in every status report,
> including to the owner, who read it and repeated it back. **A wrong number that its reader
> confirms is a different failure from one that goes unnoticed**: the confirmation is evidence to
> the author that the number was checked, so the error acquires a second source and becomes harder
> to find than it was when only one person held it. None of instances (i)–(v) had that property.
> Nothing in this repository currently distinguishes "confirmed by a reader" from "verified".
>
> **Open item — a validity guard that reads its evidence.** First scope, deliberately small: the
> four quantities in `certification_sensitivity.json` (the acceptance lower bound by allocation, the
> empirical-Bernstein probe, the AUROC bootstrap interval, and grid capacity), asserted against the
> surfaces that quote them. **Not built.** Building it before the overdue review round would repeat
> the bundling problem the round exists to catch, and naming the gap is the disclosure the paper
> carries. Whether to build it at all is the owner's call.
>
> **Reference implementation: `redteam-foundry` built the equivalent.** Two properties of it are
> the requirement, not decoration. Its checker **opens both the artifact and the document** and
> compares — the thing `verify_ledger` does not do. And it **refuses to pass on an empty claim
> list**, because a checker with nothing to check passes vacuously, which is the same failure shape
> as a metric satisfied by absence. Any guard built here inherits both or it reproduces the gap it
> was written to close.

## Live list

| # | Decision | Status |
|---|---|---|
| 1 | Reviewer records in the public bundle | ~~open~~ **DECIDED 2026-07-29 — publish as-is** |
| 2 | Repository description | ~~open~~ **DECIDED 2026-07-29 — gets its own ledger claim; sentence still to be drafted and reviewed** |
| 3 | Repository topics | ~~open~~ **DECIDED 2026-07-29 — three approved; more may be proposed** |
| 4 | §1 versus §17 on the minimum contribution | **DEFERRED 2026-07-29** — §1's seven stand; not on the path to the actual goal |
| 5 | Repository visibility | **OPEN** — routed separately, see [`proposed-visibility-change.md`](proposed-visibility-change.md) |
| 6 | An operator path inside a byte-frozen document | **OPEN** — added 2026-08-02; see §6 below |

Decisions 1–4 were ruled by Ross on 2026-07-29. Their reasoning is preserved below rather than
deleted: a struck decision is a record of *why*, and the next person to ask the same question should
find the argument, not just the answer.

---

## 1. ~~Do reviewer records ship in the public evidence bundle?~~ **DECIDED: publish as-is**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **option (a), publish as-is.**

> **The reasoning below is adopted as the basis of the decision.**
>
> **The cost is larger than every document describing it has said, this one included.** It was
> framed as "a directory name from one machine". Measured at this commit: the operator's Windows
> **account name** appears in 19 tracked lines across two files — including two full user-home
> paths — and the private-planning-directory name in 31 occurrences across three files. Decision 1
> as first written named the directory only; `publishable-and-sealed.md` §4 named one file; the
> `ALLOWED` list in `tests/test_internal_paths.py` names three. **Each description was narrower than
> the thing it described**, which is this week's recurring defect appearing in the artifacts written
> to prevent it.
>
> The decision is unchanged — an account name and a directory name disclose nothing exploitable, and
> the attestations they sit inside are worth more than their removal. But it is accepted knowingly
> now rather than on an undercount. **Note also that no gate covers the bare account name:**
> `test_internal_paths.py` deliberately hardcodes no username, which is sound design and leaves that
> class uncovered.
>
> **One addition that changes when this binds, and it was not said when the options were framed:**
> **flipping repository visibility publishes those records whether or not a bundle is ever
> assembled.** Every reviewer record is a tracked file. There is no assembly step between "the repo
> is public" and "the records are public".
>
> **This decision is therefore a precondition for any visibility change, not merely for bundle
> assembly.** It is now satisfied — but the general shape is worth keeping: a decision framed as
> being about *what we publish* can be forced by an act that publishes *everything tracked*, and
> the framing hides that.

`evidence/plan3/reviewer_record.reanalysis.json` contains four references to the private planning
directory the accepted plans were held in, including its absolute path. Two sibling occurrences
elsewhere in the repository were reworded; this one was **held**, and the reasoning should survive
whatever is decided:

- Reviewer records are immutable evidence artifacts. Other documents cite them, and the honesty
  doctrine treats them as fixed.
- The paths sit inside first-person prose recording *what was hashed against what*
  ("I hashed all four in-repo copies from git and all four sources in …"). Redacting them does not
  tidy a citation; it breaks the attestation the sentence exists to make.
- Doing it inside the record of a review whose subject was partly whether artifacts say what they
  claim would be a poor place to start editing artifacts.

The two available decisions:

**(a) Publish as-is.** The paths name a directory on one machine, disclose nothing sensitive about
its contents, and are part of the historical record. Cost: a public artifact contains an internal
filesystem path.

**(b) Exclude reviewer records from the public bundle.** Cost is much higher than it looks. The
records are the evidence that the independent-review discipline happened at all; the write-up cites
them by name as the basis for "reproduced by someone who did not compute it". Publishing the claims
while withholding the reviews that tested them inverts the project's own argument.

**Recommendation on the record, for the reviewer of this decision to test:** (a). But it is not
this seat's call, and it is not urgent until a public bundle is actually assembled.

**Do not resolve it by editing the record.** That is the one option ruled out already.

---

## 2. ~~What does the repository description say?~~ **DECIDED: its own ledger claim**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **the description gets its own ledger claim, not a compression of
an existing one.** The sentence itself is still to be drafted and routed like any other public
sentence. Currently **empty** (`gh repo view` → `"description":""`).

> **Why its own claim, and the analysis below is the specification:** the claim boundaries require
> the ~16× grounding gain and the null to travel in the **same passage**, and a description has no
> second passage. `CX-H1-PRIMARY`, `CX-CAPGAP-01` and `CX-GROUNDING-ORTHOGONAL-01` all carry the
> `abstract` surface and none is short enough as written. **So the sentence must be written for the
> constraint, not trimmed into it** — trimming an existing claim is how the null gets dropped.
>
> `"95.7% grounded event-argument extraction"` remains forbidden by name.

A description is a claim about what the repository is, rendered on every search result, every
listing, and every link preview — and it is the one public surface with no room for a caveat. This
project does not let claims land without review, and a one-line summary of a **negative** result is
harder to write honestly than a paragraph, because there is no space to attach the null.

The trap to avoid is stating the grounding result without it. "95.7% grounded event-argument
extraction" would be true, catastrophic, and forbidden by name in
[`../plan3/certification-result.md`](../plan3/certification-result.md) — the claim boundaries
require the 16× grounding gain and the null to travel in the same passage, and a description has no
second passage.

Whatever is chosen must trace to a ledger claim like any other public sentence. `CX-H1-PRIMARY`,
`CX-CAPGAP-01` and `CX-GROUNDING-ORTHOGONAL-01` all carry the `abstract` surface, which is the
closest existing analogue to a description; none of them is short enough as written, so the
decision includes whether a description needs its own ledger entry rather than a compression of an
existing one. **Not filled in now**, deliberately.

## 3. ~~What topics does the repository carry?~~ **DECIDED: three approved**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **`conformal-prediction`, `selective-prediction`,
`event-extraction`** are approved as accurate. Further topics may be proposed if they trace
honestly. Currently **none** set.

> `certified` and `production` stay **banned**. `certified` in particular is reserved by the honesty
> boundary for something this project did not achieve, and a topic is not exempt from that because
> it is metadata rather than prose.
>
> **Candidates for the "propose more" allowance, not applied:** `rams`, `qlora`, `negative-results`,
> `reproducibility`, `llm-evaluation`. Each traces to something the repository actually contains.
> `negative-results` is the one worth arguing for — it is the most accurate single word for what
> this project produced, and it is the opposite of the direction a topic list usually drifts.

Lower stakes than the description — topics are discovery metadata, not prose — but they are still a
public surface and still a claim of a kind. `conformal-prediction`, `selective-prediction` and
`event-extraction` describe the subject matter accurately. Anything implying a working system
(`certified`, `production`) does not, and `certified` in particular is reserved by the honesty
boundary for something this project did not achieve.

Both items are gated behind Plan 4 opening, and Plan 4 has not opened.

---

## 4. ~~§1 and §17 disagree on the minimum contribution~~ **DEFERRED**

**Raised:** 2026-07-29, by the independent review that rejected the staged-release amendment.
**Deferred:** 2026-07-29 by Ross. **§1's seven stand.** Deferred rather than answered, because it is
**not on the path to the thing actually wanted** — visibility is decision 5, and §1 governs the
public *contribution*, which is a different question. Resolving §1-versus-§17 would not move a
visibility change one step closer.

**Neither party had found it** — not the implementer proposing to cut §1, and not the reviewer
refusing the cut, until it read §17 in the primary text.

`accepted-plan.md` §1 names **seven** items as "the minimum useful public contribution". §17's
evidence-acceptance checklist contains a ticked line reading *"The evaluator/certifier, evidence
bundle and CPU replay are the minimum contribution"* — **three** items.

This is a genuine internal contradiction in an accepted plan, and it is the strongest argument the
rejected amendment could have made and did not. It does not rescue that proposal: §17's three are a
*different set* (they omit item 4, the versioned GitHub release, which Stage A kept), and treating a
checklist gloss as though it overrode the section it summarises is the exact trap `CLAUDE.md`
already records from the §6.3 episode — *"the repo's gloss on §6.3 was stricter than §6.3 actually
is, and an ADR was written against the gloss."*

**Not resolved here, and deliberately not resolved by a release commit.** An accepted plan is
amended by dated note and its hash pin moved in the same commit; which of the two readings governs
is a scope question for Ross, and it changes what the release must contain. Until it is answered,
**§1's seven stand**, because that is the section and §17 is the summary of it.

Both readings should be tested against the same question: which one did the plan's author intend to
bind — and if the answer is not recoverable, which one this project would rather be held to.

---

## 6. An operator path inside a byte-frozen document **OPEN**

`docs/plan3/section-12-1-certification-only-scope-addendum-2026-07-30.md` cites, at its line 36, an
operator-local implementer report held under a machine temp directory, as the source of the five
input hashes it then reproduces inline. The file is admitted **byte-for-byte** — its authority is
hash equality with the artifact independently reviewed on 2026-07-30 — so the string cannot be
edited without destroying the evidentiary value the document exists to carry.

**What was done, and what was not.** `tests/test_internal_paths.py` previously enumerated three
known roots by name and matched none of this, so the suite would have stayed green while the path
shipped. A `windows-drive-path` pattern matching the *shape* of a drive-letter path now catches it,
and the file is named in `ALLOWED` with byte-fidelity as the stated reason. **The gate now sees the
string; nothing has removed it.** That is the open decision.

**This section was rewritten by its own gate, which is the point.** The first draft quoted the paths
verbatim — the natural way to be specific — and the newly widened pattern failed the suite on nine
hits in this file. That is the 2026-07-28 defect recorded in `REVIEW.md` recurring exactly: a
disclosure that introduces the strings it exists to disclose. The difference is that this time a
mechanism caught it instead of a reviewer, in the same change that built the mechanism. The paths are
therefore described here rather than quoted; the one document that may quote one is the frozen
addendum, because it may not be edited at all.

**The choice, stated plainly.** Either (a) this repository publishes a document containing an
operator-local path, disclosed here and defensible as mention-not-use — the same ground three
reviewer records already stand on; or (b) the addendum does not ship in the public bundle, which
means the §12.1 amendment's own text is absent from what a reader can check. Interacts with decision
1: reviewer records were ruled publishable as-is on the same reasoning, so (a) is the consistent
answer, and consistency is not by itself a reason.

**Not to be confused with the packet-location finding.** That the *routing packets* for this work
also lived under the same temp directory, outside any enumerable location, is a governance defect
recorded in the PMO learning log as entry `2026-08-01-003` — it is about where packets are kept, not
about what a shipped document contains, and it is not this decision.
