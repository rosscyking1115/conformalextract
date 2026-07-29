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
> **Not being addressed, and the reason is not that it is unimportant.** Plan 4 is paused pending
> Plan 3's close on merits; naming these is new work, and starting new work during a pause is how a
> pause stops meaning anything. Recorded here so it is a known exposure rather than a discovery
> waiting to happen, and so whoever resumes Plan 4 finds it already enumerated.

## Live list

| # | Decision | Status |
|---|---|---|
| 1 | Reviewer records in the public bundle | ~~open~~ **DECIDED 2026-07-29 — publish as-is** |
| 2 | Repository description | ~~open~~ **DECIDED 2026-07-29 — gets its own ledger claim; sentence still to be drafted and reviewed** |
| 3 | Repository topics | ~~open~~ **DECIDED 2026-07-29 — three approved; more may be proposed** |
| 4 | §1 versus §17 on the minimum contribution | **DEFERRED 2026-07-29** — §1's seven stand; not on the path to the actual goal |
| 5 | Repository visibility | **OPEN** — routed separately, see [`proposed-visibility-change.md`](proposed-visibility-change.md) |

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
