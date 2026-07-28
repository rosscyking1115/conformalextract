# ADR 0004: Hash-versioned metrics JSON fulfils the run-tracking requirement

- Status: accepted (Ross-approved with the R2 plan, 2026-07-19)
- Date: 2026-07-19

## Decision

Plan 2's run-tracking requirement ("private Trackio; aggregate metrics and hashed IDs only")
is fulfilled by the pattern the R1 pilot proved: each paid run persists one **aggregate-only,
text-free metrics JSON** to the private evidence Dataset with a sha256 artifact hash and a
hub commit oid, refuse-overwrite semantics, and a `parent_commit` concurrency guard. No
standing Trackio space is created.

## Rationale

The plan's intent is that runs are tracked privately, aggregate-only, and auditable. The
evidence-repo JSON pattern meets or exceeds that: metrics are (a) versioned by hub commits,
(b) content-addressed (artifact sha256 recorded in git alongside the code that produced them),
(c) immutable (refuse-overwrite), and (d) already independently reviewed as a pattern in the
Gate 0E/0F cycle. A Trackio service would add a standing dependency and UI with no additional
scientific or audit value for a programme of ~4 paid runs; the checklist's "tracked runs"
item (DL-evidence brief, item 6) is satisfied by artifacts, not dashboards.

## Consequences

- Every paid run (R1 done; R2, prediction generation) persists its metrics JSON this way.
- The Plan 4 evidence bundle references these artifacts directly; no migration needed.
- If the programme ever grows beyond a handful of runs, revisit with a new ADR.
