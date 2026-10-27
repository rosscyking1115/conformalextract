# Release check — 2026-10-27

A public-hygiene sweep run before a proposed visibility change. **It does not open Plan 4's release
gate and it authorises nothing.** The repository was private when the sweep ran and stays private
until the owner rules. The 2026-07-28 check ([`release-check-2026-07-28.md`](release-check-2026-07-28.md))
is the predecessor; this one re-runs it at a later commit and adds history, CI and surface checks.

- Swept at `1bed6b3` (branch `codex/plan4-release`, 39 commits ahead of its remote). Fixes are on a
  local branch, `release/public-prep-2026-10-27`, and are not pushed.
- Every check below records the command that produced it, so the verdict can be re-run rather than
  trusted. A green line is a measurement at a commit and goes stale like the others in this repository.

## Results

| # | Check | Result |
|---|---|---|
| 1 | Secrets, working tree and full history | **pass** — see §1 |
| 2 | Data licences (RAMS, WikiEvents) | **pass**, with the boundary unchanged — see §2 |
| 3 | Evidence privacy re-scan (18 artifacts added since the last clearance) | **pass** — see §3 |
| 4 | Large artefacts | **pass** — largest blob in history is `uv.lock`, 650 KB |
| 5 | Commit authorship and AI attribution | **owner decision** — see §5 |
| 6 | Internal paths and planning references | **pass under decision 1**; disclosed — see §6 |
| 7 | Claims against the ledger, per surface | README **pass**; paper and abstract **open, already known** — see §7 |
| 8 | Gates | `verify-claims` ok; pytest 484 passed, 8 skipped; ruff clean; mypy strict clean |
| 9 | CI | **was failing on every push since 2026-07-17; fixed locally, unverified until pushed** — see §9 |
| 10 | README links | **pass** — 14 relative links, all resolve |
| 11 | Gate state | **Plan 4's release gate is not open** — see §11 |

## 1. Secrets

`gitleaks git . --redact` over all 172 commits on every branch: 10 findings, all rule
`generic-api-key`, all in three evidence files, all false positives. Each match is a 64-character
SHA-256 hex digest under a key whose name contains `key` or `token` (`doc_key_sha256`,
`generated_token_sha256`). No value is a credential. A pattern grep over `git log --all -p` for
Hugging Face, OpenAI, AWS, GitHub and Slack token shapes and PEM private keys returned nothing.
No `.env`, key or credential file has ever been tracked (`git log --all --name-only`). The CI guard
refuses tracked `data/raw`, `data/private` and `.env` files.

`gitleaks dir .` reports many more findings, but it walks the untracked virtual environment and
`data/` tree (8.9 GB). Neither is published by a visibility change, and the history scan covers
everything that is.

## 2. Data licences

Unchanged from [`gate0/licences/`](gate0/licences/): RAMS annotations are CC-BY-SA-4.0, and JHU does
not own the underlying news text, so raw text and text-bearing artefacts are not redistributed.
WikiEvents raw text is likewise blocked. No tracked file carries RAMS or WikiEvents text (§3). The
evidence holds hashes, counts and analytical prose only. The RAMS role ontology appears in tests and
manifests as role names, which are schema identifiers, not corpus text.

## 3. Evidence privacy re-scan

[`plan4/publishable-and-sealed.md`](plan4/publishable-and-sealed.md) §3 cleared 40 artifacts at
`128e52c` and asked for a re-run before any bundle is assembled. Eighteen evidence files were added
or changed since (`git diff --name-only --diff-filter=AM 128e52c HEAD -- evidence`). The same method
was applied to each of them: walk every string field and flag any value of four or more words that
is not a hash. Every flagged field was this project's own analytical prose (reviewer commentary,
claim wording, method notes, configuration status). A second pass over all tracked evidence, for
fields named like text carriers (`*quote*`, `*text*`, `*span*`, `*sentence*`, `*example*`), found
only quotations of this repository's own documents. The original clearance's bound still applies:
prose shape is a heuristic, and a fragment of three words or fewer would not be flagged.

## 5. Authorship

All 172 commits use `rosscyking1115@gmail.com` for both author and committer, and none carries a
`Co-Authored-By` trailer or a generated-by footer. **The author name differs.** 135 commits are
authored as `rosscyking1115` and 37 as `Cheng-Yuan King`. GitHub attributes commits by email, so the
contributor list shows the one account either way. Making the name uniform means rewriting history
and force-pushing every branch, which is the owner's call. The branch names `codex/plan2-training`
and `codex/plan4-release` name an agent tool, and they become public if they are pushed or left on
the remote at the flip.

