# ConformalExtract — Plan 4: Verification, Release & Research/Portfolio Consolidation

> **Purpose:** turn the frozen ConformalExtract experiment into an independently checkable public contribution: verify every material claim from clean environments, publish only licence-safe artifacts, connect GitHub/Hugging Face/Kaggle into one evidence trail, and translate the result—positive, null or negative—into honest research and portfolio outputs.
>
> **Owner:** Ross (Cheng-Yuan King) · **Date:** 2026-07-15 · **Status:** Direction accepted; implementation and public release pending · **Document type:** living release plan

**Inherited & locked:** Plans 1–3 are accepted in direction but not implemented. Route Z is ConformalExtract; Route Y remains a preserved deferred project. Certified acceptance is the headline object, QA–ZS is primary, QA–FS is secondary confirmatory, and static transfer under shift is explicitly uncertified. No release may imply that planning acceptance equals a completed experiment, that an infeasible certificate is a successful certificate, or that an in-domain guarantee survives schema/dataset shift.

> ### Amendment — 2026-07-29: the inherited-status line above is out of date
>
> Appended, not rewritten; the paragraph above is preserved as the historical record of what was
> true on 2026-07-15. **Read this note in its place.** Reconciled against the repository's own
> records before Plan 4 was used for anything:
>
> | Plan | The line above says | The records say |
> |---|---|---|
> | Plan 1 | accepted in direction, not implemented | **complete** — Gates 0A–0F pass, Gate 0 decision `go`, consolidated reviewer PASS 2026-07-17 (`docs/gate0/decision.md`) |
> | Plan 2 | accepted in direction, not implemented | **closed** — independent reviewer PASS at commit `2d3c6be`, 2026-07-21 (`evidence/plan2/reviewer_record.plan2-close.json`) |
> | Plan 3 | accepted in direction, not implemented | **executed and independently reviewed, not formally closed** — certification ran 2026-07-22 and returned infeasibility for all three systems; five Plan 3 reviewer records exist and **none carries `review_kind: "plan_close"`** |
>
> **What is locked has not changed, and one clause of it now binds harder than when it was
> written.** "No release may imply … that an infeasible certificate is a successful certificate"
> was drafted as a precaution against a hypothetical. The certificate came back **infeasible for
> all three systems**, so that clause is now the governing constraint on every artifact this plan
> produces, not a guard against an unlikely branch.
>
> One inherited assumption is superseded rather than merely dated: the line names certified
> acceptance as "the headline object". No certified acceptance exists. The headline object of the
> release is the **negative result** and the grounding⊥certifiability decomposition
> (`CX-GROUNDING-ORTHOGONAL-01`), bounded by
> [`../plan3/certification-result.md`](../plan3/certification-result.md) → "What may and may not
> be claimed".
>
> **This is the same defect as the README gate-state error corrected on 2026-07-28** — a document
> asserting a gate state its own repository contradicted — and it is worse here for two reasons.
> The README is read by anyone; this document *governs the release*, so a stale status line in it
> would have been inherited by every artifact built from it. And it survived a full day spent
> correcting exactly this class of error one directory away. **The lesson is recorded as a check
> in [`../../REVIEW.md`](../../REVIEW.md), not here**, because a lesson written only into the
> document it concerns fires once.

---

## 1. Executive release decision

ConformalExtract will ship as an **evidence-led research repository**, not as a model demo with claims added afterward.

The minimum useful public contribution is:

1. the tested extraction evaluator and certification library;
2. an immutable, licence-safe evidence bundle with manifests, aggregate results and claim status;
3. a CPU-compatible notebook that reproduces the certificate, result tables and figures from released evidence without retraining;
4. a versioned GitHub research release;
5. a Hugging Face evidence Dataset repository and Collection;
6. a Kaggle evidence dataset plus reproducibility notebook;
7. a paper-shaped technical report and outcome-conditional portfolio narrative.

The QLoRA adapter is published only when its base-model terms, training-data terms, output-safety review and evidence checks all pass. It strengthens the release but is not allowed to become a single point of failure.

There is no mandatory hosted UI, continuous GPU endpoint or paid serving bill. A later Hugging Face Space is optional only if it demonstrates the certifier without weakening the evidence work.

---

## 2. Release doctrine

### 2.1 Evidence before narrative

Every quantitative public sentence maps to a claim ID and immutable artifacts. The release workflow is:

```text
frozen code + frozen artifacts
          ↓
clean-room reproduction
          ↓
claim ledger + evidence manifest
          ↓
draft GitHub/HF/Kaggle release candidates
          ↓
licence, privacy and link audit
          ↓
public versioned release
          ↓
anonymous fresh-download verification
```

