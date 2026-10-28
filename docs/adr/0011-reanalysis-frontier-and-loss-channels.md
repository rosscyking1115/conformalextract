# ADR 0011: $0 re-analysis — the α-frontier and the loss-channel decomposition; WikiEvents withdrawn

- Status: accepted; **§2's headline sentence narrowed 2026-08-02** (see "Amendment 1" below)
- Date: 2026-07-22
- Trigger: a 3-agent adversarial review (2026-07-22) found the Plan 3 negative result to be
  substantially a replication of arXiv 2606.29054 — the impossibility bound, the base-risk
  feasibility test and multi-system infeasibility are all published there. The question this ADR
  answers is what, if anything, is genuinely new, and what it costs to establish.

## Decision

Add two **descriptive** re-analyses over splits that are already open, and **withdraw** the planned
WikiEvents certification arm. Nothing here is a certificate, nothing opens a new sealed label, and
nothing costs money.

1. **α-frontier** — `uv run conformalextract alpha-frontier` → `evidence/plan3/alpha_frontier.json`
2. **Loss-channel decomposition + grounding oracle** — `uv run conformalextract loss-decomposition`
   → `evidence/plan3/loss_decomposition.json`
3. **WikiEvents second arm: withdrawn**, on the arithmetic in §3 below.

## 1. Why the α-sweep is not a relaxation of α

> **Amended twice on 2026-07-22.** The first amendment, written when the accepted plan was
> brought into the repo ([`docs/plan3/accepted-plan.md`](../plan3/accepted-plan.md)), claimed the
> repo's gloss — "the headline target must not be relaxed after seeing this" — was *stricter than
> the plan*, on the grounds that §6.3 permits a sweep. **That was wrong, and it is the error most
> worth recording here**, because it would have travelled into a write-up as "the constraint was
> weaker than we thought".
>
> The gloss is not a rendering of §6.3 at all. It is a faithful rendering of **§6.2's fourth
> bullet**: *"all systems far above `alpha`: expect heavy abstention or infeasibility; do not
> relax `alpha` after seeing certification."* That is unambiguously this project's branch —
> group losses 0.9923 / 0.9580 / 0.6071 against α = 0.20. **The binding constraint is exactly as
> strict as the repo assumed it was.**
>
> **The licence for this object is §9.1, and it names it:** *"An infeasible system remains
> infeasible; its descriptive risk–coverage curve may be plotted but no test threshold is
> selected."* All three systems are infeasible and no threshold is selected, so the conditions
> are met literally. **Disclosed read-across:** §9.1 sits under §9, the final in-domain stage that
> ADR 0010 descoped. The permission is therefore being read across from a stage that was never
> run, rather than applied in its own context. It is the closest textual licence in the plan and
> the fit is exact, but it is a read-across and should not be cited as though §9 had executed.
>
> **§6.3 does permit a sweep, but not this one, and the earlier reading was too convenient.**
> Its "small, predeclared" modifies the sweep, and both status branches attach to it; taking the
> weaker branch while dropping the modifiers is not a reading the sentence supports. Ours is
> post-hoc and full-range. There is a *purposive* argument — "small" and "predeclared" are guards
> against selecting a favourable point, and publishing the **entire** range discharges that hazard
> more completely than three chosen points do — but it is purposive, not textual, and is labelled
> as such rather than leaned on.
>
> **§8.5 "No post-hoc rescue" has to be engaged, not passed over.** Its list of forbidden rescues
> includes *"reporting only empirical rather than certified acceptance"*, which in surface form is
> close to what an α-frontier does, and its escape clause is stricter than §6.3's — "predeclared
> **and** multiplicity-aware", where §6.3 offers correction **or** descriptive status. The reason
> it does not bind: §8.5 forbids rescuing a *failed hypothesis*, and every item in its list makes a
> negative result look better. This frontier does the opposite — it broadens the null from one
> operating point to a range, and §8.5's own limiting condition, that such analyses "cannot change
> the primary conclusion", is met exactly. Nothing here alters H1/H2, which remain
> `both_infeasible` at the frozen target.

Plan §6.3 governs relaxing the headline target after seeing the result. This ADR does not relax it:
α = 0.20 remains the frozen target (ADR 0007) and **no certificate is issued at any other α**.

