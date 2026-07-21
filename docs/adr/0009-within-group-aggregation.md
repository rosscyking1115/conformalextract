# ADR 0009: Within-group aggregation for certification

- Status: **proposed — requires independent review before `certify` runs against sealed labels**
- Date: 2026-07-21
- Trigger: implementing `certify` surfaced a gap. Plan 3 fixes the *unit* ("the independent unit
  is the source-document group", §2.1; "compute at the document-group unit", §7.1) but never
  specifies how the documents inside a group combine into one row. That is an evaluation
  decision, so it is recorded and reviewed rather than chosen silently in code.

## The gap

The certification split holds **3,152 documents in 1,396 groups**. Group sizes are not
degenerate — 712 groups hold more than one document (distribution: 684 singletons, 336 pairs,
146 triples, … up to one group of 22). Predictions are per-document; the certifier needs one
independent row per group. Something must combine them, and the choice changes the certificate.

Groups are near-duplicate clusters (`source-id + normalized-sha256 + word-fivegram-minhash`, per
`manifests/plan2/split_manifest.json`). Members are highly correlated by construction, which is
exactly why the group — not the document — is the independence unit.

## Decision

For each group, over its member documents:

| Quantity | Rule |
|---|---|
| Group **score** | **minimum** of member document confidences |
| Group **accepted** | every member structurally valid **and** group score ≥ threshold |
| Group **loss** | **mean** of member document losses |

Implemented by reusing `selection.accept_whole_document(frame_confidences=…,
structurally_valid=…, threshold=…)` unchanged, one level up: it already computes exactly
`all(structurally_valid) and min(frame_confidences) >= threshold`.

## Rationale

- **It is the established rule, scaled up.** Plan 2 audit correction #1 already fixed the
  frame→document rule: a document is accepted only if *every* trigger frame is valid, at the
  *minimum* frame confidence (`training.aggregate_document_prediction`). Applying the identical
  all-valid/worst-confidence rule at document→group is consistent rather than novel, and reuses
  the same tested function instead of a parallel implementation.
- **It is the conservative direction.** Min-score and all-must-be-valid both make acceptance
  *harder*, so the acceptance lower bound is not inflated by a group's easiest member. A rule
  that accepted a group when *any* member cleared the threshold would let near-duplicates
  manufacture acceptance.
- **Mean loss keeps the loss bounded in [0,1]**, which `scorc_certificate` requires, and treats a
  group as one observation whose loss is the average behaviour over its near-duplicates. Max
  loss was considered and rejected as double-conservative: acceptance is already worst-case, and
  compounding both would understate certified acceptance for a reason unrelated to the science.

## Alternative considered and rejected

**One representative document per group** (deterministic pick by lowest document-id hash). Simpler
and unimpeachably independent, but it discards 1,756 of 3,152 certification documents — over half
the split — and makes the certificate depend on an arbitrary pick within each cluster. Rejected:
it throws away real evidence to avoid a decision that the conservative aggregate already handles.

## Consequences

- `n = 1,396` independent rows for the theorem — the value ADR 0007's grid sizing already assumed
  and `evidence/plan2/threshold_grids.json` was built against. This ADR makes that assumption
  explicit rather than implicit.
- The rule is applied identically to ZS, FS and QA. No system gets a different aggregation.
- Group size varies 1–22; a 22-member group carries the same weight as a singleton, which is the
  point — they are one independent observation, not 22.
- **This ADR is `proposed`, not `accepted`.** `certify` must not open the sealed certification
  labels until it is reviewed, because the rule materially determines the certificate.