README wording, charts, CV bullets and social posts are downstream views of the same ledger. They cannot create a stronger claim than the evidence permits.

### 2.2 What “reproducible” means here

The release distinguishes three levels:

| Level | Public requirement | Meaning |
|---|---|---|
| Result replay | mandatory | a CPU user can regenerate certificates, tables and figures from immutable released predictions/results |
| Inference replay | mandatory where adapter is public | a fresh environment can load pinned base + adapter revisions and reproduce fixture outputs within declared tolerances |
| Training reproduction | documented, not promised bit-for-bit | the complete recipe, seed, data fingerprints, environment, cost and checkpoint lineage are present; stochastic GPU retraining may not be identical |

No wording such as “fully reproducible” appears without naming the level.

### 2.3 Release-worthy outcomes

All preregistered outcomes can support release:

| Outcome | Core public conclusion |
|---|---|
| QA materially improves certified acceptance | parameter-efficient adaptation crossed the predeclared reliability/usefulness boundary in-domain |
| QA improves accuracy but not certified acceptance | average task quality did not translate into a stronger deployable risk/acceptance certificate |
| all systems are infeasible | the chosen sample size, loss, target and systems could not support a non-vacuous certificate |
| QA harms certification | adaptation improved neither—or worsened—the reliability/usefulness boundary under the frozen design |
| in-domain success fails under shift | the certificate was useful in-domain but did not transport; the transferred policy is reported as uncertified |
| verification failure | release is delayed or reduced to methods/code; failed evidence is not converted into a result claim |

---

## 3. Public artifact architecture

### 3.1 Canonical homes

| Surface | Canonical artifact | Purpose |
|---|---|---|
| GitHub | `conformalextract` repository and tagged release | source, tests, methods, report and canonical version history |
| Hugging Face Dataset | `conformalextract-evidence` | licence-safe replay artifacts, cards and machine-readable manifests |
| Hugging Face Model | `conformalextract-qwen3-4b-qlora` if approved | adapter, pinned base relationship, intended use and evaluation |
| Hugging Face Collection | ConformalExtract collection | one index linking code, evidence, adapter and any later paper/Space |
| Kaggle Dataset | ConformalExtract certification evidence | versioned notebook inputs and discoverable public data contribution |
| Kaggle Notebook | “From QLoRA Extraction to a Finite-Sample Certificate” | CPU replay and educational walkthrough |
| Technical report | GitHub Markdown/PDF first | paper-shaped account of question, method, result and limitations |

Repository/Hub names are working names. Namespace availability and collision checks occur at release-candidate time; scientific identifiers inside manifests remain stable if a display name changes.

### 3.2 Repository layout at release candidate

```text
conformalextract/
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml
├── src/conformalextract/
│   ├── data/
│   ├── extraction/
│   ├── evaluation/
│   ├── certification/
│   └── reporting/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── statistical/
├── configs/frozen/
├── scripts/
├── notebooks/
│   └── reproduce_release.ipynb
├── docs/
│   ├── methods.md
│   ├── limitations.md
│   ├── data-provenance.md
│   └── evidence/releases/<release-id>/
│       ├── manifest.json
│       ├── claim-ledger.json
│       ├── verification-summary.md
│       ├── environment/
│       ├── results/
│       ├── figures/
│       └── checksums.sha256
└── paper/
    ├── report.md
    └── report.pdf
```

Generated large artifacts are not committed merely for convenience. Git holds compact evidence; the Hub/Kaggle hold approved larger replay assets, all connected by hashes and immutable revisions.

### 3.3 Evidence manifest minimum fields

Each public release contains one machine-readable manifest with:

- release ID, Git commit, tag and UTC creation time;
- Plan 1 research-contract version and frozen hypothesis IDs;
- model, tokenizer, adapter and dataset identifiers with exact revisions/fingerprints;
- calibration/final/shift artifact hashes and role labels;
- system and threshold grid definitions;
- `alpha`, `delta`, acceptance floor and material-effect threshold;
- theorem/method identifier and implementation version;
- environment lockfile hashes, OS, Python/CUDA/GPU details where applicable;
- command lines for result and inference replay;
- artifact paths, sizes, media types, hashes and redistribution status;
- licence/provenance decisions and reviewer/date;
- total remote compute time and cost;
- verification check IDs and outcomes;
- public URLs populated only after publication.

Unknown or not-applicable values are explicit; no silent blank fields.

### 3.4 Claim ledger

Each material statement receives a stable ID such as `CX-H1-PRIMARY`, `CX-H2-SHIFT-01` or `CX-REPRO-CPU-01`.