The reason a sweep is safe here is structural, not a matter of care. The oracle risk–coverage curve
**carries no α**: sorting groups by score and taking the running mean loss of the best-scoring
prefix produces one fixed object, and "max acceptance within α" is that object read at height α.
Reading it at twenty heights introduces no new statistic, no threshold selection and no
multiplicity — it is a re-rendering of a quantity already committed in
`evidence/plan3/risk_coverage_diagnostic.json`. `certification_run._curve_arrays` is now the single
source both the existing single-α frontier and the new curve read from, so they cannot drift, and
`tests/test_reanalysis_artifacts.py` asserts against the **committed artifacts** that the curve
read at α = 0.20 reproduces the committed diagnostic for all six system/split cells.

The curve is used in **one direction only**. It is an oracle *upper* bound on what any threshold
rule could achieve, so where the acceptance floor is unreachable on the curve, no certificate at
that α could have cleared it. That rules α values **out**. It never rules one in.

Result (certification split): the 20% floor first becomes oracle-reachable at **α ≈ 0.406** for QA,
0.930 for FS, 0.981 for ZS. The entire range below 0.406 is therefore excluded without a
certificate being computed anywhere in it — which is the honest answer to "you picked the one α
where it fails".

**The crossing is necessary, not sufficient.** It is emphatically not "the α at which this would
have certified". It carries no finite-sample penalty, no grid and no multiplicity correction, and a
certificate at 0.406 would not issue: at the ~280 groups a 20% acceptance implies, the Hoeffding
radius alone is 0.086 at δ/3 (0.103 under the family-wide δ/(2·9)), putting the risk upper bound
near 0.49–0.51. Any wording that lets a reader infer a workable operating point from this curve is
a §6.3 violation even though no target was changed (reviewer ruling R6).

## 2. Why the loss decomposition is the finding, not the grounding number

Plan 2 measured a ~16× grounding separation (QA 95.7% parseable-and-grounded vs ZS 39.4% /
FS 68.1%). Plan 3 found it bought no certified acceptance. Until now that gap was *interpreted*
("grounded is weaker than correct"); it is now *measured*.

Document loss splits into four channels. `structural_failure` and `grounding_failure` are forced to
loss 1.0 by `development_gate.document_loss`. `valid_empty` is **not** forced — an empty prediction
against empty gold scores F1 = 1.0 — it simply loses most of the time (measured 0.74–0.93). The
fourth, `valid_content_bearing`, is the only channel the certificate can score favourably.

The group-level channel contributions sum **exactly** to the unweighted mean of group means — the
quantity the certificate bounds under ADR 0009 — so this decomposes the certified object itself,
not a proxy. Verified against `evidence/plan3/certification_result.json` to six decimal places
(QA 0.607090, ZS 0.992332, FS 0.957993). Channel counts reconcile exactly with
`evidence/plan2/prediction_parse_summary.json`; that reconciliation is label-free, because channel
classification reads predictions only.

Under a **grounding oracle** — each system scored as though it never emitted a structural failure,
an ungrounded span or an empty frame, with coverage measured against the restricted population —
max acceptance at α = 0.20 moves from 0.0201 to 0.0374 for QA, and from 0.0000 to **0.0000** for
both baselines. Removing 58% (ZS) and 32% (FS) of documents' worth of grounding failure moves the
certifiable frontier by nothing.

**The counterfactual does not carry the claim, and the first draft of this ADR was wrong to say it
did** (reviewer ruling R5). It described the restriction as "the reading most generous to each
system". That is false: dropping a low-loss member *raises* a group's mean loss, and 24 FS groups
and 21 QA groups score worse under the restriction — now counted in the artifact as
`groups_worsened_by_restriction`. A different counterfactual (a correctness oracle) moves the
baselines off zero.

What carries the claim is arithmetic. With losses in [0,1], accepting a fraction `c` at risk `α`
requires population mean loss `μ ≤ α·c + (1−c)`, since the best achievable mean over the best `c`
fraction is `(μ − (1−c))/c`. At `c = α = 0.20` that ceiling is **0.84**. Restricted mean losses are
ZS **0.984** and FS **0.951** — above it — so **no selection rule of any kind** reaches the floor
for the baselines, oracle or otherwise. QA is at 0.582, below the ceiling, so for QA the ceiling is
silent and the measured curve is what leaves it 5× short. Both are emitted as `mean_loss_ceiling`
and `excluded_by_ceiling` so the argument is checkable rather than rhetorical.

