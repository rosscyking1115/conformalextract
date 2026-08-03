# Claim narrowing, 2026-08-02 — three claims narrowed across every surface

- Date: 2026-08-02
- Raised by: the owner's publication-sprint plan of 2026-08-02, §3 (held outside this repository)
- **Status: applied, pending independent review.** Changes to claims and release policy require an
  independent review; this document is the packet for one, not a discharge of it.
- Verification: `uv run conformalextract verify-claims` → `ok: true`, 13 publishable claims, no
  unresolved or untracked evidence.

## Why these three, and why none of them is a re-scoring

All three narrow what is asserted. **No number changed anywhere.** No artifact was re-run, no split
was opened, no threshold was selected, no evidence was re-scored, and the null is untouched. Each
change removes an inference the evidence never carried.

---

## 1. `0.406` is an empirical oracle frontier point, not a threshold

**Was:** presented as "the α at which the 20% floor first becomes oracle-reachable", with strong
oracle-upper-bound caveats attached but no statement of *when* it was measured.

**Now:** labelled an **empirical oracle frontier point** wherever it appears, with the provenance
stated: it was computed **after** the certification split was opened, from that split's own labels.

**Why it mattered.** The caveats already said "oracle upper bound" and "not sufficient". What none
of them said is that the quantity is post-hoc on opened labels. A reader could take 0.406 for a
property established under the same discipline as the frozen α = 0.20, which was fixed before any
sealed label was read. Calling it a threshold implies a certificate that was never issued at it.

**Surfaces:** `CX-ALPHA-FRONTIER-01` wording + a new leading limitation; `certification-result.md`
(table header, a new paragraph under the table, the permitted-claims list, a new forbidden-table
row); `draft-2026-07-28.md` §4; regenerated appendix.

---

## 2. "Orthogonal" replaced by a dissociation

**Was:** "Grounding fidelity and certifiability are orthogonal for grounded event-argument
extraction on RAMS."

**Now:** "QLoRA sharply improved output validity and span grounding for event-argument extraction
on RAMS, but did not make low-risk documents identifiable using transition-logprobability
confidence."

**Why it mattered.** Orthogonality asserts **independence**. One intervention observed across three
systems cannot establish independence between two properties, and nothing in ADR 0011 tested it.
The claim was carrying a stronger relation than the decomposition measures — the same failure mode
as the withdrawn "names the wrong entity" attribution (finding O2), in the sentence that survived
that correction. It is worth saying plainly that O2's fix on 2026-07-29 addressed the error-category
attribution and left this one standing; a reviewer should decide whether this counts as O2's
remaining exposure or as a separate finding of the same kind. **This document does not rule on
that.**

**The identifier `CX-GROUNDING-ORTHOGONAL-01` is retained**, deliberately. Renaming it would break
traceability to the six reviewer records that ruled on it. Both the ledger and the README say the
identifier is historical and that the claim no longer asserts orthogonality. If a reviewer prefers a
rename with a redirect, that is a cheap change.

**Surfaces:** `CX-GROUNDING-ORTHOGONAL-01` wording + two new leading limitations; `README.md`;
`certification-result.md` (section heading, a dated narrowing note, the closing paragraph, the
permitted-claims list, a new forbidden-table row); `docs/adr/0011` (Status line + "Amendment 1", the
decision and every number left intact); `docs/progress.md`; `draft-2026-07-28.md` (title, subtitle,
§"What is ours", §3 close); regenerated appendix.

---

## 3. No task-wide or field-wide impossibility

**Was:** nothing asserted field-wide impossibility outright, but nothing ruled it out either, and
several passages were readable that way.

**Now:** stated explicitly wherever the null is stated: a 20% target is **not excluded** on
structured extraction.

> **Corrected 2026-08-03 (finding F1).** This read "**is** reachable". Not being forbidden by a
> necessary condition is not achievability, and 2606.29054 finds certification practical only at
> α = 0.30–0.40 on its own tasks. The same correction was applied to the ledger, the forbidden
> table and `draft-2026-07-28.md`.
 On the datasets 2606.29054 reports, `(μ−α)/(1−α)` forbids nothing at μ = 0.033
(JSON-Extract) and permits up to 80.5% acceptance at μ = 0.356 (its easiest NER dataset) —
`docs/frontier-check/findings.md`, re-verified 2026-07-22. What is established here is that **this**
model with **this** score on **this** task at μ = 0.6071 could not.

**Provenance note.** The sprint plan cited a different figure for this point (CoNLL NER with
Ministral-8B at 37% acceptance, risk 0.13). That figure is not recorded anywhere in this repository,
so it is **not used**. The two base risks above are committed, dated and re-verified, and they carry
the same argument.

**Direction check.** This is a narrowing, not a hint that a weaker target would certify. It says the
frozen target was achievable *in principle on other populations*, which makes this system's failure
more specifically its own — the opposite of a rescue. The forbidden wording "any hint that a laxer α
would certify" is untouched and still enforced by `claims.FORBIDDEN_WORDINGS`.

**Surfaces:** new limitations on `CX-ALPHA-FRONTIER-01` and `CX-CAPGAP-01` (both gaining
`docs/frontier-check/findings.md` as evidence); `README.md`; `certification-result.md`
(a new paragraph, the permitted-claims list, a new forbidden-table row); `draft-2026-07-28.md` §3;
regenerated appendix.

---

## Two defects found while doing this, both fixed

**The generated appendix had drifted from the ledger.** `docs/writeup/claims-appendix.generated.md`
carries a "Do not hand-edit: edit the ledger and regenerate" banner and the draft describes it as
"generated from the ledger", but two `CX-SERVING-01` limitations added to the ledger after
2026-07-28 had never reached it — the Clopper-Pearson 4.80% upper bound on the top-quartile
concentration, and the statement that the cause of the divergence is not isolated to any one kernel,
quantisation path or sampler. Both are limitations that make the probe result *less* reassuring, so
the drift ran in the flattering direction. An independent reviewer verified byte-identity by hand on
2026-07-28 and nothing held it there afterwards.

`tests/test_claims.py::test_the_committed_appendix_is_byte_identical_to_what_the_ledger_renders` now asserts
BYTE-IDENTITY against `claims.render_surface`. Its first version checked only that every rendered
line appeared somewhere in the file; an independent reviewer broke that by mutation on 2026-08-02
(it passed a fabricated added claim, an added limitation, and the file reversed), so it was
strengthened to equality — which is what the human reviewer had used all along. A hand-checked
invariant with no test is a comment; a containment check is not a fidelity check.

**The write-up title repeated a phrasing already ruled against on another surface.**
`evidence/plan4/reviewer_record.visibility-and-description.json` required "bought no certified
coverage" out of the repository description on two grounds: *coverage* is not this project's term
(it is certified **acceptance**, and "coverage" means something else in conformal prediction), and
*bought no* is transactional framing compatible with a near miss, where the record is that the
target was never reachable. The draft's title — the single most quotable line in the document —
still read "A ~16× grounding gain bought no certified coverage". Retitled "A ~16× grounding gain
left certified acceptance where it was". The ruling was made about a different surface, so this is
an extension of it rather than a breach of it, but the reasoning transfers exactly.

---

## What a reviewer should check

1. That every change is a narrowing and none is a re-scoring — no number moved.
2. That the §3 direction check above is right: stating a 20% target is reachable elsewhere is not a
   hint that a weaker target would certify here.
3. Whether retaining the `ORTHOGONAL` identifier with a historical note is the right call, or
   whether it should be renamed with a redirect.
4. Whether the orthogonality narrowing discharges O2's remaining exposure or is a separate finding.