Required fields are:

| Field | Meaning |
|---|---|
| `claim_id` | stable identifier |
| `wording` | exact approved public sentence |
| `status` | `verified`, `qualified`, `negative`, `infeasible`, `failed`, or `planned` |
| `scope` | in-domain, shift stress test, software or cost |
| `evidence` | manifest paths and table/figure cells |
| `method` | test/certificate and frozen parameters |
| `limitations` | conditions that must travel with the claim |
| `surfaces` | README, report, model card, dataset card, CV, Kaggle |
| `verified_by` | automated check plus human review/date |

Only `verified`, `qualified`, `negative` and `infeasible` entries may enter public prose, with their scope and limitations. `Planned` is never written as achieved.

---

## 4. Pre-release verification matrix

### 4.1 Mandatory gates

| Gate | Check | Pass condition | Failure action |
|---|---|---|---|
| V1 source | formatting, lint, types, unit/integration tests | frozen CI commands pass | fix and rerun; new release candidate |
| V2 evaluator | golden fixtures and adversarial cases | exact expected grounded metrics | block quantitative release |
| V3 certifier | simulations, theorem-to-code cases, conservative cross-check | declared coverage/type-I behavior and fixture outputs pass | block “certified” wording |
| V4 data roles | split/fingerprint/leakage audit | no sealed-role breach; hashes match | invalidate affected run |
| V5 artifacts | manifest and SHA-256 verification | every required artifact resolves and matches | regenerate bundle without altering results |
| V6 results | independent command regenerates tables/figures | numeric cells match declared tolerance | investigate; block claims |
| V7 inference | pinned base + adapter fixture replay | schema-valid outputs and declared equivalence pass | block adapter release or qualify |
| V8 licences | code, model, data and outputs | every public file has a documented legal basis | omit restricted artifact |
| V9 safety/privacy | secret, PII and unsafe-content audit | no token/credential/private or prohibited material | purge, rotate if needed, rebuild history/bundle safely |
| V10 docs | links, commands, cards, limitations, citations | automated link/command checks plus human read pass | correct before publication |
| V11 clean install | supported install in fresh CPU environment | quickstart completes from zero state | block release |
| V12 public replay | anonymous/fresh downloads after publish | hashes, notebook and quickstart pass | patch docs or issue corrective release |

### 4.2 Statistical verification is not an ordinary unit test

The release candidate must include:

- deterministic theorem-to-code examples;
- Monte Carlo simulation summaries for valid and deliberately invalid conditions;
- the conservative audit side by side with the preferred method;
- explicit family size and failure-budget accounting;
- document-grouped independence checks;
- sensitivity outputs predeclared in Plan 3;
- `Infeasible` fixtures and expected behavior;
- a negative control demonstrating that naive threshold selection is not mislabeled as certified.

Simulation seeds and summaries are published. Large raw Monte Carlo arrays may be excluded if their generator and summary hashes are retained.

### 4.3 Clean-room environments

Use two independent release checks:

1. **CPU result-replay environment:** new environment, no developer cache assumed, installs the public package/repository and regenerates all headline tables/figures from evidence artifacts.
2. **Inference environment:** fresh GPU environment only if necessary, downloads exact base and adapter revisions and runs a small licence-safe fixture set. It does not repeat paid training.

The person executing the final replay records commands and unexpected interventions. A run that required an undocumented manual correction does not pass.

### 4.4 Independent review target

Before public claims, obtain at least one review from a technically competent reader if available. Their role is to challenge:

- whether claim wording matches the certificate;
- whether test data influenced training, scoring or selection;
- whether the shift limitation is prominent;
- whether a new user can execute the quickstart;
- whether negative/null results are represented faithfully.

External review is desirable, not a pretext to publish without the automated gates if nobody is available. Self-review must be documented when independent review is unavailable.

---

## 5. Release engineering

### 5.1 Versioning and release candidate

The first public research release is `v0.1.0` if the package/API is coherent. Otherwise publish a dated research release such as `research-evidence-2026-xx-xx` and postpone semantic package versioning.

Release sequence:

1. freeze the release-candidate commit and evidence ID;
2. build source/wheel artifacts if packaging is ready;
3. generate checksums, software bill of materials where practical, cards and report;
4. run V1–V11 against the candidate;
5. draft—not publish—the GitHub release and attach the evidence bundle;
6. stage Hub repositories privately and prepare Kaggle assets privately/draft where supported;
7. perform a final URL, licence and claim-ledger review;
8. publish in the order in Section 11;
9. run V12 from a fresh environment;
10. record any correction as a new version; never silently replace immutable evidence.

