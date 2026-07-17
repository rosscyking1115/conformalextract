# Plan 2 Claude Code handoff — paused checkpoint

Date: 2026-07-17.  Plan 1 is closed at Git commit `c719217` with an
independent Reviewer `PASS`; Gate 0 decision is `go`.  Plan 2 is active on
branch `codex/plan2-training`.  Plans 3 and 4 remain blocked by sequential
review gates.

## Safe state

- The private GitHub repository is `rosscyking1115/conformalextract`.
- The private Hugging Face evidence Dataset is
  `rosscyking/conformalextract-evidence`.
- The active Hugging Face CLI login is user `rosscyking`; do not print,
  move, commit, or re-enter any token.
- All eight historical HF Jobs are terminal.  Recorded spending is at most
  `$0.2008`; the authorised aggregate cap leaves `$24.7992`.
- RAMS and WikiEvents raw source material exists only under ignored
  `data/raw/`; never add it, predictions with recoverable text, sealed
  labels, checkpoints, or credentials to Git.
- `graphify-out/` is absent; `rg` is the approved fallback for repository
  discovery.

## Work-in-progress files

The paused implementation introduced these files and changes:

- `src/conformalextract/preparation.py` and `tests/test_preparation.py`
  (metadata-only profile and context-ladder/manifests work).
- `src/conformalextract/training.py` and `tests/test_training.py`
  (pure QLoRA, stage-ledger, document-aggregation contracts).
- `configs/plan2_sources.json` and `docs/plan2/data-contract.md`.
- `src/conformalextract/cli.py` adds the `prepare-data` seam.
- `src/conformalextract/selection.py` and `tests/test_selection.py` change
  confidence selection to allow structural `-inf` as the worst score while
  rejecting NaN and `+inf`.

Current validation: `uv run pytest -q` passes **61 tests**.  Ruff and mypy
are not yet green.  Fix their exact reported line/import issues before
treating this as a complete vertical slice, then run:

```powershell
uv run pytest -q
uv run ruff check .
uv run mypy src
git diff --check
```

## Mandatory design corrections from the independent preflight audit

1. RAMS has 9,124 trigger frames but approximately 3,988 independent source
   documents.  Train/generate per given trigger only if needed, but aggregate
   all frames into one document `PredictionRecord`; document acceptance means
   every frame is valid and confidence is the minimum frame confidence.
   Support empty-gold and multi-role frames.
2. Keep the pre-training/R0 context ladder separate from R1 compatibility
   tuning.  R2 must inherit the selected R1 configuration rather than being
   rejected for having non-default values.
3. Remote HF Jobs must not upload local raw data.  Each job must download the
   official source ephemerally, verify frozen checksums, materialise only
   allowed inputs, delete raw archives/extractions, then launch training or
   generation with allowlisted explicit paths.
4. Training must make certification/final/shift gold unrepresentable and
   unreachable before model loading.  Development gold is allowed only for
   development selection—not SFT or generation.  Use negative tests with
   sentinels and a hash-linked label-access log.
5. Persist only adapters, aggregate metrics, hashes, and label-free manifests
   during Plan 2.  Generated predictions containing grounded text require a
   separate privacy decision before upload.
6. Naive unbatched inference exceeds the remaining $24.7992 cap.  R0 must
   benchmark padded batching on the real prompt-length distribution, produce a
   conservative all-stage forecast (R1/R2/predictions/upload/reserve), and
   return an honest stop/infeasible decision if it does not fit.

## Remaining Plan 2 sequence

1. Finish and independently review the pure contracts and seven metadata-only
   manifests.
2. Run private `prepare-data` and freeze real context-window evidence.
3. Verify private Trackio and the second private adapter destination without
   GPU spend; Trackio may contain aggregate metrics and hashed IDs only.
4. Freeze the stage/time/cost ledger, then run R0 only if the above gates pass.
5. Proceed R1 pilot → R2 full only when R0’s forecast fits the cap; R3 only
   for a predeclared recoverable failure with remaining budget.
6. Select exactly one QA checkpoint on development data; prove fresh-process
   reload/resume and parsed-output equivalence; persist two checked adapter
   copies plus aligned ZS/FS/QA label-free prediction manifests.
7. Confirm no billable job remains, then obtain an independent Plan 2 Reviewer
   `PASS` before starting Plan 3.

Do not force a training result, certification claim, or release if any gate
returns `revise`, `stop`, or `infeasible`.
