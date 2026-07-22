# ConformalExtract — Plan 1: Foundations, Research Contract & Gate 0

> **Purpose:** freeze the falsifiable Route Z study, prove that the data and confidence signal can support a valid finite-sample certificate, and stop before paid QLoRA training if they cannot.
>
> **Owner:** Ross (Cheng-Yuan King) · **Date:** 2026-07-15 · **Status:** Accepted direction; Gate 0 pending execution · **Document type:** living research plan

**Inherited & locked:** Route Z is selected. The project asks whether QLoRA changes event extraction enough to cross a non-vacuous risk-certification boundary, then measures how that certificate behaves under schema or dataset shift. Route Y is preserved as a deferred follow-on. The active backbone is `Qwen/Qwen3-4B-Instruct-2507`; the training method is one NF4 QLoRA adapter; Sheffield HPC is excluded; development is local and any remote GPU use is prepaid, auto-pay-off and capped at **$25 total planning spend**. Plans are produced and accepted one at a time.

---

## 1. Executive decision

Build **ConformalExtract** as a research-grade, reusable selective-extraction system—not as another JSON prompting demo.

The project has one central comparison:

> Under the same event-extraction contract, does QLoRA increase the proportion of documents that can be returned while a predeclared finite-sample upper confidence bound on extraction risk remains below the target?

The second question is deliberately adversarial:

> When that in-domain certificate is transferred to unseen event types, schemas or a neighbouring dataset, where and how does it fail?

The scientific contribution is therefore not “conformal prediction makes LLMs reliable.” It is a bounded claim about **adaptation as a certifiability intervention**, plus a documented limit under shift.

Plan 1 authorises no full training run. It ends with one of three recorded outcomes:

- **go:** the ownership, data, evaluator, score, statistical and compute gates pass;
- **revise:** Route Z survives, but the dataset, prediction unit, score or public-release boundary must change;
- **stop/reopen:** the research question is already answered by prior work, no valid sample design is feasible, or the claimed certificate cannot be matched to verified statistics.

---

## 2. Project classification and reviewer-facing identity

### 2.1 Classification

This is an **independent modern-ML research and portfolio project** with a reusable open-source contribution. It is not a commercial product, an agent, a RAG application or a hosted inference service.

Its primary reviewers are:

1. an applied-ML or AI-systems hiring manager looking for evidence of PEFT, GPU training, evaluation and reliability engineering;
2. an ML researcher or practitioner who may reuse the risk–coverage evaluator and calibration wrapper;
3. a Kaggle or Hugging Face user who needs a reproducible notebook, adapter card and licence-safe fixtures.

### 2.2 The sentence a reviewer should remember

> I tested whether a 4B Qwen QLoRA adapter made grounded event extraction certifiably useful—not merely more accurate—then showed exactly when its finite-sample in-domain certificate stopped transferring under schema shift.

### 2.3 Working public contribution bundle

Subject to the gates in this plan, the final release should contain:

- one Hugging Face QLoRA adapter with a complete model card;
- a versioned, licence-aware data loader and split manifest rather than copied raw data by default;
- a small Python package for confidence extraction, abstention, calibration and risk–coverage evaluation;
- gold-label evaluation with grounded-span, schema-validity and selective-risk metrics;
- licence-safe synthetic fixtures and unit tests;
- a Kaggle-compatible notebook that reproduces calibration and evaluation without retraining;
- a paper-shaped report containing hypotheses, methods, results, limitations and negative-result branches.

---

## 3. Frozen research contract

### 3.1 Primary research question

For a fixed Qwen3-4B backbone, event-extraction task, decoding policy, confidence construction and finite-sample certification procedure:

> Does task-specific QLoRA produce a higher **certified acceptance rate** than zero-shot and few-shot prompting at the same target document-level extraction risk and confidence level?

“Certified acceptance rate” means the fraction of evaluation units the system returns rather than abstains on when the predeclared one-sided upper confidence bound on retained-output risk is no greater than the target. It does not mean ordinary test accuracy or an uncorrected threshold chosen after seeing test labels.

### 3.2 Secondary research question

> How much do empirical risk, the risk upper bound and acceptance change when an in-domain threshold is transferred unchanged to held-out event types, unseen schema combinations or a neighbouring event-extraction dataset?

