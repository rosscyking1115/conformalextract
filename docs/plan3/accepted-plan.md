# ConformalExtract — Plan 3: Certification & Schema-Shift Experiments

> **Purpose:** run one predeclared, document-grouped comparison of zero-shot, few-shot and QLoRA selective extraction; determine whether adaptation crosses a non-vacuous certification boundary; and measure—without overstating—what happens when the frozen policy is transferred under schema or dataset shift.
>
> **Owner:** Ross (Cheng-Yuan King) · **Date:** 2026-07-15 · **Status:** Direction accepted; implementation pending and experiments gated by Plans 1–2 · **Document type:** living research plan

**Inherited & locked:** Plans 1 and 2 are accepted. The three systems are ZS, FS and QA on the same pinned 4-bit `Qwen/Qwen3-4B-Instruct-2507` inference stack. QA is one rank-16, alpha-32, dropout-0.05, all-linear NF4 QLoRA adapter selected without calibration or final labels. The prediction task, grounded evaluator, source-document grouping, bounded document loss, primary confidence score, target risk `alpha`, failure probability `delta`, minimum acceptance floor and certification method are frozen by Gate 0. Calibration, final in-domain and shift labels are sealed from training and score construction. Static in-domain guarantees are not described as valid under shift.

---

## 1. Executive experimental decision

Plan 3 answers one question before all others:

> At the same target risk and confidence level, does QLoRA yield a materially higher **certified acceptance** than zero-shot and few-shot prompting?

The headline object is not raw F1, expected calibration error or the best-looking point on a risk–coverage plot. For each frozen system, define:

> **Certified acceptance** = the largest simultaneously valid lower bound on acceptance among predeclared policies whose finite-sample upper bound on selected document risk is no greater than `alpha` and whose acceptance meets the predeclared floor.

The primary comparison is QA versus ZS. QA versus FS is the second confirmatory comparison. The minimum material advantage is a planning default of **5 percentage points** in certified acceptance; Gate 0 may change that value only before certification and with a sample-feasibility rationale.

After the in-domain policies are frozen, transfer each threshold unchanged to the shift set. The shift result is a stress test of transportability. Unless a separate theorem and valid design say otherwise, it carries no finite-sample in-domain guarantee.

---

## 2. What counts as certification

### 2.1 Accepted public meaning

“Certified” means all of the following:

- the loss is bounded and predeclared;
- the independent unit is the source-document group;
- the predictor, score, candidate grid and user parameters are independent of the certification split;
- adaptive policy selection is covered by the chosen finite-sample procedure;
- the procedure can return **Infeasible**;
- the reported risk and acceptance statements match the verified theorem and code;
- the guarantee is explicitly scoped to exchangeable in-domain deployment units.

An empirical risk below `alpha`, a bootstrap interval, ECE, temperature scaling or a threshold tuned on calibration labels without simultaneous correction is not the headline certificate.

### 2.2 Primary method branch

The preferred Gate 0 outcome is a verified specialization of the 2026 **joint finite-sample selective conformal risk-control** construction:

- bounded, possibly non-monotone document loss;
- a finite candidate grid fixed without certification labels;
- a simultaneous upper bound on selected risk;
- a simultaneous lower bound on acceptance;
- valid adaptive selection from the certified feasible set;
- deterministic `Infeasible` when no policy qualifies.

Because ConformalExtract has a fixed output policy and one abstention score, the paper's multi-parameter construction may be specialized to one fixed output parameter plus a score threshold. The theorem-to-code note must prove that this specialization and the desired “max certified acceptance” selector remain covered.

### 2.3 Conservative audit branch

Independently implement a simpler conservative comparator:

- the candidate grid is fixed from development data;
- one-sided bounded-loss risk bounds and binomial acceptance bounds are computed with a simultaneous correction over all system–threshold candidates;
- the same deterministic selection and `Infeasible` semantics are used;
- all constants and failure-budget allocation are explicit.

This audit is expected to be looser. Its purpose is to expose implementation errors and show how much feasibility comes from the chosen variance-adaptive method rather than from hidden threshold selection.

If the preferred method fails Gate 0 reproduction or does not validly support the selected object, the conservative verified method becomes primary and the project title/claims are adjusted precisely. The work must never keep “conformal” as branding after the mathematics has been replaced by an unrelated heuristic.

### 2.4 No claim transfer under shift

The in-domain certificate assumes exchangeability/i.i.d. at the declared document-group unit. Cross-dataset and held-out-schema transfer intentionally challenge that assumption.

Under shift, report:

- empirical selected risk and uncertainty;
- acceptance and uncertainty;
- excess risk above `alpha`;
- static threshold violation status;
- confidence-score and loss-distribution movement;
- the direction and size of degradation.

