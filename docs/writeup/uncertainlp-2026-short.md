# A well-ranked score that certifies nothing: selective risk control for document-level event-argument extraction

> **Status: DRAFT for UncertaiNLP 2026 (short, 4 pages), 2026-08-02. Not submitted.**
> Two review packets this draft depends on are outstanding and neither is discharged:
> [`../plan3/sections-11-and-12-disposition-amendment-1.md`](../plan3/sections-11-and-12-disposition-amendment-1.md)
> (the §11.3 diagnostics in §4 and §5 below) and
> [`../plan3/claim-narrowing-2026-08-02.md`](../plan3/claim-narrowing-2026-08-02.md) (the wording of
> §5 and §6). **No number here may be submitted, posted or quoted until both pass.** Every
> quantitative sentence is bound by
> [`../plan3/certification-result.md` → "What may and may not be claimed"](../plan3/certification-result.md);
> claim IDs refer to [`../../evidence/plan4/claim_ledger.json`](../../evidence/plan4/claim_ledger.json)
> and the [generated appendix](claims-appendix.generated.md).
>
> **Not yet formatted for the venue.** ACL style files are not in this repository — see
> "Remaining work" at the end.

## Abstract

Selective prediction is usually judged by how well a confidence score *ranks* correct outputs above
incorrect ones — AUROC, AURC, rank correlation. Distribution-free risk control asks a different
question: how much output can be accepted while provably bounding error on what is accepted. We
show these can diverge by an order of magnitude on the same system. We define a frozen,
sealed-split selective-certification protocol for document-level event-argument extraction on RAMS,
with the source document as the independent unit and mean bounded frame loss as the document loss,
and run it once on a QLoRA-adapted Qwen3-4B and two prompted baselines. All three are infeasible at
a 20% risk target with 95% confidence and a 20% acceptance floor. The adapted system's confidence
score is *not* weak by selective-prediction standards — group AUROC 0.796, Spearman ρ = −0.403 —
yet it delivers 2.0% acceptance where a perfect ranking of the same population reaches 23.6% and
would clear the floor. Risk control needs the top of the ranking to be nearly clean, not the whole
ranking to be ordered, and ranking metrics do not report that. We also find that the choice of
independent unit is itself decisive: mean loss is flat in triggers-per-document while the share of
acceptable documents falls from 17.3% to zero.

## 1 Introduction

Two literatures measure confidence and rarely meet. Selective prediction and hallucination
detection report **ranking quality**: AUROC for separating correct from incorrect outputs, area
under the risk-coverage curve, rank correlation against loss. Distribution-free risk control
reports **certified acceptance**: the fraction of inputs a policy may accept while a finite-sample
bound holds on the error rate among accepted inputs.

These are not the same quantity, and the gap between them is not a technicality. A score can order
a population well on average and still fail to isolate a clean prefix — and it is the prefix, not
the ordering, that a certificate needs. This paper reports a case where that gap is an order of
magnitude, on a task where both numbers are worth having.

**What we contribute.** We state up front what is *not* new. That conformal risk control frequently
cannot certify LLM outputs, that base risk `μ` forces abstention of at least `(μ−α)/(1−α)`, and
that this bites across multiple systems, are all established by Kotte (2026, arXiv:2606.29054),
which we read on 2026-07-18 and folded into this study's design three days before its parameters
were frozen. Roughly 80% of what we measured is a replication of that work in a new task. Three
things are ours:

1. **A protocol** (§2): a frozen, sealed-split certification for event-argument extraction at the
   **source-document** unit, with mean bounded frame loss as the document loss. Kotte evaluates no
   event-argument extraction; we found no prior application of distribution-free risk control at
   this unit for this task, though we have not run a systematic survey.
2. **The ranking/certification divergence** (§4): the paper's main finding, and the one an
   uncertainty audience can act on.
3. **A dissociation between grounding and certifiability** (§5), measured rather than asserted.

## 2 Protocol

