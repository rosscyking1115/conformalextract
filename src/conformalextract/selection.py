"""Development-only confidence selection and whole-document acceptance policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConfidenceSelection:
    selected: str
    auc_by_candidate: dict[str, float]
    tie_order: tuple[str, ...]


def risk_coverage_auc(scores: Sequence[float], losses: Sequence[float]) -> float:
    """Empirical selective-risk AUC when documents are accepted high-score first."""

    if len(scores) != len(losses) or not scores:
        raise ValueError("scores and losses must be non-empty and aligned")
    score_array = np.asarray(scores, dtype=np.float64)
    loss_array = np.asarray(losses, dtype=np.float64)
    if not np.isfinite(score_array).all() or np.any((loss_array < 0) | (loss_array > 1)):
        raise ValueError("scores must be finite and losses bounded")
    order = np.lexsort((np.arange(len(scores)), -score_array))
    ordered_losses = loss_array[order]
    risks = np.cumsum(ordered_losses) / np.arange(1, len(losses) + 1)
    coverage = np.arange(1, len(losses) + 1) / len(losses)
    extended_coverage = np.concatenate(([0.0], coverage))
    extended_risks = np.concatenate(([risks[0]], risks))
    return float(np.trapezoid(extended_risks, extended_coverage))


def select_confidence_candidate(
    *,
    scores_by_candidate: Mapping[str, Sequence[float]],
    development_losses: Sequence[float],
    tie_order: Sequence[str] = ("mean", "tenth_percentile", "minimum"),
) -> ConfidenceSelection:
    """Select the lowest grouped development risk-coverage AUC without certification labels."""

    if set(scores_by_candidate) != set(tie_order):
        raise ValueError("candidate set must exactly match the frozen tie order")
    auc = {
        candidate: risk_coverage_auc(scores_by_candidate[candidate], development_losses)
        for candidate in tie_order
    }
    selected = min(tie_order, key=lambda candidate: (auc[candidate], tie_order.index(candidate)))
    return ConfidenceSelection(selected, auc, tuple(tie_order))


def accept_whole_document(
    *, frame_confidences: Sequence[float], structurally_valid: Sequence[bool], threshold: float
) -> bool:
    """Accept only if every frame is valid and its minimum score clears the threshold."""

    if len(frame_confidences) != len(structurally_valid) or not frame_confidences:
        return False
    return all(structurally_valid) and min(frame_confidences) >= threshold