Do not label the transferred point “certified.” Adaptive conformal inference is a future extension because it needs sequential feedback and offers a different, often asymptotic, guarantee.

---

## 3. Frozen data roles and opening protocol

### 3.1 Role sequence

| Order | Role | Permitted action | Forbidden action |
|---:|---|---|---|
| 1 | Training | fit QA adapter; build FS demonstration bank | inspect calibration/final/shift labels |
| 2 | Development | choose prompt, checkpoint, score and candidate grid | certify or report final evidence |
| 3 | Certification | run the fixed certifier once per frozen analysis version | invent scores, alter systems or tune targets |
| 4 | Final in-domain | evaluate selected policies once | recalibrate or replace thresholds |
| 5 | Shift | transfer frozen policies and run stress analyses | repair the in-domain policy using shift labels |

Every opening produces an append-only access record with timestamp, user/process, Git SHA, manifest hash, purpose and generated artifact hashes.

### 3.2 Certification-split preflight

Before labels are read, assert:

- all ZS/FS/QA predictions exist for the identical group IDs;
- system, adapter, prompt, tokenizer, model, decoding and score hashes match the frozen manifests;
- no group/hash overlaps train or development roles;
- the candidate grid and deterministic tie order are already committed;
- `alpha`, `delta`, acceptance floor and the delta ledger are already committed;
- the certifier passes synthetic coverage tests at the current Git SHA;
- the final and shift manifests remain inaccessible to the calibration command.

Any failure stops certification and records an invalid attempt. It does not silently overwrite the split.

### 3.3 Final-test opening rule

Open the final in-domain labels only after:

- the certification result is immutable;
- exactly one policy per system is selected or marked infeasible;
- primary hypotheses and minimum effect are frozen;
- tables/figure schemas are prepared with placeholder values;
- all code runs against synthetic fixtures.

Final test results audit transport from certification to a fresh in-domain sample. They do not select a different threshold.

### 3.4 Shift opening rule

Open shift labels only after final in-domain artifacts are checksummed and the preferred shift definition is locked from Gate 0:

1. compatible RAMS-to-WikiEvents cross-dataset subset where defensible;
2. otherwise event-type/schema combinations excluded from training and in-domain certification;
3. topic/source shift only where stable metadata supports it.

---

## 4. Analysis population and statistical unit

### 4.1 Independent unit

The source-document group is the unit for certification, bootstrap resampling and paired comparisons. If a source document contains multiple target frames, the primary group loss is the mean bounded frame loss declared in Plan 1.

The strict sensitivity analysis uses maximum frame loss per document. It does not replace the primary result because it looks stronger or weaker.

### 4.2 Policy action

A policy accepts or abstains at the declared deployment unit. If confidence is computed per event frame while certification is document-grouped, the group acceptance rule must be frozen—for example, accept the document only when every target frame meets its score threshold.

The exact rule must be the same across ZS, FS and QA and must not count some frames from a document as independent accepted samples.

### 4.3 Primary population

The headline population is the frozen in-domain final split after all accepted eligibility rules. Exclusions are permitted only for predeclared source corruption or task-contract impossibility and are reported by system-independent reason.

Model parse failures, schema failures, ungrounded spans and empty predictions are outcomes with maximum/default loss, not exclusion reasons.

### 4.4 Shift population comparability

For cross-dataset transfer, publish an ontology crosswalk with:

- exact/shared event types and roles;
- renamed but semantically equivalent labels;
- partially overlapping or ambiguous labels;
- excluded labels and rationale;
- support counts before and after mapping.

The primary cross-dataset result uses only mappings accepted before labels are scored. A broader/fuzzier crosswalk may appear as sensitivity analysis but cannot replace it post hoc.

---

## 5. Losses, score and candidate policies

### 5.1 Primary loss

Use the Gate 0-frozen bounded loss, expected to be:

> `L_doc = 1 - grounded_argument_F1_doc`, in `[0,1]`, with parse, schema or grounding failure assigned `1`.

The evaluator version and empty-gold/empty-prediction convention are part of the loss hash. No LLM judge appears in this path.

### 5.2 Secondary strict loss

Report the predeclared binary strict-failure loss from Plan 1. It receives an exact/binomial-style interval where appropriate, but it is not substituted as the headline when continuous grounded F1 is inconvenient.

### 5.3 Primary confidence signal

Use exactly the score frozen by Gate 0 from development-only analysis. Candidate score invention ends before certification.

For every prediction, retain:

- raw token transition scores;
- derived field/frame/document score;
- structural/grounding penalty status;
- score implementation/version hash.

Parse/schema/grounding failure receives the frozen worst-confidence treatment. Score orientation is tested: one declared direction must mean “more acceptable.”

### 5.4 Threshold grid