No distribution-free guarantee is claimed under this shift unless the selected method's assumptions explicitly support it and the implementation is independently verified.

### 3.3 Primary hypotheses

- **H1 — certifiability gain:** QLoRA has higher certified acceptance than the zero-shot baseline at the same target risk and confidence.
- **H2 — more than prompting:** QLoRA has higher certified acceptance than the few-shot baseline under the same contract.
- **H3 — shift fragility:** a threshold certified in-domain suffers a material deterioration in risk bound, empirical risk, acceptance or all three under held-out-schema/cross-dataset evaluation.

The project is successful even if H1 or H2 is not supported, provided the design passes Gate 0 and the null result is measured cleanly.

### 3.4 Predeclared comparison set

Only these systems enter the primary study:

| ID | System | Backbone | Learned task weights | Purpose |
|---|---|---|---|---|
| ZS | Zero-shot | Qwen3-4B-Instruct-2507 | No | base capability and score baseline |
| FS | Few-shot | same | No | prompting-strength baseline |
| QA | NF4 QLoRA adapter | same | Yes, adapter only | adaptation intervention |

A constrained-decoding condition may be included only as a **structural-validity ablation**. It cannot silently replace the primary decoding policy or create a fourth training configuration. No second backbone, learned verifier, judge LLM, DPO/GRPO stage, adapter merge or output-repair model enters the MVP.

### 3.5 Outcome hierarchy

The headline outcome is **certified acceptance at one frozen risk target and confidence level**. The supporting outcomes are:

- document-level bounded extraction loss;
- empirical selective risk and its upper confidence bound;
- risk–coverage curve and abstention rate;
- exact and normalized grounded-span precision, recall and F1;
- unsupported-field/hallucinated-span rate;
- JSON parse and schema-validity rates;
- macro results by event type and document difficulty;
- latency, peak memory, tokens, GPU-hours and actual cost.

No headline is selected post hoc from whichever metric looks best.

---

## 4. Task and output contract

### 4.1 Task boundary

The MVP performs **grounded event-argument extraction for a supplied target event/trigger and role schema**. Trigger detection is not added to the primary task because it would confound argument extraction, confidence and QLoRA effects.

Each input contains:

- a source document or bounded document window;
- the target trigger and event type;
- the allowed argument roles and short role descriptions;
- one fixed instruction and one fixed JSON output schema.

The target output is conceptually:

```json
{
  "event_type": "...",
  "trigger": "...",
  "arguments": [
    {"role": "...", "text": "..."}
  ]
}
```

Offsets are resolved deterministically by the evaluator rather than trusted merely because the model emits numbers. Every predicted argument text must map to the input. Ambiguous repeated spans, normalization and coreference policy must be written into the evaluator contract before any model comparison.

### 4.2 Failure semantics

The evaluator assigns the maximum loss for:

- unparseable JSON after only whitespace/code-fence normalization;
- schema-invalid roles or types;
- predicted argument text that cannot be grounded in the source under the frozen normalization rules;
- duplicate or contradictory fields that violate the contract.

No semantic repair model is allowed. Deterministic parsing must never alter the substantive prediction.

### 4.3 Prediction, abstention and statistical units

Three units must not be conflated:

- **prediction unit:** one target event frame presented to the model;
- **deployment action:** return or abstain on that frame/document contract;
- **independent statistical unit:** the source document group.

If a source document contributes multiple frames, every frame from it stays in one split and its losses are aggregated by a predeclared document rule. Event frames from the same source must not be counted as independent calibration samples.

The preferred aggregation is the mean bounded frame loss per source document, with the maximum frame loss reported as a stricter sensitivity analysis. Gate 0 must verify that the source IDs and grouping make this possible; otherwise the design is revised before training.

---

## 5. Dataset decision: RAMS-first candidate, WikiEvents shift candidate

### 5.1 Why WikiEvents is not the automatic calibration dataset

WikiEvents is directly relevant and genuinely document-level, but its number of independent documents is small relative to its event/field count. Treating correlated events or arguments as hundreds or thousands of independent calibration observations would create false precision.

