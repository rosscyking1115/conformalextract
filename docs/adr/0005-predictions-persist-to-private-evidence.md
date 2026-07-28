# ADR 0005: Generated predictions persist to the private evidence Dataset

- Status: accepted (Ross-approved, 2026-07-20)
- Date: 2026-07-20
- Trigger: audit correction #5 — "Generated predictions containing grounded text require a
  separate privacy decision before upload." The prediction-generation job is being drafted;
  this records that decision.

## Decision

Full generated predictions for all three systems (ZS/FS/QA × 9,124 RAMS trigger frames),
including parsed argument spans with their grounded text, are uploaded to the **private**
evidence Dataset `rosscyking/conformalextract-evidence` under `plan2/predictions/`. Plan 3
certification runs from a clean download of these artifacts.

## Rationale and boundaries

- The repo is private, already holds restricted-adjacent material (role metadata, adapters),
  and is the single canonical evidence home — one auditable chain from generation to
  certificate.
- **This decision does NOT extend to any public surface.** Plan 4's redistribution matrix
  governs release; raw RAMS text and predictions with recoverable text remain non-redistributable
  (RAMS's own terms; frontier check 2026-07-18 confirmed non-redistribution is required).
  Public artifacts may carry only derived, non-reconstructive statistics and hashes.
- Alternatives considered: local-only persistence (strictest, but log-based transfer of ~27k
  predictions is clumsy and less auditable) and text-redacted upload with local reconstruction
  (adds a reconstruction failure mode to the certification path). Rejected in favour of the
  auditable single home.

## Consequences

- The generation job uploads prediction JSONL per system + aggregate metrics; the label-free
  prediction *manifests* (hashes/counts) remain the only prediction artifacts referenced in git.
- Any future public release of prediction-derived data requires its own Plan 4 V8 licence gate.
