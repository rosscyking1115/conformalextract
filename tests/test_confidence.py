from __future__ import annotations

import pytest

from conformalextract.confidence import aggregate_transition_logprobs


def test_confidence_candidates() -> None:
    values = [-1.0, -0.5, -2.0, -0.25]
    scores = aggregate_transition_logprobs(values)
    assert scores.minimum == -2.0
    assert scores.mean == pytest.approx(-0.9375)
    assert scores.tenth_percentile == pytest.approx(-1.7)


def test_empty_generation_gets_worst_confidence() -> None:
    scores = aggregate_transition_logprobs([])
    assert scores.minimum == float("-inf")
