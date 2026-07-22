# ADR 0009: Within-group aggregation for certification

- Status: **accepted** (independent reviewer PASS on the rule,
  `evidence/plan3/reviewer_record.adr-0009.json`, with four amendments incorporated below)
- Date: 2026-07-21 (amended 2026-07-22 after review)
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
  group as one observation whose loss is the average behaviour over its near-duplicates.

### Why mean loss rather than max loss (amendment A1 — the original rationale was falsified)

The first version of this ADR rejected max loss as "double-conservative", implying it would
depress certified acceptance unacceptably. **That is false and the reviewer disproved it:** under
max loss the group base risk is 0.7253, giving a maximum feasible acceptance of **0.3433** —
comfortably above the 0.20 floor. Max loss would *not* make certification infeasible, so
infeasibility is not the reason to reject it.

The reason that does hold is size-dependence. Measured on the development split:

| Aggregate | correlation with group size |
|---|---|
| **mean** loss | **−0.0190** |
| **max** loss | **+0.2722** |

A maximum over more draws is mechanically larger, so max loss penalises a group *for being big* —
and group size tracks **source**, not difficulty. Max loss would therefore import a corpus
artifact into the risk estimate. Mean loss is effectively size-neutral, which is what the
independence unit requires. This confirms the premise (size ⊥ difficulty) for mean and refutes it
for max.

### What the certificate therefore bounds — stated explicitly

Mean loss means the certificate bounds **average within-group error, not the absence of error**.
A 22-member group with 21 correct members and one confidently-wrong one has mean loss 0.045, and
that wrong member was accepted by construction. This is the intended semantics and it is
defensible — a group is one observation whose loss is its average behaviour — but it must be
stated rather than left implicit. A reader must not take an accepted group to mean every document
in it was right.

## Alternative considered and rejected (amendment A4 — rewritten)

**One representative document per group** (deterministic pick by lowest document-id hash).

The original rejection said it "discards 1,756 of 3,152 documents". That phrasing was
self-defeating: it reads as a sample-size argument, which invites exactly the suspicion that
aggregation inflates effective `n`. **It does not, and that is what settles the question:
`n = 1,396` either way.** Aggregation cannot manufacture independent units — the group count is
fixed by the clustering, not by how members are combined.

What aggregation actually buys is **lower per-unit measurement variance at identical
independence**: a group's mean over its members is a less noisy estimate of that cluster's
behaviour than one arbitrarily-chosen member. Given the within-cluster correlation the gain is far
below √22, but it is strictly positive, and one-representative makes every unit a single arbitrary
draw for no compensating benefit. Rejected on that basis, not on document counts.

## Hard acceptance ceiling from invalid members (amendment A4)

Because a group is valid only if **every** member is, groups containing an invalid document can
never be accepted at any threshold. On the development split this is **37 of 398 groups (9.3%)**,
three of them carrying a `-inf` member score from a `context_overflow` document. That caps
achievable acceptance at **0.907 before any threshold applies**, independently of the score.

This is a real, disclosed cost of the all-valid rule. It is accepted because the alternative —
accepting a group while one of its members is a structural or grounding failure — would certify a
policy that knowingly emits invalid output. `certify` emits `never_acceptable_groups` and
`acceptance_ceiling` per system so the equivalent figure on the certification split is recorded
rather than assumed from development.

## Consequences

- `n = 1,396` independent rows for the theorem — the value ADR 0007's grid sizing already assumed
  and `evidence/plan2/threshold_grids.json` was built against. This ADR makes that assumption
  explicit rather than implicit.
- The rule is applied identically to ZS, FS and QA. No system gets a different aggregation.
- Group size varies 1–22; a 22-member group carries the same weight as a singleton, which is the
  point — they are one independent observation, not 22.

### Unweighted vs size-weighted risk (amendment A2)

The certificate bounds the **unweighted** mean of group means. A reader will naturally hear a
**document-level** claim, which is the size-weighted quantity. On development these agree closely
— unweighted 0.5898 vs size-weighted 0.5834, a gap of +0.0064 in the *conservative* direction and
small against α = 0.20 — but **that agreement is an empirical consequence of size ⊥ mean loss on
this split, not a theorem**. `certify` therefore emits both plus their gap per system
(`loss_summary`), so the gap is observed on the certification split rather than assumed.

### The accepted set skews small-group (amendment A3)

`corr(size, min-score) = −0.3527`, monotone in size (median min-score −0.0574 at size 1 →
−0.1079 at size 7+): a minimum over more draws is stochastically lower, so a uniform threshold
preferentially accepts small groups. **This does not violate the theorem** — the i.i.d.
requirement is over draws of clusters from the population, and size is an attribute of the draw,
not cross-unit heterogeneity. The full argument is settled in
`docs/plan3/theorem-to-code-scorc.md`. Two scope statements follow: the accepted population is not
a uniform sample of the group population (the artifact emits `accepted_size_distribution`), and
the guarantee is scoped to this corpus's natural clustering structure.

### Status

**Accepted** following independent review. The reviewer verified the group structure reproduces
from the committed role map, confirmed the safety gates by execution, and PASSed the rule
unchanged; the four amendments above are documentation and reporting only — no change to the rule
and no re-run required.
