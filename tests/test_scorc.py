from __future__ import annotations

import numpy as np

from conformalextract.certification import scorc_certificate, scorc_minimum_n


def test_scorc_refuses_to_run_below_theorem_precondition() -> None:
    n = scorc_minimum_n(candidate_count=1, delta=0.05, acceptance_floor=0.2) - 1
    result = scorc_certificate(
        losses=np.zeros((n, 1)).tolist(),
        accepted=np.ones((n, 1), dtype=bool).tolist(),
        candidate_ids=["answer-all"],
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
    )
    assert result.status == "insufficient_n"
    assert not result.feasible


def test_scorc_certifies_easy_candidate_and_respects_frozen_tie_order() -> None:
    n = scorc_minimum_n(candidate_count=2, delta=0.05, acceptance_floor=0.2)
    result = scorc_certificate(
        losses=np.zeros((n, 2)).tolist(),
        accepted=np.ones((n, 2), dtype=bool).tolist(),
        candidate_ids=["first", "second"],
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
    )
    assert result.status == "certified"
    assert result.selected_candidate == "first"
    assert result.risk_upper <= 0.2


def test_scorc_reports_infeasible_without_inventing_candidate() -> None:
    n = scorc_minimum_n(candidate_count=1, delta=0.05, acceptance_floor=0.2)
    result = scorc_certificate(
        losses=np.ones((n, 1)).tolist(),
        accepted=np.ones((n, 1), dtype=bool).tolist(),
        candidate_ids=["bad"],
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
    )
    assert result.status == "infeasible"
    assert result.selected_candidate is None
