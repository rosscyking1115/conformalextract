"""Plan 3 re-analysis (ADR 0011): the alpha-free frontier and the loss-channel decomposition.

Two questions the certification artifact cannot answer on its own, both answerable at zero cost
from splits that are **already open**:

1. *Where does the certifiable frontier actually collapse?* The single-alpha result reports one
   height on a curve. ``certification_run.risk_coverage_curve`` reports the curve, which rules
   alpha values out without certifying anything at any of them.
2. *Did the grounding gain buy any of it?* Plan 2 measured a ~16x grounding separation
   (QA 95.7% parseable-and-grounded vs ZS 39.4% / FS 68.1%) that did not move the certified
   result at all. Decomposing document loss into its four channels says why, and the
   grounding-oracle counterfactual says whether closing the gap could ever have helped.

Everything here is **descriptive**. No threshold is selected, no certificate is issued at any
alpha, no sealed label beyond the already-opened certification split is read, and the frozen
alpha = 0.20 headline is untouched (plan section 6.3).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from conformalextract.certification_run import (
    CertificationAccessLog,
    GroupRow,
    RiskCoverageCurve,
    SealedRoleError,
    aggregate_to_groups,
    build_certification_access_log,
    risk_coverage_curve,
)
from conformalextract.contracts import EventFrame, PredictionRecord
from conformalextract.predictions import DocumentContext
from conformalextract.profiles import RamsInstance

SYSTEM_IDS = ("zs", "fs", "qa")

#: The only split roles this re-analysis may touch. This is an **allowlist, not a denylist**:
#: anything not named here -- including ``final`` and ``shift`` -- is refused before a single
#: gold label is read. Returning "no access log" for an unrecognised role would have let a
#: ``--roles final`` invocation open the sealed split and then attest ``final_reads: 0``, which
#: is exactly the failure an access log exists to make impossible (reviewer ruling R1).
REANALYSIS_ROLES = frozenset({"development", "certification"})

#: Roles that stay sealed. Named separately so the error message can say *why*, but the guard
#: is the allowlist above -- a role missing from both sets is still refused.
SEALED_ROLES = frozenset({"final", "shift"})


def assert_reanalysis_role(split_role: str) -> None:
    """Refuse any split this re-analysis is not authorised to open. Fail-closed.

    Must be called **before** any gold is loaded for that role, not merely before an artifact
    is written: the point is that the sealed split is never read, not that the reading is
    disclosed afterwards.
    """

    if split_role in REANALYSIS_ROLES:
        return
    if split_role in SEALED_ROLES:
        raise SealedRoleError(
            f"{split_role!r} is a sealed split and is unreachable from the re-analysis "
            f"(ADR 0010 keeps it closed; ADR 0011 opens nothing new)"
        )
    raise SealedRoleError(
        f"{split_role!r} is not an authorised re-analysis split; "
        f"expected one of {sorted(REANALYSIS_ROLES)}"
    )

#: Document loss decomposes into exactly these four channels, in this order. The first **two**
#: are forced to loss 1.0 by ``development_gate.document_loss`` -- a non-valid prediction is
#: never scored on content it did not produce. ``valid_empty`` is *not* forced: an empty
#: prediction against empty gold scores F1 = 1.0, so the channel is scored normally and simply
#: loses most of the time (measured: 0.74-0.93 mean loss on the certification split). Channels
#: 1-3 are where the Plan 2 grounding separation lives; channel 4 -- grounded, well-formed and
#: content-bearing -- is what the certificate actually measures. That split is the point of the
#: decomposition.
LOSS_CHANNELS = (
    "structural_failure",
    "grounding_failure",
    "valid_empty",
    "valid_content_bearing",
)

#: The channel whose documents a certificate could ever score favourably.
CONTENT_CHANNEL = "valid_content_bearing"


def loss_channel(prediction: PredictionRecord) -> str:
    """Classify one prediction into its loss channel.

    The valid/empty split reuses ``predictions.parse_arm``'s exact predicate (reviewer
    condition C3: an empty frame is a first-class category, not a quiet success), so the
    counts here reconcile with ``evidence/plan2/prediction_parse_summary.json`` by
    construction rather than by coincidence.
    """

    if prediction.status != "valid":
        return prediction.status
    if any(frame.arguments for frame in prediction.frames):
        return CONTENT_CHANNEL
    return "valid_empty"


@dataclass(frozen=True)
class ChannelShare:
    """One channel's presence and its contribution to each mean-loss reading."""

    documents: int
    document_share: float
    mean_loss_within_channel: float
    document_level_contribution: float
    group_level_contribution: float


