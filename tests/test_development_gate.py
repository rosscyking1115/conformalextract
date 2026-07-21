from __future__ import annotations

import pytest

from conformalextract.contracts import Argument, EventFrame, PredictionRecord, Span
from conformalextract.development_gate import document_loss, run_development_gate
from conformalextract.training import LabelAccessPurpose


def _frame(text: str, role: str = "Attacker") -> EventFrame:
    return EventFrame(
        document_id="d1",
        event_type="Conflict.Attack",
        trigger=Span(start=1, end=2, text="attacked"),
        arguments=[Argument(role=role, span=Span(start=0, end=1, text=text))],
    )


def _prediction(status: str, *, frames: list[EventFrame] | None = None) -> PredictionRecord:
    return PredictionRecord(
        prediction_id="p1",
        document_id="d1",
        system_id="qa",
        prompt_hash="abc",
        raw_output="[]",
        frames=frames or [],
        confidence=0.0 if status == "valid" else float("-inf"),
        status=status,  # type: ignore[arg-type]
    )


def test_document_loss_is_one_minus_f1_when_valid() -> None:
    gold = [_frame("Alice")]
    prediction = _prediction("valid", frames=[_frame("Alice")])
    assert document_loss(gold, prediction) == pytest.approx(0.0)


def test_document_loss_is_one_when_not_valid_even_if_frames_present() -> None:
    """Always-answer scoring: a non-valid document is a wrong answer, never scored on content."""
    gold = [_frame("Alice")]
    prediction = _prediction("grounding_failure")
    assert document_loss(gold, prediction) == 1.0


def test_run_development_gate_selects_lowest_auc_candidate_and_logs_access() -> None:
    predictions = [
        _prediction("valid", frames=[_frame("Alice")]),
    ]
    gold_by_document = {"d1": [_frame("Alice")]}
    raw_confidence = {"d1": {"mean": -0.1, "tenth_percentile": -0.3, "minimum": -0.9}}

    result = run_development_gate(
        predictions, gold_by_document, raw_confidence, alpha=0.20, acceptance_floor=0.20
    )
    assert result.confidence_selection.selected in ("mean", "tenth_percentile", "minimum")
    assert result.n_documents == 1
    assert result.label_access.verify()
    assert len(result.label_access.entries) == 1
    assert result.label_access.entries[0].data_role == "development"
    assert result.label_access.entries[0].purpose == LabelAccessPurpose.DEVELOPMENT_SELECTION


def test_run_development_gate_scores_missing_candidates_as_negative_infinity() -> None:
    predictions = [_prediction("structural_failure")]
    gold_by_document = {"d1": [_frame("Alice")]}
    result = run_development_gate(
        predictions, gold_by_document, {"d1": None}, alpha=0.20, acceptance_floor=0.20
    )
    assert result.base_risk.base_risk == pytest.approx(1.0)  # the only document is a failure


def test_run_development_gate_never_authorizes_sealed_roles() -> None:
    """Defence in depth: even if a caller mislabels a role, sealed data must be unreachable."""
    from conformalextract.training import LabelAccessRequest, build_label_access_log

    with pytest.raises(ValueError, match="unreachable"):
        build_label_access_log(
            [
                LabelAccessRequest(
                    data_role="certification",
                    document_id_hash="0" * 64,
                    purpose=LabelAccessPurpose.DEVELOPMENT_SELECTION,
                )
            ]
        )
