from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from conformalextract.contracts import Argument, EventFrame, Span
from conformalextract.evaluation import evaluate_document


def _frame(arguments: list[Argument]) -> EventFrame:
    return EventFrame(
        document_id="d",
        event_type="Conflict.Attack",
        trigger=Span(start=1, end=2, text="attacked"),
        arguments=arguments,
    )


def _arg(role: str, start: int, end: int, text: str) -> Argument:
    return Argument(role=role, span=Span(start=start, end=end, text=text))


def test_empty_gold_and_prediction_is_perfect() -> None:
    result = evaluate_document([_frame([])], [_frame([])])
    assert result.f1 == 1.0
    assert result.loss == 0.0


def test_unmatched_nonempty_prediction_scores_zero() -> None:
    result = evaluate_document([_frame([])], [_frame([_arg("Attacker", 0, 1, "A")])])
    assert result.f1 == 0.0
    assert result.loss == 1.0


def test_matching_is_one_to_one_by_role_and_normalized_span() -> None:
    gold = [_frame([_arg("Attacker", 0, 1, "Cafe\u0301")])]
    pred = [_frame([_arg("Attacker", 0, 1, "Caf\u00e9"), _arg("Attacker", 0, 1, "Caf\u00e9")])]
    result = evaluate_document(gold, pred)
    assert result.true_positives == 1
    assert result.false_positives == 1
    assert result.false_negatives == 0


def test_structural_failure_has_worst_loss_and_confidence() -> None:
    result = evaluate_document([_frame([])], None, structural_failure="invalid_json")
    assert result.loss == 1.0
    assert result.confidence == float("-inf")


@given(st.lists(st.tuples(st.text(min_size=1), st.integers(0, 20)), max_size=20))
def test_loss_is_bounded(items: list[tuple[str, int]]) -> None:
    args = [_arg(role, i, i + 1, role) for role, i in items]
    result = evaluate_document([_frame(args)], [_frame(list(reversed(args)))])
    assert 0.0 <= result.loss <= 1.0