@dataclass(frozen=True)
class LossDecomposition:
    """Per-channel decomposition of a system's mean loss, at both aggregation levels.

    Two totals are reported because two different quantities are in play and conflating them
    would misstate what was certified:

    * ``document_level_total`` is the plain mean over documents -- equal to the *size-weighted*
      group loss, which is the number a reader naturally hears.
    * ``group_level_total`` is the **unweighted mean of group means**, which is the quantity the
      certificate actually bounds (ADR 0009).

    Both decompositions are exact: their channel contributions sum to their respective totals.
    The gap between the two totals is small here (amendment A2 measured 0.0002-0.0011 on the
    certification split) but it is reported rather than assumed.
    """

    system_id: str
    documents: int
    groups: int
    channels: dict[str, ChannelShare]
    document_level_total: float
    group_level_total: float

    @property
    def total_gap(self) -> float:
        return self.group_level_total - self.document_level_total


def decompose_losses(
    system_id: str,
    *,
    channel_by_document: Mapping[str, str],
    loss_by_document: Mapping[str, float],
    group_by_document: Mapping[str, str],
) -> LossDecomposition:
    """Split mean loss into channel contributions at document and group level.

    The group-level contribution of channel ``c`` is ``mean_g[ sum_{d in g and c} loss_d / |g| ]``.
    Summing over channels telescopes back to the unweighted mean of group means exactly, so the
    decomposition accounts for the certified quantity itself rather than a proxy for it.
    """

    documents = sorted(loss_by_document)
    if not documents:
        raise ValueError(f"{system_id}: no documents to decompose")
    missing = [d for d in documents if d not in channel_by_document or d not in group_by_document]
    if missing:
        raise ValueError(f"{system_id}: {len(missing)} documents lack a channel or group")

    members: dict[str, list[str]] = {}
    for document_id in documents:
        members.setdefault(group_by_document[document_id], []).append(document_id)
    group_count = len(members)

    channels: dict[str, ChannelShare] = {}
    for channel in LOSS_CHANNELS:
        in_channel = [d for d in documents if channel_by_document[d] == channel]
        losses = [loss_by_document[d] for d in in_channel]
        # Group-level: each document contributes its loss divided by its own group's size,
        # averaged over all groups -- the exact per-channel term of the unweighted group mean.
        group_contribution = (
            sum(
                sum(loss_by_document[d] for d in group_members if channel_by_document[d] == channel)
                / len(group_members)
                for group_members in members.values()
            )
            / group_count
        )
        channels[channel] = ChannelShare(
            documents=len(in_channel),
            document_share=len(in_channel) / len(documents),
            mean_loss_within_channel=(sum(losses) / len(losses)) if losses else 0.0,
            document_level_contribution=sum(losses) / len(documents),
            group_level_contribution=group_contribution,
        )

    document_total = sum(loss_by_document[d] for d in documents) / len(documents)
    group_total = (
        sum(
            sum(loss_by_document[d] for d in group_members) / len(group_members)
            for group_members in members.values()
        )
        / group_count
    )
    return LossDecomposition(
        system_id=system_id,
        documents=len(documents),
        groups=group_count,
        channels=channels,
        document_level_total=document_total,
        group_level_total=group_total,
    )


