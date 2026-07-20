# G2b serving benchmark — result (2026-07-20)

Job `6a5e397ed09dc1f57c6bd562`, COMPLETED on 1× L4, ~$0.10. Measures the FROZEN 4-bit serving
stack (not R0's bf16 base) at the real prompt-length distribution.

| Arm | items/hour | output tok/s |
|---|---|---|
| 4-bit base (ZS/FS) | **2,060** | 289 |
| 4-bit base + R2 QA adapter (`edd69373`) | **1,913** | 258 |

**Path:** `vllm_bitsandbytes` — the bitsandbytes-QLoRA-under-vLLM path (the R0-flagged risk) **works**;
no transformers fallback needed. Adapter loaded as a vLLM LoRA request on the bf16... (4-bit) base.

## Whole-programme forecast (measured 4-bit rates)

Using the QA rate 1,913 items/h for all 27,372 predictions (conservative — ZS/FS are faster),
spend-to-date ~$7.00, upload $0.10, reserve $2.00, 20% buffer:

| Output cap | predictions | total / $24.7992 | headroom |
|---|---|---|---|
| 512 (worst case) | $13.74 | **$22.84** | $1.96 (tight) |
| **256 (recommended)** | ~$9.16 | **$18.26** | **$6.54** |

The benchmark generated to the cap on random tokens (no natural EOS); **real RAMS completions max at
162 tokens**, so the real run stops well before any cap and the 512 figure overstates. A **256 cap is
>1.5× the real max** — it cannot truncate a genuine JSON frame set — and restores comfortable headroom.
**Recommendation: generate with `max_new_tokens=256`** (evidence-driven, not a compromise) and log
actual output lengths. Decision: **GO.**
