# ConformalExtract — frontier-practice check (pre-paid-run)

**Purpose:** before authorizing any paid Plan 2 execution, ground the approach in how frontier
teams actually do QLoRA training, finite-sample selective conformal certification, batched
inference costing, document-level event-argument extraction, and evidence-first release —
rather than relying on our own assumptions. Follows Ross's project-doctrine research pipeline
(organise → group → synthesise → incorporate).

**Session:** 2026-07-18. Access date for all sources below unless noted: **2026-07-18**.
**Method:** four parallel research subagents over primary sources (arXiv PDFs, official HF/vLLM
docs, first-party repos/cards). Aggregators are leads to primary sources, not citable evidence.

---

## 0. Research clusters (decisions they inform)

| Cluster | Decision it informs | Status |
|---|---|---|
| A. Certification method frontier | primary vs conservative certifier; theorem-to-code obligations; validation suite | pending agent |
| B. Budget QLoRA reproducible training | frozen training hyperparameters; pre-flight checks before paid R0/R1/R2 | pending agent |
| C. Batched inference cost frontier | vLLM vs padded batching; R0 benchmark design; does ~$25 fit | pending agent |
| D. Extraction SOTA + eval + release | baselines/metric/leakage currency; shift definition; Plan 4 release practice | pending agent |

---

## 1. Organise — raw findings by cluster

<!-- Each finding: claim — primary source URL — access date — decision impact. Filled from agents. -->

### A. Certification method frontier
Verdict: **primary/secondary method choice is correct — but TWO theorem-to-code items must be verified against our `certification.py` BEFORE any paid run, and one free pre-run feasibility diagnostic could change `alpha` (or the whole answerability).**