def mean_loss_ceiling(*, alpha: float, acceptance_floor: float) -> float:
    """Largest population mean loss compatible with accepting ``acceptance_floor`` at ``alpha``.

    With losses bounded in [0,1], the best possible mean over the best ``c`` fraction of a
    population with mean ``mu`` is ``max(0, (mu - (1 - c)) / c)`` -- attained when every unit of
    "goodness" is concentrated in the selected set. Requiring that to be within ``alpha`` gives
    ``mu <= alpha * c + (1 - c)``.

    This is an arithmetic impossibility bound, not a property of any score: a population whose
    mean loss exceeds it cannot reach the floor under **any** selection rule, oracle or
    otherwise. It is why the grounding-oracle conclusion does not depend on the counterfactual
    being generous (reviewer ruling R5).
    """

    return alpha * acceptance_floor + (1.0 - acceptance_floor)


@dataclass(frozen=True)
class GroundingOracleComparison:
    """What the certifiable frontier would look like if grounding were solved outright.

    The counterfactual drops every document outside ``CONTENT_CHANNEL`` and recomputes the
    oracle curve over what remains -- i.e. each system is scored as though it never emitted a
    structural failure, an ungrounded span or an empty frame, with coverage measured against the
    **restricted** population.

    That restriction is **not** uniformly generous, and must not be described as such. Dropping
    a low-loss member from a group *raises* that group's mean loss: measured on the certification
    split, 24 FS groups and 21 QA groups score worse under the restriction than without it.
    Nor is the restriction the only conceivable counterfactual -- a correctness-oracle variant
    moves the baselines off zero.

    The conclusion therefore does not rest on the counterfactual. It rests on
    ``mean_loss_ceiling``: a population whose mean loss exceeds ``alpha * c + (1 - c)`` cannot
    reach coverage ``c`` at risk ``alpha`` under any selection rule at all. ZS and FS exceed that
    ceiling on their restricted populations, so no grounding-style intervention reaches the floor
    for them. QA sits below the ceiling, so for QA the ceiling is silent and the measured curve
    is what decides it.

    Because the restricted population differs per system, conditional coverage is not a
    deployable acceptance rate and must not be compared across systems as one.
    """

    system_id: str
    unconditional_max_acceptance: float
    conditional_max_acceptance: float
    unconditional_groups: int
    conditional_groups: int
    floor_reachable_unconditionally: bool
    floor_reachable_under_grounding_oracle: bool
    restricted_mean_loss: float | None
    mean_loss_ceiling: float
    groups_worsened_by_restriction: int

    @property
    def frontier_movement(self) -> float:
        return self.conditional_max_acceptance - self.unconditional_max_acceptance

    @property
    def excluded_by_ceiling(self) -> bool:
        """True when arithmetic alone forbids the floor, independent of any score or oracle."""

        return self.restricted_mean_loss is not None and (
            self.restricted_mean_loss > self.mean_loss_ceiling
        )


@dataclass(frozen=True)
class SplitSystemData:
    """Everything the re-analysis needs for one system on one split."""

    system_id: str
    split_role: str
    confidence_candidate: str
    rows: list[GroupRow]
    channel_by_document: dict[str, str]
    loss_by_document: dict[str, float]
    score_by_document: dict[str, float]
    valid_by_document: dict[str, bool]
    group_by_document: dict[str, str]

    def content_channel_rows(self) -> list[GroupRow]:
        """Re-aggregate over content-bearing documents only (the grounding oracle)."""

        kept = [d for d, c in self.channel_by_document.items() if c == CONTENT_CHANNEL]
        if not kept:
            return []
        return aggregate_to_groups(
            document_ids=kept,
            group_by_document=self.group_by_document,
            score_by_document=self.score_by_document,
            valid_by_document=self.valid_by_document,
            loss_by_document=self.loss_by_document,
        )


