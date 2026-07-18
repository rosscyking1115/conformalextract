# Pre-paid-run gate (derived from the 2026-07-18 frontier check)

Before ANY paid Plan 2 GPU execution is authorized, these items must pass. Derived from
[findings.md](findings.md). Paid execution remains a **hard approval gate** — this checklist does
not authorize spend; it defines what must be true first. Nothing here has been executed yet.

## G1 — Validity (do first; free/CPU; could change the whole design)

- [~] **G1a Base-risk feasibility.** Diagnostic built + run over the evidence band (see status
  below): at `α=0.20` the RAMS band is answerable (ceiling ~0.56–0.65). **Still to do with real
  data:** feed measured per-system dev always-answer losses into `base_risk_feasibility` and confirm
  `α` before spend. Free/CPU.
- [x] **G1b Certifier theorem-to-code note** — DONE (`docs/plan3/theorem-to-code-scorc.md`).
  **Corrected finding:** after fetching Algorithm 1 in full, `scorc_certificate` implements it
  **correctly and completely** (Lines 5/6/7/9 + `argmax U_LCB`; EB `log(64m/δ)`, CP `δ/16m`, utility
  `log(8m/δ)`, sample size `32log(32m/δ)/π_min` all match). **U3/U4 are proof-only — NOT computed by
  the algorithm**, so there is no implementation gap and they must not be added. One minor reporting
  item: the code returns an extra `risk_upper = α + eb/p_LCB` not in the algorithm (valid conservative
  diagnostic, but the Theorem-1 certified bound is simply `α`) — report `α` as the certified bound and
  label the extra as a diagnostic. Not a validity blocker.
- [x] **G1c Selector reconciliation** — DIAGNOSED. Code == paper (`argmax U_LCB`), and with `v=1,c=0`
  the utility IS the acceptance rate, so the selector already maximizes an (M-P) acceptance lower
  bound — close to the plan's intent. Reconcile plan wording + decide whether the headline `CA_s` uses
  the M-P `U_LCB` or the Clopper–Pearson `p_LCB`; expose `max_{Ĝ}` if §8.1's max-acceptance headline is
  kept. Documentation + small accessor, not a validity blocker.
- [x] **G1d Empirical coverage validation** — DONE (`tests/test_scorc_coverage.py`). Over 80 resplits
  of a synthetic DGP with closed-form population selected risk, the certified selector never exceeds
  `α` (violations ≤ `ceil(δ·trials)`); the negative control confirms a naive accept-all policy
  genuinely violates `α` while the certificate refuses it; zero acceptance never yields zero risk.
  Follow-up (not blocking): extend to a deliberately-invalid (`μ>α`) abstention regime + binomial
  consistency table for the technical report.
- [ ] **G1d Negative control** added to the certifier validation suite: naive max-raw-acceptance
  threshold selection violates `α`; the certified selector does not. Plus Monte Carlo over a valid
  (`μ<α`) and a deliberately-invalid (`μ>α`) regime, reporting violations vs the `δ` budget.

### G1a status — diagnostic built and run over the evidence band (2026-07-18)

`certification.base_risk_feasibility` / `minimum_abstention` / `max_feasible_acceptance` are
implemented + tested (`tests/test_base_risk_feasibility.py`). Population certified-acceptance
ceiling `1 − (μ−α)/(1−α)` over the frontier base-risk band (floor 0.20; `X` = below floor):

```
  mu \ alpha |  a=0.10   a=0.20   a=0.30   a=0.40   a=0.50
   mu=0.45   |   0.61     0.69     0.79     0.92     1.00
   mu=0.48   |   0.58     0.65     0.74     0.87     1.00
   mu=0.50   |   0.56     0.62     0.71     0.83     1.00
   mu=0.55   |   0.50     0.56     0.64     0.75     0.90
```

**Read:** at **α=0.20** the RAMS band (μ≈0.48–0.55) caps certified acceptance at ~0.56–0.65 —
this **clears the 0.20 floor, so α=0.20 is answerable for RAMS** (correcting the earlier
"near-vacuous" caution, which bites at **α=0.10** or μ≥0.55). Two things still gate the answer:
(i) the QA−ZS material gain (default 0.05) must fit under this ceiling, and (ii) **ZS's own base
risk may push ZS infeasible** — which is a legitimate boundary-crossing result, not a failure.
**Remaining G1a step needs real dev predictions:** feed measured per-system always-answer losses
into `base_risk_feasibility` and confirm α before spend; the arithmetic above uses the frontier
band as a stand-in, not measured data.

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
