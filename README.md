# ConformalExtract

ConformalExtract is an evidence-first research package for selective, grounded event-argument
extraction. It tests whether a document-level abstention policy can certify bounded extraction risk
while retaining useful coverage.

The repository is being executed through four evidence gates. Plan 1 is active; training,
certification claims, and publication remain blocked until their preceding independent review
passes. Raw RAMS/WikiEvents text, sealed labels, model checkpoints, credentials, and private
tracking state are never committed.

## Local checks

```console
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy
uv run conformalextract --help
```

Scientific infeasibility is reported as an auditable result, never replaced by an empirical claim.
See `docs/gate0/decision.md` for the current gate state and `SECURITY.md` for data handling.

## Licence

Original source code is Apache-2.0. Dataset text, annotations, model adapters, predictions, and
evidence artifacts have separate licence boundaries documented under `docs/gate0/licences/`.

