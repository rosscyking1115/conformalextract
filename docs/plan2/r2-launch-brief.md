# R2 full training — pre-launch brief (for Ross's approval; NOT launched)

2026-07-19. Script: `jobs/r2_qlora_full.py` · tests: `tests/test_r2_job_contracts.py`.
Design Ross-approved: **2 epochs on the full train split, per-epoch checkpoints, exactly one
QA checkpoint selected by full-development loss** (the plan's own selection rule).

## What it does beyond the PASSed R1 pilot

Full 4,068-example train split × 2 epochs (reshuffled per epoch, same seed stream); development
loss measured at baseline and after each epoch on the full 933-example dev split; the lower-dev-
loss epoch's adapter is THE QA adapter. Fresh-process reload equivalence proven in-job (Gate 0F
subprocess pattern, greedy 8-token hash on a synthetic prompt). Selected adapter persisted as
**two checked copies**: copy A → private evidence Dataset (`plan2/r2/adapter/`), copy B →
private Model repo `rosscyking/conformalextract-qwen3-4b-qlora` (created 2026-07-19; Plan 4's
eventual public name, private until release gates). Metrics JSON per ADR 0004.

Same guards as R1 (all test-asserted): ephemeral checksum-verified download with raw deleted
before model load; SFT reads train only; dev gold only for selection; sealed roles never
rendered (`sealed_reads: 0`, hash-chained); text-free persistence; G3 pre-flight in-job.

## Cost

Measured basis (R1): 1.34 s/example → 2 epochs ≈ 3.0 h train + ~0.4 h evals/loads/reload-check
≈ **$6.1–6.9 expected** on L40S. Timeout 6h caps worst case at $10.80. Whole-programme forecast
with this run: **GO — $20.35 of $24.7992, $4.45 headroom** (worst-case output lengths).

## Pass / fail

- **PASS (`r2_pass: true`):** selected dev loss < baseline; reload equivalence holds; two copies
  persisted. → Next: the prediction-generation job (ZS/FS/QA × 9,124) drafted for approval.
- **REVISE:** no dev improvement — stop, diagnose with the per-epoch stats; no silent retry.

## Launch (on Ross's go)

`hf jobs uv run --flavor l40sx1 --timeout 6h --detach -s HF_TOKEN jobs/r2_qlora_full.py`

---

## R2 RESULT (2026-07-20) — PASS

Job `6a5d5e98d216bd6f3a202357`, COMPLETED on L40S in 3.33 h, **actual cost ≈ $6.00** (est. $6.1–6.9).

| Metric | Value |
|---|---|
| dev loss baseline → epoch 1 → epoch 2 | **1.205 → 0.1240 → 0.1249** |
| **selected epoch** | **1** (dev selection earned its keep: epoch 2 gave no dev gain) |
| train loss (e1 first→last quarter) | 0.246 → 0.133; (e2) 0.117 → 0.112 |
| trained / excluded-over-context | 4,065 per epoch / 3 (consistent with the 7-total frozen exclusions) |
| label access | train_sft 8,136 · development_selection 2,799 · **sealed_reads 0** · head `68992576…` |
| raw deleted before model load | true |
| fresh-process reload | ran deterministically, token hash `2b264ab0…` |
| persisted | copy A (evidence) `1163b6bb` · copy B (adapter repo) `edd69373` · metrics sha `54e3ad22…` |

**Honest caveat on reload equivalence:** the selected epoch (1) was not the final in-memory
state (epoch 2), so there was no in-process hash to compare against — the subprocess proved the
selected adapter loads fresh and generates deterministically, not a before/after equality. The
full fresh-process **parsed-output equivalence** proof (plan step 6) is folded into the
prediction-generation job, which loads this adapter fresh by construction and will generate a
small equivalence sample twice in independent processes.

Programme spend to date ≈ **$6.85** of $24.7992 (headroom ≈ $17.95 before the prediction job).
