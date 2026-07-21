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

## Follow-up 1 — is either stack better? No (quality-neutral)

The 41 divergent pairs scored against **train gold** (train labels are not sealed; the probe used
train frames only):

| Stack | P | R | F1 | Exact-set match |
|---|---|---|---|---|
| served (vLLM — the evidence base) | 0.321 | 0.365 | 0.341 | 5/41 |
| local (transformers+peft) | 0.379 | 0.406 | 0.392 | 2/41 |

Local edges F1; served wins exact matches. That is a 4-true-positive difference over 96 gold
arguments at n=41 — **noise, not a systematic gap**. This downgrades the severity: the served
evidence base is *not* measurably worse than the adapter is capable of. It is a reproducibility
caveat, not a quality defect.

Note the absolute level: **F1 ≈ 0.35 on divergent frames** is far below what either stack manages
generally, which motivated the next question.

## Follow-up 2 — divergence concentrates where the model is uncertain

Comparing the 41 divergent frames against the **259 tested-and-agreeing** frames (not against
untested frames — the probe's deterministic selection was reproduced exactly to get this right):

| Confidence candidate | Divergent (median) | Agreeing (median) |
|---|---|---|
| mean transition logprob | −0.0782 | −0.0529 |
| 10th percentile | −0.2989 | −0.1619 |
| minimum | −0.9387 | −0.6872 |

Divergent frames sit at median percentile **0.26** of the tested set by min-logprob: **48.8% fall in
the bottom quartile** (chance 25%) and **0.0% in the top quartile** (chance 25%).

Divergence rate under a selective acceptance policy (accept the top X% by min-logprob):

| Accept | Divergence rate |
|---|---|
| 100% (no abstention) | 13.67% |
| top 90% | 12.59% |
| top 75% | 9.33% |
| top 50% | 6.00% |
| **top 25%** | **0/75 = 0%** |

**Why this is the mechanism you would predict:** a numerical difference between kernels flips an
argmax only where the model is near-indifferent, and near-indifference is precisely what a low
transition log-probability measures. Selective prediction abstains on exactly those frames.

**This materially softens — but does not eliminate — the limitation.** The *raw* system is 13.67%
stack-dependent; the *accepted* set is far more stable, and at a 25% acceptance rate we observed
no divergence at all. It must not be reported as "0%": 0/75 carries a 95% upper bound of roughly
**4.8%** (rule of three). The honest claim is that stack-dependence falls steeply with confidence
and is small-to-negligible in the high-confidence region a certified policy would accept.

Caveats on this follow-up: train split only; n=41 divergences; `minimum` is one of three
predeclared confidence candidates and the operative one is not chosen until Plan 3 calibration;
and the relationship is correlational, established on the frames the probe happened to sample.

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

## Standing follow-up

Carry into the Plan 4 limitations section and any model/report card, scoped to the serving stack:
the **13.67% raw divergence rate**, the **1.3% abstain/extract flip rate**, the quality-neutrality
result, and the confidence-concentration result with its ~4.8% upper bound in the top quartile.
Both follow-ups above are complete; the two remaining open items are the reviewer's assessment
(no threshold was pre-registered) and re-measuring on a non-train split if that is ever wanted.