Method choice — NO CHANGE: 2606.08517 (joint finite-sample certificate) stays PRIMARY; the newer 2512.12844 (Selective CRC, Xu/Guo/Wei) does **not** supersede it — it's a narrower set-valued, single-selection framework that never addresses multi-system policy selection or a joint acceptance/utility certificate. The conservative Hoeffding+Bonferroni audit **is** the 2604.01502 non-monotone construction (`α' = α − D(m,n)`), correct as the looser-but-valid second method. Sample-size precondition `n ≥ ceil(32·ln(32K/δ)/floor)` **exactly matches** the paper's Assumption 5 — confirmed faithful.

**Theorem-to-code items to verify in `certification.py::scorc_certificate` before spending:**
1. **δ-ledger completeness (HIGHEST RISK).** Paper Theorem 1 requires **four** per-pair tails each `δ/16`: (i) empirical-Bernstein on the risk ratio, (ii) Clopper–Pearson acceptance, (iii) Chernoff **lower**-tail and (iv) Chernoff **upper**-tail on the accepted count (on the eligible set `ℋ={p_acc≥π_min}`), summing to `3δ/4 ≤ δ`. Our code appears to budget only EB + Clopper–Pearson (+ Maurer–Pontil utility) and **may omit the two Chernoff acceptance-count bounds** — if so, the certificate is not the paper's certificate and may be invalid. Verify the ledger against the paper's Lemma before any paid run.
2. **Selector reconciliation.** Paper selects `argmax U_LCB` (utility lower bound); our `scorc_certificate` also selects by `utility_lower` — but the **plan §7.3/§8.1 says select by max acceptance-LCB and defines `CA_s` = max acceptance-LCB.** Internal plan↔code↔paper mismatch on the selection objective. Selection by a data-dependent `Ĝ` is valid (guarantee holds uniformly over `Ĝ`, Lemma 3), but the reported headline object and the selector must be made consistent, and the theorem-to-code note must justify whichever we pick via the uniform-over-`Ĝ` argument. Reconcile before results.

**Validation-suite addition:** add the negative control the frontier papers use (naive max-raw-acceptance threshold selection violates `α`, certified selector does not) + Monte Carlo over both a VALID regime (`μ<α`) and a deliberately-INVALID regime (`μ>α`, impossibility bound forces abstention), reporting test-violation counts vs the `δ` budget.

**Free pre-paid-run diagnostic (do this FIRST):** the LLM-certification paper 2606.29054 gives a closed-form feasibility bound: if base risk `μ>α`, *any* valid method must abstain on `≥(μ−α)/(1−α)`. At the plan's default `α=0.20`, a task whose base risk sits near 0.5 forces certified acceptance **near-zero regardless of whether QLoRA beats ZS/FS**. Compute the base-risk band on development data (plan §6.1 already specifies this) and pick `α` from it *before* committing GPU spend.

> **Correction (2026-07-22).** This paragraph originally described 2606.29054 as "our exact task
> setting" and attributed base risks of "~0.48–0.55" to **document-level extraction**. Both are
> wrong, and the error mattered — it made our own μ look like a reproduction of theirs. Verified
> against Table 3 of `arxiv.org/html/2606.29054v1` (accessed 2026-07-22, HTML rendering, not the
> PDF): the paper evaluates four tasks over eight datasets — NER (CoNLL 0.356, Few-NERD 0.540,
> WNUT 0.480), QA (TriviaQA 0.441, NQ Open 0.804), classification (MMLU-STEM 0.516,
> MMLU-Humanities 0.333) and structured extraction (**JSON-Extract 0.033**). The 0.48–0.55 band is
> two NER datasets and one MMLU subset. **It evaluates no event-argument extraction, no RAMS and
> no WikiEvents.** Its only extraction task sits at μ = 0.033, a far easier regime than the
> μ ≈ 0.60 we measure on grounded span-exact EAE. That is a *different* task under a *different*
> metric, so it marks out a new regime rather than contradicting their measurement — an earlier
> version of this correction overstated it as a contradiction. **μ ≈ 0.60 is ConformalExtract's
> own measurement** (`evidence/plan3/loss_decomposition.json`,
> `evidence/plan3/certification_result.json`), not a figure inherited from this paper.
>
> The same paragraph reported "60–71% exchangeability violations under shift". The paper reports
> static CRC violating **71% (10/14)** of configurations, with **ACI reducing this to 21% (3/14)**.
> The range itself was defensible across their shift regimes; the material omission was ACI, which
> made shift look more hopeless than they report. The shift arm is descoped anyway
> (`docs/adr/0010-descope-final-and-shift.md`), but the citation should be accurate.
>
> The paper also reports certification becoming practical only at **α = 0.30–0.40** (at α = 0.40:
> 47% of NER, 40% of QA, 60% of CLS configurations certify). Those are *achieved certifications*;
> our α ≈ 0.406 floor crossing (`evidence/plan3/alpha_frontier.json`) is an *oracle necessary
> condition* and a weaker object. The two are not directly comparable and must not be juxtaposed
> to imply an α at which this task would certify.

### B. Budget QLoRA reproducible training
Verdict: **frozen hyperparameters are well-aligned with first-party guidance — no training-config change; add pre-flight checks + an env lockfile.**

Aligned (no change): NF4 + double-quant + bf16 compute; LoRA r16/α32 (2× ratio); `target_modules="all-linear"` (PEFT auto-excludes `lm_head` for a PreTrainedModel); lr 2e-4 with R1 range {2e-4,1e-4,5e-5} (QLoRA paper + TRL adapter tip); dropout 0.05; completion-only masking (now native in TRL via `completion_only_loss`, default→True for prompt-completion data — replaces the old `DataCollatorForCompletionOnlyLM`); `packing=False` for prompt-completion extraction; greedy decoding for deterministic JSON.

Pre-flight checks to add before paid R0/R1/R2 (config assertions, not contract changes):
1. **Assert `SFTConfig.max_length` == chosen ladder rung (2048/4096)** — TRL default is **1024** and silently truncates document-level inputs. Highest-value catch.
2. Assert `learning_rate` explicitly set to 2e-4 (SFTConfig default is 2e-5).
3. Set `use_cache=False` + `gradient_checkpointing_kwargs={"use_reentrant": False}` (reentrant + PEFT can yield silent `None` grads); confirm step-1 loss finite/non-None.
4. After `get_peft_model`, assert `print_trainable_parameters()` % is in the expected band (confirms all-linear resolved, lm_head excluded).
5. Verify `tokenizer.pad_token_id` set; pin tokenizer revision == base-model revision.

Reproducibility gaps to close:
- **Environment lockfile** pinning bitsandbytes/transformers/peft/trl/accelerate/torch/CUDA — main uncovered lever for 4-bit; NF4 numerics can drift across bitsandbytes versions.
- Explicit tokenizer-revision pin alongside the base-model pin.

Risk flags (honest): (a) Qwen3-4B-Instruct-2507 card recommends **sampling** (T=0.7, top_p=0.8), not greedy — greedy is still the correct, defensible choice for reproducible structured extraction, but low-temp sampling is the card-sanctioned lever if R1 quality looks degraded/repetitive (eval-config, not training). (b) NF4 same-version reload bit-exactness is **unverified** by any primary source — adapter-hash replay guards the trained delta, not the recomputed quantized base; cross-version drift is the mitigable risk (→ lockfile).

### C. Batched inference cost frontier
Verdict: **budget fits comfortably (~$6–15 for all 3 systems); switch the generation engine to vLLM and re-target the R0 benchmark — the forecast *structure* is sound, its measured input should change.**

HF Jobs GPU $/hr (first-party, per-minute billing, credit balance required): T4-small $0.40, T4-medium $0.60, **L4 $0.80**, A10G-small $1.00, A10G-large $1.50, L40S $1.80, A100 $2.50, H200 $5.00. Programmatic: `hf jobs hardware`.
- **Cheapest adequate flavor = 1× L4 ($0.80/hr)**, not T4: a 4B@4-bit fits 24 GB with batch room, and L4 (Ada, compute 8.9) has the FP8/Marlin/AWQ kernels + bf16 that T4 (Turing) lacks — T4 4-bit vLLM is kernel-limited/slow. A10G-small is the fallback.
- **vLLM continuous batching >> padded transformers `.generate()`** for our high-variance prompt distribution (2–4k input, ≤512 output): static padding wastes compute on padding + stragglers; continuous/ragged batching eliminates it (~10–20× aggregate throughput swing in the compute-bound regime). Padded `.generate()` is the pessimistic engine.
- Throughput anchor: Mistral-7B on L4 hit >900 tok/s aggregate at batch 16 under vLLM; a 4-bit 4B is smaller → conservative planning band ~1,000–2,000 tok/s (confirm in R0).
- **Cost sanity (stated assumptions: 27,372 generations, avg input ~1,500 tok, output ≤512):** ~45–55M total tokens → on L4 at 1,000/1,500/2,000 tok/s ≈ **$12 / $8 / $6**. R0 is very unlikely to return "infeasible" on L4+vLLM. Infeasible only if oversized flavor (A100/H200), unbatched, or padded batching on a bandwidth-bound config.
- R0 benchmark tool: `vllm bench throughput` at the **real RAMS prompt-length distribution** (not a fixed length), sweep `max-num-seqs`/batch, record KV-cache/OOM ceiling at `--gpu-memory-utilization`, report total + output tok/s. Forecast formulas: `items_per_hour = agg_tok_s*3600/(avg_in+avg_out)`; `job_cost = total_items/items_per_hour * $per_hr`.

**Key risk to validate in R0:** vLLM's fast kernels favour AWQ/GPTQ/FP8; a **bitsandbytes-QLoRA adapter may run a slower vLLM path or need merge/convert** to AWQ/GPTQ. This is the one thing that could erode the vLLM advantage — validate the 4-bit-adapter-under-vLLM path in R0 (or generate with transformers but length-sort+bucket to cut padding, treating that as a conservative floor). Contradiction logged: one V100 study found vLLM≈HF (bandwidth-bound corner case) — magnitude of the L4 win must be measured, not assumed. Also: log **actual** generated-token counts in R0 to replace the 512 upper-bound (JSON frames likely avg ~150–250 → roughly halves cost).

### D. Extraction SOTA + evaluation + release
Verdict: **baselines/leakage current — two evaluation refinements (per-dataset native metric; held-out-schema as primary shift) and confirmation that raw-text non-redistribution is required, not just cautious.**

SOTA anchors (Arg-C F1): supervised ceiling ~RAMS 54–57 (PAIE/GAM/TSAR) / WikiEvents ~70 Head, ~72 Coref (GAM). LLM **zero-shot far below**: GPT-4o ZS 35.7 RAMS / 23.4 WikiEvents; Llama3-Instruct 0.00 (format collapse). → **A zero-shot loss ~0.65 RAMS / ~0.77 WikiEvents is EXPECTED, not a bug** — validates the ZS≪FS≪QLoRA thesis and the "parse failure → loss 1" rule. Publish these as anchor numbers.

**Refinement A — metric definition (real trap):** RAMS uses **span exact-match** (official v1.0c 2023 corrected scorer); WikiEvents uses **head-word + coref** F1. These are different scales — do **not** report one blended "grounded F1" across both datasets (exactly the inconsistency TextEE, arXiv 2311.09562, warns about). Report per-dataset in its native metric and pin which grounding normaliser applies where.

**Refinement B — shift definition:** RAMS(AIDA, 139 types/65 roles) ↔ WikiEvents(KAIROS, 50/59) crosswalk (via XPO) is **lossy and many-to-many**, so cross-dataset shift confounds distribution shift with crosswalk error. **Primary shift should be held-out-schema within one dataset** (isolates schema generalization, no crosswalk noise); keep cross-dataset RAMS→WikiEvents as a secondary/robustness probe with the XPO mapping documented as a limitation. (Plan §3.4/§10 currently defaults to cross-dataset "if interpretable" — the evidence says prefer held-out-schema.)

Leakage/eval design: grounded-F1 + source-document grouping + sealed splits is **consistent with and ahead of** TextEE-era norms.

Release practice (Part 2): adapter-without-base-weights is the normal supported HF pattern — card needs `library_name: peft` + `base_model:` (+ `base_model_relation: adapter`) + `adapter_config.json` (base pointer only). **Raw-text non-redistribution CONFIRMED NECESSARY:** RAMS's own terms state the creators don't own the source news text and release only annotations (CC-BY-SA-4.0); WikiEvents raw article text is third-party/restricted-by-default. So Plan 4's "publish derived evidence (IDs/offsets/predictions/metrics/checksums), never source sentences" is **required, not merely cautious** — cite the RAMS disclaimer in the dataset card. The claim-ledger + immutable-manifest + CPU-replay + negative-result design is ahead of typical academic releases.

---

## 2. Group — findings clustered by the decision they inform

**Decision 1 — Is the paid run affordable/feasible?** → YES. (C) ~$6–15 for all 3 systems on 1× L4 ($0.80/hr) with vLLM; R0 unlikely infeasible. (B) training config sound; no hyperparameter change. The forecast structure is right; its measured input should come from a vLLM benchmark on L4.

**Decision 2 — Will a paid run actually yield a VALID, non-vacuous certificate?** → NOT YET ESTABLISHED — the real gate. (A) method choice correct, but (i) the SCoRC δ-ledger may be incomplete (missing the two Chernoff accepted-count tails) and the selector↔plan objective mismatch must be reconciled — both are theorem-to-code items to resolve before any "certified" claim; (ii) a FREE base-risk feasibility check may show the certificate is near-vacuous at α=0.20 if base risk lands near 0.5 — the level 2606.29054 measures on its *hardest* tasks (Few-NERD 0.540, MMLU-STEM 0.516, WNUT 0.480; **not** on extraction, where its JSON-Extract task sits at 0.033). See the correction under cluster A: that paper measures no event-argument extraction, and our μ ≈ 0.60 is our own measurement. (D) metric must be per-dataset native (RAMS span-exact vs WikiEvents head+coref), not blended.

**Decision 3 — Experiment framing.** (D) primary shift should be held-out-schema within one dataset, not lossy cross-dataset; (A) shift is uncertifiable (report descriptive/negative — already in plan).

**Decision 4 — Release.** (D) adapter-without-base-weights card conventions; raw RAMS/WikiEvents text non-redistributable → publish derived evidence only (confirmed required). Evidence-first plan is ahead of field norms.

## 3. Synthesise — decision-ready summary

**The paid run is affordable and the training/certifier method choices are sound — but do NOT authorize spend yet, because two cheap/free actions come first and one of them could change the whole design.**

- **Affordability is not the constraint.** vLLM on a 1× L4 puts all-three-systems generation at ~$6–15, well inside the $24.7992 cap. Our forecast machinery is correct; it just needs a vLLM-on-L4 R0 measurement at the true prompt-length distribution, and R0 must validate that a **bitsandbytes-QLoRA adapter runs efficiently under vLLM** (the one throughput risk; fallback = merge/convert to AWQ/GPTQ, or length-bucketed transformers as a conservative floor).
- **Validity is the constraint.** Before spending, resolve/verify: (a) the **base-risk feasibility** `(μ−α)/(1−α)` on development data — if μ≈0.48–0.55 > α=0.20, certified acceptance is forced near-zero *regardless of QLoRA*, making the headline question unanswerable at that α; this is free and decisive. (b) the **certifier theorem-to-code note**: confirm the δ-ledger has all required per-pair tails (our code appears to omit the two Chernoff accepted-count bounds) and reconcile the selector (code = utility-LCB; plan = acceptance-LCB). A run that produces an invalid or vacuous certificate is wasted spend.
- **What's ruled out / confirmed:** no QLoRA hyperparameter change; the primary certifier (2606.08517) is not superseded by the newer 2512.12844; the conservative audit is the correct 2604.01502 method; ZS≪FS≪QLoRA is real (ZS loss ~0.65–0.77 expected); raw-text non-redistribution is required, not optional.
- **Unknowns:** exact δ-ledger constants (64m/8m) vs the paper's lemmas; NF4 same-version reload bit-exactness; realized vLLM throughput and avg output length on L4 (R0 resolves these).

## 4. Incorporate — changes fed into plans/implementation

Actioned in this repo now (no spend, no approval needed): findings recorded here; a **pre-paid-run gate** derived from them at [pre-paid-run-gate.md](pre-paid-run-gate.md). Recommended plan/impl changes (for Ross to fold into the accepted plans):

- **Plan 2 (before paid run):** add training pre-flight assertions — `max_length`==ladder rung (TRL default 1024 truncates!), `learning_rate`==2e-4, `use_cache=False`+`use_reentrant=False`, `print_trainable_parameters()` band, `pad_token` set; add an **environment lockfile** (bitsandbytes/transformers/peft/trl/accelerate/torch/CUDA) + tokenizer-revision pin. Switch the generation engine to **vLLM**; R0 benchmarks vLLM on L4 at the real prompt-length distribution and validates the QLoRA-under-vLLM path.
- **Plan 3 (Phase A theorem-to-code — blocks any "certified" claim):** verify the SCoRC δ-ledger completeness + exact constants against 2606.08517's lemmas; add the missing Chernoff accepted-count bounds if required; reconcile selector vs headline object (acceptance-LCB vs utility-LCB). Run the base-risk feasibility diagnostic and **choose α from the measured base-risk band before spend**. Add the negative control (naive max-acceptance selection violates α; certified does not) to the validation suite. Report per-dataset native metric (no blended F1).
- **Plan 3/4 (shift):** make **held-out-schema within one dataset the PRIMARY shift**; cross-dataset RAMS→WikiEvents becomes secondary with the XPO crosswalk documented as a limitation.
- **Plan 4 (release):** adapter card `library_name: peft` + `base_model` + `adapter_config.json` (no base weights); dataset card cites the RAMS non-redistribution disclaimer; publish only derived evidence. "Investigated, no change" — the evidence-first release architecture is already ahead of field norms.

**"Investigated, no change" items:** QLoRA quantization/LoRA/lr/masking config; primary+conservative certifier choice; document-grouping + sealed-split leakage controls; the forecast's go/stop/infeasible structure; shift-is-uncertified framing.

---

## Source log

> **Refereeing status (added 2026-07-22).** The three papers this project's method rests on —
> **2606.08517** (the primary certificate), **2606.29054** (the impossibility bound and base-risk
> feasibility test) and **2604.01502** (the conservative non-monotone audit) — are all
> **unrefereed June-2026 arXiv preprints**. Their theorems are used here as stated and were
> checked line-by-line against our implementation (`docs/plan3/theorem-to-code-*.md`), but they
> carry no peer-review warrant. Any write-up must say so.

<!-- URL | what it establishes | access date | primary? -->
| Source | Establishes | Accessed | Primary |
|---|---|---|---|
| https://arxiv.org/abs/2606.08517 | Joint finite-sample certificate for adaptive selective CRC (plan's preferred method) | 2026-07-18 | yes |
| https://arxiv.org/abs/2512.12844 | Selective Conformal Risk Control (Dec 2025) — newer; assess vs 2606.08517 | 2026-07-18 | yes |
| https://arxiv.org/pdf/2305.14314 | QLoRA (Dettmers et al.): NF4, double-quant, bf16 compute, constant LR, lr 1e-4/2e-4 ≤13B | 2026-07-18 | yes |
| https://huggingface.co/docs/trl/en/sft_trainer | TRL SFTTrainer: native completion_only_loss; SFTConfig default max_length=1024, lr=2e-5, packing=False | 2026-07-18 | yes |
| https://huggingface.co/docs/peft/en/developer_guides/lora | PEFT LoraConfig: all-linear excludes output layer; alpha≈2×rank; use_rslora | 2026-07-18 | yes |
| https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | Qwen3-4B model card: recommended sampling T=0.7/top_p=0.8 (not greedy); 262k native context | 2026-07-18 | yes |
| https://huggingface.co/docs/transformers/en/quantization/bitsandbytes | bitsandbytes 4-bit BitsAndBytesConfig (NF4 / double-quant / compute dtype) | 2026-07-18 | yes |
| https://arxiv.org/abs/2208.02814 | Conformal Risk Control — monotone bounded-loss E[L]≤α, tight O(1/n) | 2026-07-18 | yes |
| https://arxiv.org/html/2606.08517v1 | Joint finite-sample certificate (PRIMARY): EB ratio + CP + 2 Chernoff + utility; n≥32log(32m/δ)/π_min; argmax-U_LCB | 2026-07-18 | yes |
| https://arxiv.org/html/2604.01502v2 | Non-monotone CRC: union+Hoeffding grid, α'=α−D(m,n) — formalizes the conservative audit | 2026-07-18 | yes |
| https://arxiv.org/html/2606.29054v1 | When Can CRC Certify LLM Outputs — impossibility bound (μ−α)/(1−α); Table 3 per-dataset μ (NER 0.356/0.540/0.480, QA 0.441/0.804, MMLU 0.516/0.333, **JSON-Extract 0.033**); no EAE/RAMS/WikiEvents; α=0.30–0.40 unlocks practical certification; static CRC violates 71% of configs under shift, ACI 21% | 2026-07-18; **re-verified 2026-07-22**; **Table 5 read 2026-08-02, below** | yes |
| https://arxiv.org/abs/2411.05895 | LLM ZS≪supervised EAE: GPT-4o ZS Arg-C 35.7 RAMS / 23.4 WikiEvents | 2026-07-18 | yes |
| https://aclanthology.org/2021.naacl-main.69/ | BART-Gen + WikiEvents; Head/Coref F1 protocol | 2026-07-18 | yes |
| https://nlp.jhu.edu/rams/ | RAMS official: v1.0c span-exact scorer; creators don't own source text (annotations CC-BY-SA-4.0) | 2026-07-18 | yes |
| https://arxiv.org/abs/2311.09562 | TextEE: standardized splits/preprocessing; eval inconsistency + split-bias warnings | 2026-07-18 | yes |
| https://huggingface.co/docs/hub/en/model-cards | HF model cards: library_name/base_model/base_model_relation adapter linkage | 2026-07-18 | yes |
| https://huggingface.co/docs/hub/jobs-pricing | HF Jobs GPU $/hr (T4 $0.40, L4 $0.80, A10G-small $1.00, A100 $2.50), per-minute billing | 2026-07-18 | yes |
| https://docs.vllm.ai/en/latest/cli/bench/throughput.html | vllm bench throughput — benchmark at real length distribution, batch sweep | 2026-07-18 | yes |

---

## Addendum, 2026-08-02 — arXiv:2606.29054 Table 5, read from the primary source

Recorded because the write-up compares our measured confidence AUROC against this paper's, and
under this repository's own standard a comparison figure has to be traceable here before it can be
used. Read directly from `https://arxiv.org/html/2606.29054v1` on **2026-08-02**. Table 5 caption:
*"AUROC of confidence scores for risk discrimination. Higher values indicate better ability to
distinguish correct from incorrect outputs."*

