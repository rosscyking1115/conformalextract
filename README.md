# ConformalExtract

ConformalExtract is an evidence-first research package for selective, grounded event-argument
extraction. It tests whether a document-level abstention policy can certify bounded extraction risk
while retaining useful coverage, and whether QLoRA adaptation beats zero/few-shot prompting on
*certified* acceptance rather than on average task quality.

At the operating point this project froze before opening any sealed label — 20% target risk, 95%
confidence, 20% acceptance floor — the answer on in-domain RAMS is **no**, for every system tested.
That null is the result, established under a procedure built before the sealed labels were opened.

## Status

The repository is executed through four sequential evidence gates. Each plan opens only after an
independent reviewer PASSes the one before it.

| Plan | Scope | State |
|---|---|---|
| **Plan 1** (Gate 0) | feasibility, licences, evaluator, statistics, paid smoke tests | **complete** — gates 0A–0F pass, Gate 0 decision `go`, consolidated reviewer PASS 2026-07-17 |
| **Plan 2** | QLoRA training, prediction generation for three systems | **closed** — independent reviewer PASS 2026-07-21 (`evidence/plan2/reviewer_record.plan2-close.json`) |
| **Plan 3** | certification against the sealed split | **executed and independently reviewed; not formally closed** — no Plan 3 close record exists |
| **Plan 4** | verification, public release, write-up | **not started** — Plan 3 has no close record, so this gate has not opened |

Plan 3's certification ran once, on 2026-07-22, and returned infeasibility for all three systems.
`evaluate-final` and `evaluate-shift` are descoped ([ADR 0010](docs/adr/0010-descope-final-and-shift.md))
because no selected policy exists to audit or transport — not for cost or effort. A subsequent $0
re-analysis ([ADR 0011](docs/adr/0011-reanalysis-frontier-and-loss-channels.md)) was reviewed over
four independent passes, opening at BLOCK and closing with the publication condition lifted and no
blocking items.

The write-up is at first draft ([`docs/writeup/draft-2026-07-28.md`](docs/writeup/draft-2026-07-28.md)),
independently reviewed. No venue is chosen and nothing is formatted for one. What it may claim is
fixed by the list in [`docs/plan3/certification-result.md`](docs/plan3/certification-result.md)
("What may and may not be claimed"), and that list is narrower than the results might suggest.

Contributor and agent rules — approvals, review gates, spend — are in
[`CONTRIBUTING.md`](CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md).

## Result

Each statement below carries a claim ID in [`evidence/plan4/claim_ledger.json`](evidence/plan4/claim_ledger.json),
which declares the surfaces it is permitted to appear on. Nothing here may be quoted without the
limitation attached to it.

**Neither the adapted system nor the zero-shot baseline could be certified** (`CX-H1-PRIMARY`). At a
target risk of 20% with 95% confidence and a 20% acceptance floor, neither the QLoRA-adapted system
nor the zero-shot baseline could be certified on RAMS: both are Infeasible, so no comparison of
certified acceptance between them is possible. H1 and H2 collapse into **one** finding, not two, and
no numerical difference is computed against an infeasible baseline. Scoped to in-domain RAMS and to
the frozen vLLM 4-bit serving stack.

**The failure is capability, not method** (`CX-CAPGAP-01`). With an unlimited threshold grid, no
finite-sample penalty and oracle threshold selection, the adapted system could accept at most 2.0%
of documents at 20% empirical error, against a required 20%. This is a diagnostic that selects no
threshold and certifies nothing; the same diagnostic on the development split gives 3.0%, so the
conclusion reproduces out of sample. **It is specific to this model, this score and this task, and
is not evidence that structured extraction cannot be certified at 20% risk** — the datasets
`2606.29054` reports include base risks of 0.033 and 0.356, at which the same arithmetic forbids
nothing and permits up to 80.5% acceptance respectively.