**Grounding and certifiability are orthogonal for this task.** That is the contribution; the
grounding number on its own is not.

> **Amendment 1, 2026-08-02 — this sentence is narrowed and no longer holds as written.** The
> decision, the two commands and every number in this ADR stand unchanged; only the wording of the
> contribution does. "Orthogonal" asserts independence between grounding and certifiability, and
> one intervention observed across three systems cannot establish independence — nothing in this
> ADR tested it. Read instead: **QLoRA sharply improved output validity and span grounding, but did
> not make low-risk documents identifiable using transition-logprobability confidence.** That is a
> *dissociation*, which is what the decomposition measures and all it supports. The claim
> identifier `CX-GROUNDING-ORTHOGONAL-01` is retained for traceability to the reviewer records that
> ruled on it and is now historical. Applied across the ledger, README, `certification-result.md`,
> the write-up draft and the generated appendix on the same date.

### Boundaries fixed here

- Conditional coverage under the grounding oracle is **not** a deployable acceptance rate. The
  restricted population differs per system, so the figures are not comparable across systems and
  support only the within-system question "does closing the grounding gap reach the floor?".
- The grounding oracle must not be described as generous, conservative, or a bound. It is one
  counterfactual among several; the ceiling is what makes the baselines' result robust.
- Both artifacts select no threshold and certify nothing. They carry `diagnostic_only: true` and
  `certifies_nothing: true`.
- **Certified ≠ safe** (ADR 0009) travels unchanged: the certificate bounds *average within-group*
  loss, not the absence of error in any document.

## 3. WikiEvents certification arm — withdrawn, not deferred

The planned second arm was a WikiEvents certification run to establish that the result holds across
two grounded-EAE benchmarks. It cannot be run, at any α, for any budget:

| | groups available | SCoRC minimum n |
|---|---|---|
| RAMS certification split | 1,396 | 1,386 (cleared by **10**) |
| WikiEvents dev | 20 | 1,386 |
| WikiEvents dev + test | 40 | 1,386 |
| **WikiEvents, every split pooled** | **246** | **1,386** |

`certification.scorc_minimum_n(candidate_count=3, delta=δ/3, acceptance_floor=0.20)` = **1,386**,
and `largest_scorc_grid` returns **0** at every WikiEvents scale — the preferred method is simply
unavailable. Counted from `data/raw/wikievents/*.jsonl`: 20 dev / 20 test / 206 train source
documents, 246 total.

The conservative Bonferroni audit (Construction B) carries no sample-size precondition, so it is
*available* at that scale — but vacuous. At n = 20 the Hoeffding radius at δ/(2·9) is **0.384**, so
an empirical risk of 0.60 certifies at an upper bound of 0.98 against α = 0.20. It cannot return
anything but infeasible regardless of the data.

Consequences:

- **No paid WikiEvents generation is requested or authorised.** The $25 aggregate cap is untouched
  by this ADR; total spend for all the work it records is **$0**.
- Changing the unit to event mentions (3,241 in WikiEvents train) would clear the precondition
  arithmetically, but is rejected: it abandons the source-document group that ADR 0009 adopted for
  independence, breaks comparability with the RAMS arm, and uses training data as a certification
  split. It is recorded here so a future agent does not rediscover it as a shortcut.
- A **descriptive** WikiEvents base-risk arm (μ measurement, no certificate) remains possible and
  is not taken here — it needs a KAIROS prompt/profile/parser and the native head-word+coref
  metric, and it would generalise the base-risk observation without adding a mechanism. The
  grounding/certifiability decomposition was judged the stronger use of the same effort, at $0.
  (Written as “grounding⊥certifiability” until 2026-08-02; see Amendment 1 above — the claim is
  a dissociation, not an orthogonality result.)
- RAMS cleared the precondition by 10 groups out of 1,386. That margin is worth knowing: a slightly
  smaller corpus, or a fourth threshold in the grid (min n **1,432** at the same δ/3 allocation),
  would have made the preferred method unavailable on RAMS too.

## 4. Citation corrections forced by this review