def grounding_oracle_comparison(
    data: SplitSystemData, *, alpha: float, acceptance_floor: float
) -> GroundingOracleComparison:
    """Compare a system's frontier with and without its grounding deficit."""

    restricted_rows = data.content_channel_rows()
    unconditional = risk_coverage_curve(data.rows)
    conditional = risk_coverage_curve(restricted_rows)
    unconditional_max = unconditional.max_acceptance_within(alpha)
    conditional_max = conditional.max_acceptance_within(alpha)
    # Restriction can RAISE a group's loss (dropping a low-loss member lifts the group mean),
    # which is why the counterfactual is not described as generous -- this counts the cases.
    before = {row.group_id: row.loss for row in data.rows}
    worsened = sum(1 for row in restricted_rows if row.loss > before.get(row.group_id, 0.0) + 1e-12)
    return GroundingOracleComparison(
        system_id=data.system_id,
        unconditional_max_acceptance=unconditional_max,
        conditional_max_acceptance=conditional_max,
        unconditional_groups=unconditional.total_groups,
        conditional_groups=conditional.total_groups,
        floor_reachable_unconditionally=unconditional_max >= acceptance_floor,
        floor_reachable_under_grounding_oracle=conditional_max >= acceptance_floor,
        restricted_mean_loss=(
            float(np.mean([row.loss for row in restricted_rows])) if restricted_rows else None
        ),
        mean_loss_ceiling=mean_loss_ceiling(alpha=alpha, acceptance_floor=acceptance_floor),
        groups_worsened_by_restriction=worsened,
    )


def curve_readout(
    curve: RiskCoverageCurve,
    *,
    alpha_grid: Sequence[float],
    coverage_grid: Sequence[float],
    acceptance_floor: float,
) -> dict[str, object]:
    """Render one curve as the sweep a reader needs, plus the floor-crossing headline."""

    return {
        "eligible_groups": curve.eligible_groups,
        "total_groups": curve.total_groups,
        # The alpha at which the frozen acceptance floor first becomes oracle-reachable. Below
        # it, no certificate at any threshold could have cleared the floor -- which is how the
        # curve rules alpha values out without a certificate being computed at any of them.
        "alpha_star_at_floor": curve.alpha_star(acceptance_floor),
        "max_acceptance_by_alpha": {
            f"{alpha:.2f}": curve.max_acceptance_within(alpha) for alpha in alpha_grid
        },
        "alpha_star_by_coverage": {
            f"{coverage:.2f}": curve.alpha_star(coverage) for coverage in coverage_grid
        },
    }


def _sample_curve(curve: RiskCoverageCurve, *, points: int) -> list[dict[str, float]]:
    """Down-sample the curve for the artifact: full arrays are large and text-free anyway."""

    if not curve.coverage:
        return []
    indices = np.unique(
        np.linspace(0, len(curve.coverage) - 1, num=min(points, len(curve.coverage))).astype(int)
    )
    return [
        {"coverage": curve.coverage[int(i)], "running_risk": curve.running_risk[int(i)]}
        for i in indices
    ]


def load_split_system_data(
    *,
    split_role: str,
    system_id: str,
    confidence_candidate: str,
    predictions_path: Path,
    contexts: Mapping[str, DocumentContext],
    instances: Mapping[str, RamsInstance],
    group_by_document: Mapping[str, str],
    gold_frames: Callable[[RamsInstance], list[EventFrame]],
) -> SplitSystemData:
    """Parse one system's predictions and build every per-document view the re-analysis needs.

    Kept deliberately close to the existing ``risk-coverage-diagnostic`` loading path so the
    two commands cannot disagree about what a document's loss or score is; the group rows come
    from the same ``aggregate_to_groups`` the certifier itself uses.
    """

    from conformalextract.development_gate import document_loss
    from conformalextract.predictions import parse_arm, read_prediction_jsonl

    # Guard here, at the only door to gold, so no caller can route around it (reviewer R1).
    assert_reanalysis_role(split_role)
    raw_records = read_prediction_jsonl(predictions_path)
    parsed, _ = parse_arm(raw_records, contexts, confidence_candidate=confidence_candidate)
    raw_confidence = {r["instance_key"]: r["confidence_candidates"] for r in raw_records}

    selected = [p for p in parsed if p.document_id in group_by_document]
    if not selected:
        raise ValueError(f"{system_id}/{split_role}: no predictions fall in this split")

    def score_of(document_id: str) -> float:
        candidates = raw_confidence.get(document_id)
        if isinstance(candidates, dict):
            return float(candidates[confidence_candidate])
        return float("-inf")

    loss_by_document = {
        p.document_id: document_loss(gold_frames(instances[p.document_id]), p) for p in selected
    }
    score_by_document = {p.document_id: score_of(p.document_id) for p in selected}
    valid_by_document = {p.document_id: p.status == "valid" for p in selected}
    channel_by_document = {p.document_id: loss_channel(p) for p in selected}
    rows = aggregate_to_groups(
        document_ids=[p.document_id for p in selected],
        group_by_document=group_by_document,
        score_by_document=score_by_document,
        valid_by_document=valid_by_document,
        loss_by_document=loss_by_document,
    )
    return SplitSystemData(
        system_id=system_id,
        split_role=split_role,
        confidence_candidate=confidence_candidate,
        rows=rows,
        channel_by_document=channel_by_document,
        loss_by_document=loss_by_document,
        score_by_document=score_by_document,
        valid_by_document=valid_by_document,
        group_by_document={d: group_by_document[d] for d in loss_by_document},
    )


