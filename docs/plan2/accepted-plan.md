# ConformalExtract — Plan 2: Data, QLoRA & Reproducible Training

> **Purpose:** turn the accepted research contract into one leakage-safe prompt/completion dataset and three same-backbone systems—zero-shot, few-shot and QLoRA—whose artifacts can be reproduced and evaluated without changing the final certification design.
>
> **Owner:** Ross (Cheng-Yuan King) · **Date:** 2026-07-15 · **Status:** Accepted direction; implementation gated by Plan 1 Gate 0 · **Document type:** living research plan

**Inherited & locked:** Plan 1 is accepted. The active question is whether QLoRA improves **certified acceptance**, not merely average F1. The task is grounded event-argument extraction for a supplied target event/trigger and role schema. Source documents are the independent grouping unit. The primary backbone is the pinned revision of `Qwen/Qwen3-4B-Instruct-2507`; the systems are zero-shot, few-shot and one NF4 QLoRA adapter on that same backbone. RAMS is the primary data candidate and WikiEvents the preferred shift candidate, subject to Gate 0. Sheffield HPC is excluded. Full-data preparation, paid training and experiment execution remain blocked until `docs/gate0/decision.md` records **go**.

---

## 1. Executive training decision

Use a single, transparent **TRL `SFTTrainer` + PEFT + bitsandbytes QLoRA** path. Do not conduct a hyperparameter sweep.

The intervention is intentionally narrow:

> Keep the model family, revision, quantization, prompt contract, output schema, decoding and evaluator fixed; change only whether task-specific LoRA weights are present.

The default adapter configuration is:

- NF4 4-bit frozen base weights with nested/double quantization;
- BF16 compute on compatible Ampere-or-newer hardware;
- LoRA rank `16`, alpha `32`, dropout `0.05`;
- `target_modules="all-linear"`;
- causal-language-model task type, no bias training;
- prompt-completion SFT with loss on completion tokens only;
- one fixed training seed and a maximum of three epochs;
- checkpoint selection by frozen grounded development metrics, never calibration or final-test performance.

This plan permits at most four paid configurations including failed configurations: Gate 0 smoke, one bounded pilot, one full run and one reserved recovery/reproducibility run. The fourth slot is not automatically spent.

---

## 2. Execution boundary inherited from Plan 1

### 2.1 What accepting this plan authorises

Acceptance authorises the implementation sequence, repository contracts, configuration defaults and evidence requirements in this document.

It does not override Gate 0. Before full-data conversion or any paid training beyond the approved Gate 0 smoke:

- ownership and redistribution boundaries must be recorded;
- source-document grouping and split feasibility must pass;
- the evaluator and bounded loss must pass fixtures;
- the selected certificate must pass simulation/theorem-to-code checks;
- the Qwen confidence-score smoke must pass;
- the paid save/reload/cost smoke must project total spend within the $25 wallet;
- the literature kill check must leave a defensible contribution.

### 2.2 What Plan 2 must not decide

Plan 2 does not reopen:

- Route Z versus Route Y;
- the backbone family;
- the headline research question;
- the independent calibration unit;
- the in-domain risk target merely to obtain a positive result;
- the final certification method after Gate 0 freezes it.

Any Gate 0 result that invalidates an inherited decision is recorded as a Plan 1 addendum before this implementation proceeds.

---

## 3. Data lineage and split contract

### 3.1 Immutable source layer

Every first-party download is stored outside Git or under ignored local storage with:

- source URL and retrieval timestamp;
- original filename and byte size;
- SHA-256 digest;
- declared licence/terms and redistribution decision;
- parser/converter version;
- dataset release/version where supplied.

Raw files are never edited in place. A corrected download creates a new content hash and invalidates downstream manifests until explicitly rebuilt.

### 3.2 Canonical event-frame record

The internal canonical record contains at least:

```json
{
  "example_id": "...",
  "source_document_id": "...",
  "source_dataset": "rams",
  "split_role": "train",
  "document": "...",
  "trigger": {"text": "...", "start": 0, "end": 0},
  "event_type": "...",
  "allowed_roles": ["..."],
  "arguments": [
    {"role": "...", "text": "...", "start": 0, "end": 0}
  ],
  "ontology_version": "...",
  "source_sha256": "..."
}
```

Offsets use one declared convention—preferably zero-based, end-exclusive character offsets after a verified source-text reconstruction. The converter must round-trip every gold span back to the exact normalized document text under the evaluator's policy.

### 3.3 Group assignment

`source_document_id` is the minimum group key. Exact normalized-document hash and near-duplicate clusters can merge apparently different IDs into a larger group.

Rules:

- every frame from one group stays in one data role;
- all fixed few-shot demonstrations come from training groups;
- no calibration, final in-domain or shift labels enter training or prompt selection;
- deterministic manifests, not ad hoc dataset slicing, define each role;
- every loader verifies group disjointness and source hashes before returning rows.

### 3.4 Data roles and visibility

| Role | Model gradients | Prompt/score decisions | Threshold/certificate | Final reporting |
|---|---:|---:|---:|---:|
| Train | Yes, QLoRA only | demonstration bank source | No | training statistics only |
| Development | No | Yes | no final certificate | checkpoint/score selection evidence |
| Calibration/certification | No | No | Yes | certificate construction |
| Final in-domain | No | No | No | opened once for frozen evaluation |
| Shift | No | No | transfer only | opened after in-domain freeze |

Training code must not load final or shift labels. Evaluation scripts use separate entry points and manifests.

### 3.5 Conversion invariants

The build fails if:

- a gold span cannot be grounded;
- a role is outside the declared event schema;
- one group occurs in multiple data roles;
- a duplicate `example_id` has different content;
- source or manifest hashes do not match;
- prompt plus completion exceeds the frozen token budget without an accepted context rule;
- target completion is truncated;
- the train conversion silently drops a class/role without an exclusion report.

The data report includes retained/dropped counts and reasons by event type, role and document length.

---

## 4. Prompt, completion and demonstration contracts

### 4.1 Conversational prompt-completion format

Store training rows in TRL-compatible conversational prompt-completion form:

```json
{
  "prompt": [
    {"role": "system", "content": "...fixed system instruction..."},
    {"role": "user", "content": "...document, trigger and schema..."}
  ],
  "completion": [
    {"role": "assistant", "content": "...canonical compact JSON..."}
  ]
}
```

Metadata remains in the canonical dataset/manifests and is removed from the trainer-facing columns after validation. The tokenizer's chat template is applied exactly once. Unit tests detect duplicated BOS/EOS markers, missing assistant boundaries and accidental loss on prompt tokens.

### 4.2 Fixed instruction

The user prompt contains, in fixed order:

1. the task statement;
2. the supplied event type and trigger;
3. allowed roles with short ontology descriptions;
4. grounding rules—copy argument text from the source and do not invent fields;
5. the compact JSON schema;
6. the source document/window.

Only the data fields vary. Wording does not change by system or split after Gate 0.

### 4.3 Canonical completion

- keys use one stable order;
- arguments are sorted by role and source offset using a declared rule;
- empty argument sets use one representation;
- JSON is compact and valid before tokenization;
- no markdown fences or explanatory text appear in gold completions;
- aliases/coreference are not rewritten beyond the accepted gold/evaluator policy.

Stable serialization reduces meaningless sequence variation without changing the task.

### 4.4 Context-length policy

Gate 0 inventory freezes `max_length`; the planning default is `2048` tokens using the current TRL `SFTConfig.max_length` argument.

If an example exceeds the cap:

1. retain the trigger sentence and all gold-argument sentences;
2. expand symmetrically with neighbouring sentences while space remains;
3. record the retained sentence IDs and truncation flag;
4. exclude only if the required gold evidence cannot fit;
5. apply the identical deterministic window policy to all systems.

