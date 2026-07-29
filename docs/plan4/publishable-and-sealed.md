# What is publishable and what stays sealed

- Date: 2026-07-29 · measured against `128e52c` on `codex/plan4-release`
- Status: **ungated Plan 4 work.** Owed under any scope, and not dependent on the three open
  decisions in [`open-release-decisions.md`](open-release-decisions.md).
- **Nothing was published, mirrored, or made visible in producing this. The repository is PRIVATE.**

This is the written statement Plan 4 §2 requires before any artifact is assembled: what may leave
the repository, what may not, and on whose authority. It is a **statement of position, not a
release**, and it decides none of the three open questions.

## 1. Never leaves, on licence grounds

Authority: [`../gate0/licences/release-matrix.csv`](../gate0/licences/release-matrix.csv), and the
per-corpus notes beside it.

| Artifact | Position | Why |
|---|---|---|
| RAMS raw source text | **blocked** | JHU does not own the underlying source text; not redistributable |
| WikiEvents raw source text | **blocked** | no separate dataset redistribution terms recorded |
| Predictions carrying recoverable text | **blocked** | may reproduce restricted source text (ADR 0005) |
| QLoRA adapter weights | **conditional** | requires a data-output and attribution review that has not run |

**Verified, not assumed.** `git ls-files` returns no path under `data/raw/`, `data/sealed/`,
`data/private/`, no `.env`, no `.safetensors`/`.ckpt`, no prediction or divergence `.jsonl`, and no
`access-log.jsonl`. The gitignore covering them is repository-local, not dependent on any
contributor's global configuration.

## 2. Never leaves, on sealed-label grounds

`final` and `shift` remain **sealed and unopened**. `evaluate-final` and `evaluate-shift` are
descoped ([ADR 0010](../adr/0010-descope-final-and-shift.md)) because no selected policy exists to
audit or transport — not for cost, and not because running them is difficult.

The certification split was opened **exactly once**, over 3,152 documents forming 1,396 groups, with
a verified hash-chained access record (`CX-SEALED-01`). Every evidence artifact asserting label
access reports `final_reads: 0` and `shift_reads: 0`, and the guard is structural: only the
`development` and `certification` roles are reachable from the analysis commands, every other role
raising before a file is opened.

**Publishing the certification result does not unseal anything.** The result is aggregate; the
labels themselves are not in the repository and are not in any artifact proposed for release.

## 3. Cleared for release on privacy grounds — reviewed, not asserted

The release matrix marks aggregate evidence *"release only after non-reconstructive privacy
review"*. **That review is this section, and it was run rather than declared.**

Method: every one of the 40 tracked evidence artifacts was parsed and every string field walked,
flagging any value that is prose-shaped (four or more word tokens) and not a hash. 27 files carry
prose-shaped strings.

**Result: none of it is corpus text.** Every flagged field is this project's own analytical or
configuration prose — reviewer commentary, claim wordings, method notes, status enums. The files
that touch real examples were inspected individually rather than sampled:

- `evaluator_adjudication.json` — three prose fields, all method notes on scorer semantics
  ("RAMS uses inclusive spans; the frozen contract uses half-open spans"). No adjudicated span text.
- `model_score_smoke.v3.json` — 20 real generations, held **only** as
  `prompt_sha256` / `output_sha256` / `doc_key_sha256` / `group_id_sha256`. Two prose fields, both
  configuration status strings.
- `certification_result.json` — three prose fields: two hypothesis verdicts and a theorem citation.

**Conclusion: the aggregate evidence bundle is non-reconstructive.** No tracked artifact permits
recovery of RAMS or WikiEvents source text, and the design reason is that the remote jobs were built
to emit hashes rather than text from the start, not that text was stripped afterwards.

**Bounded, as this repository's gates now require.** The scan covers *tracked* evidence JSON. It
does not cover binaries, the untracked `data/` tree, or artifacts on the private Hub, and prose-shape
is a heuristic — a short corpus fragment of three words or fewer would not have been flagged. It is
strong enough to clear the matrix's condition and not strong enough to be called a proof.

## 4. Cleared for release on its own terms

- **Original source code** — Apache-2.0, original work. `src/`, `tests/`, `jobs/`, `configs/`.
- **Aggregate evidence artifacts** — subject to §3 above and to **open decision 1**, which asks
  whether reviewer records form part of the public bundle. That question is open and is not settled
  here.
- **Documentation, ADRs, plans, the claim ledger** — with the caveat that
  `evidence/plan3/reviewer_record.reanalysis.json` contains internal filesystem paths, which is the
  same open decision 1.

## 5. Link audit

All 57 tracked Markdown files, 69 links: **zero broken internal links.** 33 external links were
**not fetched** — no network calls were made — so external liveness is unverified and is recorded as
unverified rather than folded into the pass.

## 6. What this statement does not do

- It does not settle whether reviewer records ship (**decision 1**), what the description says
  (**decision 2**), or what topics are carried (**decision 3**). All three go back to Ross together
  with their recorded options intact.
- It does not authorise a public bundle, a Hugging Face or Kaggle artifact, or a visibility change.
- It does not run the adapter's data-output and attribution review, which remains outstanding and
  blocks adapter release under §1.
- It does not constitute the clean-room reproduction required by §2.2 — that is separate ungated
  work and has not been done.