**QLoRA produced a large, real gain — in the wrong property** (`CX-GROUNDING-01`). 95.7% of the
adapted system's outputs parse and ground to the source document, against 39.4% zero-shot and 68.1%
few-shot, with ungrounded spans falling from 5,355 to 340. "Valid" means parseable and grounded,
**not correct** — a span can point at real document text and still name the wrong entity or role.
This improvement did not translate into a certified selective guarantee, and must never be reported
without that null attached. Scoped to the frozen vLLM 4-bit serving stack.

**QLoRA improved grounding sharply and certifiability not at all** (`CX-GROUNDING-ORTHOGONAL-01`).
It sharply improved output validity and span grounding, but did not make low-risk documents
identifiable using transition-logprobability confidence: the adapter's
~16× reduction in ungrounded spans moved the certifiable frontier by 0.017 for itself and by 0.000
for both baselines, because 87% of its remaining loss sits in output that is well-formed, grounded
and content-bearing, and is scored wrong anyway. **This is a dissociation, not an orthogonality
result** — one intervention across three systems cannot establish that two properties are
independent, and the wording was narrowed on 2026-08-02 to stop implying it did. (The claim
identifier keeps the word for traceability to the reviews that ruled on it.) **The decomposition
locates that loss; it does not
identify the error category that produced it**, and no such attribution is claimed here — an earlier
wording said "names the wrong entity" and was withdrawn on review, because false positives exceed
false negatives by 637 arguments on those frames, which is over-generation rather than
entity-naming. The decomposition is descriptive: it selects no threshold and certifies
nothing, the grounding-oracle counterfactual is *not* uniformly generous, and for the baselines the
conclusion rests on an arithmetic ceiling rather than on the counterfactual. The QLoRA system sits
below that ceiling, so for it the ceiling is silent and only the measured curve leaves it short. See
the claim's `limitations` field before citing it.

**Sealed-label discipline held** (`CX-SEALED-01`). Certification opened the sealed split exactly
once, over 3,152 documents, with a verified hash-chained access record and zero reads of the `final`
or `shift` splits, which remain sealed.

**Cost** (`CX-COST-01`). The programme of GPU work — inference benchmarking, QLoRA training,
prediction generation for three systems over 27,372 frames, and serving-equivalence probes — is
recorded job by job and sums to between about $18.7 and $18.9 against an authorised $25 ceiling,
each figure derived from the instance's hourly price and the job's measured duration rather than
from a billing statement. All certification and analysis ran on CPU at no cost. The figure excludes
the value of free-tier and local compute. There is no single spend ledger — Gate 0 has a per-job
artifact and Plan 2's costs live in each run's brief or result document, so the total is assembled
by a reader; one job has no per-job figure at all and is recovered by differencing the recorded
running totals, which is what makes the total a band rather than a point. Individual figures are
rounded as recorded, so the total is stated to one decimal place and not to the cent
([ADR 0012](docs/adr/0012-cost-claim-evidence-correction.md)).

## How the evidence is held to account

The gate discipline is the substantive engineering contribution here, and it is enforced rather
than described.

- **An independent reviewer, with a real BLOCK verdict.** Review is performed by an agent that did
  not implement the work under review, against [`REVIEW.md`](REVIEW.md), with the verdict vocabulary
  PASS · PASS-WITH-NITS · BLOCK, and it is recorded as a committed artifact
  (`evidence/*/reviewer_record*.json`). BLOCKs have been issued and have held up work — on the
  QLoRA smoke test (below) and on the ADR 0011 re-analysis, where the reviewer reproduced the
  load-bearing numbers by from-scratch reimplementation with zero mismatches and still blocked on
  six items — including a `--roles` hole that would have let a sealed split be opened while the
  artifact attested zero reads of it.