No right truncation may remove part of a gold completion. Long-example exclusions are reported, not hidden.

### 4.5 Zero-shot contract

Zero-shot uses the fixed instruction, role schema and document with no labelled demonstrations. It uses the same 4-bit base model load, tokenizer, context policy and decoding settings as the adapter system.

### 4.6 Few-shot contract

Few-shot uses exactly `k=2` labelled demonstrations from training groups unless Gate 0 token accounting proves that two do not fit.

Demonstrations are selected deterministically before evaluation:

- prefer training examples with the same event type;
- otherwise use a fixed global fallback pair covering distinct role patterns;
- never retrieve using gold test arguments;
- never select by observed evaluation performance;
- record demonstration IDs in every prediction manifest.

The QLoRA system does not receive few-shot demonstrations in the primary comparison. It uses the zero-shot prompt contract plus the adapter, isolating learned adaptation from in-context examples.

---

## 5. Frozen QLoRA configuration

### 5.1 Model and quantization

The loader pins the exact model and tokenizer Hub revision recorded by Gate 0.

```python
BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
```

BF16 is used only after the hardware smoke confirms support. If not supported, FP16 is an allowed compatibility substitution with a dated manifest entry; TF32 may be enabled for eligible FP32 matmuls but is not described as BF16.

The training process uses one explicit GPU. It does not rely on multi-GPU sharding or `device_map="auto"` as an accidental training strategy.

### 5.2 Adapter

```python
LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules="all-linear",
    bias="none",
    task_type="CAUSAL_LM",
)
```

`all-linear` follows the current PEFT QLoRA guidance and avoids architecture-specific hand lists. The resolved targeted-module names and trainable/total parameter counts are written to the run manifest. Embeddings and `lm_head` are not independently made trainable unless the resolved PEFT behavior and smoke evidence require a reviewed correction.

No DoRA, rsLoRA, LoftQ, PiSSA, KappaTune or adapter merging enters the primary run. Those are possible future ablations, not hidden tuning choices.

### 5.3 Training-state preparation

- enable gradient checkpointing;
- disable model cache during training and restore it for inference;
- prepare the quantized model for k-bit training through the supported PEFT/TRL path;
- print and assert trainable parameter counts;
- fail if unexpected base parameters require gradients;
- run a one-batch forward/backward test and verify non-zero adapter gradients before the paid pilot.

---

## 6. SFT configuration and checkpoint policy

### 6.1 Primary `SFTConfig`

The planning defaults are:

| Setting | Value | Reason |
|---|---:|---|
| `max_length` | Gate 0 value; default 2048 | derived from tokenizer inventory |
| `completion_only_loss` | `True` | learn the target JSON, not repeat the prompt |
| `packing` | `False` | preserve example boundaries and auditability |
| epochs | maximum 3 | bounded task adaptation |
| learning rate | `1e-4` | one conservative PEFT default, not a sweep |
| scheduler | cosine | smooth bounded decay |
| warmup ratio | `0.03` | short warmup without many extra decisions |
| weight decay | `0.0` | avoid an unmotivated adapter regularisation change |
| max grad norm | `1.0` | divergence guard |
| train batch/device | `1` or `2` from smoke | memory-bound physical batch |
| gradient accumulation | set for effective batch `16` frames | stable comparable update scale |
| precision | BF16 when supported | Ampere-class compute path |
| optimizer | `paged_adamw_8bit` | QLoRA memory control |
| eval/save/log | steps derived from epoch size | bounded, deterministic checkpoints |
| seed | `42` | primary training and sampler seed |
| reporting | Trackio plus local JSON/CSV export | inspectable evidence |

The resolved config is a checked-in YAML/JSON artifact. Current argument names are validated against the locked TRL version; deprecated aliases are not copied from old tutorials.

### 6.2 Evaluation during training

Trainer evaluation loss is logged on the development split, but it does not choose the research result.

At the end of each epoch, a separate frozen generation evaluator runs on the same fixed development subset and records:

- grounded exact and normalized argument F1;
- parse/schema/grounding failure rates;
- bounded document loss;
- output-token count and latency;
- obvious degeneration such as empty-output collapse.

Calibration/certification and final-test labels are not used during checkpoint selection.

### 6.3 Checkpoint selection

Choose the checkpoint with the lowest **development mean bounded document loss**. Ties within `0.005` are broken by:

1. lower unsupported-field rate;
2. higher normalized grounded argument F1;
3. earlier/cheaper checkpoint.

The selection rule is frozen before the full run. The selected checkpoint is copied to an immutable adapter artifact; later checkpoints are not substituted because they look better on calibration or test.

### 6.4 Early termination rules

Stop and mark the run failed if:

- loss or gradients become non-finite;
- all adapter gradients remain zero;
- outputs collapse to empty or repeated invalid structures across two evaluations;
- checkpoint save/reload fails;
- the projected wallet or storage boundary is exceeded;
- data/split/hash assertions fail.

Ordinary small metric fluctuations are not a reason for autonomous retuning.

---

## 7. Fixed experiment budget

### 7.1 Paid run ledger

| Slot | Run | Scope | Exit decision |
|---|---|---|---|
| R0 | Gate 0 smoke | 20–50 steps, tiny deterministic subset | stack, gradients, save/reload, throughput and cost pass |
| R1 | bounded pilot | roughly 10% of training groups, at most one epoch | loss decreases and generated outputs do not degenerate |
| R2 | primary full run | full accepted train manifest, maximum three epochs | select one frozen adapter checkpoint |
| R3 | reserved | one recovery **or** one reproducibility repeat | spent only by recorded rule and remaining budget |

Every started paid configuration consumes its slot even if it crashes. Re-running the same command after a provider outage may be classified as a continuation only when it resumes the same checkpoint/config and the interruption is documented.

### 7.2 R3 decision

Use R3 in this order:

1. required compatibility recovery after a documented R2 infrastructure failure;
2. second seed only if R2 completes, the complete project remains within $25 and the repeat materially improves credibility;
3. otherwise leave it unused.

R3 is never used for rank, alpha, dropout, target-module or learning-rate shopping. If a second seed runs, it uses the identical configuration with seed `123` and is reported as a stability check, not merged opportunistically.

### 7.3 One allowed pilot correction

R1 may trigger one predeclared correction before R2:

- if non-finite/unstable loss occurs without a data defect, reduce learning rate from `1e-4` to `5e-5`;
- if memory fails, reduce physical batch before sequence length;
- reduce `max_length` only through the accepted evidence-preserving context rule;
- do not change rank, target modules, epochs and prompt simultaneously.

The correction and reason become an addendum/run-ledger entry. A stable but unimpressive pilot is not failure and does not justify tuning.

---

## 8. Remote GPU execution and financial controls

### 8.1 Provider boundary

The active path remains RunPod or an equivalent **prepaid** single-GPU provider. Hugging Face Jobs is not selected automatically because the project already adopted a hard-wallet/auto-pay-off boundary; Jobs may be reconsidered only through a dated cost-and-billing comparison.

Preferred hardware is one A40-class 48 GB GPU. An A100 is used only if the measured smoke indicates a lower total cost-to-completion. GPU model, VRAM, driver and hourly price are recorded at run start.

### 8.2 Three-stage lifecycle

**Before launch**

- all code/tests/configs committed;
- source/model licences and data upload boundary passed;
- frozen, encrypted or licence-permitted training bundle prepared;
- wallet balance and auto-pay state captured;
- shutdown and artifact-sync scripts dry-run locally;
- secrets scoped and excluded from shell history/configs.

**During run**

- start from an immutable provider image or record the exact image ID/digest;
- install from `uv.lock`/pinned environment;
- verify hashes before training;
- log Trackio metrics plus local machine-readable logs;
- checkpoint at the declared interval;
- sync the selected/latest recoverable adapter, run manifest and logs off the ephemeral filesystem;
- monitor actual elapsed cost against the run ledger.