Therefore WikiEvents is the **preferred external/shift stress candidate**, not the default source of the headline in-domain certificate.

### 5.2 Primary candidate: RAMS

RAMS is the default candidate for in-domain training and certification because it provides many event-centred examples across a broad KAIROS-style role ontology and is already used alongside WikiEvents by the official conditional-generation reference implementation.

It is not finally accepted until Gate 0 confirms:

- stable source-document identifiers and the number of unique source groups;
- no source leakage across train/development/calibration/final-test partitions;
- enough unique non-training groups for score development, certification and final evaluation;
- role/event mapping sufficient for the selected extraction contract;
- download, use, derivative-artifact and redistribution terms;
- a deterministic conversion from source annotations to the frozen JSON/evaluator contract.

### 5.3 Shift hierarchy

Use the first feasible stress test in this order:

1. **cross-dataset:** train and certify in-domain on RAMS, transfer the frozen system and threshold to the compatible WikiEvents ontology subset;
2. **held-out event types/schema:** partition RAMS by event types or role combinations, with no held-out schema examples used for training or calibration;
3. **document-topic shift:** only if reliable topic/source metadata permits a predeclared group split.

Cross-dataset evaluation is preferred because it tests more than random split variation, but it is not forced if annotation or ontology differences make the comparison uninterpretable. In that case the within-dataset held-out-schema test becomes primary and the cross-dataset result is explicitly descriptive.

### 5.4 Required inventory artifact

Gate 0 produces `data_inventory.json` and a human-readable report containing, for every candidate split:

- raw rows, target event frames and unique source documents;
- event-type and role frequencies;
- frames per document distribution;
- document/token length distribution under the Qwen tokenizer;
- overlap by exact ID, normalized text hash and near-duplicate hash;
- ontology overlap between RAMS and WikiEvents;
- proposed group assignments and seed;
- licence/source URL, retrieval date, file hashes and redistribution decision.

### 5.5 Sample-feasibility rule

The final minimum number of independent groups is determined by a checked-in simulation/table for the chosen risk bound, target, confidence and acceptance floor—not by a generic train/test percentage.

As an initial screening rule, the preferred design has at least:

- 200 unique groups for score/prompt development;
- 300 untouched groups for calibration/certification;
- 300 untouched groups for final in-domain evaluation;
- a separate shift set large enough to report uncertainty rather than a single aggregate percentage.

If grouping drops below these provisional floors, Gate 0 must recompute what can be certified. It may revise the dataset or weaken the research claim; it may not count fields/events as independent to recover sample size.

---

## 6. Statistical reliability contract

### 6.1 Primary bounded loss

The default candidate is:

> `L_doc = 1 - grounded_argument_F1_doc`, bounded to `[0, 1]`, with parse, schema or grounding failure assigned `1`.

This retains partial extraction quality while penalising ungrounded structure. Plan 1 execution must validate its behavior on hand-built cases and decide how empty-gold/empty-prediction documents are handled.

A secondary binary **strict document failure** loss is also reported. Its exact definition is frozen before calibration—for example, any parse/grounding failure or grounded F1 below a predeclared task threshold.

### 6.2 Confidence/nonconformity signal

The score must be available from the model itself, deterministic under the frozen inference stack and computable for all three comparison systems.

Candidate white-box signals are limited to:

- length-normalized completion negative log-likelihood;
- worst predicted field/argument negative log-likelihood;
- a low-quantile or minimum token transition score over predicted argument values;
- the same score plus a deterministic infinite penalty for parse/schema/grounding failure.

Hugging Face generation transition scores are collected using a pinned `transformers` version with `return_dict_in_generate=True`, `output_scores=True` and a tested `compute_transition_scores` path. Gate 0 chooses **one primary score using development data only** and freezes it before certification labels are used.

The choice rule is not “whichever looks best on the test set.” It must consider score–loss association, risk–coverage ordering, empty-output behavior, sequence-length sensitivity and reproducibility.

### 6.3 Certification method

The project may use the word **conformal** publicly only if the chosen theorem's assumptions, selection rule and implementation correspond exactly.

Plan 1 execution must produce a short theorem-to-code note that specifies:

