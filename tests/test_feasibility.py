from __future__ import annotations

from conformalextract.certification import largest_scorc_grid, scorc_minimum_n


def test_preferred_method_precondition_matches_worked_values() -> None:
    assert scorc_minimum_n(candidate_count=1, delta=0.05, acceptance_floor=0.2) == 1034
    assert scorc_minimum_n(candidate_count=50, delta=0.05, acceptance_floor=0.2) == 1660


def test_grid_is_zero_when_even_one_candidate_is_ineligible() -> None:
    assert largest_scorc_grid(independent_documents=1033, delta=0.05, acceptance_floor=0.2) == 0
    assert largest_scorc_grid(independent_documents=1034, delta=0.05, acceptance_floor=0.2) == 1
