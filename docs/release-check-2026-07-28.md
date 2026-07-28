# Release-readiness check — 2026-07-28

> **This is a dated record of one check, not a description of the repository's present state.** It
> was run on 2026-07-28 against HEAD `80ec2fa` and is **not maintained after that date**. Where it
> reports a fix, the fix was made in the same change as this report; where it reports a hold, the
> hold was open on that date and may have been resolved since. Read it as a reviewer record is read
> — past tense, scope-bounded — and check the tree, not this file, for what is true now.
>
> **The one live item does not live here.** Whether reviewer records belong in a public evidence
> bundle is an open Plan 4 release-policy decision, not a finding about 2026-07-28, and it is
> recorded in [`docs/plan4/open-release-decisions.md`](plan4/open-release-decisions.md).

**Assessment only. Nothing was deleted, moved, committed or pushed by the scan itself.** This is not
Plan 4 execution; Plan 4 has not opened. Remediations described as applied were made deliberately in
the same change and independently reviewed.

**This document deliberately contains every string it reports as a leak** — `_pmo`, and the operator
path fragments in the grep pattern below. A scan has to be re-runnable to be worth anything, and a
pattern cannot be re-run if it is redacted. That is mention, not use, the same category the honesty
doctrine already permits for forbidden wordings.

It follows that **no bare count of those strings can ever be the check.** Any number is stale the
moment something quotes the strings in order to report them — this paragraph included. The honest
form carries an exclusion list: outside the artifacts that exist to report the leak (this report, the
held reviewer record, and the records ruling on both), the strings appear nowhere. A test can carry
that exclusion list; a sentence in a report cannot, which is the argument for making this mechanical.

## What is actually true about this repository

**It is `PRIVATE`.** `gh repo view` returns `"visibility":"PRIVATE"`, `"isPrivate":true`. The
description is empty and there are no topics. **Nothing here is published, and nothing has been.**

The README is therefore a **prospective** public surface, not a live one. Work in this repository has
sometimes been discussed as though the README were already the front page; it is not. That does not
lower the bar. Plan 4 is the unstarted release plan, the claim ledger exists precisely so that what
may be published is settled before anything is, and a claim written now is the claim that ships
later. But the report should say what is true rather than what was assumed, so: private, unlisted,
undescribed.

## Per-check results

| # | Check | Verdict |
|---|---|---|
| 1 | Claims-vs-reality | **PASS** |
| 2 | Secret scan | **PASS** |
| 3a | Internal-path strings | **FIXED** — 2 of 3 reworded; 1 held, see below |
| 3b | Retired-brand strings | **NOT RUN** — reference list absent |
| 4 | Dead links | **PASS** |
| 5 | Honesty framing | **PASS** |
| 6 | Gitignore completeness | **FIXED** |

### Check 3b is unrun, not passing

The skill's `references/banned-strings.md` **does not exist** — only `SKILL.md` is installed in the
operator's local skills directory. The retired-brand list it was meant to supply was
therefore never applied, and **no verdict on retired-brand strings is available from this report.**
It is recorded here as an unrun check rather than folded into a passing one. Check 3a below was run
with explicitly supplied patterns, which are recorded so the scan reproduces.

### 1. Claims-vs-reality — PASS

Every quantitative sentence in `README.md` carries a `CX-` claim ID; every cited ID is granted the
`README` surface (enforced by `tests/test_doc_references.py`). `uv run conformalextract verify-claims`
→ `ok: true`, 14 claims / 12 publishable, `unresolved_evidence {}`, `untracked_evidence {}`.

### 2. Secret scan — PASS

```bash
git grep -nE "hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}" -- . ':!uv.lock'
```

No match. No `.env*` file is tracked. `data/raw/`, `data/sealed/`, `data/private/`, checkpoints,
adapters and `access-log.jsonl` are all gitignored.

### 3a. Internal path strings — two fixed, one held

```bash
git grep -n -iE "C:\\\\dev|C:\\\\Users|leaff|_pmo" -- . ':!uv.lock'
```

At the time of the scan, internal infrastructure paths were committed in three tracked files, all
naming a private planning directory outside the repository:

| File | Leak | Outcome |
|---|---|---|
| `docs/plan3/phase-a-implementation.md:4` | absolute path to the private plans directory | reworded |
| `docs/adr/0011-reanalysis-frontier-and-loss-channels.md:294` | relative path to the same directory | reworded |
| `evidence/plan3/reviewer_record.reanalysis.json:337,383,398` | both forms, ×4 | **held** — see below |

**Two were reworded.** Both were stale as well as leaky: all four accepted plans had been brought
in-repo (recorded in ADR 0011 §7, and pinned to their hashes by `tests/test_doc_references.py`), so
`phase-a-implementation.md` was pointing outside the repository at a document that by then sat
beside it. It now cites `accepted-plan.md` directly. The ADR line keeps its provenance meaning
without the path, under a dated amendment note.

**One was held, deliberately: `evidence/plan3/reviewer_record.reanalysis.json`.**
`evidence/*/reviewer_record*.json` are immutable evidence artifacts that other documents cite.
Rewriting one to tidy a path would edit an artifact the honesty doctrine treats as fixed, and the
paths there sit inside first-person prose recording what was hashed against what — so redacting
them breaks the attestation rather than tidying a citation.

**That is a release-policy decision, not a hygiene fix.** It is recorded as open in
[`docs/plan4/open-release-decisions.md`](plan4/open-release-decisions.md), where Plan 4 will look
for it, with both options and the reasoning that must survive either.

