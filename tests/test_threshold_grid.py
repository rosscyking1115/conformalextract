from __future__ import annotations

import math

import pytest

from conformalextract.threshold_grid import (
    build_threshold_grid,
    theorem_max_grid_size,
)


def _scores(n: int = 200) -> list[float]:
    # A spread of finite scores plus some -inf failures (worst-confidence treatment).
    finite = [-2.0 + 4.0 * i / (n - 1) for i in range(n)]
    return finite + [float("-inf")] * 20


def test_theorem_max_grid_size_matches_the_certifier_precondition() -> None:
    # 1396 certification groups, delta 0.05, floor 0.20 -> 9 (verified against scorc_minimum_n).
    assert theorem_max_grid_size(n_groups=1396, delta=0.05, acceptance_floor=0.20) == 9
    # Splitting delta three ways (a possible §5.5 global allocation) shrinks it sharply.
    assert theorem_max_grid_size(n_groups=1396, delta=0.05 / 3, acceptance_floor=0.20) == 3


def test_grid_contains_the_two_boundary_policies() -> None:
    grid = build_threshold_grid("qa", _scores(), grid_size=9)
    kinds = [candidate.kind for candidate in grid.candidates]
    assert kinds.count("always_answer") == 1
    assert kinds.count("abstain_all") == 1
    always = next(c for c in grid.candidates if c.kind == "always_answer")
    abstain = next(c for c in grid.candidates if c.kind == "abstain_all")
    assert always.threshold == float("-inf")  # accepts every structurally-valid document
    assert abstain.threshold == float("inf")  # accepts nothing


def test_abstain_all_is_diagnostic_only_and_not_counted_toward_the_theorem() -> None:
    grid = build_threshold_grid("qa", _scores(), grid_size=9)
    abstain = next(c for c in grid.candidates if c.kind == "abstain_all")
    assert abstain.certifiable is False  # cannot satisfy the floor (plan §5.4)
    # The 9-candidate theorem budget covers exactly the certifiable candidates.
    assert sum(1 for c in grid.candidates if c.certifiable) == 9
    always = next(c for c in grid.candidates if c.kind == "always_answer")
    assert always.certifiable is True


def test_candidates_are_sorted_ascending_so_acceptance_is_monotone() -> None:
    grid = build_threshold_grid("qa", _scores(), grid_size=9)
    thresholds = [c.threshold for c in grid.candidates]
    assert thresholds == sorted(thresholds)  # ascending threshold => descending acceptance


def test_construction_is_deterministic_and_permutation_invariant() -> None:
    scores = _scores()
    first = build_threshold_grid("qa", scores, grid_size=9)
    second = build_threshold_grid("qa", list(reversed(scores)), grid_size=9)
    assert first.grid_hash == second.grid_hash
    assert [c.threshold for c in first.candidates] == [c.threshold for c in second.candidates]


def test_duplicate_quantiles_are_collapsed_and_realized_size_reported() -> None:
    # All-identical finite scores collapse every quantile to one value.
    grid = build_threshold_grid("qa", [0.5] * 100 + [float("-inf")] * 5, grid_size=9)
    quantile_values = {c.threshold for c in grid.candidates if c.kind == "quantile"}
    assert len(quantile_values) <= 1  # collapsed
    assert grid.realized_certifiable_size <= grid.requested_grid_size
    assert grid.non_finite_scores == 5


def test_grid_size_over_theorem_max_is_rejected() -> None:
    with pytest.raises(ValueError, match="exceeds the theorem-eligible maximum"):
        build_threshold_grid(
            "qa", _scores(), grid_size=10, n_groups=1396, delta=0.05, acceptance_floor=0.20
        )


def test_grid_hash_changes_when_any_threshold_changes() -> None:
    base = build_threshold_grid("qa", _scores(), grid_size=9)
    shifted = build_threshold_grid("qa", [s + 0.001 for s in _scores()], grid_size=9)
    assert base.grid_hash != shifted.grid_hash


def test_empty_or_all_nonfinite_scores_fail_loudly() -> None:
    with pytest.raises(ValueError, match="at least one finite"):
        build_threshold_grid("qa", [float("-inf")] * 10, grid_size=9)
    with pytest.raises(ValueError, match="at least one finite"):
        build_threshold_grid("qa", [], grid_size=9)


def test_nan_or_positive_inf_in_scores_is_rejected() -> None:
    with pytest.raises(ValueError, match="NaN"):
        build_threshold_grid("qa", [0.1, math.nan, 0.2], grid_size=5)
    with pytest.raises(ValueError, match="positive infinity"):
        build_threshold_grid("qa", [0.1, float("inf"), 0.2], grid_size=5)
