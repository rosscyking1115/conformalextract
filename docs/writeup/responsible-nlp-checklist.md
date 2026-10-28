# Responsible NLP Research Checklist — UncertaiNLP 2026 short paper

Answers for the \*ACL Responsible NLP Checklist, which is submitted through the venue's form rather
than inside the 4-page PDF. Kept here so the answers are drafted, reviewable and consistent with the
paper rather than improvised at the submission deadline.

Subject: [`uncertainlp-2026-short.tex`](uncertainlp-2026-short.tex). **Not submitted.**

---

## A. For every submission

**A1. Did you discuss the limitations of your work?** **Yes** — unnumbered `Limitations` section.
It covers: not production-grade; the certificate bounds average within-group loss rather than the
absence of error; the system is not competitive on extraction quality (mean per-document F1 ≈ 0.393,
explicitly *not* comparable to corpus-level micro Arg-C); single seed, no ablations, one frozen
serving stack with a measured 1.3–1.8% abstain/extract flip rate; in-domain RAMS only; `final` and
`shift` descoped and sealed, so no shift claim in either direction; the mechanism-2 and mechanism-3
quantities are post-hoc on an opened split; the infeasibility was knowable for \$0 beforehand and
nobody ran the check; and only one score family was tested.

**A2. Did you discuss any potential risks of your work?** **Yes, and the principal risk is
misreading the result.** The paper is a negative result about certification. Two misreadings are
foreclosed in the text: that the target is unreachable for the task in general (§6 shows it is not
excluded at other base risks), and that a good AUROC implies fitness for risk-controlled deployment
(the paper's central point). A third risk — a reader treating "certified" as "safe" — is addressed
directly in Limitations: the certificate bounds *average within-group* loss, not the absence of
error in any document.

**A3. Do the abstract and introduction summarize the paper's main claims?** **Yes.** The abstract
states the protocol, the three-mechanism decomposition, the AUROC/certified-acceptance divergence,
and that infeasibility is overdetermined. Each figure it quotes appears with its evidence in §3–§4.

**A4. Have you used AI assistants in this work?** **Yes, and substantially.** The analysis code,
the diagnostics, the figure and the draft were produced in collaboration with an AI coding agent
under human direction. Scientific decisions, the target parameters, the review gates and the
submission decision were the author's. Every quantitative claim resolves to a committed artifact
with a reproduction command, and the manuscript was reviewed by independent agents whose findings
are recorded in the repository. *Confirm the venue's exact disclosure wording before submitting.*

---

## B. Did you use or create scientific artifacts?  **Yes.**

**B1. Cite the creators.** RAMS \cite{ebner2020rams}. Qwen3-4B-Instruct-2507 (model card cited in
the repository's source log). Comparison figures from \citet{kotte2026crc}. Prior extraction results
from \citet{huang2026rose}. Conformal risk control \cite{angelopoulos2024crc}.

**B2. Discuss the licence / terms.** RAMS annotations are CC-BY-SA-4.0; **the corpus creators do not
own the underlying source text**, which is why raw text is not redistributed. The ACL style files
are used but **not vendored** — that repository declares no licence. Released artifacts are the
project's own code and derived evidence.

**B3. Consistent with intended use?** **Yes.** RAMS is a public event-argument-extraction benchmark
used here for event-argument extraction. No repurposing.

**B4. Personally identifying or offensive content?** RAMS is built from news text and **does contain
named public figures in their public capacity** — this is inherent to the corpus, not introduced
here. No new annotation was collected. The project does not redistribute raw source text, so no PII
is republished. No anonymisation step was applied to the corpus, and none is claimed.

**B5. Documentation of the artifacts.** Yes: the repository documents splits, the group unit, the
loss definition, the frozen parameters, and the sealed-label discipline; each released artifact
carries its generating command.

**B6. Relevant statistics.** Yes: 3,152 documents forming 1,396 groups in the certification split;
27,372 frames across three systems; per-system eligible and ineligible group counts in Table 1.

---

## C. Did you run computational experiments?  **Yes.**

**C1. Model size and computational budget.** Qwen3-4B-Instruct-2507, QLoRA-adapted, served 4-bit.
The GPU programme — inference benchmarking, training, prediction generation for three systems, and
serving-equivalence probes — totals **about \$18.7–18.9** against an authorised \$25 ceiling, recorded
job by job. All certification and analysis ran on CPU at no cost.

**C2. Experimental setup and hyperparameters.** Frozen before any sealed label was read and recorded
in the repository: α = 0.20, δ = 0.05, acceptance floor 0.20; three pre-registered confidence
candidates; per-system candidate selection on the development split.

**C3. Descriptive statistics.** Partially, and stated as such. The paper reports a bootstrap
confidence interval for the headline AUROC (95% CI [0.737, 0.850], 10,000 resamples) and exact
counts throughout. **It reports a single seed** and no variance over training runs — recorded in
Limitations, not concealed. The central result is a certification outcome, which is deterministic
given the frozen artifacts.

**C4. Existing packages.** Yes: numpy, scipy, pydantic, typer, vLLM, transformers, PEFT, TRL,
matplotlib (figures only). Versions are pinned in `uv.lock`.

---

## D. Did you use human annotators or research with human participants?  **No.**

D1–D5 not applicable. No annotation was collected, no participants were recruited, no crowdworkers
were employed. All labels are RAMS's existing gold annotations.

---

## E. Did you use AI assistants in your research or writing?  **Yes.**

See A4. Disclosed rather than minimised: the work was done with an AI coding agent throughout,
under human direction, with independent agent review and an evidence-first discipline in which no
claim reaches a public surface without a committed artifact behind it.

---

## Open items before submission

1. Confirm the venue's exact AI-assistance disclosure wording and format.
2. Confirm whether UncertaiNLP wants the checklist in the PDF appendix or only through the form.
   This draft assumes the form; if an appendix is required it does not count toward the page limit.
3. B4 deserves a second read by the author: "public figures in public capacity" is accurate for
   RAMS but is the kind of answer a reviewer may probe.
