# Prediction-generation launch brief (Plan 2, final paid step) — NOT LAUNCHED

Status: **drafted 2026-07-20, awaiting explicit Ross approval.** Job:
`jobs/plan2_prediction_generation.py`. Contract tests:
`tests/test_prediction_generation_contracts.py` (13, all passing).

## What it does

One HF Job (l4x1, $0.80/h) generates **ZS / FS / QA × 9,124 RAMS trigger frames = 27,372
predictions** on the G2b-proven vLLM bitsandbytes 4-bit path, and persists each system's full
predictions (with grounded text, per ADR 0005) to the **private** evidence Dataset
`rosscyking/conformalextract-evidence` under `plan2/predictions/`. This unblocks every remaining
Plan 2/3 step — everything after it is $0 CPU work.

| System | Prompt | Model |
|---|---|---|
| ZS | frozen zero-shot template (identical to R2's, test-asserted) | 4-bit base |
| FS | two frozen demonstrations (hash `879baed7…`) + ZS prompt | 4-bit base |
| QA | ZS prompt | 4-bit base + R2 adapter `edd69373` (LoRA request) |

Decoding is greedy (`temperature=0`), **`max_new_tokens=256`** — the G2b evidence decision
(>1.5× the measured real max of 162 output tokens; cannot truncate a genuine frame set) — with
`logprobs=1` so every prediction carries the three predeclared confidence candidates
(mean / p10 / min transition log-probability; empty output → null ≙ −inf).

## Design points frozen by this brief

- **FS composition rule (frozen here):** `demo1.prompt \n demo1.completion \n\n demo2.prompt \n
  demo2.completion \n\n instance_prompt`, demonstrations in file order. Measured FS prefix:
  **3,097 tokens** (+separators ≈ 3,105); worst-case FS prompt 9,249 → `max_model_len = 9,728`
  (G3-style in-job assert).
- **Context overflow is explicit, never silent.** The 6,144 rung was selected on train+dev
  (5,001 profiles); sealed-split prompts may exceed it. Any frame whose ZS prompt exceeds 6,144
  tokens gets a `context_overflow` record **in all three systems** (identical comparison sets;
  flows into certification as a non-valid frame, preserving the risk guarantee — no
  cherry-picking easy documents). Expected ≈ 0.14% (~13 frames).
- **Label isolation by construction:** prompts are rendered from `evt_triggers` + `sentences`
  only; the string `gold_evt_links` does not appear in the job; `gold_links_read: 0`,
  `sealed_reads: 0`. Raw archive is checksum-verified and deleted before any model work.
- **Per-arm persistence + resume:** each arm commits to the evidence repo the moment it
  finishes (ZS → FS → QA order). A crash loses at most one arm; a relaunch skips arms whose
  file already exists. A 12-hour guard between arms stops a runaway job with completed arms
  already saved (`status: partial`).
- **Fresh-process parsed-output probe (closes the R2 serving caveat):** after the QA arm, a
  subprocess regenerates 12 deterministic train-split prompts on the *training* stack
  (transformers+peft, NF4 4-bit) and reports parsed-JSON agreement with the served vLLM
  outputs. Recorded as evidence, not a gate — the QA system under certification is *defined*
  as the adapter on the frozen serving stack.
- **Serving-latency capture (DL-evidence item 9):** per-arm elapsed, items/hour, output-token
  stats, and cap-hit counts in the report.
- Report is aggregate and text-free; printed via `PRED_REPORT=` and persisted to
  `plan2/predictions/report.vN.json` (attempts never overwrite).

## Cost forecast (measured G2b rates; remaining budget $17.80 of $24.7992)

- **Worst-case bound:** G2b rates assume every item decodes to the full cap. ZS 9,124/2,060 h
  + QA 9,124/1,913 h + FS at half rate for the 2.5× prefill (9,124/1,030 h) ≈ 18.1 h ≈
  **$14.50** — still inside the $15.80 available after the $2.00 reserve.
- **Realistic:** real completions average ~40 tokens (max 162), so decode is ~6–8× shorter than
  the benchmark's forced 512; dominant cost becomes FS prefill. Estimate **≈ $8–10**, in line
  with the G2b forecast's $9.16.
- Probe + model load + upload ≈ $0.30. In-job kill-guard caps runtime damage at ~$10 before
  the third arm would be skipped with prior arms safe.

## Launch steps (in order, after approval)

1. **One-time free upload** (launch prep, no GPU): copy the frozen
   `data/private/plan2/fs_demonstrations.jsonl` (sha256 `879baed7…`, pinned in the prompt
   manifest) to the private evidence Dataset at `plan2/fs_demonstrations.jsonl` — same pattern
   as `rams_roles.jsonl`. The job hash-verifies it on download.
2. Submit:
   `hf jobs uv run --flavor l4x1 --timeout 20h --detach -s HF_TOKEN jobs/plan2_prediction_generation.py`
   (Windows: prefix `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`; poll detached, never stream.)
3. On completion: verify `PRED_REPORT`, pull the three prediction files locally, run the real
   parser (`parsing.parse_generated_frame`) to build `PredictionRecord`s, freeze label-free
   prediction manifests (hashes/counts only) in git, and record actual cost.

## After this run (all $0)

Prediction manifests → independent Plan 2 reviewer PASS → Plan 3 Phases B–E (calibration,
certification, H1/H2 decisions) on CPU.
