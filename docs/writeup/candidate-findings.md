# Candidate findings for the write-up — recorded, not acted on

- Created 2026-07-29
- **The write-up is not open.** Nothing here has been added to any draft, and nothing here is a
  claim: none has a ledger entry, and none may reach a surface without one.

A holding place for observations that look like contributions about **evaluation practice** rather
than about this project. The test for entry is that the finding would still be true in a repository
that had never heard of ConformalExtract.

---

## C1 — Limitations lists degrade directionally under carry-forward

**The claim.** When findings are carried from one review or artifact to the next, the set that
survives is not a random sample of the set that started. Qualifiers on reassuring results are
dropped preferentially, and the result is a limitations list that is **individually true in every
sentence and collectively flattering**.

**Why it would be a contribution.** The degradation is invisible to the checks a careful project
actually runs. Claim-fidelity checking asks whether each published sentence is supported; every
surviving sentence passes. Forbidden-wording checks ask whether a claim overstates; none does.
Citation checks ask whether evidence resolves; it does. **The defect is in the complement — what is
absent — and no check reads the complement**, because a check evaluates what is in front of it.

**The evidence, from this project.** Across two carried-forward lists in one plan close, four items
failed to arrive or arrived incomplete:

- the operating-point dependence of a near-zero divergence result, which holds only under
  aggressive abstention *(qualifier)*;
- the abstain/extract flip rate, 1.3–1.8% at plausible operating points, dropped for eight days
  *(risk statement)*;
- the 4.80% Clopper–Pearson upper bound on a "0 of 75" concentration result — the reassurance
  travelled, the bound saying how reassuring it is did not *(qualifier)*;
- "cause is not isolated to a specific kernel" *(risk statement)*.

**The supported statement is that every reassurance survived** — no dropped item was itself a
reassurance. It is **not** supported that every omission was a qualifier: two were free-standing
risks, and one qualifier (probe frames are train-split only) did travel. **The bias is in what
survives, not in what is lost**, and the first draft of this file said otherwise — an overclaim
inside a candidate finding about overclaiming, corrected on independent review.

**The proposed countermeasure**, which is the transferable part: record each carried item's
**direction** — does it qualify a reassurance, or state a risk? A carried set whose omissions all
point one way is then detectable as a signal, **without needing to establish intent**, which is
neither knowable nor necessary.

**The strongest single instance, and the one that should lead if this is ever written up.** The
defect recurred *inside the fix for itself*. While correcting a carried-forward omission, the author
carried a two-sentence finding onto two prose surfaces, **kept the dependent sentence and dropped
its antecedent**, and thereby asserted something provably false — that substitution errors explain a
false-positive excess, when the identity `fp − fn = predictions − gold` makes their contribution
exactly zero. The author had recorded the pattern one commit earlier and was actively working on it.
**Knowing a failure mode is not protection against it.**

**What would have to be true before this could be claimed.** n = 1 project, one plan close, six
items. The direction coding was done by the same party that made the omissions — and the
characterisation that first framed the pattern was *supplied by the reviewing seat rather than
derived from the data*, then transcribed without being tested against a counter-example sitting one
row away. That is itself worth reporting if this becomes a contribution: **a directional finding
handed down gets less scrutiny than one derived locally.** To be a finding about practice rather
than an anecdote it needs the pattern reproduced somewhere with independent coding — the sibling
repositories are the obvious place, and none has been checked. **Until then this is a hypothesis
with a worked example, and the write-up may not present it as more.**

**Related, and separate.** A register built to prevent dropped obligations is only as good as its
source enumeration, and nothing checks the enumeration. Its *absence* is visible; a register built
on an incomplete enumeration looks exactly like a complete one. Distinct mechanism, same family.

---

## What this file does not do

- It does not open the write-up, and nothing here has been drafted into one.
- It creates no claim and needs no ledger entry **because nothing here is asserted publicly**. The
  moment any of it reaches a surface it needs an entry and a review, like anything else.
- It does not assert that the pattern generalises. That is the open question, stated as open.
