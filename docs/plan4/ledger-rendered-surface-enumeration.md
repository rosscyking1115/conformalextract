# Which ledger fields reach a reader, and which can be edited with no effect at all

**Read-only enumeration. Nothing here is repaired.** This exists because a correction was applied
to a ledger field that nothing renders, the generated appendix inherited the stale sentence
byte-identically, and the byte-identity guard held it there with a green suite over it. The guard
was working exactly as designed: it enforces *agreement between two documents*, and both documents
agreed on the wrong text.

## The record type, field by field

`claims.render_surface` (`src/conformalextract/claims.py:307-319`) emits **three** fields and
nothing else — `claim_id`, `wording`, and each entry of `limitations`. Read from the code, not
assumed.

| Field | Rendered? | Class | What checks its *content* |
|---|---|---|---|
| `claim_id` | **yes** | rendered prose | appendix byte-identity |
| `wording` | **yes** | rendered prose | appendix byte-identity |
| `limitations[]` | **yes** | rendered prose | appendix byte-identity |
| `method` | no | **blind prose** | **nothing** |
| `scope` | no | **blind prose** | **nothing** |
| `verified_by` | no | **blind prose** | **nothing** |
| `evidence[]` | no | blind structural | `verify_ledger` — path exists and is git-tracked, never opened |
| `status` | no | blind structural | `publishable()` logic |
| `surfaces[]` | no | blind structural | `publishable()` logic |

**The blind-prose class is `{method, scope, verified_by}`.** A change to any of them alters no
rendered output, so the byte-identity guard cannot fail; carries no path, so `verify_ledger` has
nothing to resolve; and never enters the paper, so `check_paper_claims` never sees it. **Three
guards, and this class is outside all of them by construction.** That is the mechanism, stated
generally rather than as one incident: *the correction landed in `method`.*

## The sweep

**Population searched:** all 15 claim records in `evidence/plan4/claim_ledger.json`, every field,
every list element — 9 field names, both prose and structural. Two passes: a pattern pass over nine
known-stale phrasings, and a **structural pass** that extracts every numeric token per claim and
reports figures present in blind prose and absent from every rendered field. The structural pass
does not depend on my choosing the right pattern, which the pattern pass does.

**Not searched, stated:** git history; other branches; the private HF evidence repo; paraphrase.
The registry records that a literal check cannot catch a paraphrase and that only a reviewer
reading end to end can; that limit applies here unchanged.

### Rendered defects: three, and the sweep found no fourth

| Claim | Field | Visible? | Defect |
|---|---|---|---|
| `CX-CAPGAP-01` | `wording` | **RENDERED** | attributes 0.0925 to "the certifier's Hoeffding bound" — a construction neither certifier ran |
| `CX-CAPGAP-01` | `limitations[3]` | **RENDERED** | the risk-test-only witness, offered as showing a model could be certified |
| `CX-SERVING-01` | `limitations[3]` | **RENDERED** | `1.3-1.8%` dash-joined — one numerator, two denominators, read as an interval |

**Six further hits were checked and are legitimate**, and they are listed because a sweep that
reports only its positives cannot be audited: `CX-CAPGAP-01.limitations[5]` and
`CX-GROUNDING-ORTHOGONAL-01.limitations[8]` *disclose* withdrawn wordings, which is what the
registry exempts them for; `CX-GROUNDING-ORTHOGONAL-01`'s `claim_id` retains the word for
traceability under a recorded decision, and its `limitations[0]`/`[1]` narrow it explicitly; and
`CX-REPO-DESCRIPTION-01.method` names the sibling claim by ID rather than asserting orthogonality.

**Against the four members named in advance:** two are ledger-resident and both were found
(`CX-CAPGAP-01.wording`, the `1.3-1.8` band). The other two are not in the ledger and were
confirmed by reading the files directly — `docs/plan3/certification-result.md:37` carries the same
"certifier's Hoeffding bound" phrase **80 lines above its own correction at :117, in the same
file**; and `evidence/plan3/derived_quantities.json` keys the block `at_the_acceptance_floor` with
`k_definition: "…the smallest prefix that MEETS the 0.20 floor"`, which
`evidence/plan4/paper_claims.json` then pins **as declared configuration** for the figure `280`.
The pattern sweep added `CX-CAPGAP-01.limitations[3]`, which was not on the advance list.

### The structural pass found a class nobody had named

**79 figures across 14 of the 15 claims appear in blind prose and in no rendered field.** Dates and
ADR numbers are part of that count and are noise, but the substantive members are not:

| Claim | Figures reachable only through unrendered prose |
|---|---|
| `CX-CAPGAP-01` | `2.01` — the oracle acceptance to three significant figures, in `verified_by` |
| `CX-ALPHA-FRONTIER-01` | `0.383`, `20,000` |
| `CX-GROUNDING-ORTHOGONAL-01` | `0.84`, `0.951`, `0.984` |
| `CX-SERVING-01` | `300` |
| `CX-COST-01` | `0.10`, `0.40`, `0.45`, `0.48`, `6.00`, `6.85`, `18.33`, `0.0002`, `0.2008`, `24.7992` — effectively the whole per-job cost table |
| `CX-H1-PRIMARY` | `1,396`, `0.05`, `0.20` |

**These are asserted quantities that no reader of any rendered surface can see and no guard checks.**
`verify_ledger` sees only paths; the appendix guard sees only rendered text; `check_paper_claims`
sees only the paper. A figure in `method` or `verified_by` is in the authority, is quotable by
anyone reading the ledger directly, and is checked by nothing — the same shape as the original gap,
one level in.

## The guard, and where it stopped

`scripts/check_ledger_prose.py` covers the blind class. **Its field map is derived, not declared:**
a probe claim carrying a unique sentinel in every field is rendered, and the sentinels that survive
*are* the rendered set. Hardcoding `{claim_id, wording, limitations}` would go stale the first time
somebody extended the renderer and the guard would keep reporting against a world that had moved.
Broken deliberately before being trusted, and each failure read rather than counted:

| Mutation | Result |
|---|---|
| a figure planted in `method` | fails, **naming the claim, the field and the numeral** |
| the *same* figure in `wording` | **correctly silent** — the rule is about *where*, not *what* |
| empty claim list | fails cleanly as unloadable, rather than passing vacuously |
| the renderer changed to drop `limitations` | **the derived map tracked it**, `{wording, limitations}` → `{wording}` |

**It is not wired into the suite, and that is deliberate.** It reports **46 violations across 13
claims** and a permanently red gate stops being read — the failure mode this project has already
named. Wiring it follows the migration, not the other way round.

## The 79-figure ruling: shape of the work, and the exceptions it needs

**The ruling:** a figure may not be *asserted* in blind prose; blind prose may *reference* a checked
field but may not *restate* a number.

**Structural exemptions are already implemented** and are matched on context, never on value —
identifiers and hashes, dates, call signatures, notation and formula operands, enumerators, list
ordinals, paths, and named phases (`Plan 4`, `Gate 0`, `Thm 1`). Those take the raw ~93 numeral
occurrences down to **46**.

**The residue is materially larger than "move a few numbers", and it is not uniform:**

| Claim · field | n | Character |
|---|---|---|
| `CX-COST-01.method` | **17** | a per-job cost reconciliation whose *purpose* is to show the arithmetic |
| `CX-CAPGAP-01.method` | 4 | restates 0.0925 / 0.1075 / 280 / 0.1139, all of which already live in artifacts |
| `CX-REPO-DESCRIPTION-01.method` | 3 | restates 95.7 / 39.4 / 16 / 5,355 / 340 — **inside a passage whose own text says "NO FIGURE IS QUOTED, deliberately"** |
| `CX-GROUNDING-ORTHOGONAL-01` | 5 | 0.84 / 0.984 / 0.951 — measurements with no artifact home yet |
| `CX-SERVING-01`, `CX-ALPHA-FRONTIER-01`, others | 17 | mixed: some measurements, some scope statements of the frozen operating point |

**The proposed rule, for a decision rather than an assumption.** Three tiers:

1. **Measurements of this project's own results may never appear in blind prose.** They live in a
   rendered field or an artifact, and blind prose points at them. This covers the clear cases —
   `2.01`, `0.383`, `0.84`/`0.984`/`0.951`, and the `CX-REPO-DESCRIPTION-01` block.
2. **The frozen operating point is exempt** — α, δ, the acceptance floor, *n*. It is a *declared
   constant*, not a measurement; it is pinned in the certification artifact; and a method
   description that cannot say what parameters it ran at is not a method description.
3. **`CX-COST-01.method` needs its own decision, not this rule applied mechanically.** It is a
   costed audit trail, and the reason it exists is that no single spend ledger does. The figures
   *should* move to `programme_facts.json`, which already carries the band — but that is a
   migration of a governance record, and doing it in the same pass that proposed the rule is the
   shape this project has been correcting all along.

**Not done. Reported for a ruling.**

## What this changes about the repair

Repairing the three rendered defects means editing `wording` and `limitations` and regenerating the
appendix. **It does not touch the 79.** Whether the blind-prose class should be rendered, checked,
or emptied of figures is a design question and is not decided here.

**And the enumeration is now the population.** Any future claim that a ledger correction is
complete has to say which of the nine fields it searched, because "I fixed the claim" has meant
"I fixed a field nothing renders" once already.