**After run**

- reload the selected adapter in a fresh process and reproduce fixed development outputs;
- sync checksummed artifacts to local storage and optionally a private Hub staging repository;
- record end balance and actual compute/storage cost;
- terminate the Pod, then delete unneeded network storage;
- verify no billable resource remains.

### 8.3 Storage and recovery

At least two copies of the selected adapter and manifest must exist before resource destruction: one local copy and one checksummed remote/staging copy. Partial optimizer checkpoints may be discarded after the chosen adapter is verified unless they are required for R3 continuation.

Raw or restricted dataset text is never uploaded to a public Hub repository, public Trackio dashboard or logs.

---

## 9. Experiment tracking and run manifest

### 9.1 Trackio contract

Every trainer run sets:

- `report_to="trackio"`;
- `TRACKIO_PROJECT="conformalextract-training"`;
- descriptive run names such as `r2-qwen3-4b-r16-seed42-<gitsha>`;
- config fields excluding tokens, raw documents and other sensitive content.

Trackio is local-first. A Hugging Face Space/dashboard may be used for remote monitoring only after visibility and token permissions are deliberately configured. Regardless of dashboard use, metrics are exported to a local machine-readable artifact before the remote instance is deleted.

Alert conditions cover non-finite loss, missing evaluation metrics, checkpoint failure and projected cost overrun. Alerts inform a human decision; they do not authorise autonomous hyperparameter changes.

### 9.2 Required `run.json`

Each run records:

- run ID, purpose, status and paid-slot number;
- Git commit and dirty-worktree flag;
- data, split, prompt and schema manifest hashes;
- model/tokenizer repo and immutable revision;
- adapter, quantization and SFT configs;
- package lock hash and container/image identity;
- CUDA, driver, PyTorch, Transformers, TRL, PEFT, Accelerate and bitsandbytes versions;
- GPU model/VRAM, host CPU/RAM and precision support;
- seeds and deterministic settings;
- timestamps, steps, tokens, throughput, peak VRAM and checkpoints;
- starting/ending wallet, compute/storage cost and provider;
- selected checkpoint rule/result;
- output artifact names and SHA-256 digests;
- deviations, warnings and failure reason.

### 9.3 Reproduction levels

- **Exact artifact replay:** load the published adapter/config and reproduce frozen predictions.
- **Training rerun:** same data hashes, environment, hardware class, seed and config; numerical identity is not promised across kernels/hardware.
- **Scientific reproduction:** independently train and compare the same systems under the declared contract.

The README must not claim bitwise deterministic GPU training unless demonstrated.

---

## 10. Baseline and adapter prediction contract

### 10.1 Frozen inference stack

All three systems use:

- the same pinned tokenizer/base revision;
- the same 4-bit quantization configuration;
- deterministic greedy decoding;
- the same maximum input/output lengths;
- the same parser, grounding resolver and evaluator;
- the same hardware class for headline latency where feasible;
- the same confidence-score extraction implementation.

The adapter path differs only by loading the selected LoRA weights. Generation does not merge the adapter into the base for the primary result.

### 10.2 Prediction artifact

Each output row records:

- example and source-document group IDs;
- system ID and run/checkpoint IDs;
- prompt/template and demonstration IDs;
- raw completion and parsed structure;
- token transition scores needed by the frozen confidence function;
- parse/schema/grounding flags;
- generation token count and latency;
- no gold label in the raw inference artifact.

Gold joins occur in the evaluator using a separate manifest. This keeps prediction generation independent from scoring.

### 10.3 What Plan 2 may evaluate

Plan 2 may use development labels for data validation, score selection and checkpoint selection under the accepted rules. It may not inspect final in-domain or shift results. Plan 3 owns calibration, frozen final evaluation and all headline comparisons.

---

## 11. Validation, tests and CI