- calibration exchangeability unit;
- bounded loss;
- threshold grid or selection rule;
- treatment of adaptive threshold selection;
- risk target `alpha`;
- confidence failure probability `delta`;
- minimum useful acceptance/participation floor;
- one-sided finite-sample upper confidence construction;
- which guarantee is in expectation, conditional, marginal or simultaneous.

The preferred design is a finite-grid selective risk certificate that accounts for adaptive threshold choice. A deliberately conservative independent selection/certification split is retained as the audit fallback. A naïve empirical-error threshold, ordinary calibration plot or bootstrap interval does not qualify as the headline certificate.

If the recent selective-conformal method cannot be reproduced on simulation or its assumptions do not fit clustered event extraction, the project must either:

1. use a verified conservative finite-sample selective-risk method and rename claims precisely; or
2. stop calling the wrapper conformal.

### 6.4 Target-risk decision rule

`alpha`, `delta` and the minimum acceptance floor are frozen after the dataset inventory and baseline pilot but before QLoRA training.

The starting candidates are:

- `delta = 0.05` for a one-sided 95% certificate;
- `alpha = 0.20` for mean bounded document loss;
- minimum accepted fraction of `0.20` in-domain.

These are planning defaults, not yet results. They may change only through the Gate 0 sample-feasibility table and a dated rationale based on task meaning—not to manufacture a passing result.

### 6.5 Separation of data roles

- **training:** QLoRA gradient updates only;
- **development:** prompt, few-shot examples, decoding, score construction and limited hyperparameter choice;
- **calibration/certification:** threshold/risk procedure only, never gradient updates or score invention;
- **final in-domain test:** opened once after all systems and thresholds are frozen;
- **shift test:** opened after the in-domain decision is fixed; never used to repair the in-domain certificate.

Every script must reject overlapping source-document hashes across these roles.

---

## 7. Novelty boundary and literature kill test

### 7.1 What is already known

The project does not claim invention of:

- event-argument extraction with conditional generation;
- RAMS or WikiEvents evaluation;
- QLoRA/PEFT structured-output fine-tuning;
- conformal risk control or selective abstention;
- generic confidence thresholding, JSON-constrained decoding or output repair;
- the observation that conformal behavior can degrade under distribution shift.

Recent 2026 work already studies risk-controlled extraction, selective conformal certificates and certification of structured LLM generation. Therefore “we calibrated an extractor” is not a novelty claim.

### 7.2 Surviving contribution claim

The project contributes a controlled empirical study of **whether parameter-efficient adaptation changes certificate feasibility**, on the same backbone and task contract, with source-document grouping and a predeclared shift stress test. The reusable engineering contribution is a transparent, gold-label calibration/evaluation wrapper and artifact manifest.

### 7.3 Kill/reframe condition

Before executing Plan 2 experiments, rerun the literature search and record a comparison matrix. Reframe or stop if a prior study already combines all of the following in substantially the same setting:

- zero/few-shot versus LoRA/QLoRA on the same open LLM backbone;
- grounded structured event extraction;
- finite-sample selective-risk certification rather than ordinary calibration;
- adaptation framed as the intervention;
- held-out-schema or cross-dataset certificate transfer;
- an equivalent reusable public wrapper and release bundle.

Similarity on two or three elements does not kill the work; it changes attribution and the exact claimed gap.

---

## 8. Model, decoding and compute contract

### 8.1 Backbone

Lock `Qwen/Qwen3-4B-Instruct-2507` because it is Apache-2.0, small enough for one bounded GPU and already selected after the route comparison. Pin the exact Hub revision before collecting baseline outputs.

No backbone substitution is allowed merely because a newer model appears. A substitution requires a dated addendum showing that the selected model is unavailable, technically incompatible or clearly superseded before experiments begin.

### 8.2 Inference defaults

- non-thinking chat template as documented by the model card;
- deterministic greedy generation for primary evaluation;
- fixed maximum input and output token limits derived from the inventory;
- batch size recorded, not optimised separately by system for headline latency;
- exact tokenizer, model revision, `transformers`, CUDA and quantization versions in every manifest;
- no external judge model.

### 8.3 Training envelope inherited by Plan 2