Construct each system's finite threshold grid from development-score quantiles plus explicit boundary policies such as always-answer and abstain-all, subject to the certification theorem's sample-size/grid-size condition.

Rules:

- grid hashes are committed before certification labels open;
- grid size is chosen by Gate 0 feasibility, not by final performance;
- ties use one deterministic ordering;
- no threshold is added after observing calibration risk;
- abstain-all may be represented for diagnostics but cannot satisfy the minimum acceptance floor.

### 5.5 Global multiplicity object

Treat the candidate family as:

> `{ZS, FS, QA} × {their frozen thresholds}`

The theorem-to-code note must show how the failure budget covers adaptive selection across thresholds and across the three systems. If the preferred procedure is only valid within one system, allocate `delta` across the three system families in a predeclared way or use the verified global conservative construction.

---

## 6. Feasibility before certification

### 6.1 Base-risk diagnostic

For each system, use development data to compute the always-answer base risk and its uncertainty. The deterministic decomposition implies that when base risk exceeds `alpha`, any valid selective policy must abstain substantially; in population form a common diagnostic lower bound is:

> minimum abstention ≥ `(base_risk - alpha) / (1 - alpha)` when `base_risk > alpha`.

This is a feasibility diagnostic, not the final certificate. Its uncertainty and finite-sample version must be reported.

### 6.2 What the diagnostic decides

- **QA lower bound materially below ZS/FS:** adaptation may genuinely move the certifiability frontier.
- **all systems already below `alpha`:** certification may be trivial; the contribution becomes acceptance/efficiency and strict-loss behavior.
- **all systems far above `alpha`:** expect heavy abstention or infeasibility; do not relax `alpha` after seeing certification.
- **QA worse than baselines:** proceed as a valid negative intervention unless a pipeline defect is found.

### 6.3 Risk-target sweep boundary

The single frozen `alpha` is confirmatory. A small, predeclared sweep—such as `0.10`, `0.20`, `0.30` if Gate 0 supports it—may be reported as **secondary feasibility analysis** with simultaneous correction or clearly descriptive status.

The headline target never changes because a neighbouring target certifies more systems.

---

## 7. Certification algorithm and outputs

### 7.1 Per-candidate quantities

For every frozen system–threshold candidate, compute at the document-group unit:

- accepted count and fraction;
- lower confidence bound on population acceptance;
- selected mean bounded risk;
- upper confidence bound on selected risk;
- accepted-loss variance and effective accepted sample size;
- any utility quantity required by the verified method;
- all bound components and allocated failure probabilities.

Pairs with zero accepted units, insufficient accepted count or failed theorem preconditions are **ineligible**, not zero-risk.

### 7.2 Feasible set

A candidate is certified feasible only if:

- risk UCB `<= alpha`;
- acceptance LCB `>= p_min`;
- all method-specific sample-size/eligibility requirements pass;
- no data, score or manifest validation failed.

If a system has no feasible candidate, return `Infeasible` for that system. Do not select its empirically lowest-risk point and call it certified.

### 7.3 System selector

For each system, select the feasible candidate with the largest acceptance LCB. Ties follow the precommitted threshold order, preferring the less complex/more conservative policy where the method requires it.

This selector is used only if the theorem-to-code audit verifies simultaneous coverage for that post-selection rule. Otherwise use the accepted method's native selector and adjust the headline wording.

### 7.4 Certification artifact

Write one immutable `certification_result.json` containing:

- method name/version and theorem reference;
- system and prediction-manifest hashes;
- certification split/group hash and `n`;
- score/grid/config hashes;
- `alpha`, `delta`, acceptance floor and delta ledger;
- every candidate's raw statistics and bound components;
- feasibility status/reason;
- selected threshold/policy or `Infeasible`;
- risk UCB and acceptance LCB;
- conservative-audit result;
- execution environment, Git SHA, timestamp and output checksum.

The public evaluator must be able to reproduce this JSON from licence-safe fixtures and from user-provided prediction/gold files.

---

## 8. Primary comparison and decision rules

### 8.1 Derived system quantity

For system `s`, define:

> `CA_s = max acceptance_LCB(s, threshold)` among certified feasible candidates; otherwise `CA_s = Infeasible`.

This makes the comparison certificate-aware: a high empirical acceptance with an invalid risk bound does not win.

### 8.2 H1 — QA versus zero-shot

H1 is supported only if:

- QA is feasible;
- `CA_QA >= CA_ZS + delta_material`, where the planning default `delta_material = 0.05`;
- QA's selected policy remains at or below the frozen risk target under its certification UCB;
- final in-domain empirical behavior does not reveal a pipeline-invalidating contradiction.

If QA is feasible and ZS is infeasible, record a boundary-crossing result; do not invent a numerical difference from `Infeasible`.

