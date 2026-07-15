"""Grounded document-level evaluation for the frozen task contract."""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from conformalextract.contracts import EventFrame


@dataclass(frozen=True)
class EvaluationResult:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    loss: float
    confidence: float | None
    structural_failure: str | None = None


def normalize_text(value: str) -> str:
    """Apply the contract's Unicode and newline normalization."""

    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _argument_counter(frames: Sequence[EventFrame]) -> Counter[tuple[str, str, int, int, str]]:
    values: Counter[tuple[str, str, int, int, str]] = Counter()
    for frame in frames:
        for argument in frame.arguments:
            values[
                (
                    frame.event_type,
                    argument.role,
                    argument.span.start,
                    argument.span.end,
                    normalize_text(argument.span.text),
                )
            ] += 1
    return values


def evaluate_document(
    gold: Sequence[EventFrame],
    prediction: Sequence[EventFrame] | None,
    *,
    confidence: float | None = None,
    structural_failure: str | None = None,
) -> EvaluationResult:
    """Return one-to-one argument micro-F1 and bounded document loss."""

    if structural_failure is not None or prediction is None:
        return EvaluationResult(0, 0, 0, 0.0, 0.0, 0.0, 1.0, float("-inf"), structural_failure)

    gold_items = _argument_counter(gold)
    predicted_items = _argument_counter(prediction)
    tp = sum((gold_items & predicted_items).values())
    gold_count = sum(gold_items.values())
    prediction_count = sum(predicted_items.values())
    fp = prediction_count - tp
    fn = gold_count - tp

    if gold_count == 0 and prediction_count == 0:
        precision = recall = f1 = 1.0
    elif tp == 0:
        precision = recall = f1 = 0.0
    else:
        precision = tp / prediction_count
        recall = tp / gold_count
        f1 = 2 * precision * recall / (precision + recall)
    return EvaluationResult(tp, fp, fn, precision, recall, f1, 1.0 - f1, confidence)