## 6. Internal paths and planning references

`tests/test_internal_paths.py` passes. The remaining operator paths and planning-directory
references sit in reviewer records and in the 2026-07-28 report, under
[decision 1](plan4/open-release-decisions.md) ("reviewer records publish as-is"). They are
disclosed here rather than removed. To list them, run the grep recorded in the 2026-07-28 report;
the patterns are not repeated here, because doing so would add a new occurrence to the guard. At
`1bed6b3` they are in six tracked files: four reviewer records, that report, and the guard's own
test.

A visibility flip publishes the 24 internal-audience files listed in
[`plan4/proposed-visibility-change.md`](plan4/proposed-visibility-change.md) (agent instructions,
handoffs, briefs, deliberation). Gate G5 there, "every internal-audience file read as public prose",
is still not done, and this sweep did not do it.

## 7. Claims against the ledger, per surface

**README: pass.** It cites six claim IDs, all granted `README`: `CX-H1-PRIMARY`, `CX-CAPGAP-01`,
`CX-GROUNDING-01`, `CX-GROUNDING-ORTHOGONAL-01`, `CX-SEALED-01` and `CX-COST-01`. Each numeric
token was matched against the wording and limitations of every claim. Each figure appears on a
README-granted claim, or is not a claim (ADR numbers, artifact hash prefixes, the code constant
`REMAINING_BUDGET_USD` and its derivation, and the withdrawn "349 tests" quoted as withdrawn).

**Paper abstract and body: open, already recorded.** The abstract of
[`writeup/uncertainlp-2026-short.tex`](writeup/uncertainlp-2026-short.tex) prints group AUROC 0.796
and Spearman ρ −0.403. No ledger claim carries them; `evidence/plan4/paper_claims.json` backs both
against `calibration_diagnostics.json`. The body has many more figures in the same position, backed
by the paper gate but not ledger claims. Plan 4 §10.1 says the abstract is "generated/reviewed
against the claim ledger". This is step 2 of the chain in
[`writeup/uncertainlp-2026-short.md`](writeup/uncertainlp-2026-short.md) ("ledger entries for the
§11.3 quantities … not written"), so it is known, not new. The 11.4% in the abstract is
`CX-CAPGAP-01`'s 0.1139 written as a percentage.

**CV: outside this repository.** Only `CX-COST-01` is granted `CV`.

## 9. CI

`gh run list` showed every run failing, on `main` as well as the release branch, since 2026-07-17.
The failing step is mypy: `uv sync --locked --extra dev` installs neither datasketch nor transformers
nor torch, so the run ends with 7 `import-not-found` / `unused-ignore` errors in `data.py`,
`profiles.py` and `model_smoke.py`. This is the prune gotcha in `CLAUDE.md`. The workflow now syncs
`--extra dev --extra data --extra train`. Locally, `uv lock --check` is consistent and the locked
export resolves torch, transformers and datasketch. **Whether the Linux run passes is unverified
until a push.** It also downloads the CUDA wheels, which is slow but inside the 20-minute timeout.

## 11. Gate state

[`evidence/gate_state.json`](../evidence/gate_state.json) is the authority: Plan 3 is executed but
not closed (its close was refused on O1–O3), and Plan 4 is open by owner override and paused. The
paper's companion states the consequence: nothing may be "submitted, posted, published or quoted
until step 6 issues a PASS", including the public release of this repository. Six steps stand
between here and a close. Five need an independent review that no seat may issue to itself, and
step 2 needs ledger work first.

So visibility gate **G1** (Plan 4 open on a Plan 3 close record) is unsatisfied, as are G2 (V8/V9
re-walked at the flip commit) and G5 (internal-audience files read as public prose). Making the
repository public now would be a second owner override, on the same footing as the 2026-07-29 one,
and the act cannot be rolled back.

## What this sweep changed

One local commit on `release/public-prep-2026-10-27`:

- `.github/workflows/ci.yml`: sync every extra the gates import (§9).
- `README.md`: the Plan 3 and Plan 4 status rows say what the records say, and the write-up
  paragraph names the current paper and its status. No claim, figure or surface grant changes.

## Not done here

`ruff format --check` would reformat 37 files. Formatting is not one of this repository's gates, so
this is recorded and not changed. The gate-chain reviews, ledger entries, history rewrite and
internal-audience read are not within a hygiene sweep.