`docs/frontier-check/findings.md` attributed base risks of "~0.48–0.55" to 2606.29054's
**document-level extraction** results. Verified against its Table 3 (accessed 2026-07-22, HTML
rendering at `arxiv.org/html/2606.29054v1`, not the PDF): that band is Few-NERD 0.540, WNUT 0.480
and MMLU-STEM 0.516 — two NER datasets and one MMLU subset. The paper evaluates **no** event-
argument extraction, no RAMS and no WikiEvents; its only extraction task is JSON-Extract at
**μ = 0.033**.

This matters beyond tidiness. Our μ ≈ 0.60 was being read as a reproduction of their number; it is
our own measurement, in a much harder regime than their extraction datapoint. It does **not**
contradict their JSON-Extract figure — different task, different metric — and an earlier draft of
this ADR overstated that; what the comparison establishes is a new operating regime, not an error
in their work (reviewer ruling R6).

The same paragraph's "60–71% exchangeability violations" is corrected to **71% static / 21% under
ACI**. Note the original range was defensible across their shift regimes; the material omission was
the ACI mitigation, which made shift look more hopeless than they report. The three pillar papers
(2606.08517, 2606.29054, 2604.01502) are recorded as unrefereed June-2026 preprints.

## 5. What this ADR does not do

- No new sealed-label access. The certification split was already opened once
  (`docs/plan3/certification-result.md`); `final` and `shift` remain sealed. ADR 0010 is unchanged
  and not reopened.

  **This was not true of the first implementation, and the fix is the substantive one this review
  produced.** `certification_access_for` originally *returned `None`* for any role other than
  `certification`, and `_load_reanalysis_splits` had no role guard at all — so
  `conformalextract alpha-frontier --roles final` would have opened the sealed final split (971
  documents in the role map) and written an artifact attesting `final_reads: 0`. The disclosure
  would have been a lie produced by the disclosure mechanism itself. It was never executed, but
  the path existed (reviewer ruling R1).

  It is now closed with an **allowlist**, `reanalysis.assert_reanalysis_role`: only `development`
  and `certification` are permitted, every other role — named or unknown — raises `SealedRoleError`,
  and the guard fires in `_load_reanalysis_splits` before any file is opened as well as inside
  `load_split_system_data`, the single door to gold. Tests exercise the actual command path with a
  sealed role, using non-existent input paths so that a pass proves the guard fired before any read
  rather than after. The lesson generalises: an access log records what a caller *did*, so it can
  only be trusted behind a guard that constrains what a caller *may do*.
- No certificate at any α. The frozen α = 0.20 result stands exactly as recorded; its artifact hash
  `71c0de3e…` is unchanged.
- No write-up. Drafting is a separate step, gated on the independent review of this ADR's artifacts.

## 6. Defects found during review and left open, deliberately

Both were found by the independent review of this ADR
(`evidence/plan3/reviewer_record.reanalysis.json`). Recording them is the point: an
acknowledged defect that is not written down is a defect that returns.