### 8.3 H2 — QA versus few-shot

Apply the identical rule to QA versus FS. H2 is secondary confirmatory: failure against a strong few-shot baseline is not hidden even if H1 succeeds.

### 8.4 Interpretation matrix

| Certification pattern | Interpretation |
|---|---|
| QA feasible; ZS and FS infeasible | clearest adaptation-crosses-boundary evidence |
| all feasible; QA materially higher | adaptation improves useful certified participation |
| all feasible; QA difference < 5 pp | no material certifiability gain at the frozen target |
| QA and FS similar; both beat ZS | task examples and adaptation both help; QLoRA advantage over prompting unsupported |
| QA infeasible; baseline feasible | adaptation harmed certifiability |
| all infeasible | meaningful feasibility/impossibility result at the chosen model, score, data and target |
| QA higher raw F1 but not `CA` | adaptation improved average task quality without crossing the certification boundary |

### 8.5 No post-hoc rescue

Do not rescue a failed hypothesis by:

- changing `alpha`, `delta`, acceptance floor or loss;
- switching to a secondary score;
- choosing a different QLoRA checkpoint;
- excluding hard event types;
- reporting only empirical rather than certified acceptance;
- replacing exact/grounded evaluation with an LLM judge.

Such analyses may appear as labelled exploratory work if predeclared and multiplicity-aware, but they cannot change the primary conclusion.

---

## 9. Final in-domain evaluation

### 9.1 Frozen-policy audit

Apply each selected threshold unchanged to the final in-domain predictions and report:

- empirical acceptance;
- empirical selected risk;
- grounded exact/normalized F1 among accepted and over all documents;
- parse, schema and unsupported-span rates;
- strict failure rate;
- accepted document count;
- realized gap from certification estimates/bounds.

An infeasible system remains infeasible; its descriptive risk–coverage curve may be plotted but no test threshold is selected.

### 9.2 Paired uncertainty

Use a source-document-group paired bootstrap with a frozen seed and predeclared number of replicates, planning default `2,000`, for descriptive 95% intervals on:

- QA–ZS and QA–FS difference in mean bounded loss;
- difference in empirical acceptance at selected policies;
- difference in accepted-output risk where both systems accept enough comparable groups;
- grounded F1 and unsupported-span differences.

The bootstrap supports effect-size interpretation. It does not replace the finite-sample certificate.

### 9.3 Risk–coverage curves

Plot the complete frozen threshold family for each system:

- x-axis: acceptance/coverage;
- y-axis: empirical selected risk;
- horizontal target-risk line;
- selected certified point with risk UCB and acceptance LCB;
- infeasible candidates visibly distinguished;
- uncertainty based on document groups.

Only the predeclared selected point receives the headline certified label.

### 9.4 Sanity baselines

Include:

- always answer;
- random abstention matched to each selected acceptance rate, repeated with fixed seeds;
- heuristic empirical-risk threshold selected on development without a certificate.

These show whether the confidence score meaningfully orders risk and what formal certification costs in acceptance. They are not additional trained models.

---

## 10. Schema and dataset shift stress test

### 10.1 Static transfer experiment

For every system feasible in-domain:

1. keep model, adapter, prompt, score and threshold fixed;
2. apply the exact in-domain policy to the shift population;
3. compute empirical risk, acceptance and grouped uncertainty;
4. record whether empirical risk exceeds `alpha` and by how much;
5. explicitly label the result **uncertified under shift**.

For an in-domain-infeasible system, report descriptive shift behavior without implying it had a transferable policy.

### 10.2 Primary shift outcomes

- `risk_shift - risk_in_domain`;
- `accept_shift - accept_in_domain`;
- `risk_shift - alpha`;
- change in score–loss rank association;
- change in always-answer base risk and feasibility lower bound;
- proportion of event types/roles for which risk worsens;
- parse/schema/grounding failure decomposition.

### 10.3 Shift severity descriptors

Report without claiming causality:

- event-type and role-frequency divergence;
- seen versus unseen schema coverage;
- source-document/token length shift;
- arguments-per-frame and frames-per-document shift;
- cross-sentence argument-distance shift;
- score distribution movement;
- base-risk movement.

### 10.4 Optional shift recalibration diagnostic

Only if the shift set has enough independent groups, split it into a shift-calibration and untouched shift-test subset and ask:

> Could a new in-domain-style certificate be established after collecting labelled target-domain data?

This is a separate target-domain recalibration diagnostic, not transfer. It cannot retroactively validate the static threshold. If sample size is insufficient, report that limitation rather than pooling events/fields.

### 10.5 ACI exclusion from the MVP