If repository settings support immutable GitHub releases, enable immutability only after all intended assets are attached and the draft is complete.

### 5.2 Package publication decision

PyPI publication is conditional, not a vanity requirement. Publish the `conformalextract` package only if:

- the distribution name is available and not misleading;
- public APIs have docstrings and typed examples;
- CPU dependencies are separated from optional training/GPU extras;
- wheel and source distribution install in clean environments;
- import, CLI and fixture tests pass;
- licence metadata matches repository files;
- no model weights, raw restricted text or secrets enter the package.

Until then, the canonical install can be a pinned Git tag. The useful public object is the evaluator/certifier, not a rushed package badge.

### 5.3 Dependency and supply-chain hygiene

- pin model and dataset revisions rather than floating `main`;
- lock or constrain Python dependencies and record platform variants;
- use safe tensor formats for released adapter weights where supported;
- scan repository and built artifacts for secrets;
- generate dependency/vulnerability reports and explain unresolved findings;
- store credentials only in environment/secret facilities;
- test downloads and verify cache/files against expected hashes;
- never commit Hugging Face or Kaggle tokens.

---

## 6. Hugging Face publication contract

### 6.1 Evidence Dataset repository — default public contribution

`conformalextract-evidence` contains only artifacts whose redistribution has passed Gate 0 and V8. Expected contents:

- manifest and claim ledger;
- aggregate result tables and figure data;
- configuration files and schema definitions;
- licence-safe synthetic or author-created fixtures;
- calibration/final prediction-and-score artifacts only if their text/content is legally redistributable;
- otherwise, derived non-reconstructive statistics plus scripts that licensed users can run locally;
- notebook inputs and expected output hashes;
- dataset card with provenance, structure, licences, limitations and responsible-use notes.

**Default rule:** do not upload raw RAMS or WikiEvents documents, annotations, prompts containing recoverable source text, or model outputs that reproduce restricted text unless the exact redistribution right is documented. “Publicly downloadable” is not treated as “free to republish.”

### 6.2 Adapter Model repository — conditional

If approved, the model repository contains the PEFT adapter and tokenizer/config deltas only—not an unnecessary copy of the base model. Its model card records:

- exact `base_model` and immutable revision;
- `library_name: peft` and compatible Transformers/PEFT versions;
- training-data names, provenance and access requirements without redistributing restricted data;
- QLoRA configuration, seed, token count, hardware, duration and cost;
- intended use: research on structured event extraction and selective reliability;
- out-of-scope use: open-domain factual authority, safety-critical automation or implied robustness under shift;
- evaluation tables linked to the immutable evidence release;
- certificate scope, infeasibility semantics and shift limitation;
- known failure taxonomy, bias/ethical considerations and citation;
- licence chosen only after code/base/data/adapter-output compatibility review.

If the adapter cannot be released, publish its reproducible lineage and evaluation evidence without weights and state the reason plainly.

### 6.3 Collection and optional Paper Page

Create one Hugging Face Collection linking the evidence dataset, adapter if public, GitHub release, and any later Space or paper.

The technical report can be public on GitHub without arXiv. A Hugging Face Paper Page is created only after a genuine arXiv submission/identifier exists. No placeholder arXiv ID, fabricated publication status or fake peer-review implication is allowed.

### 6.4 Hub verification

Use the current `hf` CLI, not the deprecated `huggingface-cli`, for authenticated upload and fresh-download checks. The release record captures:

- authenticated namespace check;
- exact commit/revision after upload;
- uploaded file inventory and hashes;
- `hf cache verify` or equivalent file verification where supported;
- a download-and-replay test from a clean cache;
- public card rendering and link checks.

Large-folder upload is used only when the evidence bundle genuinely requires it. A private staging repository is preferred until V1–V11 pass.

---

## 7. Kaggle contribution contract

### 7.1 Contribution choice

Kaggle will not be a redundant model mirror by default. Its distinctive contribution is an accessible, CPU-compatible learning artifact:

- a versioned **ConformalExtract certification evidence** dataset; and
- a notebook that explains and reruns the selective-risk certificate, result comparison and shift caveat.

This makes the work useful to practitioners who cannot reproduce QLoRA training.

### 7.2 Notebook requirements

The notebook must:

- execute top to bottom in a clean Kaggle CPU session;
- pin the evidence dataset version;
- require no private API token for public replay;
- install only necessary, versioned dependencies;
- validate manifest hashes before analysis;
- reconstruct the headline certificate/table/figure, not merely display saved images;
- explain `alpha`, `delta`, selected risk, acceptance and `Infeasible` in plain language;
- show the conservative audit next to the preferred certifier;
- label the shift result as an uncertified stress test;
- state what cannot be reconstructed because of licence restrictions;
- finish within a declared CPU memory/time budget;
- contain no claims absent from the claim ledger.

