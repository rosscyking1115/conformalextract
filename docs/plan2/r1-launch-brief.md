# R1 QLoRA pilot — pre-launch brief (for Ross's approval; NOT launched)

2026-07-19. Script: `jobs/r1_qlora_pilot.py` · contract tests: `tests/test_r1_job_contracts.py`.
This is the briefing the DL-evidence process commitment promised: what the run does, why each
value, what it costs, and what pass/fail means — so you can defend it, not just approve it.

## What this run is

The first real training run: a **pilot** that proves a learning signal on the frozen contract
before R2 commits the full budget. It trains one rank-16 NF4 QLoRA adapter on **512 train-role
examples** (of 4,068) for one pass and measures **development loss before vs after** on 128
development examples. If the adapter learns (dev loss drops), R2 trains on the full train split
with epochs sized from this pilot's measured step time.

## Why each value (defence points)

| Value | Why |
|---|---|
| NF4 4-bit + double-quant, bf16 compute | QLoRA paper's exact recipe; Gate 0F proved it on this GPU class |
| LoRA r=16, α=32, dropout 0.05, all-linear | frozen trainer manifest; α=2r is first-party PEFT guidance |
| lr 2e-4, AdamW | QLoRA paper's setting for ≤13B models; frozen in the manifest |
| batch 1 + grad-accum 16 | long variable-length documents; effective batch 16 |
| context 6,144 | ADR 0003 rung selected by the frozen exclusion policy on real token counts |
| seed 42, pinned model+tokenizer revision | single-seed decision per ADR 0002; bit-level reproducibility path |
| L40S (48 GB, $1.80/hr) | "only budget is a hard limit": no memory ceiling at 6,144 context, no quality compromise; Gate 0E/0F both passed on L40S |
| subset 512 train / 128 dev | enough steps (32 optimizer steps) to see a loss trend, cheap enough to throw away |

## Safety properties (enforced in-script, asserted by repo tests)

- **Ephemeral raw data:** downloads official RAMS from the frozen URL, verifies the frozen
  sha256, renders examples, then **deletes the raw archive+extraction before the model loads**
  (re-checked at runtime; test asserts the deletion precedes model load in the code).
- **Label isolation:** SFT reads **train role only**; development gold is read only for the
  before/after loss measurement (its sanctioned "development selection" purpose);
  certification/final/shift are never rendered. A hash-chained label-access summary
  (head hash + counts, `sealed_reads: 0`) goes into the report.
- **Text-free persistence:** only the adapter (safetensors), aggregate metrics, and hashes are
  persisted — no prompts, no gold, no generations, no source text (test greps the report dict).
- **G3 pre-flight in-job:** pad token set; `use_cache=False`; non-reentrant checkpointing;
  trainable-parameter band asserted; only `lora_` params trainable; finite-loss check.
- **Roles metadata:** the job downloads `plan2/rams_roles.jsonl` from the private evidence repo
  and verifies it against the frozen split-assignment hash (`1771…aaf3`) before use.
- **Persistence guard:** private-repo check, refuse-overwrite on the evidence path,
  `parent_commit` concurrency guard (same pattern as the PASSed Gate 0F job).

## Cost

- Estimated **$0.60–1.20** (~20–40 min on L40S at $1.80/hr; model load + 512 examples at
  6,144-max context + two 128-example eval passes + upload). Timeout 2h caps worst case at $3.60.
- Ledger context: ~$0.45 spent so far; forecast headroom $6.24 worst-case. R1 fits comfortably.

## Pass / fail (decided by the report, not by hope)

- **PASS (`r1_pilot_pass: true`):** dev loss after < before (real learning signal), all G3/
  isolation asserts held, adapter saved+persisted. → R2 sizing uses `seconds_per_trained_example`.
- **REVISE (`status: revise`):** run completed but no learning signal — do NOT proceed to R2;
  investigate (lr, data rendering, masking) with the persisted metrics.
- **Hard failure (job error):** asserts fired (checksum, isolation, non-finite loss, OOM…) —
  nothing persisted except possibly nothing; diagnose from logs; no silent retry.

## Launch steps (on Ross's go)

1. One-time: upload the metadata-only role assignment to the private evidence repo
   (`hf upload rosscyking/conformalextract-evidence data/private/splits/rams_roles.jsonl
   plan2/rams_roles.jsonl --repo-type dataset`). Metadata only (ids/groups/roles — no text,
   no labels); its hash is already public in the frozen lineage manifest.
2. Submit: `hf jobs uv run --flavor l40sx1 --timeout 2h --detach -s HF_TOKEN
   jobs/r1_qlora_pilot.py` (token needed for the private-repo read + evidence upload;
   passed as a secret, never printed).
3. Poll detached; on completion, verify the report, commit the evidence reference, and bring
   the R2 sizing decision back for approval.

---

## R1 RESULT (2026-07-19) — PASS

Job `6a5d58e6d216bd6f3a2022c3`, COMPLETED on L40S in 13.4 min, **actual cost ≈ $0.40**.
Evidence persisted: `plan2/r1_pilot.v1.json` + adapter at `plan2/r1/adapter/` (hub commit
`f76f92a54ce8ab5bb981fbd267447e5968fa961d`, artifact sha256 `4e300a57…dcb6c6e`).

| Metric | Value |
|---|---|
| dev loss before → after | **1.197 → 0.204** (Δ −0.993, an ~83% drop) |
| train loss first→last quarter | 0.485 → 0.224 |
| trained / excluded-over-context | 511 / 1 (of 512 sampled; consistent with 7-total frozen exclusions) |
| optimizer steps | 32 |
| seconds per trained example | **1.340** (L40S) |
| label access | train_sft 512 · development_selection 128 · **sealed_reads 0** · chain head `0e96e589…` |
| raw deleted before model load | true |

`r1_pilot_pass: true` — a real, strong learning signal on the frozen contract. R2 sizing from
the measured rate: 1 epoch $2.72 / 2 epochs $5.44 / 3 epochs $8.16 raw on L40S.