Adaptive conformal inference is not part of the primary project because it assumes sequential feedback/verification and provides a different control statement. It is a named future extension after the static failure mode is measured.

---

## 11. Secondary and sensitivity analyses

### 11.1 Predeclared analyses

- mean document loss versus maximum-frame document loss;
- exact versus normalized grounded-span matching;
- binary strict-failure certificate/interval alongside continuous loss;
- primary score versus one simple completion-mean-NLL score, descriptive only unless jointly corrected;
- accepted-output quality by cross-sentence distance and argument count;
- effect of deterministic constrained decoding only if Plan 1 admitted it as a structural-validity ablation.

### 11.2 Subgroup reporting

Report event type, role, document-length quartile, cross-sentence distance and seen/unseen-schema results only where group counts meet a displayed minimum.

Subgroup intervals are exploratory unless a separate simultaneous procedure was predeclared. Rare subgroups show counts and raw outcomes; they are not merged opportunistically.

### 11.3 Calibration diagnostics

Use development/final data to report:

- score–loss Spearman association;
- AUROC/AUPRC for the predeclared strict-failure indicator;
- binned confidence/risk diagrams with counts;
- selective-risk curves.

ECE may be shown as a familiar diagnostic but is not the formal guarantee and must not be compared directly across incompatible score scales without explanation.

### 11.4 Multiplicity

- H1 and H2 are the only confirmatory system comparisons.
- All threshold adaptivity is handled inside the certification procedure.
- Secondary target sweeps, strict-loss and score analyses are simultaneous-corrected where a formal claim is made or explicitly labelled exploratory.
- Subgroup findings do not receive standalone significance claims based on uncorrected p-values.

---

## 12. Failure taxonomy and qualitative analysis

### 12.1 Machine-coded taxonomy

Assign every non-zero-loss prediction one or more deterministic categories:

- invalid JSON;
- schema-invalid key/type/role;
- hallucinated or ungrounded span;
- missing gold argument;
- extra grounded but incorrect argument;
- wrong role;
- boundary/normalization mismatch;
- duplicate argument;
- coreference/alias mismatch under policy;
- empty-output collapse;
- context-window evidence loss.

> **Scope amendment:** The reviewed [2026-07-30 certification-only scope addendum](section-12-1-certification-only-scope-addendum-2026-07-30.md) amends the population scope of the sentence introducing the list above — every non-zero-loss prediction in the already-open `certification` role, across `zs`, `fs` and `qa` — and leaves the eleven categories and their multi-label semantics unchanged. It additionally imposes, among other things, a fail-closed role guard, pinned input identities, a retain-uncertainty rule, required per-system reporting, and seven preconditions on any future execution against this section. It does not authorise execution.

> **Descoped 2026-10-27.** §12.1 was never executed and is descoped from Plan 3 by
> [Amendment 2 to the §11/§12 disposition](sections-11-and-12-disposition-amendment-2.md), on Ross's choice under
> close-chain review item S1-B1. It was computable at $0; the ground is that no live claim
> depends on it. Plan 3 makes no error-category claim. The text above is unchanged.

### 12.2 Manual audit sample

Create a frozen stratified sample before reading examples:

- 10 QA improvements over both baselines;
- 10 QA regressions;
- 10 high-confidence/high-loss accepted cases;
- 10 abstained low-loss cases;
- 10 shift-only failures;
- all categories sampled by source-document group without replacement where possible.

If fewer cases exist, report all. The audit explains failure mechanisms; it does not relabel gold data or alter the main metrics.

> **Disposed 2026-10-27.** Three strata are empty and two are computable but descoped; the
> sample is not constructed. Stratum by stratum in [Amendment 2](sections-11-and-12-disposition-amendment-2.md).

### 12.3 Error attribution limits

Use phrasing such as “associated with,” “concentrated in” or “consistent with.” Do not claim QLoRA caused a linguistic failure type from a few examples without a designed causal test.

---

## 13. Reproducibility and anti-leakage controls

### 13.1 Separate commands

Use distinct entry points with non-overlapping permissions:

```text
build-grid        # development only
certify           # certification labels only; writes immutable result
evaluate-final    # final labels; requires certification result hash
evaluate-shift    # shift labels; requires final result hash
render-report     # reads completed artifacts; no model calls
```

The commands validate prerequisite artifact hashes and refuse out-of-order execution.

### 13.2 Immutable analysis version

An analysis version binds:

- prediction manifests for all systems;
- data/group/split hashes;
- evaluator/loss/score hashes;
- candidate grids;
- certification config and delta ledger;
- Git commit and environment lock.

Any change creates a new version. Results from different versions are never mixed in one headline table.

### 13.3 Test expectations