**Task and unit.** RAMS (Ebner et al., 2020), in-domain. A system may **abstain** on a document
rather than emit event frames. The independent unit is the **source document**, which we call a
*group* because one source document carries one or more trigger instances: it is the level at which
the corpus has near-duplicates, so it is the level at which independence is defensible. **Group
loss** is the mean bounded frame loss over the document's triggers (1 − span-exact micro-F1 per
frame); a structurally invalid or ungrounded output scores 1.0 and is never rewarded for content it
did not produce. **Group score** is the **minimum** confidence over the group's instances, and a
group is eligible for acceptance only if **every** instance parsed and grounded. Accepting the
weakest member's score and averaging the loss is a deliberate pairing — it is what makes acceptance
a statement about the whole document — and §4 shows it is also consequential.

**Target, frozen before any sealed label was read.** Risk α = 0.20, confidence δ = 0.05, acceptance
floor 0.20. The target is a commitment this study made, not a natural constant. Nothing below
relaxes it and no certificate is issued at any other operating point.

**Systems.** Zero-shot (ZS), few-shot (FS), and a QLoRA-adapted (QA) Qwen3-4B-Instruct-2507, all
served on one frozen 4-bit vLLM stack. Confidence is mean transition log-probability over the
parsed object; two alternatives (10th percentile, minimum) were pre-registered and are reported.

**Discipline.** The certification split was opened **exactly once** — 3,152 documents forming 1,396
groups — under a hash-chained access log, with zero reads of the held-out `final` and `shift`
splits, which remain sealed (`CX-SEALED-01`). Certification and all analysis ran on CPU at no cost;
the GPU programme totalled about $18.7–18.9 (`CX-COST-01`).

## 3 The null

**No system certifies** (`CX-H1-PRIMARY`, `CX-H2-SECONDARY`). All three are infeasible under the
primary construction and under a conservative audit. Because both baselines are infeasible, the two
pre-registered comparisons collapse to **one** finding, not two, and no numerical difference is
computed against an infeasible baseline.

The result is not an artefact of the bound. Under an **oracle** reading — unlimited threshold grid,
zero finite-sample penalty, threshold chosen with the labels in hand — the best system still
accepts at most **2.0%** of documents at 20% empirical error, against a floor of 20%
(`CX-CAPGAP-01`). The same diagnostic on the development split gives 3.0%, so it reproduces out of
sample. Nor is the target a specially unlucky choice: on the oracle risk-coverage curve the 20%
floor first becomes reachable at **empirical oracle frontier points** of 0.406 (QA), 0.930 (FS) and
0.981 (ZS) (`CX-ALPHA-FRONTIER-01`). These are frontier points measured after the split was opened,
from its own labels — **not thresholds, and not certified operating points**. The curve rules
operating points out; it never rules one in, and no claim here uses it in that direction.

| Certification split, 1,396 groups | ZS | FS | **QA** |
|---|---|---|---|
| base risk `μ` (group level) | 0.9923 | 0.9580 | **0.6071** |
| ineligible groups (any invalid member) | 1,020 | 684 | **130** |
| arithmetic bound `1−(μ−α)/(1−α)` | 0.0096 | 0.0525 | **0.4911** |
| **loss-optimal oracle acceptance** | 0.0036 | 0.0244 | **0.2357** |
| acceptance delivered by the score | 0.0000 | 0.0000 | **0.0201** |
| AUROC (error detection) | 0.344 | 0.727 | **0.796** |
| normalized AURC (0 = perfect, 1 = chance) | 0.926 | 0.920 | **0.531** |
| Spearman ρ, score vs group loss | −0.027 | +0.073 | **−0.403** |

*Each system at the confidence candidate its development gate selected (QA and ZS mean, FS 10th
percentile); all nine system × candidate combinations are in the released artifact.*

**Two different failures, which must not be merged.** For ZS and FS the arithmetic settles it: base
risks of 0.992 and 0.958 permit at most 0.96% and 5.25% acceptance, and their loss-optimal oracles
are 0.36% and 2.44% — an order of magnitude below the floor. **No score whatever could certify
them.** QA is the interesting case, and §4 is about it.

## 4 Ranking quality does not transfer to certified acceptance

Read as a selective-prediction result, QA's confidence score is respectable. Group AUROC for error
detection is **0.796**. Rank correlation against group loss is **ρ = −0.403** at *p* ≈ 1e-55, and a
normalized AURC of **0.531** says the score closes roughly half the distance between a random
ranking and a perfect one. On the development split the same figures are 0.834, −0.313 and 0.568.