### 7.3 Kaggle upload and validation

Use `kagglehub.dataset_upload` for the evidence dataset with version notes and ignore rules. A model upload is optional only if the adapter is already public, licence-compatible and valuable to Kaggle users.

Notebook publication uses the currently supported Kaggle workflow/API or UI rather than assuming KaggleHub alone publishes notebooks. After publication, rerun against the public dataset version and record the notebook URL, version and successful output in the manifest.

### 7.4 Kaggle quality bar

- concise title, subtitle and dataset description;
- clear provenance/licence for every file class;
- data dictionary and schema examples;
- meaningful tags without keyword stuffing;
- version notes tied to the GitHub/Hub release ID;
- no leader-board optimization or invented benchmark ranking;
- comments/questions redirected to reproducible issues where appropriate.

---

## 8. Technical report and research record

### 8.1 Working title and contribution statement

Working title:

> **Can QLoRA Make Structured Extraction Certifiable? Risk-Controlled Event Extraction Under Schema Shift**

The report's contribution is conditional on results, but its structure is fixed:

1. problem and falsifiable question;
2. relationship to structured event extraction, QLoRA and conformal/selective risk control;
3. same-backbone ZS/FS/QA systems and leakage controls;
4. grounded evaluator, document loss and confidence score;
5. finite-sample certificate, conservative audit and assumptions;
6. preregistered in-domain comparisons;
7. frozen transfer under schema/dataset shift;
8. results, uncertainty and failure taxonomy;
9. compute/cost and reproducibility;
10. limitations, ethics, licences and future work.

### 8.2 Result-writing rules

- report absolute estimates, bounds and denominators before adjectives;
- distinguish observed risk, certified upper bound and target risk;
- distinguish empirical acceptance from its certified lower bound;
- state `Infeasible` rather than deleting a system/threshold;
- write the QA–ZS primary decision before exploratory analyses;
- label QA–FS secondary confirmatory;
- separate in-domain certificate claims from shift observations in headings and captions;
- include null and adaptation-harms results in the abstract if they are the principal result;
- do not call a preprint peer reviewed;
- do not claim state of the art without a valid comparable benchmark review.

### 8.3 Publication ladder

1. versioned GitHub technical report with evidence release;
2. Hugging Face/Kaggle artifacts linked to that version;
3. optional Zenodo/DOI archive if useful and metadata/licences are ready;
4. optional arXiv submission after the report, authorship and evidence receive adequate review;
5. Hugging Face Paper Page only after an arXiv ID exists;
6. future workshop/journal submission only if the result and novelty justify it.

Authorship follows actual intellectual and writing contributions. Tools and assistance are acknowledged according to venue policy; citations are never replaced by model-generated summaries.

### 8.4 Route Y preservation

Route Y remains a named, separate follow-on in the report's future-work and project decision record:

> Extend the reliability question from parameter adaptation to training-data correction, testing whether corrected supervision improves certified acceptance rather than only average task metrics.

The preserved Route Y research is not copied into ConformalExtract results, presented as completed, or allowed to blur Route Z's causal comparison. Its notes remain reusable for a future repository/project plan.

---

## 9. Responsible release, licences and privacy

### 9.1 Licence matrix

Before staging, maintain one matrix covering:

| Artifact class | Questions that must be resolved |
|---|---|
| source code | original/third-party code, compatible notices, chosen repository/package licence |
| base model/tokenizer | access terms, derivative/adaptor obligations, attribution |
| adapter | interaction of base terms, code licence, training-data restrictions and intended distribution |
| datasets/annotations | access versus redistribution, required citations, derivative-output constraints |
| predictions/prompts | whether source passages are reconstructive or contain restricted/private text |
| report/figures | citation, image/table rights and chosen document licence |
| synthetic fixtures | generation/source record and absence of copied protected text |

Ambiguity resolves to omission from the public bundle, not optimistic publication. The manifest can record a private artifact hash without exposing the artifact.

### 9.2 Privacy, safety and misuse

- audit fixtures and outputs for personal or sensitive information;
- never publish credentials, local paths containing secrets or cloud billing data beyond aggregate cost;
- document hallucinated roles, entity confusion and abstention failure modes;
- state that event extraction output requires domain review and is not a factual database by default;
- do not market finite-sample statistical control as semantic truth, fairness certification or safety approval;
- provide a security contact/process in `SECURITY.md` without promising unsupported response service levels.

### 9.3 Corrections and withdrawal

