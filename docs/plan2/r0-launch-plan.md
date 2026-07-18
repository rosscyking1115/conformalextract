# R0 inference-benchmark launch plan (DRAFT — awaiting Ross's approval)

**Nothing here has been run.** Paid GPU execution is a hard approval gate. This document is the
exact spec for the first small paid step; the assistant will not launch it. Ross runs it (or
explicitly authorizes a single run) after confirming prepaid Hugging Face Jobs credit.

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