- one NF4 4-bit QLoRA path;
- one adapter configuration, with at most one predeclared low-cost correction after a failed smoke run;
- completion-only supervised loss where the formatted dataset supports it;
- no full-model fine-tuning;
- no more than four total paid training configurations including failed configurations;
- local tests and tiny CPU/GPU fixtures before rental;
- initial prepaid wallet stage of $10 and at most $15 additional after a recorded estimate;
- auto-pay off, storage lifecycle documented, actual cost captured.

### 8.4 Compute claim

The final claim is “single rented GPU QLoRA training under a recorded capped budget,” not HPC training or large-scale distributed training. Sheffield resources, dissertation queues and University accounts remain outside this project.

---

## 9. Gate 0 execution

Gate 0 is a sequence. Later checks do not excuse an earlier failure.

### Gate 0A — ownership, licence and provenance

**Actions**

- inventory every intended dataset, evaluator, prompt, schema and prior team artifact;
- independently reimplement anything whose ownership is unclear;
- record dataset and code licences separately—the repository's MIT licence does not automatically grant raw-data redistribution;
- record model licence and planned adapter lineage;
- decide for each artifact: redistribute, generate on demand, publish hashes/manifest only, or exclude.

**Pass**

- the study can be reproduced without copying unapproved team assets;
- data can be lawfully used for the experiment;
- the public release has a defensible licence boundary.

### Gate 0B — data, grouping and split feasibility

**Actions**

- download from first-party sources;
- create the required inventory and ontology-overlap reports;
- group by stable source ID, exact normalized hash and near-duplicate checks;
- compute unique-group counts and the certification sample-feasibility table;
- construct candidate in-domain and shift manifests without opening final labels for model tuning.

**Pass**

- a non-leaking group design has enough independent units for a meaningful bound and final estimate;
- the task conversion is deterministic and reviewable;
- the shift question is interpretable.

**Fail response**

- revise the primary dataset or stress-test hierarchy; do not subdivide correlated examples to inflate `n`.

### Gate 0C — evaluator validity

**Actions**

- implement a small standalone evaluator before training;
- create hand-built fixtures for exact match, aliases, repeated spans, coreference policy, missing roles, surplus roles, malformed JSON, schema violations and hallucinated text;
- cross-check a sample against an official scorer where compatible;
- have one manual adjudication sheet for at least 25 varied examples.

**Pass**

- fixture expectations are explicit and all tests pass;
- disagreements with official metrics are explained rather than hidden;
- the primary bounded loss cannot leave `[0,1]` and assigns failures consistently.

### Gate 0D — statistical implementation validity

**Actions**

- reproduce a toy or published synthetic experiment for the chosen certification method;
- run Monte Carlo coverage checks under exchangeable simulated data across easy, boundary and low-acceptance regimes;
- test adaptive-threshold handling and random accepted sample counts;
- compare against a deliberately conservative audit bound;
- write the theorem-to-code note.

**Pass**

- empirical violation frequency is consistent with the declared `delta` within simulation uncertainty;
- edge cases return “no certificate” rather than a fabricated threshold;
- the code and public wording describe the same guarantee.

### Gate 0E — model and score smoke test

**Actions**

- pin and load the selected Qwen revision in 4-bit inference on the available local environment where feasible;
- generate 20–50 development examples under the frozen output contract;
- capture transition scores and verify token alignment after the chat prompt;
- test all candidate score constructions, including empty and malformed outputs;
- record latency, peak memory and failure modes;
- select one primary score using development data only.

**Pass**

- the model produces evaluable outputs;
- the score is finite or deliberately penalised for every case, deterministic across repeated runs and meaningfully ordered enough to justify a risk–coverage experiment;
- score extraction does not require a second model or inaccessible API logprobs.

**Fail response**

- repair the score/inference implementation once; if no usable score exists, revise the research question before paid training.

### Gate 0F — paid QLoRA feasibility smoke

This gate begins only after 0A–0E pass.

**Actions**

- create a prepaid remote instance with auto-pay disabled;
- run a tiny 20–50 step QLoRA job on a deterministic training subset;
- save, reload and use the adapter for generation;
- estimate full-run wall time, storage and total cost from measured throughput;
- destroy or stop billable resources and verify the remaining balance.

**Pass**

