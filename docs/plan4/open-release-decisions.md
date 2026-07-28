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