- known synthetic risks produce expected feasible/infeasible decisions;
- zero acceptance never yields zero risk;
- monotone threshold fixtures produce ordered acceptance;
- grid permutation cannot change the result except the declared tie rule;
- document duplication within a group cannot increase independent `n`;
- delta allocations sum to at most the declared failure probability;
- serial/parallel execution produces identical JSON;
- QA/ZS/FS IDs align exactly;
- shift command cannot write or modify the in-domain certificate.

### 13.4 No GPU requirement for certification

After Plan 2 creates label-free prediction artifacts, certification, scoring, bootstrap and report rendering run on CPU. No remote GPU remains active merely to calculate statistics.

---

## 14. Result tables and figures frozen before final opening

### 14.1 Main tables

**Table 1 — systems and task quality before abstention**

- model/adapter ID;
- always-answer document loss and grounded F1;
- parse/schema/unsupported-span rates;
- inference cost/latency.

**Table 2 — in-domain certification**

- selected threshold;
- empirical accepted count/risk;
- risk UCB;
- empirical acceptance and acceptance LCB;
- `CA_s` and feasible/infeasible reason;
- conservative-audit result.

**Table 3 — final in-domain frozen-policy audit**

- empirical risk/acceptance and grouped intervals;
- grounded F1 and failure components;
- QA–baseline paired differences.

**Table 4 — static shift transfer**

- in-domain versus shift risk/acceptance;
- excess over target;
- shift descriptors;
- explicit “no transferred guarantee” status.

### 14.2 Main figures

1. risk–coverage curves with certified points;
2. certified acceptance comparison across ZS/FS/QA;
3. in-domain-to-shift risk/acceptance change;
4. failure-type composition for accepted errors;
5. optional score–loss diagnostics.

Figures are generated from machine-readable result JSON/Parquet/CSV, never manually edited values.

---

## 15. Claim language by outcome

### 15.1 Strong positive

Allowed only if the rules pass:

> On the frozen in-domain document distribution, the QLoRA system achieved a higher simultaneously certified acceptance than zero-shot/few-shot at the same bounded-risk target and confidence level.

### 15.2 Boundary crossing

> QLoRA produced a non-vacuous certified operating point where the same-backbone baseline was infeasible under the predeclared certificate.

### 15.3 Accuracy-only improvement

> QLoRA improved average grounded extraction quality but did not produce a material certified-acceptance gain at the frozen target.

### 15.4 Null/impossibility

> None of the tested systems supported a non-vacuous certificate at the chosen risk target and sample size; the feasibility analysis quantifies the abstention/sample boundary rather than claiming reliability.

### 15.5 Shift result

> The in-domain threshold did not retain its risk behavior under the tested schema/dataset shift. This is an empirical stress result, not a violation of an in-domain theorem whose exchangeability assumption no longer holds.

### 15.6 Forbidden language

- “guaranteed accurate” without scope;
- “safe under distribution shift”;
- “95% accurate with 95% confidence” unless that is literally the verified object;
- “distribution-free” without naming the exchangeability/unit assumptions;
- “QLoRA causes calibration” when the evidence is comparative;
- “state of the art” without a matched benchmark and complete comparison.

---

## 16. Six-track Plan 3 responsibilities

| Track | Plan 3 responsibility | Exit artifact |
|---|---|---|
| Research / novelty | test adaptation as the intervention and preserve null outcomes | hypothesis decision matrix and claim record |
| Data / grounding | enforce document grouping and interpretable ontology shift | frozen population manifests and crosswalk |
| Model / adaptation | compare immutable ZS/FS/QA systems | system/prediction hashes |
| Statistical reliability | valid adaptive certification, paired uncertainty and shift scoping | certificate JSON, audit and final/shift reports |
| Systems / reproducibility | ordered commands, immutable versions and CPU replay | analysis lock, tests and evidence manifest |
| Public contribution / release | reusable evaluator/certifier artifacts | draft result bundle for Plan 4 |

---

## 17. Experiment execution sequence

### Phase A — freeze the analysis

1. Confirm Plans 1–2 implementation gates and immutable systems.
2. Freeze loss, score, grid, target, confidence, participation floor and minimum material effect.
3. Complete theorem-to-code note and preferred/conservative synthetic validation.
4. Commit placeholder table/figure schemas and analysis version.

### Phase B — certify

1. Run certification preflight.
2. Open certification labels once.
3. Produce all candidate bounds and selected/infeasible policies.
4. Run conservative audit and reconcile discrepancies.
5. Checksum and lock certification artifacts.

### Phase C — final in-domain audit

1. Open final labels after certification lock.
2. Apply selected thresholds unchanged.
3. Produce paired uncertainty, risk–coverage figures and primary H1/H2 decisions.
4. Freeze the in-domain report and claim branch.

### Phase D — shift stress