def certification_access_for(
    split_role: str, document_ids: Sequence[str]
) -> CertificationAccessLog | None:
    """Chain certification-split gold reads; return None for the development split.

    The certification split is legitimately open (it was opened once, under
    ``docs/plan3/certification-result.md``), but a re-analysis that reads its gold should still
    leave the same tamper-evident trace the certifier leaves. Any role outside the allowlist
    raises rather than returning ``None`` -- an unrecognised role must never be silently
    treated as "nothing to disclose" (reviewer ruling R1).
    """

    assert_reanalysis_role(split_role)
    if split_role != "certification":
        return None
    return build_certification_access_log(sorted(document_ids))


def access_block(log: CertificationAccessLog | None) -> dict[str, object]:
    """The access disclosure carried on every re-analysis artifact."""

    if log is None:
        return {"certification_gold_read": False, "final_reads": 0, "shift_reads": 0}
    return {
        "certification_gold_read": True,
        "head_hash": log.head_hash,
        "documents_read": log.document_count,
        "verified": log.verify(),
        "final_reads": 0,
        "shift_reads": 0,
    }


def alpha_frontier_artifact(
    data_by_split: Mapping[str, Mapping[str, SplitSystemData]],
    *,
    alpha_grid: Sequence[float],
    coverage_grid: Sequence[float],
    frozen_alpha: float,
    acceptance_floor: float,
    curve_points: int,
    access: Mapping[str, object],
) -> dict[str, object]:
    """Assemble the alpha-frontier artifact (text-free, certifies nothing)."""

    splits: dict[str, object] = {}
    for split_role in sorted(data_by_split):
        per_system: dict[str, object] = {}
        for system_id in sorted(data_by_split[split_role]):
            data = data_by_split[split_role][system_id]
            curve = risk_coverage_curve(data.rows)
            per_system[system_id] = {
                "confidence_candidate": data.confidence_candidate,
                **curve_readout(
                    curve,
                    alpha_grid=alpha_grid,
                    coverage_grid=coverage_grid,
                    acceptance_floor=acceptance_floor,
                ),
                "curve": _sample_curve(curve, points=curve_points),
            }
        splits[split_role] = per_system
    return {
        "schema_version": "1",
        "diagnostic_only": True,
        "certifies_nothing": True,
        "frozen_alpha": frozen_alpha,
        "acceptance_floor": acceptance_floor,
        "interpretation": (
            "Oracle risk-coverage curves read at many alpha. The curve is alpha-free: "
            "max_acceptance_by_alpha is one fixed object read at different heights, so this "
            "introduces no new statistic, no threshold selection and no multiplicity. It is an "
            "UPPER bound on what any threshold rule could achieve, which is the only direction "
            "it is used in: where the floor is unreachable here, no certificate at that alpha "
            "could have cleared it. The frozen headline target remains alpha=0.20 and NO "
            "certificate is issued at any alpha on this curve."
        ),
        "certification_access": dict(access),
        "splits": splits,
    }


