# Serving-equivalence probe — result (2026-07-21)

Reviewer-required control (decision 2 of `evidence/plan2/reviewer_record.extraction-policy.json`).
Compares the **vLLM 4-bit + LoRA** stack that generated the entire Plan 2 evidence base against the
**transformers+peft** training stack, on real train-split prompts, greedy, `max_new_tokens=256`.

| Run | Job | n | Agreement | Cost |
|---|---|---|---|---|
| v1 | `6a5fa55913e6ef894d549ee7` | 24 | 87.5% | $0.046 |
| **v2 (authoritative)** | `6a5fab15d09dc1f57c6bfb68` | **300** | **86.33% (259/300)** | $0.48 |

v2 report: `plan2/serving_equivalence_probe.v2.json` (commit `3d207c99`).
Divergent pairs: `plan2/serving_equivalence_divergences.v2.jsonl` (private, ADR 0005).

## Headline

- **Prompt reproduction is exact: 300/300** `prompt_sha256` matches. Prompt construction is
  faithful and reproducible; nothing drifted between the generation run and this probe.
- **Parsed-output agreement: 86.33%**, 95% Wilson CI **[81.98%, 89.76%]**.
- **Divergence rate: 13.67%**, 95% CI **[10.24%, 18.02%]**.

## The divergences are substantive, not cosmetic

Of 41 divergences, **40 change the predicted frame content**. Only one is a serialisation triviality.

| Category | n | What it means |
|---|---|---|
| `argument_count_differs` | 18 | The stacks extract a different *number* of arguments |
| `same_roles_different_spans` | 18 | Same roles, but pointing at **different entities** |
| `empty_vs_nonempty` | 4 | One stack abstains entirely; the other extracts arguments |
| `same_roles_same_spans_different_text` | 1 | Cosmetic |

Representative pairs (verbatim from the private divergence file):

- **abstain vs extract** — served `{"arguments":[]}` against local
  `[{"role":"participant","text":"Trump"},{"role":"participant","text":"Fox"}]`.
- **different entities** — served `killer = "WikiLeaks editor Julian Assange"` against local
  `killer = "Bob Beckel"` (both agree `victim = "Julian Assange"`).
- **different count and spans** — served 3 arguments against local 2, with disjoint spans.

These are different answers, not rounding noise. **We cannot say which stack is "more correct"**
without scoring against gold; that is a legitimate, permitted $0 follow-up because these are
train-split frames whose labels are not sealed.

## What this threatens, stated precisely

- **Internal validity — intact.** All three systems (ZS/FS/QA) were generated on the *same* vLLM
  stack, so the QA-vs-baseline comparison is consistent, and the certified system is *defined* as
  the adapter as served on the frozen stack. Certification remains meaningful.
- **Portability — not established, and must not be implied.** The same adapter on a different
  4-bit stack produces a materially different frame on roughly one in seven documents.
- **Selective behaviour is itself stack-dependent — the sharpest concern.** The abstain/extract
  decision flips on 4/300 (1.3%) of frames. Abstention is the mechanism the entire thesis rests
  on, so a guarantee about *selective* extraction inherits this instability when the serving stack
  changes. Any claim must be scoped to the exact serving stack, quantified with this figure.

## Honest limitations

- **No pass threshold was pre-declared.** The probe was specified to *quantify* parity, not gate on
  it. Declaring 86.33% acceptable would be the post-hoc reasoning ADR 0006's C4 guards against.
  The assessment belongs to the reviewer at the Plan 2 close.
- Probe frames are **train-split only** (by design — no sealed-split document is touched), so the
  rate is measured on data the adapter was trained on and may not equal the rate on certification
  or final splits.
- Cause is not isolated here: the two bitsandbytes kernel paths differ numerically, but this run
  does not attribute the divergence to a specific kernel, batching effect, or prefix-caching
  behaviour.

## Recommended follow-ups ($0)

1. Score the 41 divergent pairs against **train gold** (not sealed) to establish whether either
   stack is systematically better, or whether divergence is quality-neutral noise. This changes the
   severity materially: neutral divergence is a reproducibility caveat, whereas a systematic
   quality gap would mean the served evidence base is measurably worse than the adapter can do.
2. Carry the 13.67% figure and the 1.3% abstention-flip rate into the Plan 4 limitations section
   and any model/report card, scoped to the serving stack.