- save/reload works;
- no OOM or unrecoverable stack incompatibility occurs;
- projected end-to-end spend remains within the $25 wallet after evaluation/storage allowance;
- the exact environment can be reconstructed.

**Fail response**

- one documented reduction in sequence length, batch/microbatch or adapter settings is allowed;
- no automatic top-up;
- if the capped plan still fails, revise scale or stop before a full run.

### 9.1 Gate decision record

Gate 0 ends with `docs/gate0/decision.md` containing:

- result and evidence link for 0A–0F;
- final dataset/split/shift decision;
- final prediction and calibration unit;
- final loss, score, `alpha`, `delta`, acceptance floor and certification method;
- final backbone revision and environment;
- measured cost projection;
- literature-kill result;
- explicit **go**, **revise** or **stop/reopen** decision.

Plan 2 may be drafted after this plan is accepted, but its full-data preparation, paid training and experiment execution cannot begin without a Gate 0 go decision.

---

## 10. Six-track Plan 1 responsibilities

| Track | Plan 1 decision/evidence | Exit artifact |
|---|---|---|
| Research / novelty | hypotheses, prior-work matrix, claim and kill condition | `docs/research/novelty_matrix.md` |
| Data / grounding | task contract, provenance, grouping, split and ontology audit | `data_inventory.json`, split manifests, evaluator fixtures |
| Model / adaptation | backbone revision, prompt/decoding contract, score smoke | baseline/score smoke report |
| Statistical reliability | unit, loss, target, certificate, simulation validation | theorem-to-code note and simulation report |
| Systems / reproducibility | environment pins, manifests, capped-compute smoke | environment lock and Gate 0 run manifest |
| Public contribution / release | licence boundary and artifact release decision | release matrix and attribution file |

These tracks continue through all four plans. They do not become six separate workstreams or six repositories.

---

## 11. Planned repository shape after Gate 0

```text
conformal-extract/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── configs/
│   ├── task.yaml
│   ├── inference.yaml
│   └── certification.yaml
├── src/conformalextract/
│   ├── data/
│   ├── prompting/
│   ├── scoring/
│   ├── calibration/
│   └── evaluation/
├── scripts/
│   ├── inventory_data.py
│   ├── run_baseline.py
│   ├── validate_certificate.py
│   └── gate0_smoke.py
├── tests/
│   ├── fixtures/
│   ├── test_grounding.py
│   ├── test_metrics.py
│   ├── test_splits.py
│   └── test_certification.py
├── manifests/
├── docs/
│   ├── gate0/
│   └── research/
└── notebooks/
```

This is a target shape, not permission to scaffold the repository before this plan is accepted.

---

## 12. Risks and pre-agreed responses

| Risk | Early signal | Pre-agreed response |
|---|---|---|
| Too few independent documents | grouping collapses nominal sample count | change primary dataset or claim; never count fields as independent |
| Ontology mismatch makes cross-dataset shift meaningless | few roles/types map cleanly | use held-out-schema shift as primary; report cross-dataset descriptively |
| Model confidence does not rank errors | flat/inverted dev risk–coverage curve | test only the bounded candidate score set; revise question if all fail |
| Certificate is vacuous | no threshold meets risk and acceptance floors | preserve as a baseline result; QLoRA must earn the boundary rather than change it |
| QLoRA improves F1 but not certified acceptance | similar/worse risk–coverage frontier | report the distinction; do not substitute average F1 as the headline |
| Both baseline and adapter certify equally | no meaningful delta | publish a null intervention result and useful wrapper if rigor gates pass |
| In-domain certificate fails under shift | transferred risk exceeds target | this supports H3; state that the guarantee did not transfer |
| Recent paper duplicates the full thesis | novelty matrix finds equivalent study | reframe contribution or stop/reopen before paid training |
| Dataset terms block redistribution | no clear raw-data grant | publish loaders, hashes and derived aggregate evidence only |
| Local 8 GB environment cannot train | smoke OOM/unsupported kernels | keep local for tests/inference; use one prepaid remote GPU as planned |
| Remote estimate exceeds $25 | measured smoke projection | reduce bounded configuration once or stop; no automatic budget expansion |
| Test leakage through repeated experimentation | final labels accessed early | regenerate a clean group split if allowed and record the breach; otherwise invalidate headline |