If a material post-release error is found:

1. open or record the issue promptly;
2. mark affected claim IDs as disputed;
3. preserve the historical release where platform policy allows;
4. publish a corrected version with explicit version notes;
5. update cards/notebooks/CV wording and cross-links;
6. withdraw an artifact if licence/privacy requires it and retain a non-sensitive audit note.

---

## 10. Documentation and contribution design

### 10.1 README order

The README should answer in this order:

1. What question does ConformalExtract test?
2. What was the outcome and evidence status?
3. What does “certified” mean—and not mean?
4. How can a CPU user replay the result in minutes?
5. How can a licensed-data user rerun evaluation or training?
6. What artifacts exist on GitHub, Hugging Face and Kaggle?
7. What are the limitations, especially under shift?
8. How can someone contribute or cite the work?

The abstract and results banner are generated/reviewed against the claim ledger.

### 10.2 Public extension points

The library should make useful contributions possible without editing core logic:

- new extraction schemas and dataset adapters;
- alternative bounded document losses;
- alternative confidence-score plugins;
- certifier implementations that satisfy a common result interface;
- evaluation-only support for additional open models;
- schema-shift stress tests;
- future ACI experiments clearly separated from static certification.

`CONTRIBUTING.md` includes environment setup, test commands, fixture rules, licence requirements, statistical-test expectations and a statement that new methods cannot inherit “certified” wording without verified assumptions.

### 10.3 Initial issue backlog

After release, seed only genuine, bounded issues such as:

- add a licence-safe synthetic end-to-end tutorial dataset;
- implement an additional conservative bound behind the same interface;
- add a new schema mapper with golden fixtures;
- reproduce the evidence notebook on another OS/Python version;
- investigate online ACI as a separately scoped follow-on.

Labels such as `good first issue` are used only when the task is truly self-contained and documented.

---

## 11. Publication order and rollback points

### Stage R0 — evidence freeze

- Plans 1–3 implementation checklists pass or the release is explicitly reduced in scope.
- Freeze commit, evidence ID, claim ledger and candidate artifact hashes.
- No result-changing edits after this point without a new candidate.

### Stage R1 — local and clean-room candidate

- Run V1–V11.
- Render and inspect the report, cards and notebook.
- Resolve or disclose every failure.

**Rollback:** return to a new candidate; do not edit frozen evidence in place.

### Stage R2 — private/draft staging

- Draft GitHub release with assets.
- Upload private Hugging Face evidence/model candidates.
- Prepare Kaggle dataset/notebook candidate.
- Populate provisional cross-links and perform licence/claim review.

**Rollback:** delete/replace private drafts and generate a new manifest version.

### Stage R3 — public canonical release

1. publish GitHub tag/release and canonical report;
2. publish Hugging Face evidence Dataset, then adapter if approved;
3. publish/update the Hugging Face Collection;
4. publish Kaggle evidence Dataset and notebook;
5. update all cross-links and manifest URLs;
6. optionally publish PyPI after package gates;
7. optionally archive/submit the report only after its separate review.

### Stage R4 — public verification

- fresh/anonymous installation and download;
- verify public hashes/revisions;
- execute quickstart and Kaggle notebook;
- check rendered cards, report and links;
- record V12 in a small post-release verification amendment.

**Rollback/correction:** documentation-only mistakes receive a traceable patch; result, licence or artifact errors require a new release and correction notice.

---

## 12. Portfolio consolidation

### 12.1 Positioning

ConformalExtract is the portfolio's **modern-ML reliability research** project. It should complement—not masquerade as—the data-engineering projects by demonstrating:

- same-backbone experimental design;
- parameter-efficient LLM adaptation;
- finite-sample selective reliability;
- leakage-safe evaluation under schema shift;
- cost-aware reproducibility and public artifact stewardship.

The strongest story is disciplined decision-making under uncertainty, not merely “fine-tuned an LLM.”

### 12.2 Outcome-conditional CV bullets

Only one evidence-matched version is used after results.

**Positive boundary-crossing result**

> Built ConformalExtract, a Qwen3-4B QLoRA event extractor with finite-sample selective-risk control; under a preregistered document-grouped comparison, increased certified acceptance by **[verified value] pp** versus zero-shot at risk target **[alpha]**, with reproducible GitHub/Hugging Face/Kaggle evidence.

**Accuracy-only result**

> Built and preregistered a same-backbone QLoRA reliability study for document-level event extraction; showed that **[verified task gain]** did not yield a material certified-acceptance gain at **[alpha]**, and released the evaluator, certifier and CPU reproduction assets.

**Infeasible/null result**

