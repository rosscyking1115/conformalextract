from __future__ import annotations

from conformalextract.selection import accept_whole_document, select_confidence_candidate


def test_confidence_selection_uses_development_risk_coverage_auc() -> None:
    losses = [0.0, 0.0, 1.0, 1.0]
    selection = select_confidence_candidate(
        scores_by_candidate={
            "mean": [4.0, 3.0, 2.0, 1.0],
            "tenth_percentile": [1.0, 2.0, 3.0, 4.0],
            "minimum": [4.0, 2.0, 3.0, 1.0],
        },
        development_losses=losses,
    )
    assert selection.selected == "mean"
    assert selection.auc_by_candidate["mean"] < selection.auc_by_candidate["minimum"]


def test_whole_document_policy_is_all_frames_or_abstain() -> None:
    assert accept_whole_document(
        frame_confidences=[-0.2, -0.4], structurally_valid=[True, True], threshold=-0.5
    )
    assert not accept_whole_document(
        frame_confidences=[-0.2, -0.6], structurally_valid=[True, True], threshold=-0.5
    )
    assert not accept_whole_document(
        frame_confidences=[-0.2, -0.4], structurally_valid=[True, False], threshold=-0.5
    )