---

## 13. Explicit non-goals

- No general-purpose information-extraction platform.
- No UI, chatbot, RAG layer, agent workflow or hosted API in the MVP.
- No trigger-detection benchmark in the primary experiment.
- No leaderboard sweep across datasets and backbones.
- No judge-model grading when gold spans and schemas exist.
- No claim of validity under distribution shift without a matching theorem and evidence.
- No use of calibration/test labels for prompt, score, adapter or threshold invention outside the declared procedure.
- No raw-data upload to Hugging Face or Kaggle until redistribution rights are verified.
- No University/HPC compute, Slurm claim or dissertation resource mixing.
- No Route Y implementation inside Route Z; Y remains a separately preserved future study.

---

## 14. Four-plan sequence

### Plan 1 — Foundations, Research Contract & Gate 0 (this document)

Freeze and validate what is being claimed before full training.

### Plan 2 — Data, QLoRA & Reproducible Training

Implement the validated data path and same-backbone zero-shot, few-shot and QLoRA systems within the capped experiment budget.

### Plan 3 — Conformal Certification & Schema-Shift Experiments

Run the frozen certification comparison, shift stress tests, ablations, uncertainty analysis and negative-result branches.

### Plan 4 — Verification, Hugging Face/Kaggle Release & Research/Portfolio Consolidation

Reproduce the evidence cleanly and publish the reusable, licence-compliant contribution with honest research and portfolio claims.

---

## 15. Open decisions resolved by Gate 0—not blockers to accepting this plan

1. Exact RAMS unique-document counts after grouping.
2. Whether cross-dataset ontology alignment is sufficient for the primary shift test.
3. Exact score chosen from the bounded candidate set.
4. Exact finite-sample selective-risk method after theorem-to-code and simulation validation.
5. Final `alpha`, `delta` and acceptance floor after the sample-feasibility table.
6. Exact QLoRA rank/alpha/target modules and remote GPU SKU, which Plan 2 may specify conditionally and Gate 0 must validate before execution.
7. Final public repository slug and package name.

These are empirical decisions with written selection rules. They are not permission to tune against the final test set.

---

## 16. Acceptance checklist — Plan 1 is done when

### Direction acceptance now

- [x] The project is accepted as a research/portfolio contribution, not a product.
- [x] The adaptation-as-certifiability question and shift question are accepted.
- [x] The zero-shot / few-shot / one-QLoRA comparison is accepted.
- [x] RAMS-first inventory and WikiEvents-first shift hierarchy are accepted as candidates, not unverified facts.
- [x] Source-document grouping is accepted as mandatory.
- [x] The bounded loss, score-selection and certificate-validation process is accepted.
- [x] The $25 prepaid, auto-pay-off compute boundary and no-HPC rule are accepted.
- [x] The six tracks and four-plan sequence are accepted.

### Gate 0 execution before Plan 2 implementation

- [ ] Ownership, licences, provenance and redistribution decisions are recorded.
- [ ] Dataset inventory, grouping, leakage and sample-feasibility checks pass.
- [ ] The output contract and evaluator fixtures pass.
- [ ] The certification implementation passes theorem-to-code and simulation checks.
- [ ] The Qwen baseline and confidence score smoke pass.
- [ ] The paid QLoRA save/reload/cost smoke passes within the staged wallet.
- [ ] The literature kill test is rerun and the contribution boundary survives or is explicitly reframed.
- [ ] `docs/gate0/decision.md` records go, revise or stop/reopen.

Acceptance of this plan approves the research design and Gate 0 work. It does **not** mark the execution checks complete. It authorises drafting Plan 2, while full-data preparation, paid training and experiment execution remain blocked until Gate 0 records a go decision.

---

## 17. Research and skills addendum

### 17.1 Primary sources informing this plan

