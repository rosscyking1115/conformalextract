# Serving-equivalence probe — result (2026-07-21)

Job `6a5fa55913e6ef894d549ee7`, COMPLETED on 1× L4, 207s, **$0.046**. Reviewer-required control
(decision 2 of `evidence/plan2/reviewer_record.extraction-policy.json`). Report persisted to
`plan2/serving_equivalence_probe.v1.json` (commit `1073d1f9`).

Compares the **vLLM 4-bit + LoRA** stack that generated the entire Plan 2 evidence base against
the **transformers+peft** training stack, on 24 real train-split prompts, greedy, `max_new_tokens=256`.

| Metric | Result |
|---|---|
| Prompt reproduction (`prompt_sha256` vs saved records) | **24 / 24** |
| Both stacks yield an extractable object | 24 / 24 |
| Exact raw-string match | 21 / 24 |
| **Parsed-output agreement (adopted extraction policy)** | **21 / 24 = 87.5%** |
| Local output tokens | mean 49.8, max 95 |

## Reading this honestly

**Prompt reproduction is clean.** All 24 re-rendered prompts hash-match what the generation run
recorded. Prompt construction is faithful and reproducible; nothing drifted between runs.

**Output parity is not clean: the two stacks disagree on ~12.5% of frames.** Under greedy
(deterministic) decoding, the same adapter on the same base model produced different parsed
output on 3 of 24 prompts — attributable to numerical differences between the two bitsandbytes
4-bit kernel paths. This is a real, measured residual, not noise to be waved away.

**No pass threshold was pre-declared.** The probe was specified to *quantify* parity, not to gate
on it. Declaring 87.5% "acceptable" now would be precisely the post-hoc reasoning ADR 0006's C4
exists to guard against. The number is reported; the assessment belongs to the reviewer.

**n = 24 is small.** The 95% Wilson interval on 21/24 is roughly **[0.69, 0.96]** — wide enough
that the true divergence rate could plausibly be anywhere from ~4% to ~31%. A headline caveat
should not rest on an interval this loose.

## What it does and does not threaten

- **Internal validity — unaffected.** All three systems (ZS/FS/QA) were generated on the *same*
  vLLM stack, so the QA-vs-baseline comparison is internally consistent. The certified system is
  *defined* as the adapter as served on the frozen stack.
- **External validity — caveated.** The same adapter deployed on transformers+peft would produce
  different output on a measurable fraction of frames. Any claim must be scoped to the serving
  stack; portability across stacks is **not** established and must not be implied.

## Limitation of this run

The report is text-free by design, so the three divergent cases could not be inspected — we know
*that* they differ, not *how* (a single argument differing vs a wholesale different frame have
very different implications for the risk guarantee). A follow-up should persist the divergent
pairs to the private evidence repo (permitted under ADR 0005) so the divergence can be
characterised, and should raise `n` — at $0.046 for 24 prompts, n≈300 costs well under $1.

## Status

Reviewer-required control **executed**; result recorded. Whether 87.5% at n=24 satisfies the
control is a reviewer judgement, pending at the Plan 2 close.
