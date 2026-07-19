# R0 inference-benchmark launch plan + RESULT

## R0 RESULT (2026-07-18) — completed, decision GO

Ran on 1× L4 (job `6a5bcee6bee6ee1cf4ecfe08`, COMPLETED). Measured, at the assumed length
distribution (mean 1502 input / ~502 output):

| Metric | Value |
|---|---|
| items/hour | **2,771** (worst-case: random tokens ran to the full 512 cap, so real RAMS output is shorter → real throughput higher) |
| aggregate tok/s | 1,542 · output tok/s 386 |
| cost / 1M tokens | $0.144 |

Whole-programme forecast (`forecast_whole_programme`, measured 2,771 items/hr, predictions =
9124×3 = 27,372 items essential, R0+R1/R2 allowance $4.50, upload $0.10, reserve $2.00, 20%
buffer): **decision = GO**, total **$16.08 of the $24.7992 cap**, **$8.72 headroom**. Conservative;
real cost likely ~$8–12 once true (shorter) output lengths and the real prompt distribution apply.

**Fixes applied to make it run** (record for the next job): token needed **Write** scope; deps
must pin only `vllm==0.25.1` (+ numpy) — over-pinning numpy/hf-hub breaks uv resolution; the slim
uv image lacks nvcc so use `enforce_eager=True` and `VLLM_USE_FLASHINFER_SAMPLER=0` (flashinfer JITs
its sampler); vLLM 0.25.x takes token prompts positionally as `{"prompt_token_ids": ids}` dicts.

**Remaining before R1/R2:** ~~re-run with the real frozen prompt-length distribution~~ **DONE
2026-07-19** (below); and the training pre-flight (G3) at R1 submission.

## R0 re-run at the REAL distribution (2026-07-19) — new-rung smoke, decision GO

Job `6a5d517ed216bd6f3a2021f1`, COMPLETED on 1× L4. Parameters from the frozen evidence
(analysis `plan2prep-f3f2f7a938061a92b2cb`): mean-input 2,000 (measured 2,011), max-input 6,144
(the ADR-0003 selected rung — this run satisfies the data contract's changed-rung smoke),
max-model-len 6,656, output cap 512 (worst case; real completion max = 162).

| Metric | Value |
|---|---|
| items/hour | **2,196.6** |
| aggregate / output tok/s | 1,536.9 / 309.5 |
| cost per 1M tokens | $0.1446 |
| run cost | ≈ $0.10 |

Whole-programme forecast at the measured rate (27,372 predictions essential, R0+training
allowance $4.50, upload $0.10, reserve $2.00, 20% buffer): **GO — total $18.56 of $24.7992,
headroom $6.24** (worst-case output lengths; real ≤162-token completions will land lower).

---

## Original launch spec (below) — retained for reference

Paid GPU execution is a hard approval gate. The assistant will not launch expensive stages;
Ross approves each after confirming prepaid Hugging Face Jobs credit.

## Purpose
Measure Qwen3-4B vLLM batched-generation throughput on the real RAMS prompt-length distribution,
on a **1× Nvidia L4 ($0.80/hr)**, and feed the measured `items_per_hour` into
`forecast_whole_programme` to get an honest go/stop/infeasible decision for R1 + R2 + full
prediction generation — before committing the expensive stages. Script: `jobs/r0_inference_benchmark.py`.

## Cost
R0 itself is tiny: 256 random-length prompts, a few minutes on L4 plus model load/queue.
**Estimated ≤ $0.30** (well under $1). It does not train and does not touch the $2 reserve.

## Privacy / safety (built into the script)
- **Text-free:** benchmarks from RANDOM in-vocab token ids at the real *lengths* (token counts
  are metadata). It never reads/downloads/uploads raw RAMS/WikiEvents text, sealed labels, or
  predictions. Output is aggregate throughput metrics only.
- **No token exposure:** the job needs `HF_TOKEN` only if persisting a report to the private
  evidence dataset (optional); the script never prints it. Prefer running without persistence
  first (report goes to logs).

## Pre-launch checklist (must all be true before the run)
- [ ] Prepaid HF Jobs credit confirmed positive (past jobs hit HTTP 402 without it).
- [ ] `vllm` version pin in the PEP 723 header is compatible with the HF Jobs L4 image — the
      header pins `vllm==0.11.0` as a **placeholder**; confirm the current working version, and
      that `LLM.generate(prompt_token_ids=...)` matches that version's API (newer vLLM may need
      `prompts=[TokensPrompt(prompt_token_ids=...)]`). The first run doubles as this smoke test.
- [ ] Real RAMS length distribution: pass `--mean-input/--min-input/--max-input` from the frozen
      `prepare-data` context-window evidence once it exists; until then the defaults
      (mean 1500, 512–4096) are a stated assumption, not measured.
- [ ] Flavor = `l4x1`; timeout ≥ `30m` (model download + benchmark).

## Launch command (choose one; NOT executed here)

**Hugging Face CLI (local script upload):**
```bash
hf jobs uv run --flavor l4x1 --timeout 30m \
  jobs/r0_inference_benchmark.py -- --num-prompts 256
```

**MCP `hf_jobs` (inline script):** read `jobs/r0_inference_benchmark.py` and pass its contents as
the `script` string with `{"flavor": "l4x1", "timeout": "30m"}` (add
`"secrets": {"HF_TOKEN": "$HF_TOKEN"}` only if persisting a report). Monitor with `hf jobs logs`.

## After R0 — decide before any expensive stage
Take `items_per_hour` from the `R0_BENCHMARK_REPORT=` log line and run the forecast locally
(CPU, no spend):
```python
from conformalextract.training import forecast_whole_programme, InferenceBenchmark, StageDemand
bench = InferenceBenchmark(batch_size=64, items_per_hour=<MEASURED>, hourly_rate_usd=0.80)
forecast_whole_programme(
    benchmark=bench,
    stages=(StageDemand(stage="R1", items=<R1>), StageDemand(stage="R2", items=<R2>),
            StageDemand(stage="predictions", items=9124*3, essential=True)),
    r0_cost_usd=<R0 actual>, upload_cost_usd=0.10, reserve_usd=2.00,
)
```
**Decision rule:** proceed to R1/R2 + generation only if the forecast returns `go`. `stop` →
rescope (fewer prompts, shorter output cap, drop a system). `infeasible` → halt. (Illustration:
at 1500 items/hr and the full 27,372-item generation with a 512 output cap, the forecast is `go`
at ~$21.4 — but with modest margin, so the real measured throughput and output length matter.)

## What R0 does NOT cover (validate later)
- The QA path uses base bf16 + a LoRA adapter served by vLLM; R0 benchmarks the base (a fair
  proxy). The actual adapter-under-vLLM path is validated once R1 produces an adapter.
- Training pre-flight (G3: `max_length` == ladder rung, lr 2e-4, `use_cache=False` +
  `use_reentrant=False`, `print_trainable_parameters` band, env lockfile) applies to R1/R2, not R0.
