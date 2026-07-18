# Pre-paid-run gate (derived from the 2026-07-18 frontier check)

Before ANY paid Plan 2 GPU execution is authorized, these items must pass. Derived from
[findings.md](findings.md). Paid execution remains a **hard approval gate** — this checklist does
not authorize spend; it defines what must be true first. Nothing here has been executed yet.

## G1 — Validity (do first; free/CPU; could change the whole design)

- [ ] **G1a Base-risk feasibility.** On development data, compute base risk `μ` per system and the
  abstention floor `(μ−α)/(1−α)`. Frontier evidence (2606.29054) puts document-level extraction
  `μ≈0.48–0.55`; at the plan default `α=0.20` the certificate is forced near-vacuous **regardless of
  QLoRA**. **Choose `α` from the measured band before spend**, or explicitly declare a near-zero
  acceptance floor. Decisive and free — run before committing GPU budget.
- [ ] **G1b Certifier theorem-to-code note** (blocks any "certified" claim). Verify against
  arXiv 2606.08517 lemmas that `scorc_certificate`'s δ-ledger has **all** required per-pair tails.
  Current code has EB risk (`log 64m/δ`) + Clopper–Pearson acceptance (`δ/16m`) + Maurer–Pontil
  utility (`log 8m/δ`) but **no explicit Chernoff lower/upper bounds on the accepted count** — confirm
  whether the paper requires them (each `δ/16`) and add if so; verify the `64m`/`8m` constants.
- [ ] **G1c Selector reconciliation.** Code selects `argmax utility_LCB` (matches the paper);
  plan §7.3/§8.1 says `argmax acceptance_LCB` and defines `CA_s` = max acceptance-LCB. Make
  code ↔ plan ↔ reported-headline consistent; justify via the uniform-over-`Ĝ` argument.
- [ ] **G1d Negative control** added to the certifier validation suite: naive max-raw-acceptance
  threshold selection violates `α`; the certified selector does not. Plus Monte Carlo over a valid
  (`μ<α`) and a deliberately-invalid (`μ>α`) regime, reporting violations vs the `δ` budget.

## G2 — Cost/engine (design the paid run correctly)

- [ ] **G2a Engine = vLLM** (continuous batching) for generation, on **1× L4 ($0.80/hr)**; A10G-small
  fallback. Not padded transformers `.generate()` (pessimistic for the 2–4k-input / ≤512-output
  skew).
- [ ] **G2b R0 validates the QLoRA-under-vLLM path** — a bitsandbytes 4-bit adapter may run a slow
  vLLM path or need merge/convert to AWQ/GPTQ. This is the main throughput risk; confirm in R0.
- [ ] **G2c R0 benchmark** measures `vllm bench throughput` at the **real RAMS prompt-length
  distribution**, sweeps `max-num-seqs`, records the KV-cache/OOM ceiling, and logs **actual**
  generated-token counts (to replace the 512 upper bound). Feed measured items/hour into the existing
  forecast (≥0.20 buffer + positive reserve unchanged). Expected total ~$6–15 → forecast should say GO.

## G3 — Training pre-flight (assert before the paid job; cheap, prevents wasted spend)

- [ ] **G3a** `SFTConfig.max_length` == chosen ladder rung (TRL default **1024** silently truncates).
- [ ] **G3b** `learning_rate` explicitly 2e-4 (SFTConfig default is 2e-5).
- [ ] **G3c** `use_cache=False` + `gradient_checkpointing_kwargs={"use_reentrant": False}`;
  step-1 loss finite/non-None.
- [ ] **G3d** After `get_peft_model`, `print_trainable_parameters()` % in expected band (all-linear
  resolved, lm_head excluded).
- [ ] **G3e** `tokenizer.pad_token_id` set; tokenizer revision pinned == base-model revision.
- [ ] **G3f** Environment lockfile pinning bitsandbytes/transformers/peft/trl/accelerate/torch/CUDA.
- [ ] **G3g** `packing=False` (default) for prompt-completion extraction.

## G4 — Experiment framing (before certification/final/shift phases)

- [ ] **G4a** Per-dataset native metric: RAMS span-exact (v1.0c scorer), WikiEvents head+coref.
  No blended "grounded F1" across datasets.
- [ ] **G4b** Primary shift = **held-out-schema within one dataset**; cross-dataset RAMS→WikiEvents
  is secondary with the XPO crosswalk documented as a limitation.

## G5 — Release (Plan 4; not now)

- [ ] Adapter card `library_name: peft` + `base_model` + `adapter_config.json` (no base weights);
  dataset card cites the RAMS raw-text non-redistribution disclaimer; publish derived evidence only.

---

**Sequence:** G1a (free, decisive) → G1b/c/d + G3 (CPU/config) → G2 R0 micro-benchmark (small paid,
needs approval) → forecast GO → R1/R2 (paid, needs approval). Any `stop`/`infeasible`/vacuous-certificate
outcome halts before the next spend.
