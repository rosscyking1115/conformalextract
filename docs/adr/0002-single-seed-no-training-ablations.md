# ADR 0002: Single training seed; no training-time ablations

- Status: accepted (records an existing plan reality as an explicit decision)
- Date: 2026-07-19
- Trigger: portfolio DL-evidence checklist item 6 (2026-07-19 Manager brief) requires that
  "multiple seeds + controlled ablations", if cut for budget, be an explicit ADR — not an omission.

## Decision

Plan 2 trains the QA adapter with **one frozen seed (42)** and runs **no training-time ablation
grid** (no rank/alpha/dropout/target-module sweeps; the R1 learning-rate set {2e-4, 1e-4, 5e-5}
exists only as a predeclared compatibility adjustment, not an ablation study).

## Rationale

The authorized aggregate compute cap is **$25.00** with **$24.7992** remaining at decision time.
The R0-measured forecast puts the full single-seed programme (R1 + R2 + 27,372-generation
prediction pass + upload + reserve) at ~**$16.08 buffered**. A second seed roughly doubles the
training+prediction cost and breaches the cap; a minimal ablation grid (3 ranks × 2 lrs) would
multiply it several-fold. Within a fixed small budget, the certified-acceptance question (H1/H2)
is better served by one well-evidenced run than by an underpowered seed/ablation sample whose
variance estimate would itself be statistically weak (n=2–3 seeds).

## Substitutes in place (what carries the reproducibility burden instead)

- Deterministic seed + pinned environment (model/tokenizer revisions; env lockfile per
  `docs/plan2/r1-training-env.md`) — bit-level reproducibility of the single run.
- Gate 0F-style fresh-process adapter reload + greedy-equivalence proof, and two persisted
  adapter copies with matching hashes (Plan 2 sequence step 6).
- Tracked runs: Trackio aggregate metrics + the stage/time/cost ledger.
- CPU-side sensitivity analyses remain in scope (Plan 3 §11.1: mean-vs-max document loss,
  exact-vs-normalized matching, secondary score) — ablations of the *analysis*, which the budget
  does permit, as distinct from ablations of the *training*.

## Consequences

- The report must name **seed variance as an explicit limitation**: results are for one seed;
  no claim of robustness-across-seeds is made or implied.
- Any future multi-seed extension is a new paid-run decision against a new budget, not a silent
  reopening of this one.