Kotte's Table 5 gives the natural comparison, and it is a close one. Log-probability scores there
reach AUROC 0.485–0.604 across NER, QA and classification — but **0.793 on JSON extraction**, the
one structured-generation task in that paper. Our 0.796 sits almost exactly on it. Two independent
studies therefore find log-probability confidence discriminating errors at close to 0.80 AUROC on
structured generation, and the comparison is worth making precisely because the certification
outcomes diverge completely: JSON extraction has base risk 0.033 and certifies easily, ours has
0.6071 and does not. **The score quality is the same; the certified acceptance is not.** (Not a
like-for-like measurement — theirs is instance-level and ours is group-level over documents — so
the agreement is indicative rather than exact.)

Read as a risk-control result, the same score is close to useless. It delivers **2.0%** acceptance
at α = 0.20. A perfect ranking of the identical population delivers **23.6%** — which clears the
20% floor. **The target was reachable by ranking alone, and the score reached less than a tenth of
what was available.** Figure 1 is that sentence as a picture.

![Risk-coverage curves for the QLoRA system on the certification split. Both curves cover the same
1,396 groups and differ only in how they are ranked: red accepts best-scoring groups first (what
the certifier sweeps), blue accepts lowest-loss groups first (what a perfect ranking would reach).
Where each crosses the α = 0.20 rule is the acceptance it supports — 0.0201 against 0.2357. The
acceptance floor at 0.20 sits between them, so the blue curve clears the target and the red does
not. The gap between the crossings, 0.216, is attributable to the ranking alone: the population is
held fixed.](fig/risk-coverage-qa.pdf)

*Figure 1.* Generated by `scripts/plot_risk_coverage.py`, which reads the same guarded loader the
certifier uses and refuses to draw if its recomputed curve disagrees with the committed
`evidence/plan3/alpha_frontier.json`.

We report that gap against the loss-optimal oracle rather than against the arithmetic bound, and
the distinction matters. The bound `1−(μ−α)/(1−α)` gives 49.1% for this population, but it assumes
the population's "goodness" can be concentrated arbitrarily, which this population does not supply.
Quoting 49.1% would charge the score for 25 points that were never on offer. The honest shortfall
is **21.6 points, not 47** — a correction we make against our own earlier framing.

**Why good ranking does not buy a certificate.** A certificate at α needs the accepted *prefix* to
average below α. Global ordering quality does not guarantee that any prefix is clean enough. QA's
best-scoring 5% of groups still average **0.274** loss; at 10% coverage, 0.324; at 20%, 0.405. The
running risk never drops below the target at any coverage worth having. AUROC integrates over all
pairs and is dominated by the bulk of the distribution, where this score does order documents
sensibly; the certificate depends entirely on the extreme tail, where it does not.

This is the practical message for uncertainty work: **an AUROC in the 0.8 range is not evidence
that a score can support risk-controlled selective prediction.** The two should be reported
together, and where a paper reports only ranking metrics, the certified quantity may be an order of
magnitude worse.

**The unit definition is also decisive**, and this is easy to miss. Stratifying QA's groups by
number of triggers per document, mean group loss is essentially flat (0.606, 0.608, 0.589, 0.634,
0.596 from 1 to 6+ triggers) — but the share of groups whose loss is within α collapses from
**17.3% to 0.7% to zero**, and 23 of the 28 oracle-accepted groups are single-trigger documents.
Groups with three or more triggers contribute **none**. Averaging frame loss across a document and
scoring the group by its weakest member makes acceptance vanish with document complexity even where
mean loss does not move. Cross-sentence argument distance behaves the same way: 25 of 28
acceptances have no cross-sentence argument, and groups with three or more contribute none. A
protocol that reports only aggregate loss will not see either effect.

## 5 What the adapter changed, and what it did not

QLoRA adaptation produced a large, real improvement in **grounding fidelity**: 95.7% of QA outputs
parse and ground to the source document against 39.4% zero-shot and 68.1% few-shot, with ungrounded
spans falling from 5,355 to 340 (`CX-GROUNDING-01`). "Valid" here means parseable and grounded,
**not correct** — a span can point at real document text and still name the wrong entity or role —
and **this improvement did not translate into a certified selective guarantee**. Neither half of
that sentence may be reported without the other.

