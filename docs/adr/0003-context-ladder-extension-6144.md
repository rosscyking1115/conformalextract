# ADR 0003: Extend the context ladder from 4,096 to 6,144

- Status: accepted (Ross-approved, 2026-07-19)
- Date: 2026-07-19
- Trigger: the first real `prepare-data` run failed by design — "context exclusions exceed
  policy at the maximum context rung" — on the measured Qwen token counts of the 5,001
  train/development profiles.

## Decision

Extend the frozen context ladder from (2048, 2560, 3072, 3584, 4096) to
**(2048, 2560, 3072, 3584, 4096, 4608, 5120, 6144)**. The selection policy itself is unchanged:
lowest rung with exclusions ≤5% overall and ≤10% in every event-role slice, `<EMPTY>` as an
explicit slice, output cap 512.

## Evidence (measured 2026-07-19, metadata only — no text read)

- Prompt-token percentiles over 5,001 profiles: p50=1,838 · p75=2,238 · p90=2,721 · p95=3,081 ·
  p99=4,071 · max=7,384. Completion max = 162 tokens (vs the 512 cap).
- At 4,096: overall exclusion **0.90%** (45/5,001) — well under the 5% overall limit — but the
  **per-slice 10% limit is unsatisfiable**: tiny event-role slices (n=1–2) whose single example is
  long produce 50–100% slice exclusion (e.g. `conflict.attack.bombing::<EMPTY>` = 1/1 excluded).
- At 6,144: policy **passes** — overall 0.14% (7/5,001), worst slice 9.1%.

## Why extend the ladder rather than change the policy

The alternative (exempting tiny slices from the 10% rule) would redefine the policy's statistical
meaning after seeing data and permanently drop whole rare slices from training. Extending the
ladder keeps the policy's semantics intact — the ladder simply did not reach far enough for the
real distribution — and Qwen3-4B natively supports 262k context, so 6,144 is well within the
model's envelope. Cost impact is modest and partly offset by the measured real completion
lengths (≤162 vs the 512 planning cap).

## Consequences

- Per the data contract, **a changed rung requires a new R0 smoke** — satisfied by the already
  planned R0 re-run at the real prompt-length distribution (max-input 6,144).
- Training/serving configs must track the selected rung (the G3 pre-flight already asserts
  `max_length == context_tokens`); memory headroom at 6,144 is verified in the R1 smoke.
- The 7 still-excluded frames receive the predeclared treatment (excluded from preparation;
  reported by count and slice, never silently).
- `CONTEXT_LADDER` (training.py), `choose_context_window` default (preparation.py),
  `configs/model.json`, and `docs/plan2/data-contract.md` updated together in this change.