- **A bit-exact reproducibility gate on quantized model loading.** Gate 0F's paid QLoRA smoke test
  was BLOCKed on a mismatch in generated tokens between two independently quantized loads of the
  same base model. The fix aligned k-bit preparation, gradient checkpointing, cache and generation
  state across both inference paths; **exact equality was retained as a hard gate** rather than
  relaxed to a tolerance. The corrected run reproduced exact adapter and greedy-token hashes in a
  fresh process. ([`docs/gate0/decision.md`](docs/gate0/decision.md), [`docs/progress.md`](docs/progress.md))
- **SHA-256 matched across storage boundaries.** Remote job artifacts are hashed on the private Hub
  and against the in-Git evidence copy, and both must agree — e.g. Gate 0F at `adb61606…`, pinned to
  Hub revision `840fb41e…`. Separately, the certification artifact is pinned at `71c0de3e…` over
  git-canonical (LF) bytes; a Windows working copy is checked out CRLF and hashes differently, and
  that correction is recorded ([`docs/plan3/certification-result.md`](docs/plan3/certification-result.md))
  rather than left as a trap for an independent verifier.
- **Per-job cost recorded for every job but one** — in a per-job evidence artifact for Gate 0
  ([`evidence/gate0/hf_jobs_submission_attempts.json`](evidence/gate0/hf_jobs_submission_attempts.json)),
  and in each run's launch brief or result document for Plan 2 — against a hard aggregate ceiling
  enforced in code (`training.REMAINING_BUDGET_USD` = $24.7992, the $25 cap less $0.2008 of prior
  recorded spend), with a run ledger imposing R0→R1→R2 order. No single spend ledger exists and the
  figures are price×duration estimates, not billed amounts
  ([ADR 0012](docs/adr/0012-cost-claim-evidence-correction.md)).
- **Claims cannot outrun their evidence.** `conformalextract verify-claims` fails closed if a
  claim's evidence is not git-tracked, and a regression tripwire refuses a claim that holds a public
  surface while its own verification literally reads as pending. The tripwire is not a verification
  gate and does not claim to be — what it catches and what it misses is measured and written down in
  ADR 0011 §6 rather than left implied by the function's name.
- **Sealed roles are guarded, not merely logged.** Only `development` and `certification` are
  reachable from the analysis commands; every other role raises before a file is opened. A test
  discovers the command list by introspection, so a *new* unguarded command fails rather than
  passing silently.

Typing and tests are strict: **`mypy` runs with `strict = true`** over the package (which ships
`py.typed`), `ruff` is clean, and the suite is 349 tests, all passing — a measurement taken at this
commit, not a standing property. The green command below must pass before any hand-off.

## Local checks

```console
uv sync --extra dev --extra data
uv run pytest -q
uv run ruff check .
uv run mypy
uv run conformalextract --help
```

## What this is not

- **Not certified.** "Certified" is claimed only behind an independent reviewer PASS, and no
  certified acceptance is claimed for any system.
- **Not production-grade**, and not portable beyond the frozen vLLM 4-bit serving stack — a
  serving-equivalence probe measured 86.3% parsed-output parity, and portability is not established.
- **Not generalised beyond in-domain RAMS.** An in-domain guarantee is never claimed to survive
  schema or dataset shift.
- **Not an accuracy claim.** The 95.7% grounding figure is validity, not correctness, and may not
  be quoted without the null result attached.

Scientific infeasibility is reported as an auditable, first-class result, never replaced by an
empirical claim. Gate state and decisions live in [`docs/progress.md`](docs/progress.md),
[`docs/gate0/decision.md`](docs/gate0/decision.md) and [`docs/adr/`](docs/adr/); data handling is in
[`SECURITY.md`](SECURITY.md). Raw RAMS/WikiEvents text, sealed labels, model checkpoints,
credentials, predictions with recoverable text, and private tracking state are never committed.

## Licence

Original source code is Apache-2.0. Dataset text, annotations, model adapters, predictions, and
evidence artifacts have separate licence boundaries documented under `docs/gate0/licences/`.
