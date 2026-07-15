# ADR 0001: Evidence-first sequential research contract

- Status: accepted
- Date: 2026-07-15

## Decision

Use a Python 3.12 `src/` package with typed immutable records and thin Typer commands. Treat label
access and artifact freezing as protocol boundaries. Each plan is blocked until an independent
Reviewer passes the previous plan. Scientific infeasibility and negative results are first-class
outputs. Training and publication are never inferred from implementation progress.

## Consequences

CPU-only contract, evaluator, and statistical tests precede model spend. Raw datasets and secrets
stay outside Git. Results bind configuration, code, environment, systems, scores, splits, and inputs
through hashes and an immutable analysis ID.

