"""Frozen confidence candidates from generated-token transition log probabilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConfidenceCandidates:
    mean: float
    tenth_percentile: float
    minimum: float


def aggregate_transition_logprobs(values: list[float]) -> ConfidenceCandidates:
    """Compute the three predeclared, higher-is-better confidence candidates."""

    if not values:
        return ConfidenceCandidates(float("-inf"), float("-inf"), float("-inf"))
    array = np.asarray(values, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError("transition log probabilities must be finite")
    return ConfidenceCandidates(
        mean=float(np.mean(array)),
        tenth_percentile=float(np.quantile(array, 0.1)),
        minimum=float(np.min(array)),
    )