### 11.1 CPU/local pull-request checks

- schema validation for canonical and trainer rows;
- prompt/completion golden snapshots;
- group leakage and duplicate-hash tests;
- gold-span round-trip grounding tests;
- tokenizer special-token and label-mask tests;
- target completion never truncated;
- config schema and run-ID validation;
- tiny fake-model tests for save/reload and prediction artifact shape;
- evaluator fixtures inherited from Plan 1;
- secret scanning and no raw-data tracking.

CI uses synthetic/licence-safe fixtures. It does not download the 4B model or run CUDA training.

### 11.2 Local model smoke

Where the 8 GB laptop GPU permits, load the 4-bit model at batch size one and run fixed inference examples. Local inability to train the 4B model is not a failure because remote QLoRA is the accepted boundary.

### 11.3 Remote GPU acceptance checks

- environment installs from the lock without manual drift;
- model revision/hash matches;
- all-linear target list and trainable count are captured;
- one batch completes forward/backward;
- loss decreases on the overfit subset;
- adapter save/reload produces the same deterministic output;
- checkpoint resume advances from the expected global step;
- Trackio and local logs both contain the required fields;
- artifacts survive a fresh-process replay.

---

## 12. Artifact and Hub staging contract

### 12.1 Private staging first

During Plans 2–3, the adapter may be copied to a private Hugging Face model repository for resilience. The staging card must say **experimental/unverified**, identify the base revision and prevent accidental inference-provider deployment where possible.

Public release waits for Plan 4 and all of:

- data and derivative-artifact licence decisions;
- final evidence and limitations;
- adapter lineage and training disclosure;
- safety/content review of example outputs;
- clean replay from the intended public artifact.

### 12.2 Adapter artifact contents

- adapter weights in safe serialization;
- `adapter_config.json`;
- base model/revision pointer, never copied base weights;
- inference/quantization config;
- prompt/schema version;
- selected checkpoint and run manifest;
- draft model card with training data source, intended use and limitations;
- checksums.

Optimizer state is not part of the public adapter unless a clear reproducibility reason outweighs size and risk.

### 12.3 Data publication boundary

By default publish:

- loader/converter code;
- source URLs and checksums;
- split/group manifests containing IDs where permitted;
- schema/ontology mapping;
- synthetic fixtures;
- aggregate data statistics.

Publish transformed raw text or gold completions only if the source terms explicitly allow redistribution.

---

## 13. Failure and recovery runbook

| Failure | Detection | Response | Paid-slot consequence |
|---|---|---|---|
| Data hash or split mismatch | preflight assertion | stop; rebuild from accepted source/manifests | no new slot if before GPU allocation |
| Gold completion truncation | converter/token test | repair context policy through accepted rule | no training |
| CUDA OOM | smoke/pilot | reduce physical batch, then checkpointing/context by rule | started configuration consumes slot |
| Non-finite loss | Trackio/local alert | stop; inspect data; one LR reduction only if data clean | consumes slot |
| No adapter gradients | gradient assertion | stop and repair PEFT wrapping | consumes slot if paid run started |
| Save/reload mismatch | smoke/replay test | stop; fix serialization/version stack | no full run |
| Provider interruption | run disappears/log stops | resume same config/checkpoint if intact | continuation, not new configuration |
| Trackio sync unavailable | dashboard missing | continue local logging and external artifact sync | no scientific change |
| Hub upload fails | checksum absent remotely | retain local/network copies; retry before deletion | no public claim |
| Pilot stable but weak | dev metrics modest | proceed once if gates pass; do not tune | null result remains possible |
| Full adapter harms task loss | frozen dev evaluation | preserve result; do not choose baseline using test | Plan 3 reports negative intervention |
| Spend projection exceeds wallet | cost monitor | checkpoint, stop, do not top up | revise scope/addendum required |

---

## 14. Implementation sequence

### Phase A — contracts and synthetic path