### 4. Dead links — PASS

All internal Markdown links in `README.md` and `docs/writeup/draft-2026-07-28.md` resolve to files
that exist. External links not fetched (no network calls made during this scan) — **stated, not
skipped silently.**

### 5. Honesty framing — PASS

```bash
git grep -in "production.grade" -- . ':!uv.lock'
```

Six hits, **all legitimate** on inspection — this is a judgement call, not a blind pass:

- `README.md:150`, `CLAUDE.md:9`, `REVIEW.md:28` — all *negations* ("Not production-grade")
- `src/conformalextract/claims.py:90` — the forbidden-pattern definition itself
- `tests/test_claims.py:66` — a fixture asserting the pattern rejects the phrase
- `evidence/plan4/reviewer_record.writeup-draft.json:331` — a reviewer quoting the pattern

No use-as-claim anywhere. Mention, not use.

### 6. Gitignore completeness — FIXED

`.claude/` and `.agents/` were ignored **only** by the operator's global gitignore, not by the
repository's own `.gitignore`. On a fresh clone by anyone else — or on another machine — agent
configuration would appear as untracked and could be committed by accident. For a repository
intended for publication this is the wrong place for that rule.

`.superpowers/` self-ignores via a nested `.superpowers/sdd/.gitignore` containing `*`. It works
today and leaks nothing, but the protection is invisible from the root `.gitignore`.

**Applied to `.gitignore`:**

```gitignore
.claude/
.agents/
.superpowers/
.hypothesis/
```

## Editorial finding — internal governance vocabulary on the README

Not a leak, and outside the six checks, but it is what "is this fit to show publicly" turns on.

The README currently addresses an internal audience in several places:

- `README.md:22` — "**not started, not authorised**"
- `README.md:32–35` — "require the owner's explicit approval; every change to evaluation,
  certification or release policy requires an independent review"
- `README.md:121` — "No paid run proceeds without explicit owner approval; a plan's budget ceiling
  is not spending permission"

These are instructions to agents working in the repository, not information for a reader evaluating
the work. The gate/plan vocabulary itself is **not** a problem — the evidence trail is this
project's subject matter — but "not authorised" and "budget ceiling is not spending permission" read
as internal process control.

**Actioned.** The audience is now split. The README states what was done, what was found and what may
be claimed, and points to `CONTRIBUTING.md` and `AGENTS.md` for the rest. The approval rules moved to
`AGENTS.md`, which already held the $25-cap approval rule and the review gate. Two things were
genuinely new and are added by this same change, not merely relocated: the nuance that a budget
ceiling in a plan is not permission to spend it, and the claim-citation obligation now in
`CONTRIBUTING.md`, which was recorded nowhere.

One line in the same passage was **stale**, not just misdirected: the README said the write-up "is
not started" after a first draft had been committed. Corrected in the same change. It is the defect
this whole sweep began with, reintroduced by the commit that added the draft — which is the argument
for the README pointing at generated or tested state wherever it can.

README wording is a claims surface, so this change is routed for independent review like the others.

## The path check is portable, and three repositories needed it this week

Recorded as a recommendation, not an adoption. **Nothing outside this repository has been changed.**

`tests/test_internal_paths.py` was built for one defect here, but the defect class is not local to
this repository. Three instances in one week, in three repositories, all the same shape — a
machine-local path treated as if it were durable:

| Repository | Instance | Consequence |
|---|---|---|
| `lakehouse-capstone` | Jobs API run IDs held only under a local temp directory | blocked a C4 assessment |
| `agent-release-gates` | a machine-local temp file recorded as the provenance of a committed evidence artefact | a published verdict was not reproducible |
| `conformalextract` | private planning paths in tracked docs — then a hygiene report that introduced operator home paths while removing them | this report |

**The test would have caught all three, and caught the third before it was committed** — which is
not a projection: the stale-exception guard rejected an over-broad entry on its first run, and the
untracked-file probe fails on exactly the case `git grep` could not see. That last point is what
makes it worth porting rather than re-deriving: the two failures here were invisible to an
index-based scan, and an index-based scan is what every one of these repositories would reach for
first.

Porting it needs three edits and no new thinking: the `ALLOWED` list (each repository's own
legitimate quoters), `PROSE_SUFFIXES` if the repository holds other readable formats, and
`SKIP_DIR_NAMES`. The patterns match the *shape* of an operator path rather than any username and
should carry across unchanged.

**Not adopted elsewhere by this change**, and each of those repositories would want its own
exclusion list reasoned out rather than inherited — an exclusion copied from another repository is
the blanket this design exists to prevent.

## Reproducing this report

Every grep above is recorded inline. Re-run them after any remediation; check 3 and check 6 are the
only two that should change verdict.

## One pointer that is owed and not made

`REVIEW.md` now points at `redteam-foundry`'s
`docs/findings/what-does-this-metric-return-when-nothing-happened.md`, which catalogues six
instances of the same failure one level down — metrics satisfied by the absence of what they
measured, so scope did not cover what the **name** claimed, where here scope did not cover what the
**sentence** claimed.

**The reciprocal pointer, from that catalogue back to this gate, has not been made and is not this
repository's commit.** That repo is closed. Recorded here so the debt is visible rather than
forgotten: until it is made, a reader arriving at the catalogue sees six bugs in one harness and
has no route to the mechanism.

## What was NOT checked

- The retired-brand list (reference file absent — see above).
- External link liveness (no network calls).
- Licence/redistribution compliance of the evidence bundle — that is a Plan 4 gate with its own
  review, not a hygiene scan.