def loss_decomposition_artifact(
    data_by_split: Mapping[str, Mapping[str, SplitSystemData]],
    *,
    alpha: float,
    acceptance_floor: float,
    access: Mapping[str, object],
) -> dict[str, object]:
    """Assemble the loss-channel + grounding-oracle artifact (text-free, certifies nothing)."""

    splits: dict[str, object] = {}
    for split_role in sorted(data_by_split):
        per_system: dict[str, object] = {}
        for system_id in sorted(data_by_split[split_role]):
            data = data_by_split[split_role][system_id]
            decomposition = decompose_losses(
                system_id,
                channel_by_document=data.channel_by_document,
                loss_by_document=data.loss_by_document,
                group_by_document=data.group_by_document,
            )
            comparison = grounding_oracle_comparison(
                data, alpha=alpha, acceptance_floor=acceptance_floor
            )
            per_system[system_id] = {
                "confidence_candidate": data.confidence_candidate,
                "documents": decomposition.documents,
                "groups": decomposition.groups,
                "document_level_total_loss": decomposition.document_level_total,
                "group_level_total_loss": decomposition.group_level_total,
                "total_gap": decomposition.total_gap,
                "channels": {
                    channel: {
                        "documents": share.documents,
                        "document_share": share.document_share,
                        "mean_loss_within_channel": share.mean_loss_within_channel,
                        "document_level_contribution": share.document_level_contribution,
                        "group_level_contribution": share.group_level_contribution,
                    }
                    for channel, share in decomposition.channels.items()
                },
                "grounding_oracle": {
                    "unconditional_max_acceptance": comparison.unconditional_max_acceptance,
                    "conditional_max_acceptance": comparison.conditional_max_acceptance,
                    "unconditional_groups": comparison.unconditional_groups,
                    "conditional_groups": comparison.conditional_groups,
                    "floor_reachable_unconditionally": (
                        comparison.floor_reachable_unconditionally
                    ),
                    "floor_reachable_under_grounding_oracle": (
                        comparison.floor_reachable_under_grounding_oracle
                    ),
                    "frontier_movement": comparison.frontier_movement,
                    "restricted_mean_loss": comparison.restricted_mean_loss,
                    "mean_loss_ceiling": comparison.mean_loss_ceiling,
                    "excluded_by_ceiling": comparison.excluded_by_ceiling,
                    "groups_worsened_by_restriction": comparison.groups_worsened_by_restriction,
                },
            }
        splits[split_role] = per_system
    return {
        "schema_version": "1",
        "diagnostic_only": True,
        "certifies_nothing": True,
        "alpha": alpha,
        "acceptance_floor": acceptance_floor,
        "interpretation": (
            "Document loss split into its four channels, and a counterfactual in which each "
            "system's grounding deficit is removed outright. structural_failure and "
            "grounding_failure are forced to loss 1.0; valid_empty is scored normally and is "
            "not forced (empty prediction against empty gold scores F1=1.0), it simply loses "
            "most of the time. Those three channels are where the Plan 2 grounding separation "
            "lives; valid_content_bearing is what the certificate actually measures. The "
            "grounding oracle measures coverage against the RESTRICTED population. That is NOT "
            "uniformly generous -- dropping a low-loss member raises a group's mean loss, and "
            "groups_worsened_by_restriction counts the cases -- so the conclusion does not rest "
            "on it. It rests on mean_loss_ceiling: a population whose mean loss exceeds "
            "alpha*c + (1-c) cannot reach coverage c at risk alpha under ANY selection rule. "
            "Where excluded_by_ceiling is true, arithmetic alone forbids the floor. Where it is "
            "false the ceiling is silent and the measured curve decides. Conditional coverage is "
            "not a deployable acceptance rate and is not comparable across systems. Nothing here "
            "selects a threshold or certifies anything."
        ),
        "certification_access": dict(access),
        "splits": splits,
    }


def write_artifact(artifact: Mapping[str, object], out: Path) -> str:
    """Write an artifact deterministically and return its path."""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(out)
