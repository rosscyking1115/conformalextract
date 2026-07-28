# Contributing

Use Python 3.12 and `uv`. Add a failing test before production code, keep commits scoped and
Conventional, and run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` before review.
Changes to evaluation, label access, certification, or release policy require an independent review.

Anything quantitative that reaches a reader — README, report, model card — has to cite a claim ID
from `evidence/plan4/claim_ledger.json`, on a surface that claim actually grants, with the
limitations the ledger attaches to it. `uv run conformalextract verify-claims` checks the citations
resolve; it cannot check that a cited document says what you claim it says. Read the file.

Paid compute, opening a sealed split, and opening the next gate each need the owner's approval, per
run and per gate — a budget ceiling in a plan is not permission to spend it. The full rules are in
[`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md); read those before doing anything that costs
money or touches a label.

