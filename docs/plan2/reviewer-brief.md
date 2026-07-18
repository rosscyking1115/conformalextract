# Plan 2 independent reviewer brief

Purpose: give a reviewer who did **not** implement Plan 2 a self-contained basis to
return `PASS`, `revise`, or `stop` on the Plan 2 pure contracts. Plan 3 is blocked
until this review returns `PASS`. Do not treat any implementer self-review (including
the `/code-review` self-pass on the branch) as satisfying this gate.

## Scope

- Branch: `codex/plan2-training`
- Review range: `c719217..fb6b55f` (Plan 1 close → current HEAD)
- Implementer commits in scope:
  - `41de176` wip(plan2): checkpoint data and training contracts *(the paused checkpoint you are also confirming)*
  - `c59554c` fix(plan2): make paused contracts lint-clean
  - `f21d627` feat(plan2): hash-linked label-access log + sealed-role guard
  - `edb3725` feat(plan2): ephemeral job input-materialization plan
  - `12449bb` feat(plan2): forecast batched R0 whole-programme cost
  - `fb6b55f` harden(plan2): enforce raw-deletion invariant on materialization plan

**Out of scope for approval:** launching any paid HF Job, spending budget, uploading
predictions with recoverable text, or starting Plan 3. This review covers pure,
GPU-free contracts and their tests only.

## How to reproduce the state

```powershell
git checkout codex/plan2-training
uv run pytest -q          # expect: 83 passed
uv run ruff check .       # expect: All checks passed!
uv run mypy src           # expect: Success: no issues found
git diff --check          # expect: clean
```

Independent evidence to gather yourself (do not take the implementer's word):
- Confirm no HF token appears in tracked files: `git grep -nE "hf_[A-Za-z0-9]{20,}" -- . ':(exclude)uv.lock'`
- Confirm no paid job was launched this session (no `hf_jobs` calls in transcript/logs).
- Re-run the four gate commands above from a clean checkout.

## Acceptance criteria — one row per mandatory audit correction

Judge each against the code **and** its tests. A correction is only `PASS` if the
behaviour is enforced in code (not just asserted in a comment) and a test would fail
if the behaviour regressed.

| # | Audit correction | Where implemented | Tests | What PASS requires |
|---|---|---|---|---|
| 1 | RAMS trigger frames aggregate to one document `PredictionRecord`; accept only if **every** frame valid; confidence = **minimum** frame confidence; support empty-gold and multi-role frames | `src/conformalextract/training.py` `aggregate_document_prediction`, `FrameGeneration`; `contracts.py` `EventFrame`/`PredictionRecord` | `tests/test_training.py` (aggregation, worst-confidence), `tests/test_preparation.py` (empty-gold/multi-role) | Any invalid frame ⇒ record rejected at `-inf`; valid doc ⇒ min confidence; multiple frames fold into one record |
| 2 | Pre-training/R0 context ladder kept separate from R1 compatibility tuning; R2 inherits selected R1 config (not rejected for non-default values) | `training.py` `validate_stage_config`, `choose_pretraining_context` | `tests/test_training.py` (R1 evidence, R2 inherit, ladder) | R0 rejects tuning; R1 tuning needs evidence id; R2/R3 must equal frozen R1 config |
| 3 | Structural `-inf` allowed as worst confidence; NaN and `+inf` rejected | `src/conformalextract/selection.py` `risk_coverage_auc` | `tests/test_selection.py` | `-inf` scored as worst; NaN/`+inf` raise |
| 4 | HF Jobs download official data ephemerally, verify checksums, never upload raw text / sealed labels / predictions with recoverable text; delete raw before launch | `training.py` `plan_ephemeral_materialization`, `EphemeralMaterializationPlan` (+ validator); `preparation.py` manifests | `tests/test_ephemeral_jobs.py` | Ordered download→verify→delete_raw→launch; launch never reads `/raw`; uploads restricted to label-free allowlist; a hand-built plan that skips delete_raw is **rejected** |
| 5 | Training cannot access certification/final/shift gold; negative sentinel + access-log tests | `training.py` `LabelAccessRequest`, `_authorize_label_access`, `build_label_access_log`, `LabelAccessLog.verify` | `tests/test_label_access.py`, `tests/test_training.py` (unrepresentable `certification_labels_path`) | Sealed roles unrepresentable and unreachable; development gold only for development selection; tamper of any entry fails `verify()`; log is text-free |
| 6 | No paid R0 until real manifests, privacy checks, Trackio controls, and a conservative whole-programme forecast are frozen | `preparation.py` `freeze_preparation_manifests` (7 text-free manifests); `training.py` forecast | `tests/test_preparation.py`, `tests/test_cost_forecast.py` | Manifests are text-free and role-bound; forecast exists and is frozen before any launch. **This review does not authorize a launch** |
| 7 | Naïve unbatched inference is infeasible under the $24.7992 cap; return stop/infeasible if the batched R0 forecast can't fit | `training.py` `forecast_whole_programme`, `REMAINING_BUDGET_USD=24.7992` | `tests/test_cost_forecast.py` | Naïve benchmark ⇒ `infeasible`; over-scoped-but-essential-affordable ⇒ `stop`; forecast **never** returns `go` when total > cap |
| 8 | Independent reviewer PASS required before Plan 3 | this document | — | This gate is the criterion; it cannot be self-satisfied by the implementer |

## Reviewer challenge list (try to break it)

Spend most effort here — the tests above are the implementer's claims, not yours.

- **Label isolation:** can you construct a training input that reads sealed gold by any
  path (extra field, alternate role spelling, purpose confusion)? Does `LabelAccessLog.verify`
  detect a re-ordered or substituted entry, not just a single-field edit?
- **Raw-data escape:** can a valid `EphemeralMaterializationPlan` be built that launches
  while a raw path survives, or uploads a non-allowlisted kind? Is the `/raw` substring check
  defeatable (e.g. a differently-cased or nested raw path)?
- **Cost forecast honesty:** find inputs where `forecast_whole_programme` returns `go` while
  the true committed spend (with buffer and reserve) exceeds $24.7992. Check the `essential`
  vs full-plan split and whether `safety_buffer`/`reserve_usd` can be zeroed to force a false `go`.
- **Aggregation:** does a document with a mix of valid and grounding-failure frames ever
  produce an *accepted* record? (Frames from failed generations are retained in `frames` by
  design — confirm that does not leak into acceptance.)
- **Config pinning:** the float `Field(ge=X, le=X)` pins and the `Literal`-alias model identity
  — confirm they actually reject off-nominal values and are not merely defaults.

## Decision

- `PASS` — every row above holds under your own reproduction and challenge attempts.
  Record the PASS with the reviewed commit (`fb6b55f`) and your identity, mirroring the
  Plan 1 close record. Only then may Plan 3 begin.
- `revise` — list the specific rows/tests that fail and the concrete failing input. The
  implementer fixes and re-submits; the gate stays closed.
- `stop` — a correction is structurally unsound or a budget/privacy invariant can be
  violated. Halt Plan 2; do not proceed.

Do not force a `PASS` to unblock Plan 3. A gate returning `revise` or `stop` is the
expected, safe outcome when criteria are unmet.
