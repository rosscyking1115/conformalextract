# ConformalExtract

ConformalExtract is a research project on whether a language model that pulls structured facts out
of documents can be told to skip the documents it is likely to get wrong, with a statistical
guarantee on the error rate of the ones it keeps.

The task is **event-argument extraction**: given a news document and an event mentioned in it, name
who or what fills each role in that event (the attacker, the target, the place, and so on). The
data is [RAMS](https://aclanthology.org/2020.acl-main.718/), an English news-domain benchmark for
this task. The model is `Qwen/Qwen3-4B-Instruct-2507`, run three ways: zero-shot, few-shot, and
adapted with QLoRA (a low-cost form of fine-tuning).

A system is **certified** here when, with high confidence, the average error over the documents it
chooses to answer stays under a fixed target, while it still answers a fixed minimum share of them.
The question is whether QLoRA adaptation buys more certified answers than prompting does: it is
asked of the share of documents a system may answer under a guarantee, not of average accuracy.
The two predeclared hypotheses, H1 and H2, compare QLoRA with the zero-shot and the few-shot
system respectively.

## The headline result

The operating point was fixed before the held-out labels were opened.

> At a target risk of 20% with 95% confidence and a 20% acceptance floor, neither the QLoRA-adapted
> system nor the zero-shot baseline could be certified on RAMS: both are Infeasible, so no
> comparison of certified acceptance between them is possible. (`CX-H1-PRIMARY`)

Limitations:

- H1 and H2 collapse to a single test when both baselines are infeasible; this is ONE finding, not two.
- No numerical difference is computed against an infeasible baseline.
- Scoped to the frozen vLLM 4-bit serving stack and to in-domain RAMS.

Neither system was certified, so the comparison the project set out to make could not be made.
That null is the result. The rest of this page covers why it failed, what QLoRA did change, and how
to check the evidence.

## State of the project

- **The experiment is finished.** Certification has been run. The final and shift evaluations were
  descoped rather than run, for the reason given with `CX-SEALED-01` below.
- **The paper is a draft.** It is in preparation for UncertaiNLP 2026 and has not been submitted.
- **This is research code, not production-grade.** No result is claimed beyond the scope stated
  with it.

## Quick start

You need Python 3.12 and [uv](https://docs.astral.sh/uv/). The checks below run on a CPU and need no
dataset and no credentials.

```console
uv sync --extra dev --extra data
uv run pytest -q
uv run ruff check .
uv run mypy
uv run conformalextract verify-claims
uv run python scripts/check_paper_claims.py
```

`verify-claims` checks that every claim's cited evidence exists and is tracked in git. It does not
open those files or compare any number, so passing it means the paths resolve, not that the claims
are right. `check_paper_claims.py` checks that each figure in the paper draft traces to a committed
artifact carrying that value and its configuration.

Running the pipeline itself (`uv run conformalextract --help`) needs RAMS, which this repository does
not redistribute; its terms are in [`docs/gate0/licences/rams.md`](docs/gate0/licences/rams.md). GPU
training and inference ran as Hugging Face Jobs, and the `train` extra installs only on Linux.

## Results

Each result below is the claim's approved wording, copied exactly from
[`evidence/plan4/claim_ledger.json`](evidence/plan4/claim_ledger.json), with the claim's ID. Its
limitations are copied the same way and travel with it: none of these results may be quoted
without them. The ledger also records where each claim may appear, and only claims it allows in
this README are shown.

### The causes of the infeasibility (`CX-CAPGAP-01`)

> The infeasibility has two separable causes and only the first is a capability gap. (1) CAPABILITY, specific to this model and score on this task: with an unlimited threshold grid, no finite-sample penalty and oracle threshold selection, the adapted system accepts at most 2.0% of documents at 20% empirical error, where a perfect ranking of the same population reaches 23.6%. Both figures are empirical and penalty-free, so the 21.6-point gap is attributable to the score and not to the coarse grid, the delta split, the bound looseness or a distribution difference between splits. (2) METHOD AND BENCHMARK, independent of capability: at n = 1,396 groups with delta/3, a Hoeffding bound spends 0.0925 of the 0.20 risk budget on the finite-sample penalty before any data is seen - a DIAGNOSTIC pairing belonging to neither certifier construction, since the primary risk test is empirical Bernstein and the conservative audit ran Hoeffding at a single candidate on the full delta. Under that diagnostic, passing the RISK test at exactly the 20% acceptance floor (k = 280) requires mean loss at most 0.1075 - barely half the nominal target - whoever produced it; that is the risk test's requirement under one bound, not what every certificate requires, since the primary test's requirement depends on the loss distribution. For this model the outcome is settled independently of the score and of the risk bound (for any risk bound never below the accepted set's empirical mean): at the frozen allocation acceptance needs at least 332 groups, and the loss-optimal 332-group prefix, which no score can beat, already averages 0.2012 loss, above the target (under the Hoeffding diagnostic the loss-optimal ranking certifies 0.1139 at delta/3, below the floor). Separately, at delta/3 this corpus admits at most a three-candidate grid, which the frozen configuration exactly fills.

Limitations:

- A diagnostic, not a certificate: it selects no threshold and certifies nothing.
- The same oracle diagnostic on the development split gives 3.0%, so cause (1) reproduces out of sample.
- Cause (1) is specific to this model, this confidence score and this task. It is not evidence that event-argument extraction, or structured extraction generally, cannot be certified at 20% risk: 2606.29054's own datasets include base risks of 0.033 and 0.356, at which the arithmetic bound forbids nothing and permits up to 80.5% acceptance respectively (docs/frontier-check/findings.md, re-verified 2026-07-22).
- Cause (2) is NOT the claim that no model could be certified on this corpus. The witness has to clear BOTH tests, and the one first offered here did not: mean loss at most 0.1075 over an accepted 20% clears the risk test at n = 1,396 and delta/3 while its Clopper-Pearson acceptance lower bound is 0.16566, so that system is NOT certified. The corrected witness is stated at the smallest prefix that clears acceptance, k = 332: there the acceptance lower bound is 0.2004 and the Hoeffding radius 0.0849, so a system carrying mean loss at most 0.1151 over its 332 best-ranked groups would pass both tests under that Hoeffding diagnostic. Under the primary empirical-Bernstein test the condition depends on the loss distribution, not the mean alone: an independent review found a constant-loss set of that size at 0.1151 certifies while a 0/1 set at a slightly lower mean does not (evidence/plan3/reviewer_record.c1-2026-08-03-packets.json), and a zero-loss set certifies under either. Clearing one of two constraints is not a counter-example to infeasibility. What cause (2) establishes is that, under the Hoeffding diagnostic at this allocation, the corpus halves the risk test's effective target for every system, and that for THIS model no score whatsoever clears what remains.
- The two causes attach to different mechanisms of the three-way decomposition and must not be merged: cause (1) is ranking (mechanism 2), cause (2) is the finite-sample penalty (mechanism 3) plus grid capacity. Base risk (mechanism 1) belongs to neither - it settles ZS and FS outright and permits QA 49.1%.
- Narrowed 2026-08-03. This claim previously read 'a capability gap rather than a limitation of the certification method' and attributed BOTH causes to capability, which is the same flattering direction as the five quoting errors recorded in the write-up's limitations, expressed in attribution rather than in arithmetic.
- The Hoeffding figures in cause (2) use the conservative TWO-SIDED constant; the tight one-sided radius at k = 280 and delta/3 is about 8% smaller (certification.hoeffding_upper docstring). 'Barely half the nominal target' therefore slightly overstates the penalty, in the direction that strengthens cause (2), and is disclosed here for that reason.

### What QLoRA improved: grounding (`CX-GROUNDING-01`)

> QLoRA adaptation produced a large improvement in grounding fidelity: 95.7% of the adapted system's outputs parse and ground to the source document, against 39.4% zero-shot and 68.1% few-shot, with ungrounded spans falling from 5,355 to 340.

Limitations:

- "Valid" means parseable and grounded, NOT correct: a span can point at real document text and still name the wrong entity or role.
- This improvement did NOT translate into a certified selective guarantee (see CX-H1-PRIMARY); it must never be reported without that null attached.
- Scoped to the frozen vLLM 4-bit serving stack.

### Grounding and certifiability (`CX-GROUNDING-ORTHOGONAL-01`)

> QLoRA sharply improved output validity and span grounding for event-argument extraction on RAMS, but did not make low-risk documents identifiable using transition-logprobability confidence: the adapter's ~16x reduction in ungrounded spans over the baselines moved the certifiable frontier by 0.017 for itself and by 0.000 for both baselines, because 87% of its remaining loss sits in output that is well-formed, grounded and content-bearing, and is scored wrong anyway.

Limitations:

- This is a DISSOCIATION, not an orthogonality or independence result, and the wording was narrowed to say so on 2026-08-02. One intervention observed across three systems cannot establish that two properties are independent; what is measured is that a large gain in the first produced almost none in the second. Any reading as statistical independence, or as a general relationship between grounding and certifiability, exceeds this evidence.
- The claim identifier still contains the word ORTHOGONAL. It is retained only so that the reviewer records which ruled on this claim remain traceable to it; the identifier is historical and the claim no longer asserts orthogonality.
- Descriptive only: the decomposition and the grounding-oracle counterfactual select no threshold and certify nothing.
- Conditional coverage under the grounding oracle is not a deployable acceptance rate and is not comparable across systems; the restricted population differs per system.
- The restriction is NOT uniformly generous: it raises the loss of 24 few-shot and 21 QLoRA groups, and a correctness-oracle variant moves the baselines off zero. The baselines' result is carried by the arithmetic ceiling, not by the counterfactual.
- The QLoRA system sits below that ceiling, so for it the ceiling is silent and only the measured curve leaves it short of the floor.
- Scoped to in-domain RAMS under span-exact matching and to the frozen vLLM 4-bit serving stack (86.3% parsed-output parity); portability is not established.
- The certificate bounds average within-group loss, not the absence of error in any document (ADR 0009).
- The decomposition locates loss by CHANNEL; it does not identify the error category that produced it, and this claim no longer asserts one. Until 2026-07-29 the wording said the residual loss was output 'that names the wrong entity' — an attribution whose only source was ADR 0007's unquantified inspection of two development examples, which plan section 12.3 forbids generalising from. Removed on independent review (evidence/plan3/reviewer_record.plan3-close.json, finding O2).
- A measurement points the other way and is recorded here rather than left in the review. On QA's content-bearing certification frames: tp 2,984, fp 4,434, fn 3,797 — false positives EXCEED false negatives by 637 arguments, i.e. systematic over-generation, which is not an entity-naming error. 2,003 of 2,515 error-bearing documents show both fp and fn, consistent with substitution, so 'mostly missing arguments' is ruled out. Wrong-role, boundary and coreference errors share that signature. Plan section 12.1's machine-coded taxonomy is what would separate them; it was descoped from Plan 3 on 2026-10-27 (disposition Amendment 2, ruled acceptable by the independent delta review in evidence/plan3/reviewer_record.plan3-close-chain-delta.json) rather than run, so no error-category claim is made.
- Directional, and specific to the adapted system: on the same channel and the same frozen scorer, the two baselines run the OTHER way - they under-generate where QA over-generates. Normalised per document in the content-bearing channel, the excess of false positives over false negatives is +0.224 for QA against -1.168 for zero-shot and -1.328 for few-shot. The figures must be read per document and not as raw counts: the content-bearing channel is defined per system and the baselines reach it on far fewer documents (2,847 for QA against 1,238 and 1,130), so the channel filter alone would make raw totals incomparable. What survives normalisation is the SIGN, which is the whole of the claim.

### Held-out label discipline (`CX-SEALED-01`)

> Certification opened the sealed split exactly once, over 3,152 documents, with a verified hash-chained access record and zero reads of the final or shift splits, which remain sealed.

Limitations:

- The final and shift splits are descoped because no selected policy exists to audit or transport, not for reasons of cost or effort; both commands are free to run.
- 'Zero reads' means no final or shift gold entered the access record or scoring. It does not mean those records went untouched: RAMS stores text and gold in one record, the certify command parsed the whole archive, and the 2026-07-22 run also parsed the final split's predictions against their source text, which uses no gold. The role map assigns no shift documents at all.
- The final_reads and shift_reads fields of the 2026-07-22 artifact were written as the constant 0, not counted. The code path made them true, because gold was looked up only for certification-role documents, but the artifact did not measure it. The command now counts the gold it uses, by role. The zero for other roles still holds by construction of the certification filter; the count checks that it held.
- The Plan 3 section 3.2 preflight did not run before the 2026-07-22 read, because certify never called it. Run afterwards on the hash-identical inputs, label-free, it passes (evidence/plan3/certification_preflight_retrospective.json).

### Cost (`CX-COST-01`)

> The programme of GPU work — inference benchmarking, QLoRA training, prediction generation for three systems over 27,372 frames, and serving-equivalence probes — is recorded job by job and sums to between about $18.7 and $18.9 against an authorised $25 ceiling, each figure derived from the instance's hourly price and the job's measured duration rather than from a billing statement; all certification and analysis ran on CPU at no cost.

Limitations:

- Excludes the value of free-tier and local compute.
- These are operator-recorded estimates from price and duration, NOT billed amounts. No invoice or billing statement is held, so the figure is not reconciled against what Hugging Face actually charged.
- No single committed spend ledger exists. Gate 0 has a per-job artifact; Plan 2's per-job costs live as prose across six documents, so the total is assembled by a reader rather than read off one artifact.
- One paid job has no per-job figure: the first R0 inference benchmark (6a5bcee6bee6ee1cf4ecfe08, 1x L4). Its cost is recovered by differencing two committed running totals, which is an inference and not a recorded figure; the two readings of those totals are what set the width of the band.
- 18 is a floor, not a count. docs/plan2/r0-launch-plan.md records fixes (the nvcc/flashinfer and vLLM prompt-format ones) that could only have been discovered by a job that reached GPU execution and was therefore billed, with no job id or cost recorded anywhere. The recovered $0.15-$0.35 bounds ALL unrecorded pre-R1 spend rather than isolating a single job. The total is unaffected because the running totals capture money regardless of how many attempts produced it — which is a further reason the figure is published as a band.
- Individual figures are themselves rounded as recorded ("about $0.05", "~$11.2"); the total inherits that and is stated to one decimal place, not to the cent.

## How the evidence is organised

| Path | What it holds |
|---|---|
| [`evidence/plan4/claim_ledger.json`](evidence/plan4/claim_ledger.json) | Every claim: approved wording, limitations, evidence paths, and where it may appear |
| [`evidence/`](evidence/) | Committed result artifacts and independent review records, one folder per stage |
| [`docs/plan3/certification-result.md`](docs/plan3/certification-result.md) | The certification result, and what may and may not be claimed from it |
| [`docs/adr/`](docs/adr/) | One decision record per material decision |
| [`docs/domain-glossary.md`](docs/domain-glossary.md) | Definitions of the terms used here |
| [`src/conformalextract/`](src/conformalextract/) | The package: data roles, parsing, scoring, the certifier and the claim checks |
| [`tests/`](tests/) | The test suite, including the checks that keep prose in line with the ledger |

Raw RAMS and WikiEvents text, held-out labels, model checkpoints, credentials and predictions from
which the text could be recovered are never committed. [`SECURITY.md`](SECURITY.md) covers data
handling.

## Paper draft

The draft is [`docs/writeup/uncertainlp-2026-short.tex`](docs/writeup/uncertainlp-2026-short.tex).
Its status, where each external number came from, and the remaining work are in
[`docs/writeup/uncertainlp-2026-short.md`](docs/writeup/uncertainlp-2026-short.md). It builds with
`pwsh -File scripts/build_paper.ps1`, which needs a LaTeX installation.

## Related work

The certification method follows conformal risk control
([Angelopoulos et al., 2024](https://arxiv.org/abs/2208.02814)). The closest prior work,
[Kotte (2026)](https://arxiv.org/abs/2606.29054), asks when conformal risk control can certify
language-model outputs for structured generation. This project puts that question to event-argument
extraction, with the whole source document as the unit, and reports where it fails.

## What this is not

- **Not certified.** No certified acceptance is claimed for any system.
- **Not an accuracy claim.** The grounding result measures whether output parses and points at real
  document text, not whether it is correct.
- **Not general.** No result is claimed to survive a change of schema or dataset, or a different
  serving stack.
- **Not production-grade.**

## Project governance

The work ran as four plans in sequence, each meant to open only after an independent reviewer had
passed the one before it. Plans 1 to 3 are closed. Plan 4 (verification, release and write-up) was
opened early by owner override; the override lapsed when Plan 3 closed, and Plan 4 is now open on
its merits. Every review verdict is committed under `evidence/`. The gate table, the review history
and the engineering checks behind the evidence are in [`docs/governance.md`](docs/governance.md),
and the current gate state is in [`evidence/gate_state.json`](evidence/gate_state.json).

## Licence

Original source code is Apache-2.0 ([`LICENSE`](LICENSE)). Dataset text, annotations, model
adapters, predictions and evidence artifacts have separate licence terms, set out in
[`docs/gate0/licences/`](docs/gate0/licences/).