| Score | CoNLL | Few-NERD | WNUT | TriviaQA | NQ Open | MMLU-STEM | MMLU-Hum. | **JSON** |
|---|---|---|---|---|---|---|---|---|
| Token margin | 0.539 | 0.517 | 0.521 | 0.616 | 0.583 | 0.491 | 0.531 | **0.818** |
| Self-consistency | 0.708 | 0.721 | 0.653 | 0.816 | 0.805 | 0.600 | 0.672 | **0.732** |
| NLL | 0.536 | 0.514 | 0.514 | 0.604 | 0.588 | 0.485 | 0.542 | **0.793** |

Also reported: semantic entropy **0.496–0.677** across all datasets; entity agreement 0.616–0.690
on the NER sets; field completeness 0.734 on JSON.

**A correction this addendum forced.** A summary relayed to this project gave "NLL / mean logprob
0.485–0.604" as *the* NLL AUROC band. That range is NLL over the **NER, QA and classification** sets
only — it excludes **JSON at 0.793**, which is this paper's one structured-generation task and
therefore the single most relevant comparison for our own work. A draft sentence reading "above the
0.485–0.604 band Kotte reports for NLL" was **false as written** and has been rewritten. The
self-consistency band 0.600–0.816 relayed in the same summary **is** correct across all eight
datasets.

**Not verified, and dropped rather than used.** The same summary attributed a mean AUROC of 0.790
for semantic entropy to Farquhar et al. (Nature 630). The Nature full text is behind
authentication, the earlier arXiv:2302.09664 abstract states no AUROC, and the authors' own blog
post gives none. It is not recorded here and is not used anywhere. Note that this paper measures
semantic entropy itself at 0.496–0.677, well below 0.790; the two are different setups and this
addendum does not adjudicate between them.