- [Qwen3-4B-Instruct-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) — selected Apache-2.0 backbone and documented Transformers usage.
- [Hugging Face Transformers generation utilities](https://huggingface.co/docs/transformers/main_classes/text_generation) — transition-score extraction used by the confidence-signal gate.
- [Hugging Face PEFT LoRA guide](https://huggingface.co/docs/peft/en/developer_guides/lora) — adapter and quantized-training contract.
- [Hugging Face TRL SFTTrainer](https://huggingface.co/docs/trl/en/sft_trainer) — supervised fine-tuning and PEFT integration.
- [Multi-Sentence Argument Linking](https://arxiv.org/abs/1911.03766) — introduces the RAMS resource and its document-level argument-linking task.
- [Document-Level Event Argument Extraction by Conditional Generation](https://aclanthology.org/2021.naacl-main.69/) and its [reference repository](https://github.com/raspberryice/gen-arg) — WikiEvents, RAMS/WikiEvents conditional-generation framing and official data links.
- [Conformal Risk Control](https://arxiv.org/abs/2208.02814) — foundational bounded-loss risk-control framework.
- [Conformal Prediction for Risk-Controlled Medical Entity Extraction Across Clinical Domains](https://arxiv.org/abs/2603.00924) — extraction-specific calibration and domain-dependence evidence.
- [When Can Conformal Risk Control Certify LLM Outputs?](https://arxiv.org/abs/2606.29054) — current structured-generation certification boundary and novelty constraint.
- [A Joint Finite-Sample Certificate for Adaptive Selective Conformal Risk Control](https://arxiv.org/abs/2606.08517) — candidate modern treatment of risk, acceptance and adaptive threshold selection; it must be reproduced, not trusted merely because it is recent.
- [Non-monotonicity in Conformal Risk Control](https://arxiv.org/abs/2604.01502) — warning that threshold-grid selection and monotonicity assumptions require explicit treatment.
- [Is Conformal Factuality for RAG-based LLMs Robust?](https://arxiv.org/abs/2603.16817) — shift fragility motivating the frozen transfer stress test.

### 17.2 Evidence and prior project context inspected

- `AREA-2-modern-ml-scoping.md`;
- `AREA-2-modern-ml-project-decision.md`, including the Route Y preservation record;
- `NEW-CHAT-HANDOFF-workflow-and-starterkit.md`;
- the accepted four-plan/six-track structure;
- the prior MUC/MAVEN/WikiEvents/Qwen inference context recorded in the decision memo;
- Hugging Face Hub dataset searches for maintained RAMS/WikiEvents mirrors, which returned no suitable repository result; first-party dataset sources therefore remain the planning default.

### 17.3 Skills applied

- **Hugging Face datasets:** checked Hub discoverability and kept first-party data inventory/licence verification as a Gate 0 requirement rather than assuming a community mirror is authoritative.
- **OpenAI Library:** this plan is persisted as the living Plan 1 artifact.
- **Handoff workflow:** used the research-project pattern—foundations/inventory, falsifiable Gate 0, one plan at a time, acceptance checklist and dated addenda.

### 17.4 Research limitations at planning time

- The exact number of independent source-document groups in the downloaded RAMS and WikiEvents files has not yet been computed; nominal example counts are not substituted for that inventory.
- Code-repository licences and dataset redistribution rights may differ. Raw-data publication remains gated.
- The 2026 certification papers are recent preprints. Their theorems and code, where available, require reproduction and assumption checks.
- A frontier search can bound a contribution but cannot prove global novelty. The kill search is repeated immediately before Plan 2 experiments execute.
- The planning values for risk, confidence and participation are defaults. The checked-in feasibility analysis must justify the final frozen values.

---

## 18. Living-document rule

After acceptance, do not silently rewrite this plan to make later outcomes appear inevitable. Material changes append a dated addendum containing:

- trigger/evidence;
- decision change;
- scope impact;
- acceptance impact.

Where addenda conflict, the newest accepted addendum controls execution while the earlier record remains visible.

### Addenda

#### 2026-07-15 — Plan accepted

**Trigger/evidence:** Ross explicitly replied “Accepted, next.”  
**Decision change:** Plan 1's direction, research contract and Gate 0 design are accepted.  
**Scope impact:** Plan 2 may be drafted. No Gate 0 execution item is marked complete, and full-data preparation, paid training and experiment execution remain gated.  
**Acceptance impact:** Direction-acceptance checklist items are complete; Gate 0 execution items remain open.
