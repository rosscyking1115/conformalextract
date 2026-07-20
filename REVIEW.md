# REVIEW.md — ConformalExtract

Projects the org reviewer rubric into this repo so a repo-local agent can self-review with zero extra
context.

**Green command (external signal — must pass before any hand-off):**
```bash
uv run pytest -q && uv run ruff check . && uv run mypy
```

## The 6-point rubric
1. **Correctness** — does it do what the plan/gate/ADR says? Edge cases, off-by-ones, bad refs. For
   statistical code, verify against the paper (theorem-to-code), not just that tests pass.
2. **External signal** — the green command passes; CI green. No stub/placeholder tests; assertions must
   assert something real.
3. **Scope** — inside the current gate/plan (`docs/plan2/`, `docs/plan3/`); no scope creep; descopes
   recorded in an ADR (e.g. `docs/adr/0002` single-seed, `0003` context ladder).
4. **Safety / reversibility** — no secrets committed; no destructive ops; **raw text, sealed labels,
   checkpoints, and predictions-with-recoverable-text are gitignored/private, never tracked.**
5. **Fit** — matches `CLAUDE.md` conventions, the gated doctrine, and prior ADRs.
6. **Learning** — a genuine mistake gets a recorded lesson (ADR or evidence note), not just a fix.

## Repo-specific gates (this project's non-negotiables)
- **Claims-vs-reality:** every metric in the README/report/cards traces to a committed evidence artifact
  + the command that produced it. "certified" appears only behind an independent reviewer PASS.
- **Honesty boundary:** synthetic/random-token benchmarks ≠ measurements of real extraction quality;
  infeasibility/negative/shift-failure are reported as first-class results; in-domain guarantees are not
  claimed under shift; not "production-grade".
- **Label isolation:** training/scoring never read `certification`/`final`/`shift` gold; expect
  `sealed_reads: 0` in run evidence; the label-access hash chain must verify.
- **Paid-run discipline:** any HF-Jobs spend has explicit Ross approval and fits the \$25 aggregate cap;
  the run's cost is recorded; ephemeral downloads are checksum-verified and raw is deleted before model
  load.
- **Licence/provenance:** RAMS/WikiEvents raw text is non-redistributable — recorded and enforced.
- **No-secrets sweep:** `.env` gitignored; no tokens/keys in tracked files.

**Verdict vocabulary:** PASS · PASS-WITH-NITS · BLOCK. A BLOCK escalates to the human Reviewer seat.
For Plan 2 specifically, the independent reviewer basis is `docs/plan2/reviewer-brief.md`.
