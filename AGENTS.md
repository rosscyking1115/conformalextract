# AGENTS.md

Agent entry point for ConformalExtract. **Read [`CLAUDE.md`](CLAUDE.md) first** — it carries the
purpose, honesty boundary, conventions, and the non-obvious gotchas. This file is only the quick
command card.

```bash
uv sync --extra dev      # uv.lock is the authority
uv run pytest -q
uv run ruff check .
uv run mypy              # strict
```

Hard rules (full detail in `CLAUDE.md`): paid HF-Jobs execution needs explicit Ross approval (\$25 cap);
sealed labels (`certification`/`final`/`shift`) are never read in training; raw text / checkpoints /
predictions-with-text are never committed; changes to evaluation, label access, certification, or
release policy need an independent review. Review standard: [`REVIEW.md`](REVIEW.md).
