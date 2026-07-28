# ADR 0006: First-object output-extraction policy for generated predictions

- Status: accepted (independent reviewer ruling `adopt`, 2026-07-20; Ross-approved 2026-07-21)
- Date: 2026-07-21
- Reviewer record: `evidence/plan2/reviewer_record.extraction-policy.json` (reviewed commit `26e41d5`)
- Basis document: `docs/plan2/reviewer-brief-extraction-policy.md`

## Decision

Before the frozen structural parse in `parse_generated_frame`, extract the **first balanced
top-level JSON object** from `raw_output`, and parse that. Applied **identically to all three
systems (ZS/FS/QA) from one code path**.

### Algorithm (condition C2 — normative)

Single pass from **index 0**, tracking JSON string and escape state globally:

- iterate characters from position 0; maintain `in_string` and `escaped`;
- while `in_string`, a `{`/`}` is inert — a brace inside a string literal can never open or
  close an object;
- outside a string, `{` increments depth (recording `start` when depth goes 0→1) and `}`
  decrements it; when depth returns to 0, return the slice `[start, index]`;
- if no object closes, return `None` — the record remains a structural failure.

The rejected alternative — find the first `{` and match forward — is correct on this data (the
reviewer measured **zero divergence** across all 27,318 generated records) but only *incidentally*:
it begins matching without knowing whether that brace is inside a string. The from-index-0 scan is
correct by construction, so it is the one adopted.

## Why (and the honest history)

**Condition C4 — post-hoc disclosure.** The pre-registered artifact was the strict parser
(`json.loads` of the entire `raw_output`). This policy was **discovered and chosen after the
prediction run**, in response to two harness defects found while verifying the saved outputs:

- **ZS** prepends an instruction echo (`"Only return the JSON object, nothing else.\n\n"`) before
  emitting correct JSON, then stops cleanly.
- **FS** emits a correct JSON object first, then `\n\n`, then generates a fabricated *next example*
  until it hits the 256-token cap. **The generation job set no stop sequence** — an implementer
  bug. All 9,106 FS records have `finish_reason="length"`.

Under the strict parser both baselines score **0** structural validity while QA scores 9,085.
Reporting that would attribute a missing stop sequence to model quality, which the `CLAUDE.md`
honesty boundary forbids.

The post-hoc objection is answered by verified properties, not assertion:

- the transformation is uniform and deterministic;
- it is a **strict no-op on the untreated comparator**: of 9,085 QA records valid under both raw
  and extracted parsing, parsed content is identical in **9,085**, differing in **0**;
- genuine failures are preserved (140 ZS + 1 QA remain structural failures);
- under greedy decoding the tokens forming the first object are identical whether or not a stop
  sequence halts generation afterward, so this is equivalent to regeneration for the recoverable
  mass. Regeneration was offered and declined as an upgrade, not a correction.

## Measured effect (condition C1 — real frozen-parser semantics)

The structural check is `json.loads` **+ duplicate-key rejection + strict pydantic
(`extra="forbid"`, `strict=True`)** — not a loose "is `arguments` a list" proxy. The reviewer
corrected the implementer's brief, which overstated two figures; these are the authoritative
numbers, independently reproduced by both parties:

| Arm | Strict (raw) | Extracted | Empty-argument frames | Content-bearing |
|---|---|---|---|---|
| ZS | 0 | **8,959** | 46 (0.5%) | 8,913 |
| FS | 0 | **9,105** | 2,887 (31.7%) | 6,218 |
| QA | **9,085** | 9,085 | 452 (5.0%) | 8,633 |

(The brief's 8,965 / 9,091 were the loose-proxy figures and are superseded.)

## Consequences

**Condition C6 — the structural gap changes sign.** Strict: QA leads both baselines by +9,085.
Extracted: QA −20 vs FS (FS slightly *exceeds* QA) and +126 vs ZS. On content-bearing frames it
inverts again: +2,415 vs FS but **−280 vs ZS**. The +9,085 was a pure harness artifact. The
post-extraction structural metric is near-saturated for all three arms and **no longer
discriminates**, so **H1/H2 must rest on grounding and certified acceptance**, not structural
validity.

**Condition C3 — empty frames are first-class.** An empty frame is structurally valid *and*
passes grounding trivially (no spans to validate), so it flows through to acceptance as a
contentless prediction. FS's 31.7% empty rate could inflate its certified acceptance with
predictions that say nothing. Every downstream table must report empty-argument frames as a
separate column, and certified acceptance must state explicitly how an empty prediction scores
against empty vs non-empty gold. FS acceptance must never be reported as a single number
conflating 2,887 contentless frames with content-bearing ones. This asymmetry is **genuine model
output**, not an artifact of this policy — regeneration would not change it.

**Condition C5 — unrecovered residual.** 140 ZS records (1.5%) never close an object: all have
`finish_reason="length"` at exactly 256 tokens, i.e. cap-truncated mid-object, not degenerate
rambling. They are unrecoverable from the saved output and remain structural failures. They are a
**residual harness artifact**, and must not be reported as model failures.

**Condition C7 — one code path, guarded.** The policy is implemented once and applied to all
arms, with a test asserting the QA no-op so any future change that perturbs the comparator fails
loudly.

**Not affected:** grounding. Extraction changes only the structural stage — for ZS/FS the raw
output never parsed so grounding never ran; for QA the parsed content is byte-identical.

## Scope

This ADR governs Plan 2 prediction parsing and the Plan 3 certification that consumes it. It does
not re-open the Plan 2 PASS at `8e5a2c8`, and does not authorise Plan 3, spend, or sealed-label
access. A template-echo false-accept path was probed (the frozen template contains two literal
JSON objects, and an echoed `{"arguments":[]}` would be schema-valid and ground trivially): it is
real by construction but **does not occur in this data** — 0 competing later objects in ZS and QA.
Any future change to the prompt template must re-run that probe.