Decomposing loss into four channels says why (`CX-GROUNDING-ORTHOGONAL-01`). The ~16×
separation in ungrounded spans lives in the channels that are forced to loss 1.0 or are contentless.
The certificate scores the fourth channel — well-formed, grounded, content-bearing output — which
holds **90.3%** of QA's documents and **87%** of its loss, at a within-channel mean loss of 0.579.
The adapter moved the channels the certificate does not score and left the one it does.

**This is a dissociation, not an orthogonality result.** One intervention observed across three
systems cannot establish that two properties are independent, and we did not test independence. At
group level the two are in fact weakly associated — grounded share against group loss gives
ρ = −0.206 at *p* ≈ 8e-15 — but the 1,266 QA groups whose every member is grounded still average
**0.589** loss, roughly three times the target. Grounding was necessary and nowhere near sufficient.

The decomposition locates loss by channel; it does **not** identify the error category that produced
it, and we claim none. An earlier version of this claim attributed the residual to output "that
names the wrong entity"; that rested on unquantified inspection of two development examples and was
withdrawn on independent review. A measurement points elsewhere — on these frames false positives
exceed false negatives by 637 arguments, which is over-generation rather than entity-naming.

## 6 Relation to prior work

Kotte (2026) establishes the impossibility bound, the base-risk feasibility test, and infeasibility
across multiple systems; we reproduce all three in a new task and at a new unit. Our measured base
risk (0.6071) is **not** a reproduction of their extraction figure and does not contradict it: their
one extraction task, JSON-Extract, sits at μ = 0.033, a different task under a different metric. The
comparison marks out a harder operating regime and settles nothing about their number.

**This is not a task-wide impossibility, and must not be read as one.** A 20% target is demonstrably
reachable on structured extraction: `(μ−α)/(1−α)` forbids nothing at μ = 0.033 and permits up to
80.5% acceptance at μ = 0.356, the easiest NER dataset Kotte reports. What we establish is that
*this* model with *this* score on *this* task at μ = 0.6071 could not — a model- and
score-specific result.

The score-quality comparison in §4 is with Kotte's Table 5 rather than with the semantic-entropy
literature, for a reason worth stating: within that one table, log-probability reaches 0.793 on
structured extraction while semantic entropy reaches only 0.496–0.677 across all eight datasets.
Which uncertainty score is strongest is evidently setup-dependent, and our finding does not need
that question settled — it needs only that the score we used is a normal one, performing about as
well as its family does elsewhere on this kind of task. It is.

> **Provenance of the comparison figures, checked 2026-08-02.** Every number about *our* systems
> resolves to a committed artifact. The external AUROC figures were relayed to this project through a
> research summary rather than read from source, so they were read from source before use and are now
> recorded in `docs/frontier-check/findings.md`. **One was wrong as relayed**: "NLL 0.485–0.604" is
> that band over NER, QA and classification only and **excludes JSON at 0.793**, which is the single
> most relevant cell for this paper. An earlier draft read "above the band Kotte reports for NLL",
> which was false; §4 now states the JSON figure and the argument is stronger for it. The
> self-consistency band 0.600–0.816 checked out across all eight datasets. A claimed mean AUROC of
> 0.790 for semantic entropy (Farquhar et al., Nature 630) could **not** be verified — the Nature full
> text is behind authentication, the earlier arXiv:2302.09664 abstract states no AUROC, and the
> authors' blog post gives none — so it is **not used anywhere in this paper**. Kotte measures
> semantic entropy at 0.496–0.677, well below it; different setups, and we do not adjudicate. A
> fourth figure was dropped the same way in §6: a summary reported Kotte certifying CoNLL NER with
> Ministral-8B at 37% acceptance and risk 0.13, which the repository cannot corroborate, so §6 argues
> from the committed base risks instead.

## 7 Conclusion

On document-level event-argument extraction, a confidence score with AUROC 0.796 and ρ = −0.403
delivered 2.0% certified-eligible acceptance where a perfect ranking of the same population reached
23.6% and would have cleared the 20% floor. Ranking quality and certified acceptance are different
measurements and can differ by an order of magnitude. Selective-prediction work that reports only
the former should not be read as evidence about the latter.