1. Lock ontology crosswalk/shift definition.
2. Open shift labels.
3. Transfer policies unchanged and quantify risk/acceptance movement.
4. Run optional target-domain recalibration only if independently powered and clearly separated.
5. Freeze shift limitations and future ACI note.

### Phase E — failure analysis and handoff

1. Generate deterministic taxonomy counts and manual-audit sample.
2. Complete result tables/figures from machine artifacts.
3. Create the Plan 4 evidence manifest and public/private artifact decisions.
4. Verify no result depends on a post-test configuration change.

---

## 18. Risks and pre-agreed responses

| Risk | Signal | Response |
|---|---|---|
| Preferred theorem does not cover selector | theorem-to-code mismatch | use native selector or conservative verified branch; change wording |
| Certification set too small for grid | sample-size precondition fails | shrink predeclared grid using development only or return infeasible |
| No accepted samples | threshold accepts zero | ineligible; never record zero risk |
| All systems infeasible | no policy meets both bounds | publish the feasibility/null result; do not relax target post hoc |
| QA F1 rises but `CA` does not | task metric improves, certificate unchanged | report accuracy-only improvement |
| QA harms certifiability | QA infeasible/lower `CA` | report negative intervention; do not swap checkpoint |
| Preferred/audit certifiers disagree unexpectedly | feasibility/status mismatch beyond expected tightness | halt final opening and debug implementation |
| Final empirical risk exceeds target | rare realization, shift/leak/bug possibility | audit hashes/assumptions; report honestly; never recalibrate on final |
| Cross-dataset mapping is ambiguous | low shared ontology support | use held-out-schema primary shift; retain mapping as sensitivity only |
| Shift set too small | wide intervals/few groups | report descriptive counts; no target-domain recalibration claim |
| Subgroups invite cherry-picking | isolated positive cells | label exploratory and show all eligible groups |
| Bootstrap resamples frames not documents | suspiciously narrow intervals | fail test; resample source-document groups only |
| Test labels accessed out of order | access-log breach | invalidate analysis version and follow data-governance recovery |

---

## 19. Explicit non-goals

- No QLoRA retraining or checkpoint replacement in Plan 3.
- No new confidence model, learned verifier or LLM judge.
- No automatic score fusion unless Gate 0 had already frozen and validated it.
- No online ACI deployment in the MVP.
- No claim that static conformal validity transfers to unseen schemas/domains.
- No field/event count inflation of independent calibration sample size.
- No manual correction of model predictions.
- No leaderboard comparison against differently sized/proprietary models.
- No UI or hosted production service.
- No public release before Plan 4 verification and licence review.

---

## 20. Four-plan sequence

### Plan 1 — Foundations, Research Contract & Gate 0

Accepted; execution gates remain evidence-dependent.

### Plan 2 — Data, QLoRA & Reproducible Training

Accepted direction; implementation remains Gate 0-gated.

### Plan 3 — Certification & Schema-Shift Experiments (this document)

Freeze and run the in-domain certificate, final audit and shift stress test.

### Plan 4 — Verification, Hugging Face/Kaggle Release & Research/Portfolio Consolidation

Independently replay the evidence, package the reusable contribution and publish only supportable claims.

---

## 21. Open decisions and deadlines

| Decision | Default | Frozen by | Evidence |
|---|---|---|---|
| preferred certificate | verified joint selective finite-sample method | Gate 0D | theorem-to-code and simulation |
| conservative audit | simultaneous bounded-risk + acceptance bounds | Gate 0D | simulation and delta ledger |
| `alpha` | 0.20 planning default | before Plan 2 full run | task meaning and sample feasibility |
| `delta` | 0.05 | before certification | accepted theorem/config |
| acceptance floor | 0.20 | before certification | deployment usefulness and sample feasibility |
| material `CA` gain | 0.05 | before certification | smallest meaningful contribution |
| grid size | theorem/sample-dependent | development freeze | score distribution and precondition |
| shift definition | RAMS→WikiEvents if interpretable | before final labels open | ontology/group inventory |
| bootstrap replicates | 2,000 | before final labels open | compute/time check |

None of these may be revised after certification or final results merely to improve the conclusion.

---

## 22. Acceptance checklist — Plan 3 is done when

### Direction acceptance now

- [x] Certified acceptance—not raw F1—is accepted as the headline object.
- [x] QA–ZS is primary and QA–FS secondary confirmatory.
- [x] The joint risk/acceptance preferred method plus conservative audit is accepted.
- [x] Global system–threshold adaptivity and failure-budget accounting are mandatory.
- [x] Source-document grouping governs certification and bootstrap uncertainty.
- [x] Final labels are opened only after immutable certification.
- [x] Static shift transfer is explicitly uncertified under shift.
- [x] ACI and learned verifiers remain outside the MVP.
- [x] Null, infeasible and adaptation-harms outcomes are publishable results.

