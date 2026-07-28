# ConformalExtract

Evidence-first research on **selective, grounded event-argument extraction**: does a document-level
abstention policy certify bounded extraction risk while keeping useful coverage, and does QLoRA beat
zero/few-shot on **certified acceptance**? **Honesty boundary:** "certified" is never claimed until an
independent reviewer PASSes; **infeasibility / negative / shift-failure results are first-class
publishable outcomes**, not failures; synthetic or random-token benchmarks measure throughput/plumbing,
never real extraction quality; in-domain guarantees are never claimed to survive schema/dataset shift;
**not production-grade**.

## Build / run / test (exact commands)
```bash
uv sync --extra dev          # uv.lock is the authority; --extra train for GPU jobs (Linux only)
uv run pytest -q
uv run ruff check .
uv run mypy                  # strict; must be clean
uv run conformalextract --help   # CLI seams (build-profiles, prepare-data, freeze-demonstrations…)
```

## Environment
- Python 3.12 (uv-managed). Secrets: Hugging Face token via `hf auth login` (needs **Write** scope for
  Jobs) — never committed. `.env` gitignored.
- **Windows gotcha:** prefix `hf jobs …` commands with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` — the CLI's
  streamed job logs charmap-crash the Windows console; that is a *display* failure, not a job failure.

## Conventions
- Gated doctrine: four sequential plans (Plan N+1 starts only after Plan N's independent reviewer PASS);
  in-repo plan docs live in `docs/plan2/`, `docs/plan3/`, `docs/gate0/`, `docs/plan4/`, with a
  `docs/adr/000X` per material decision. Nothing is a claim until it traces to committed evidence.
- **The four accepted plans are in-repo**, one per gate directory as `accepted-plan.md`
  (`docs/gate0/`=Plan 1 … `docs/plan4/`=Plan 4). A bare `§N.M` in the docs means Plan 3 unless the
  text names another. Read the section before relying on a paraphrase of it — the repo's gloss on
  §6.3 was stricter than §6.3 actually is, and an ADR was written against the gloss.
- **Paid execution ($25 aggregate cap) needs explicit Ross approval, every time.** Budget ceilings in a
  plan are not spending permission. R0→R1→R2 order enforced by `TrainingRunLedger`.
- Changes to evaluation, label access, certification, or release policy require an **independent review**.
- Commits: author only (no AI attribution/co-author trailers). Raw RAMS/WikiEvents text, sealed labels,
  checkpoints, and predictions-with-recoverable-text are **never committed** (they live in gitignored
  `data/` or the private HF evidence repo).

## Gotchas (save the next agent the debugging)
- **Sealed labels** (`certification`/`final`/`shift`) must never be read during training/scoring. The
  label-access log enforces this; `sealed_reads: 0` is a hard expectation.
- **Canonical document id is `rams:<doc_key>`** — the RAMS parser and `rams_roles.jsonl` must share this
  prefix or the role join fails loud (it did once; that's why the prefix exists).
- **Aggregation key is `group_id_hash`, NOT `document_id_hash`** (per-trigger). Wiring the wrong one
  silently defeats whole-document aggregation (spec: `docs/superpowers/specs/…rams-profiles…`).
- **TRL `SFTConfig.max_length` defaults to 1024** and silently truncates 6,144-token inputs — the G3
  pre-flight (`validate_training_preflight`) asserts `max_length == context_tokens`.
- **HF Jobs + vLLM:** the slim uv image has no `nvcc` → use `enforce_eager=True` +
  `VLLM_USE_FLASHINFER_SAMPLER=0`; vLLM 0.25.x takes token prompts as `{"prompt_token_ids": ids}` dicts;
  submit `--detach` and poll (streaming charmap-crashes locally, above).
- `graphify-out/` is absent — use `rg`.

## Pointers
- Gates/decisions: `docs/adr/`, `docs/plan2/`, `docs/plan3/`, `docs/gate0/`. Review standard: `REVIEW.md`.
- Terms: `docs/domain-glossary.md`. Reviewer basis (Plan 2): `docs/plan2/reviewer-brief.md`.