> Developed an open finite-sample certification toolkit for structured LLM extraction and identified the sample-size/risk regime in which zero-shot, few-shot and QLoRA systems could not support a non-vacuous certificate, with reproducible negative-result evidence.

**Shift-failure result**

> Measured how a frozen in-domain selective extraction policy degraded under schema/dataset shift, separating valid in-domain guarantees from uncertified transfer and publishing a reusable stress-test workflow.

Numbers, links and adjectives remain placeholders until their claim IDs are verified.

### 12.3 Interview walkthroughs

Prepare three evidence-consistent versions:

- **60 seconds:** problem → why ordinary F1 was inadequate → intervention → honest result.
- **3 minutes:** same-backbone baselines → leakage controls → document loss/certificate → outcome/shift → public contribution.
- **10 minutes:** data and evaluator contract → QLoRA budget → theorem-to-code checks → ordered label opening → failure taxonomy → release architecture.

Each version includes one limitation and one decision that prevented overclaiming.

### 12.4 GitHub/profile presentation

- pin ConformalExtract only after the public quickstart works;
- use one architecture/evidence graphic, not a badge wall;
- surface the result status and limitations above training details;
- link to one canonical release and one replay notebook;
- keep Route Y in future work, not as an unfinished promise on the landing page;
- describe all prior/team/dissertation boundaries accurately.

---

## 13. Six-track Plan 4 responsibilities

| Track | Plan 4 responsibility | Exit artifact |
|---|---|---|
| Research / novelty | claim ledger, report, related-work boundary and outcome wording | versioned technical report |
| Data / grounding | redistribution matrix, evidence dataset and data card | licence-safe evidence bundle |
| Model / adaptation | adapter lineage, inference replay and model card | verified adapter or documented non-release |
| Statistical reliability | certifier replay, simulations, audit and scoped claims | verified certificate/result package |
| Systems / reproducibility | clean installs, hashes, manifests, CI and release tag | reproducible GitHub release |
| Public contribution / release | Hub Collection, Kaggle notebook, contribution guide and portfolio artifacts | connected public contribution set |

---

## 14. Cost and operational boundary

Plan 4 does not require a standing GPU subscription.

Expected compute:

- CPU for tests, result replay, cards, report and Kaggle notebook;
- one short GPU inference verification only if the public adapter requires it;
- no full retraining unless a prior run is invalid and a new paid-run decision is explicitly made;
- no continuous endpoint, monitoring service or hosted application in the MVP.

Every paid action requires the existing prepaid/manual budget controls. Public storage duplication is minimized; large artifacts are kept in one canonical home with links elsewhere.

---

## 15. Failure and reduced-release paths

| Failure | Reduced but honest release |
|---|---|
| adapter licence blocks weights | code, lineage, aggregate evidence and replayable certificate without weights |
| source-data terms block predictions/text | synthetic fixtures, non-reconstructive aggregates and local rebuild scripts |
| preferred certifier fails verification | conservative verified method, renamed claims and full discrepancy report |
| training artifact is invalid | methods/tooling release without adaptation-result claim, or rerun only after explicit decision |
| no feasible policy | publish infeasibility boundary, simulator and diagnostics |
| Kaggle environment cannot run method | smaller validated CPU fixture or omit notebook until it can pass; never publish decorative output only |
| package API is immature | install from pinned Git tag; postpone PyPI |
| report not ready for arXiv | publish versioned technical report only |
| post-release claim error | correction version, disputed claim status and synchronized cards/CV updates |

The release is cancelled only when the remaining artifacts are misleading, unsafe, unlawful or not independently useful.

---

## 16. Open decisions and freeze points

| Decision | Default | Freeze point | Evidence |
|---|---|---|---|
| GitHub/Hub/Kaggle namespace | Ross's consistent public namespace | before private staging | account availability |
| package publication | conditional | after clean build/install | API/test readiness and name availability |
| adapter publication | conditional go/no-go | V8/V9 before staging | base/data/output licence and safety review |
| raw/derived evidence contents | minimum licence-safe bundle | Gate 0 licence decision + V8 | redistribution matrix |
| first release identifier | `v0.1.0` if package coherent; otherwise dated evidence release | R0 | packaging readiness |
| Kaggle model mirror | no by default | R2 | distinct user value and licence cleanliness |
| hosted Space | no for MVP | after public release | demonstrated need and zero/acceptable operating cost |
| PyPI | no until stable | R1 | wheel/sdist tests |
| DOI/Zenodo | optional | after R3 | citation need and metadata quality |
| arXiv/HF Paper Page | optional after evidence review | after R3 | report quality, authorship and genuine arXiv ID |
| independent reviewer | seek one | before R3 | availability; document self-review fallback |