1. Scaffold only the accepted repository modules/config schemas.
2. Implement canonical record, prompt/completion serializer and synthetic fixtures.
3. Add split/hash/grounding/token-mask tests.
4. Implement zero-shot/few-shot prompt builders and prediction schema.

### Phase B — Gate 0 data and baseline integration

1. Consume accepted first-party source files and group manifests.
2. Produce inventory/conversion reports.
3. Pin Qwen revision and inference environment.
4. Run the baseline/score smoke and freeze prompt, context and score contracts.

### Phase C — QLoRA smoke and pilot

1. Implement the locked quantization, LoRA and SFT configs.
2. Verify gradients, labels, overfit behavior, save/reload and resume.
3. Complete R0 and Gate 0 go/revise/stop record.
4. If go, run R1 and apply at most the one permitted correction.

### Phase D — primary training

1. Freeze R2 config and manifests.
2. Train for at most three epochs with declared checkpoints/logging.
3. Run frozen development generation at each checkpoint.
4. Select exactly one adapter by the predeclared rule.
5. Replay it in a fresh process and checksum the artifact.

### Phase E — freeze systems for Plan 3

1. Freeze ZS, FS and QA system manifests.
2. Generate development-only validation artifacts.
3. Confirm calibration/final/shift labels remain unopened by training code.
4. Stage the selected adapter privately and export evidence.
5. Hand the immutable system IDs, score function and prediction schema to Plan 3.

---

## 15. Six-track Plan 2 responsibilities

| Track | Plan 2 responsibility | Exit artifact |
|---|---|---|
| Research / novelty | preserve adaptation as the only learned intervention | frozen comparison manifest |
| Data / grounding | lineage-safe conversion, grouping and grounded completions | canonical dataset report and split hashes |
| Model / adaptation | one audited NF4 all-linear QLoRA | selected adapter and training manifest |
| Statistical reliability | keep calibration/test isolated; preserve score outputs | label-free prediction schema with transition scores |
| Systems / reproducibility | locked environment, run ledger, recovery and replay | `run.json`, locks, logs, checksums |
| Public contribution / release | private staging and licence-aware artifact boundary | draft model card and release matrix |

---

## 16. Open decisions and decision deadlines

| Decision | Default | Must be frozen by | Selection evidence |
|---|---|---|---|
| exact source dataset/splits | RAMS-first candidate | Gate 0B | grouping, licence and feasibility report |
| `max_length` | 2048 | Gate 0E | tokenizer length distribution and memory smoke |
| physical batch | 1 or 2 | R0 | measured peak VRAM |
| BF16 vs FP16 | BF16 | R0 | hardware capability and stable backward pass |
| paid GPU SKU | A40-class 48 GB | before R0 allocation | live price/availability and cost estimate |
| Trackio Space sync | local-first; optional hosted mirror | before R0 | visibility, token and persistence decision |
| private Hub staging | yes if token/terms permit | before R2 | licence and secret boundary |
| R3 use | unused | after R2 | failure/repeat rule and remaining wallet |

Rank, alpha, dropout, target modules, learning rate, epoch maximum and system count are not open-ended tuning axes. Only the explicitly defined compatibility correction is allowed.

---

## 17. Acceptance checklist — Plan 2 is done when

### Direction acceptance now

- [x] One TRL/PEFT/bitsandbytes QLoRA path is accepted.
- [x] The canonical data, source-document grouping and split-visibility contracts are accepted.
- [x] Zero-shot, deterministic two-shot and adapter prompt contracts are accepted.
- [x] Rank-16/alpha-32/dropout-0.05/all-linear QLoRA is accepted as the single primary configuration.
- [x] Completion-only SFT and the development-only checkpoint rule are accepted.
- [x] The four-paid-configuration maximum and R3 decision rule are accepted.
- [x] Trackio plus local run manifests/checksums are accepted as the evidence layer.
- [x] Private staging before public Hugging Face release is accepted.
- [x] Full implementation remains blocked by Plan 1 Gate 0 go.

