"""Development-only gate: select the primary confidence candidate and check base-risk
feasibility using development-split evidence.

Development gold is not sealed (Plan 2 audit correction #5 permits it for exactly this
purpose), but every read is still authorized and hash-chained through
``training.build_label_access_log`` with purpose ``DEVELOPMENT_SELECTION`` -- the same
discipline sealed-label-adjacent code uses everywhere else in this project. Certification,
final, and shift gold remain categorically unreachable here: ``_authorize_label_access``
rejects any sealed ``data_role`` regardless of caller intent.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from conformalextract.certification import BaseRiskFeasibility, base_risk_feasibility
from conformalextract.contracts import EventFrame, PredictionRecord
from conformalextract.evaluation import evaluate_document
from conformalextract.selection import ConfidenceSelection, select_confidence_candidate
from conformalextract.training import (
    LabelAccessLog,
    LabelAccessPurpose,
    LabelAccessRequest,
    build_label_access_log,
)

CONFIDENCE_CANDIDATES = ("mean", "tenth_percentile", "minimum")


@dataclass(frozen=True)
class DevelopmentGateResult:
    confidence_selection: ConfidenceSelection
    base_risk: BaseRiskFeasibility
    label_access: LabelAccessLog
    n_documents: int


def document_loss(gold: Sequence[EventFrame], prediction: PredictionRecord) -> float:
    """Always-answer document loss: a non-valid prediction always scores as wrong (1.0).

    Content is only scored when the document is ``valid`` -- a structural or grounding
    failure is never rewarded for coincidentally-correct-looking frames it did not
    actually produce (``aggregate_document_prediction`` empties ``frames`` on failure
    anyway, but this makes the always-answer intent explicit rather than incidental).
    """

    predicted = prediction.frames if prediction.status == "valid" else None
    return evaluate_document(gold, predicted).loss


def run_development_gate(
    predictions: Sequence[PredictionRecord],
    gold_by_document: Mapping[str, Sequence[EventFrame]],
    raw_confidence_candidates: Mapping[str, Mapping[str, float] | None],
    *,
    alpha: float,
    acceptance_floor: float,
) -> DevelopmentGateResult:
    """Select the primary confidence candidate and check base-risk feasibility.

    ``raw_confidence_candidates`` maps document id to the three predeclared candidates
    (or ``None`` for a document with no generation, e.g. a context_overflow record),
    read directly from the frozen prediction artifact -- not recomputed here.
    """

    losses: list[float] = []
    scores_by_candidate: dict[str, list[float]] = {c: [] for c in CONFIDENCE_CANDIDATES}
    access_requests: list[LabelAccessRequest] = []

    for prediction in predictions:
        document_id = prediction.document_id
        gold = gold_by_document[document_id]
        losses.append(document_loss(gold, prediction))
        candidates = raw_confidence_candidates.get(document_id)
        for candidate in CONFIDENCE_CANDIDATES:
            scores_by_candidate[candidate].append(
                candidates[candidate] if candidates is not None else float("-inf")
            )
        access_requests.append(
            LabelAccessRequest(
                data_role="development",
                document_id_hash=hashlib.sha256(document_id.encode()).hexdigest(),
                purpose=LabelAccessPurpose.DEVELOPMENT_SELECTION,
            )
        )

    label_access = build_label_access_log(access_requests)
    confidence_selection = select_confidence_candidate(
        scores_by_candidate=scores_by_candidate, development_losses=losses
    )
    risk = base_risk_feasibility(losses, alpha=alpha, acceptance_floor=acceptance_floor)
    return DevelopmentGateResult(
        confidence_selection=confidence_selection,
        base_risk=risk,
        label_access=label_access,
        n_documents=len(predictions),
    )
