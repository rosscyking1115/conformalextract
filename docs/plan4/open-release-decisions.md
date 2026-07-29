# Open release-policy decisions for Plan 4

Decisions that must be made **before** anything is published, recorded here so Plan 4 finds them
rather than rediscovering them. Nothing here is decided. Plan 4 has not opened, and each item below
needs the owner's approval and an independent review in its own right.

This file is a live list: items are added when found and struck when decided. It is deliberately not
a dated record — see `docs/release-check-2026-07-28.md` for the check that surfaced the first item.

---

## 1. Do reviewer records ship in the public evidence bundle?

**Raised:** 2026-07-28, by the release-hygiene check.
**Status:** open.

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

## 2. What does the repository description say?

**Raised:** 2026-07-28, by the release-hygiene check.
**Status:** open. Currently **empty** (`gh repo view` → `"description":""`).

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

## 3. What topics does the repository carry?

**Raised:** 2026-07-28, by the release-hygiene check.
**Status:** open. Currently **none**.

Lower stakes than the description — topics are discovery metadata, not prose — but they are still a
public surface and still a claim of a kind. `conformal-prediction`, `selective-prediction` and
`event-extraction` describe the subject matter accurately. Anything implying a working system
(`certified`, `production`) does not, and `certified` in particular is reserved by the honesty
boundary for something this project did not achieve.

Both items are gated behind Plan 4 opening, and Plan 4 has not opened.

---

## 4. §1 and §17 of the accepted plan disagree on what the minimum contribution is

**Raised:** 2026-07-29, by the independent review that rejected the staged-release amendment.
**Status:** open. **Neither party had found it** — not the implementer proposing to cut §1, and not
the reviewer refusing the cut, until it read §17 in the primary text.

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