### Implementation acceptance before Plan 3 experiments

- [ ] Source, canonical and trainer artifacts pass hash/schema/group tests.
- [ ] Prompt/template/completion masking and context policy pass golden tests.
- [ ] ZS/FS/QA manifests use the same pinned inference stack.
- [ ] R0 and R1 evidence satisfy the run rules.
- [ ] R2 completes within the wallet or records an accepted negative/stop result.
- [ ] Exactly one adapter checkpoint is selected without calibration/final labels.
- [ ] Fresh-process replay, save/reload and checksum verification pass.
- [ ] Run manifests, Trackio export, environment lock and actual cost are complete.
- [ ] No billable remote resource remains after artifact recovery.
- [ ] Plan 3 receives immutable system IDs, prediction schema and confidence-score outputs.

Acceptance of this plan authorises drafting Plan 3. It does not mark implementation complete or permit calibration/final-test inspection before the inherited gates and system freeze.

---

## 18. Research and skills addendum

### 18.1 Current primary documentation

- [Qwen3-4B-Instruct-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) — selected 4.02B-parameter Apache-2.0 text-generation backbone and chat-template usage.
- [TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer) — prompt-completion datasets, completion-only loss, `SFTConfig.max_length`, PEFT and quantization integration.
- [PEFT LoRA reference](https://huggingface.co/docs/peft/package_reference/lora) and [quantization guide](https://huggingface.co/docs/peft/developer_guides/quantization) — `target_modules="all-linear"` for QLoRA-style training.
- [Transformers bitsandbytes guide](https://huggingface.co/docs/transformers/quantization/bitsandbytes) — NF4, compute dtype and nested quantization behavior.
- [QLoRA](https://arxiv.org/abs/2305.14314) — underlying 4-bit frozen-base plus LoRA method.
- [Trackio integration for TRL](https://huggingface.co/docs/trl/trackio_integration) — `report_to="trackio"`, project/run naming and optional Hugging Face Space hosting.
- [Hugging Face model cards](https://huggingface.co/docs/hub/model-cards) — adapter lineage, training, evaluation, limitations and licence disclosure.

### 18.2 Skills applied

- **Hugging Face LLM trainer:** grounded the TRL prompt-completion/SFT structure, cloud-job failure boundaries, artifact persistence and current `max_length` argument. No job was submitted because this turn plans the work and the accepted provider remains prepaid burst GPU rather than Hugging Face Jobs.
- **Hugging Face Trackio:** made experiment metrics, named runs, alerts and portable exports part of the required evidence rather than optional screenshots.
- **OpenAI Library:** this plan and the accepted Plan 1 record are persisted as living project artifacts.

### 18.3 Planning limitations

- Exact resolved package versions are intentionally produced by the Gate 0 lock/smoke; writing today's versions into a plan without testing their joint compatibility would be weaker evidence.
- GPU SKU and price are live availability decisions. The plan freezes the memory class and financial rule, not a stale hourly number.
- RAMS conversion, unique-group counts and redistribution terms remain empirical Gate 0 results.
- A single training seed is the budget default. The result must disclose that limitation unless R3 funds a true repeat.
- Trackio/Hub staging must not expose restricted source text, credentials or unreviewed public claims.

---

## 19. Living-document rule

After acceptance, material changes append a dated addendum rather than rewriting the original decision history. Each addendum records trigger/evidence, decision change, scope impact and acceptance impact. The newest accepted addendum controls execution where entries conflict.

### Addenda

#### 2026-07-15 — Plan accepted

**Trigger/evidence:** Ross explicitly replied “Accepted next.”  
**Decision change:** Plan 2's data, QLoRA, run-budget and reproducibility direction is accepted.  
**Scope impact:** Plan 3 may be drafted. No Plan 2 implementation item is marked complete, and training remains gated by Plan 1 Gate 0.  
**Acceptance impact:** Direction-acceptance checklist items are complete; implementation items remain open.