- **`claims.py` treated untracked evidence as resolved.** `unresolved_evidence` checked
  `Path.exists()`, not whether the path is git-tracked, and `publishable()` ignored `verified_by`
  entirely. So a claim citing an uncommitted artifact passed `verify-claims`, and a claim whose
  `verified_by` said "pending review" still counted as publishable.

  **Now fixed, in two deliberately different scopes** (see §7 below for why they are not the same
  kind of change):
  - `untracked_evidence` runs `git ls-files` and reports evidence that exists locally but is not
    committed. An uncommitted artifact resolves perfectly on the machine that produced it and not
    at all for a reader, so a claim resting on one is unsupported the moment it is published.
    `verify_ledger` now fails closed when tracked status cannot be determined at all — "I could
    not tell whether the evidence is committed" is not a pass for a publication gate — with an
    explicit `require_tracked=False` for deliberately verifying outside a checkout.
  - A claim may not hold a public surface while its own `verified_by` reports verification
    pending. Enforced at construction, like the other claim rules, so it cannot be bypassed by
    calling `publishable()` directly.

  **This is narrower than re-defining `publishable()`, on purpose.** The reviewer's warning was
  that changing what `publishable()` means silently re-classifies all fourteen existing claims.
  It does — so that is not what was done. The pending-verification rule targets exactly the harm
  named and re-classifies nothing: all twelve currently-publishable claims already record a
  completed verification, and the two carrying `pending` wording hold no surfaces. Verified by
  running it: 14 claims, 12 publishable, before and after.

  **The pending rule is a regression tripwire, not a verification gate, and the name must not be
  read as evidence the hole is closed.** Measured against 18 strings that genuinely describe
  pending verification, it catches 7 and **misses 11** — including "under review", "in progress",
  "unreviewed", "no reviewer yet", "self-assessed by the implementer" and "verification
  outstanding". An unverified claim can still be published; only the specific literal regression is
  caught.

  It is anchored to the leading token after measurement showed the unanchored form was close to
  inverted: it blocked "independent review complete; no items **pending**" and "review closed;
  nothing **awaiting** sign-off" while passing most genuine cases. That is worse than useless — it
  applied pressure toward vagueness in exactly the field the honesty doctrine depends on, blocking
  a detailed provenance record while passing the word "reviewed". The anchored form has zero false
  positives across the same corpus. **Lesson: a substance-blind rule must be measured on realistic
  inputs before shipping; this one's flaw was not visible from reading the pattern.**

  Still open, and deliberately: `verified_by` remains free text, so the rule reads wording rather
  than structure. The fuller fix is a typed field — a reviewer-record path plus a verdict, checked
  for existence like `evidence` — which would re-classify existing claims and therefore belongs to
  its own review, not this one.

  One precision on the tracked check: `git ls-files` reads the **index**, so a staged-but-
  uncommitted file counts as tracked. That is one step weaker than "a reader can fetch it".
  Tracked is the right condition for this gate — an untracked file is certainly unpublishable —
  but it does not establish that evidence has been pushed anywhere.
- **The `--roles` sealed-split hole was not unique to the new commands.** `risk-coverage-diagnostic`
  carried it too and would have opened `final` the same way. That one **is** fixed here, because
  the guard is restrictive only and provably behaviour-preserving: after adding it,
  `risk-coverage-diagnostic` regenerates `evidence/plan3/risk_coverage_diagnostic.json`
  byte-identically. `tests/test_reanalysis.py::test_every_split_reading_command_refuses_a_sealed_role`
  discovers the command list by introspecting the Typer app for commands that declare a `roles`
  option, so a **new** unguarded command fails it rather than passing silently.

## 7. The accepted plans are now in the repo

> **Amended 2026-07-28.** The sentence below named the private planning directory the plans were
> copied from, as a relative filesystem path into it. The path is removed and is not restated here —
> a note recording the removal of a string does not need to reproduce it, and the change is legible
> in git history. The provenance claim — that the copies are byte-identical to an external
> authoritative source — is unchanged, as is everything else in this section. Recorded in the
> dated-note form §1 uses, rather than made silently, because this ADR was ruled on by four review
> passes and a reader who finds a reworded sentence with no note cannot tell whether the change was
> reviewed.

All four accepted plans are committed, one per gate directory as `accepted-plan.md`
(`docs/gate0/`=Plan 1, `docs/plan2/`, `docs/plan3/`, `docs/plan4/`), copied byte-identically from
the private planning directory that held them. Until now the repo cited roughly twenty distinct `§N.M`
sections it did not contain, and the ADR 0011 reviewer flagged that as limiting what they could
rule on — correctly, as §1's amendment shows: the repo's gloss on §6.3 was **stricter than §6.3**,
and this ADR was originally argued against the gloss.

They are historical records. An accepted plan is amended by appended, dated note — never rewritten
to match what was actually built. `tests/test_doc_references.py` excludes them from its
resolve-every-named-test check for that reason: a plan naming a test is issuing an instruction
about work not yet done, not asserting a guarantee that currently holds.

### Deliberate duplication, recorded

`cli._reanalysis_inputs` repeats the RAMS loading and `gold_frames` closure that `certify` and
`risk-coverage-diagnostic` each already contain. Refactoring all three onto one helper is the
tidier change and was **not** made: those two commands produced committed artifacts whose
byte-reproduction is a verification step, and a cosmetic refactor of their internals is the wrong
risk to take for the benefit. The re-analysis path is instead pinned to the same
`aggregate_to_groups` and `document_loss` the certifier uses, which is where a divergence would
actually matter.