None of these choices may strengthen claims beyond the verified ledger.

---

## 17. Acceptance checklist — Plan 4 is done when

### Direction acceptance now

- [x] Evidence before narrative is accepted as the release doctrine.
- [x] The evaluator/certifier, evidence bundle and CPU replay are the minimum contribution.
- [x] GitHub is canonical; Hugging Face and Kaggle have distinct, connected roles.
- [x] Raw source text and annotations are not assumed redistributable.
- [x] Adapter release is conditional on licence, safety and verification gates.
- [x] The paper-shaped report precedes any optional arXiv/HF Paper Page step.
- [x] Null, infeasible, adaptation-harms and shift-failure narratives are acceptable.
- [x] No hosted UI, continuous GPU bill or PyPI release is mandatory.
- [x] Route Y remains preserved as a separate future project.

### Evidence acceptance before public release

- [ ] Plans 1–3 implementation/evidence gates pass or the release scope is reduced explicitly.
- [ ] V1–V11 pass against one frozen release candidate.
- [ ] Manifest, checksums and claim ledger are complete and immutable for the release.
- [ ] Licence/provenance matrix permits every public artifact.
- [ ] CPU result replay regenerates all headline tables and figures.
- [ ] Adapter inference replay passes or adapter publication is removed.
- [ ] GitHub release, cards, notebook and report use identical approved claims.
- [ ] Limitations and uncertified shift transfer are prominent everywhere relevant.
- [ ] GitHub, Hugging Face and Kaggle drafts are cross-linked and inspected.
- [ ] Public V12 fresh-download verification passes and is recorded.
- [ ] CV/profile/interview wording points only to verified claim IDs.
- [ ] Corrections process, contribution guide and citation metadata are present.

Acceptance of this plan completes the **four-plan planning set**. It does not mark ConformalExtract implemented, verified, released, published or accepted by any venue.

### Acceptance addendum

**Date:** 2026-07-15  
**Trigger/evidence:** Ross explicitly accepted Plan 4.  
**Decision change:** The verification, release, research-reporting and portfolio-consolidation direction is accepted.  
**Scope impact:** The four-plan planning set is complete. All evidence-acceptance boxes above remain open until implementation produces and verifies the required artifacts.  
**Acceptance impact:** Work may proceed to Plan 1 Gate 0. This acceptance does not authorise paid training, sealed-label access, redistribution, public release or result claims before their respective gates pass.

---

## 18. Planning-set exit and implementation start

Once this direction is accepted, the project has four accepted sequential plans:

1. **Plan 1:** Foundations, Research Contract & Gate 0.
2. **Plan 2:** Data, QLoRA & Reproducible Training.
3. **Plan 3:** Certification & Schema-Shift Experiments.
4. **Plan 4:** Verification, Release & Research/Portfolio Consolidation.

Implementation begins at Plan 1 Gate 0—not at training and not at publication. The first operational milestone is the Gate 0 go/revise/stop evidence package. Full-data preparation, paid training and label opening remain blocked until their explicit gates pass.

---

## 19. Skills and current platform references

### 19.1 Skills applied

- **Hugging Face CLI:** used to define current `hf` upload, revision and verification workflows rather than deprecated commands.
- **Hugging Face paper publisher:** used to separate a GitHub technical report from an arXiv-dependent Hugging Face Paper Page.
- **GitHub workflow:** used to define draft-first, tagged and optionally immutable evidence releases.
- **OpenAI Library:** this plan and accepted-plan records are persisted as living project artifacts.
- **Handoff workflow:** preserved one concern per plan, explicit evidence gates, acceptance semantics and the deferred Route Y record.

### 19.2 Current primary platform references

- [Hugging Face model cards](https://huggingface.co/docs/hub/model-cards) — card metadata and responsible model documentation.
- [Hugging Face dataset cards](https://huggingface.co/docs/hub/datasets-cards) — dataset provenance, structure, limitations and responsible-use documentation.
- [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) — draft/tagged releases and immutable-release workflow.
- [KaggleHub](https://github.com/Kaggle/kagglehub) — versioned dataset/model upload and download mechanisms.

### 19.3 Limitations of this plan

- Platform commands, pricing, quotas and UI details may change; verify them immediately before publication.
- This is a release contract, not legal advice. Unclear redistribution rights require source/licence-owner confirmation or omission.
- A clean replay validates the released artifact path; it cannot prove that every third-party environment will behave identically.
- An arXiv identifier creates a paper page, not peer review.
- Public usefulness depends on documentation, maintenance and contributor response after launch; this plan cannot promise adoption.