### Experimental acceptance before Plan 4 release work

- [ ] Plans 1–2 implementation gates and immutable system artifacts pass.
- [ ] The analysis version, hypotheses, tables and figure schemas are frozen.
- [ ] Preferred and conservative certifiers pass simulations and preflight.
- [ ] Certification produces immutable results or explicit infeasibility.
- [ ] Final in-domain policies are evaluated without recalibration.
- [ ] H1/H2 decisions follow the predeclared material-effect rules.
- [ ] Paired group bootstrap and sensitivity analyses are complete.
- [ ] Shift policies are transferred unchanged and limitations are explicit.
- [ ] Failure taxonomy/manual audit and all result artifacts are generated.
- [ ] Reproduction command regenerates tables/figures from immutable artifacts.
- [ ] No post-test configuration change enters the headline evidence.

> **Noted 2026-10-27.** The failure taxonomy/manual audit half of the ninth line is waived:
> both are descoped by [Amendment 2](sections-11-and-12-disposition-amendment-2.md). The "all result artifacts" half is not
> waived. The checklist above is unchanged.

Acceptance of this plan authorises drafting Plan 4. It does not mark experiments complete or permit out-of-order label access.

### Acceptance addendum

**Date:** 2026-07-15  
**Trigger/evidence:** Ross explicitly accepted Plan 3 and requested the next plan.  
**Decision change:** The certification, comparison, ordered-evaluation and schema-shift direction is accepted.  
**Scope impact:** None beyond the accepted plan. The experimental checklist above remains open and must be completed before public result claims.  
**Acceptance impact:** Plan 4 may be drafted. Planning acceptance does not authorise training, calibration, final-label access, shift-label access or public release before their stated gates.

---

## 23. Research and skills addendum

### 23.1 Current primary sources

- [Conformal Risk Control](https://arxiv.org/abs/2208.02814) — bounded monotone-loss CRC foundation and exchangeability scope.
- [A Joint Finite-Sample Certificate for Adaptive Selective Conformal Risk Control](https://arxiv.org/abs/2606.08517) — preferred candidate for simultaneous selected-risk, acceptance and utility bounds over a cert-independent finite grid; recent preprint requiring reproduction.
- [Non-monotonicity in Conformal Risk Control](https://arxiv.org/abs/2604.01502) — finite-grid and non-monotone-loss warning relevant to adaptive threshold choice.
- [When Can Conformal Risk Control Certify LLM Outputs?](https://arxiv.org/abs/2606.29054) — structured-generation feasibility bound, bound hierarchy and static/ACI shift evidence. Its “adaptation” is adaptive conformal inference, not LoRA fine-tuning, so it sharpens rather than duplicates ConformalExtract's intervention.
- [Conformal Prediction for Risk-Controlled Medical Entity Extraction Across Clinical Domains](https://arxiv.org/abs/2603.00924) — extraction-specific evidence that confidence behavior and required rejection can reverse across domains.
- [Adaptive Conformal Inference Under Distribution Shift](https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html) — future online-feedback extension deliberately excluded from the MVP.
- [Multi-Sentence Argument Linking](https://arxiv.org/abs/1911.03766) and [Document-Level Event Argument Extraction by Conditional Generation](https://aclanthology.org/2021.naacl-main.69/) — task/dataset foundations for RAMS and WikiEvents.

### 23.2 Skills applied

- **Hugging Face papers:** checked current CRC/selective-certification, structured-generation and shift research; this changed Plan 3 by separating parameter adaptation from adaptive conformal inference and by requiring a joint risk/acceptance object plus a conservative audit.
- **OpenAI Library:** this plan and accepted-plan records are persisted as living project artifacts.
- **Handoff workflow:** kept one concern per plan, open empirical decisions, explicit acceptance criteria and dated addenda.

### 23.3 Research limitations

- The preferred joint certificate is a June 2026 preprint. The plan treats it as a method to reproduce and audit, not an unquestioned authority.
- Mathematical notation rendered in source HTML is occasionally incomplete in machine retrieval; implementation must be based on the paper/PDF/code and checked equations, not this planning summary alone.
- The exact sample-size/grid precondition and failure-budget constants remain Gate 0 outputs.
- The shift analysis cannot prove general robustness from one ontology/domain transfer.
- If source-document groups are not i.i.d./exchangeable even in-domain, the public guarantee must be weakened or replaced rather than stated anyway.

---

## 24. Living-document rule

After acceptance, material changes append a dated addendum recording trigger/evidence, decision change, scope impact and acceptance impact. The newest accepted addendum controls execution where entries conflict; prior decisions remain visible.

### Addenda

None yet.
