"""Per-system threshold grid construction (Plan 3 §5.4) -- development-only, label-free.

Each system's finite threshold grid is built from quantiles of its development-set confidence
scores (the Gate-0 frozen ``minimum`` candidate, ADR 0007) plus two explicit boundary policies:
always-answer (accept every structurally-valid document) and abstain-all (accept nothing;
diagnostic only -- it can never satisfy the acceptance floor). Grid size is bounded by the
certification theorem's sample-size/grid-size condition, chosen by feasibility not by final
performance, and the grid is hashed so it can be committed before certification labels open.

Structural facts this module enforces (plan §5.4):
- thresholds come from development scores only -- the function has no other input;
- ties use one deterministic ordering (ascending threshold => descending acceptance);
- no threshold is added after the fact -- construction is a pure function of the dev scores;
- abstain-all is represented but flagged non-certifiable and excluded from the theorem count.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from conformalextract.artifacts import canonical_json_bytes, sha256_bytes
from conformalextract.certification import (
    FROZEN_ACCEPTANCE_FLOOR,
    FROZEN_DELTA,
    largest_scorc_grid,
)

ThresholdKind = str  # "always_answer" | "quantile" | "abstain_all"


@dataclass(frozen=True)
class ThresholdCandidate:
    threshold: float
    kind: ThresholdKind
    certifiable: bool


@dataclass(frozen=True)
class ThresholdGrid:
    system_id: str
    candidates: tuple[ThresholdCandidate, ...]
    grid_hash: str
    requested_grid_size: int
    realized_certifiable_size: int
    non_finite_scores: int

    def certifiable_thresholds(self) -> tuple[float, ...]:
        """The columns a per-system certificate ranges over (excludes diagnostic abstain-all)."""

        return tuple(c.threshold for c in self.candidates if c.certifiable)


def theorem_max_grid_size(
    *, n_groups: int, delta: float = FROZEN_DELTA, acceptance_floor: float = FROZEN_ACCEPTANCE_FLOOR
) -> int:
    """Largest theorem-eligible certifiable candidate count for this many independent groups.

    Wraps ``largest_scorc_grid`` so grid size is a *feasibility* decision (how many candidates
    the finite-sample theorem admits at this ``n``/``delta``/floor), never a performance one.
    """

    return largest_scorc_grid(
        independent_documents=n_groups, delta=delta, acceptance_floor=acceptance_floor
    )


def build_threshold_grid(
    system_id: str,
    development_scores: Sequence[float],
    *,
    grid_size: int,
    n_groups: int | None = None,
    delta: float = FROZEN_DELTA,
    acceptance_floor: float = FROZEN_ACCEPTANCE_FLOOR,
) -> ThresholdGrid:
    """Build one system's frozen, hashed threshold grid from its development scores.

    ``grid_size`` is the requested number of *certifiable* candidates (always-answer plus
    quantile thresholds); abstain-all is appended as a diagnostic and not counted. When
    ``n_groups`` is given, ``grid_size`` is checked against the theorem-eligible maximum for
    the certification split so an over-sized grid is refused before any label opens.
    """

    if grid_size < 2:
        raise ValueError("grid_size must be at least 2 (always-answer plus one quantile)")
    if n_groups is not None:
        maximum = theorem_max_grid_size(
            n_groups=n_groups, delta=delta, acceptance_floor=acceptance_floor
        )
        if grid_size > maximum:
            raise ValueError(
                f"grid_size {grid_size} exceeds the theorem-eligible maximum {maximum} "
                f"for {n_groups} groups at delta={delta}, floor={acceptance_floor}"
            )

    scores = np.asarray(development_scores, dtype=np.float64)
    if scores.size and np.any(np.isnan(scores)):
        raise ValueError("development scores must not contain NaN")
    if scores.size and np.any(np.isposinf(scores)):
        raise ValueError("development scores must not contain positive infinity")
    finite = scores[np.isfinite(scores)]
    non_finite = int(scores.size - finite.size)
    if finite.size == 0:
        raise ValueError("development scores must contain at least one finite value")

    # always-answer is one certifiable candidate; the remaining budget goes to quantiles.
    n_quantiles = grid_size - 1
    quantile_levels = [(i + 1) / (n_quantiles + 1) for i in range(n_quantiles)]
    quantile_values = sorted(
        {round(float(np.quantile(finite, level)), 12) for level in quantile_levels}
    )

    certifiable = [ThresholdCandidate(float("-inf"), "always_answer", True)]
    certifiable += [ThresholdCandidate(value, "quantile", True) for value in quantile_values]
    certifiable.sort(key=lambda candidate: candidate.threshold)
    candidates = (*certifiable, ThresholdCandidate(float("inf"), "abstain_all", False))

    grid_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "system_id": system_id,
                "candidates": [
                    {
                        "threshold": (
                            "-inf"
                            if math.isinf(c.threshold) and c.threshold < 0
                            else "+inf"
                            if math.isinf(c.threshold)
                            else c.threshold
                        ),
                        "kind": c.kind,
                        "certifiable": c.certifiable,
                    }
                    for c in candidates
                ],
            }
        )
    )
    return ThresholdGrid(
        system_id=system_id,
        candidates=candidates,
        grid_hash=grid_hash,
        requested_grid_size=grid_size,
        realized_certifiable_size=sum(1 for c in candidates if c.certifiable),
        non_finite_scores=non_finite,
    )