## Limitations

- **Not production-grade**, and no deployment claim is made.
- **The certificate bounds average within-group loss, not the absence of error** in any document.
  Certified ≠ safe.
- **The system is not competitive on extraction quality.** Group loss 0.6071 corresponds to a mean
  per-document span-exact F1 of about 0.393. That is a mean of per-document F1 at the source-document
  unit and is **not** directly comparable to corpus-level micro Arg-C figures such as RoSE's 54.4
  (Huang et al., 2026), but the gap is real and large; we make no claim about competitiveness.
- **Single seed, no training ablations.** One frozen 4-bit vLLM serving stack, with 86.3%
  parsed-output agreement measured against the training stack; the abstain/extract decision itself
  flips between stacks at 1.3–1.8% of frames at plausible operating points (`CX-SERVING-01`).
  Portability is not established.
- **In-domain RAMS only**, under span-exact matching. `final` and `shift` are descoped and remain
  sealed; no distribution-shift claim is made in either direction.
- **The empirical oracle frontier points and the §4 diagnostics are post-hoc on an opened split.**
  They select no threshold and certify nothing.
- **The infeasibility was knowable for $0 before the sealed split was opened**
  (`CX-FEASIBILITY-LESSON-01`): the development-split oracle diagnostic already showed 3.0% against
  a 20% floor and neither the implementer nor the reviewer ran it. Recorded as a joint process
  failure.
- **The self-consistency alternative was not tested.** Agreement-based scores reach AUROC 0.600–0.816
  across Kotte's eight datasets and might behave differently here; we did not run it. Our finding is about
  one score family — transition log-probability — and does not show that no score can certify this
  task.

## Reproducibility

The protocol, certifier, diagnostics and claim ledger are code, and every figure above resolves to a
committed artifact. Released with publication: source, the frozen group mapping, per-system
predictions with confidence candidates, and the certification and diagnostic artifacts. Raw corpus
text and sealed labels are not redistributable.

## Remaining work before this can be submitted

1. **Both review packets must pass** (see the status banner). This is the blocking item.
2. **ACL formatting.** No LaTeX sources exist in this repository and the ACL style files are not
   vendored. Obtaining `acl_latex.sty` and the class files needs a download, which needs your
   go-ahead.
3. **Length check against the real template.** This is written to a 4-page budget but that is an
   estimate until it is typeset; §4 and §5 are where to cut.
4. **References** are cited by name and arXiv id above and need a `.bib`.
5. ~~Verify the external comparison figures against primary sources.~~ **Done 2026-08-02**, and it
   caught a real error — see the provenance note in §4. Kotte's Table 5 is now recorded in
   `docs/frontier-check/findings.md`; the unverifiable Farquhar figure was dropped rather than kept
   with a caveat. No unverified external figure remains in the paper.
6. **Figure 1 is drawn** (`scripts/plot_risk_coverage.py`, matplotlib added as a `docs` extra only
   — never a runtime dependency; nothing under `src/` imports it and no test needs it). It renders
   at 5.5 in wide, which is a full-width `figure*`; at single-column width the annotations will
   need larger relative type. Decide which when the template is in place.
7. **Length is now tight, not comfortable.** ACL counts the abstract and body but not Limitations:
   that is 2,786 words, roughly 3.3 pages of prose, plus the table (~0.25) and Figure 1 (~0.3 as a
   full-width `figure*`) — about 3.85 of the 4 pages. It fits, with nothing spare. **First cut if
   it overruns: the provenance note in §4** (~180 words). It is the right thing to keep in the
   repository copy and the easiest thing to compress to one sentence in a submitted version.
   Second cut: §6's second paragraph.

## References

- Ebner, S., Xia, P., Culkin, R., Rawlins, K., Van Durme, B. (2020). Multi-Sentence Argument
  Linking. *ACL 2020*. arXiv:1911.03766.
- Huang, G. et al. (2026). RoSE: A Role Correlation Structure-Enhanced Model for Multi-Event
  Argument Extraction. *AAAI 2026*.
- Kotte, V. (2026). When Can Conformal Risk Control Certify LLM Outputs? Bounds, Impossibility, and
  Adaptation for Structured Generation. arXiv:2606.29054.
