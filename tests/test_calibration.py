"""Plan 3 §11.3 group-level calibration diagnostics.

The properties tested here are the ones a reader of the paper would have to trust: that AUROC is
oriented the way the literature reports it, that the normalized AURC really is 0 for a perfect
ranking and 1 for chance, and that the minimum-abstention arithmetic agrees with the ceiling the
re-analysis already committed. Everything else is presentation.
"""

from __future__ import annotations

import math
import typing

import numpy as np
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from conformalextract.calibration import (
    COVERAGE_GRID,
    GroupFeature,
    _bucket,
    _oracle_accepted,
    auroc,
    average_precision,
    build_group_features,
    cross_sentence_arguments,
    grounding_association,
    headline,
    minimum_abstention,
    selective_risk,
    stratify,
    system_readout,
)
from conformalextract.certification_run import GroupRow
from conformalextract.contracts import PredictionRecord
from conformalextract.profiles import RamsArgument, RamsInstance
from conformalextract.reanalysis import SplitSystemData, mean_loss_ceiling


def _rows(
    losses: list[float], scores: list[float], valid: list[bool] | None = None
) -> list[GroupRow]:
    flags = valid if valid is not None else [True] * len(losses)
    return [
        GroupRow(group_id=f"g{i}", score=s, all_valid=v, loss=loss, document_count=1)
        for i, (loss, s, v) in enumerate(zip(losses, scores, flags, strict=True))
    ]


# --- the arithmetic that separates base risk from score discrimination ---------------


@given(
    mean_loss=st.floats(min_value=0.0, max_value=1.0),
    alpha=st.floats(min_value=0.0, max_value=0.9),
    coverage=st.floats(min_value=0.01, max_value=1.0),
)
def test_minimum_abstention_is_the_ceiling_read_for_the_other_unknown(
    mean_loss: float, alpha: float, coverage: float
) -> None:
    """``minimum_abstention`` and ``mean_loss_ceiling`` must be one identity, not two rules.

    A population reaches coverage ``c`` at risk ``alpha`` iff its mean loss is within the
    ceiling, iff ``1 - c`` is at least the minimum abstention. If these ever disagreed, the
    publication claim ("base risk permitted 49% acceptance") and the committed re-analysis
    claim ("arithmetic alone forbids the floor") would rest on different arithmetic.
    """

    within_ceiling = mean_loss <= mean_loss_ceiling(alpha=alpha, acceptance_floor=coverage)
    within_abstention = (1.0 - coverage) >= minimum_abstention(mean_loss, alpha) - 1e-12
    assert within_ceiling == within_abstention


def test_minimum_abstention_reproduces_the_publication_plan_figure() -> None:
    """The §2 correction's worked number, pinned so a later edit cannot drift it silently."""

    assert minimum_abstention(0.6071, 0.20) == pytest.approx(0.508875, abs=1e-6)
    assert 1.0 - minimum_abstention(0.6071, 0.20) == pytest.approx(0.491125, abs=1e-6)


def test_base_risk_within_alpha_forces_no_abstention() -> None:
    assert minimum_abstention(0.15, 0.20) == 0.0


def test_minimum_abstention_refuses_an_out_of_range_alpha() -> None:
    with pytest.raises(ValueError, match="alpha"):
        minimum_abstention(0.5, 1.0)


# --- AUROC orientation, which is the single easiest thing to get backwards -----------


def test_auroc_is_one_when_confidence_ranks_every_success_above_every_failure() -> None:
    assert auroc([0.9, 0.8, 0.2, 0.1], [False, False, True, True]) == 1.0


def test_auroc_is_zero_when_the_ranking_is_exactly_inverted() -> None:
    assert auroc([0.1, 0.2, 0.8, 0.9], [False, False, True, True]) == 0.0


def test_auroc_counts_a_full_tie_as_chance() -> None:
    assert auroc([0.5, 0.5, 0.5, 0.5], [False, False, True, True]) == 0.5


def test_auroc_is_none_when_a_class_is_empty_rather_than_reporting_chance() -> None:
    """A system with no failures has no AUROC. Returning 0.5 would invent a measurement."""

    assert auroc([0.1, 0.2], [False, False]) is None
    assert auroc([0.1, 0.2], [True, True]) is None


def test_auroc_refuses_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        auroc([0.1, 0.2], [True])


@given(
    values=st.lists(st.floats(-5.0, 5.0, allow_nan=False), min_size=2, max_size=40),
    seed=st.integers(0, 2**32 - 1),
)
def test_auroc_is_invariant_to_any_monotone_relabelling_of_the_score(
    values: list[float], seed: int
) -> None:
    """Log-probability is an arbitrary monotone scale, so AUROC must not depend on it."""

    rng = np.random.default_rng(seed)
    labels = rng.random(len(values)) < 0.5
    stretched_values = [math.atan(v) for v in values]
    # atan can round two adjacent doubles onto one another (5.0 and 4.999999999999999 collide),
    # inventing a tie the original ranking did not have. That is a limit of the test's transform,
    # not of auroc, so those draws are excluded rather than asserted on.
    assume(len(set(stretched_values)) == len(set(values)))
    plain = auroc(values, labels)
    stretched = auroc(stretched_values, labels)
    if plain is None:
        assert stretched is None
    else:
        assert stretched == pytest.approx(plain)


def test_average_precision_is_one_when_every_failure_sorts_to_the_bottom() -> None:
    assert average_precision([0.1, 0.2, 0.8, 0.9], [True, True, False, False]) == 1.0


def test_average_precision_is_none_without_a_positive_class() -> None:
    assert average_precision([0.1, 0.2], [False, False]) is None


# --- selective risk: AURC, its normalization, and the acceptance gap -----------------


def test_normalized_aurc_is_zero_for_a_perfect_ranking() -> None:
    """Score descending exactly as loss ascends: the score has extracted everything there is."""

    result = selective_risk(_rows([0.0, 0.0, 1.0, 1.0], [4.0, 3.0, 2.0, 1.0]), alpha=0.2)
    assert result.normalized_aurc == pytest.approx(0.0)
    assert result.aurc == pytest.approx(result.aurc_optimal)


def test_normalized_aurc_exceeds_one_for_an_inverted_ranking() -> None:
    """Worse than chance is a real outcome and must not be clipped into [0,1]."""

    result = selective_risk(_rows([0.0, 0.0, 1.0, 1.0], [1.0, 2.0, 3.0, 4.0]), alpha=0.2)
    assert result.normalized_aurc is not None
    assert result.normalized_aurc > 1.0


def test_normalized_aurc_is_none_when_every_group_carries_the_same_loss() -> None:
    """With nothing to rank, "how well did it rank" has no answer."""

    result = selective_risk(_rows([0.5] * 4, [4.0, 3.0, 2.0, 1.0]), alpha=0.2)
    assert result.normalized_aurc is None


def test_random_ranking_area_equals_the_base_risk_over_eligible_groups() -> None:
    result = selective_risk(_rows([0.0, 0.25, 0.75, 1.0], [4.0, 3.0, 2.0, 1.0]), alpha=0.2)
    assert result.aurc_random == pytest.approx(0.5)
    assert result.base_risk_eligible == pytest.approx(0.5)


def test_coverage_is_diluted_by_groups_that_can_never_be_accepted() -> None:
    """Half the groups are invalid, so the reachable coverage tops out at half. This is the
    ``ni_groups`` effect the certifier applies, reproduced rather than re-derived."""

    rows = _rows([0.0, 0.0, 1.0, 1.0], [4.0, 3.0, 2.0, 1.0], valid=[True, True, False, False])
    result = selective_risk(rows, alpha=0.2)
    assert result.eligible_groups == 2
    assert result.total_groups == 4
    assert result.max_acceptance_within_alpha == pytest.approx(0.5)


def test_the_two_shortfalls_differ_and_the_oracle_one_is_the_tighter() -> None:
    """Base risk 0.45 at alpha 0.2 permits 68.75% acceptance arithmetically. But this population
    holds its goodness in two all-or-nothing groups, so a PERFECT ranking stops at 50% -- the
    third group would drag the accepted mean to 0.30. Quoting 68.75% as the score-discrimination
    gap would charge the score for 18.75 points the population never made available."""

    rows = _rows([0.0, 0.0, 0.9, 0.9], [1.0, 2.0, 3.0, 4.0])
    result = selective_risk(rows, alpha=0.2)
    assert result.base_risk_all_groups == pytest.approx(0.45)
    assert result.acceptance_permitted_by_base_risk == pytest.approx(0.6875)
    assert result.acceptance_under_loss_optimal_ranking == pytest.approx(0.5)
    # The score is exactly inverted, so it delivers nothing at all.
    assert result.max_acceptance_within_alpha == pytest.approx(0.0)
    assert result.acceptance_shortfall_vs_oracle == pytest.approx(0.5)
    assert result.acceptance_shortfall_vs_base_risk == pytest.approx(0.6875)
    assert result.acceptance_shortfall_vs_oracle < result.acceptance_shortfall_vs_base_risk


def test_the_arithmetic_bound_can_be_attained_and_then_the_two_agree() -> None:
    """Not every population wastes the arithmetic headroom: here four zero-loss groups plus one
    lossy one average exactly alpha, so the oracle reaches the bound and the two coincide."""

    rows = _rows([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], [1, 2, 3, 4, 5, 6, 7, 8])
    result = selective_risk(rows, alpha=0.2)
    assert result.acceptance_permitted_by_base_risk == pytest.approx(0.625)
    assert result.acceptance_under_loss_optimal_ranking == pytest.approx(0.625)


def test_a_perfect_ranking_has_no_oracle_shortfall() -> None:
    """The score already is the loss ordering, so nothing is left for a better score to find."""

    result = selective_risk(_rows([0.0, 0.0, 1.0, 1.0], [4.0, 3.0, 2.0, 1.0]), alpha=0.2)
    assert result.acceptance_under_loss_optimal_ranking == pytest.approx(0.5)
    assert result.acceptance_shortfall_vs_oracle == pytest.approx(0.0)


def test_selective_risk_reports_nothing_measurable_when_no_group_is_eligible() -> None:
    rows = _rows([0.3, 0.4], [1.0, 2.0], valid=[False, False])
    result = selective_risk(rows, alpha=0.2)
    assert result.aurc is None
    assert result.max_acceptance_within_alpha == 0.0
    assert result.acceptance_under_loss_optimal_ranking == 0.0
    assert set(result.risk_at_coverage) == {f"{c:.2f}" for c in COVERAGE_GRID}
    assert all(value is None for value in result.risk_at_coverage.values())
    # Base risk is still measurable and still forces abstention — the arithmetic does not need
    # an eligible group to say the population is too lossy.
    assert result.base_risk_all_groups == pytest.approx(0.35)


def test_risk_at_coverage_reads_the_score_ranked_curve_not_the_oracle_one() -> None:
    """Losses ascend with the score, so risk at 50% coverage is the mean of the worst half of
    the accepted prefix — 0.25 — not the 0.0 an oracle ranking would give."""

    rows = _rows([0.0, 0.5, 1.0, 1.0], [4.0, 3.0, 2.0, 1.0])
    assert selective_risk(rows, alpha=0.2).risk_at_coverage["0.50"] == pytest.approx(0.25)


def test_oracle_accepted_set_is_the_within_alpha_prefix_and_nothing_more() -> None:
    rows = _rows([0.0, 0.0, 1.0, 0.0], [4.0, 3.0, 2.0, 1.0])
    assert _oracle_accepted(rows, alpha=0.2) == frozenset({"g0", "g1"})


def test_oracle_accepted_set_is_empty_when_the_best_group_already_breaches_alpha() -> None:
    assert _oracle_accepted(_rows([1.0, 1.0], [2.0, 1.0]), alpha=0.2) == frozenset()


# --- cross-sentence distance, recovered separately from the flattened tokens ---------


def _instance(trigger_start: int, argument_starts: list[int]) -> RamsInstance:
    return RamsInstance(
        instance_key="rams:x",
        source_id="x",
        tokens=tuple(f"t{i}" for i in range(30)),
        event_type="life.die.n/a",
        trigger_start=trigger_start,
        trigger_end=trigger_start + 1,
        arguments=tuple(RamsArgument(role="victim", start=s, end=s + 1) for s in argument_starts),
    )


def test_cross_sentence_counts_arguments_outside_the_trigger_sentence() -> None:
    starts = (0, 10, 20)  # three sentences
    instance = _instance(trigger_start=12, argument_starts=[11, 15, 3, 25])
    assert cross_sentence_arguments(instance, starts) == 2


def test_cross_sentence_is_zero_when_boundaries_are_unavailable() -> None:
    """No boundaries means no measurement; it must not silently count everything as crossing."""

    assert cross_sentence_arguments(_instance(5, [1, 2]), ()) == 0


def test_bucket_labels_are_stable_and_open_upward_at_the_last_edge() -> None:
    edges = (1, 2, 3, 4, 6)
    assert [_bucket(v, edges) for v in (1, 2, 3, 4, 5, 6, 99)] == [
        "1",
        "2",
        "3",
        "4-5",
        "4-5",
        "6+",
        "6+",
    ]


# --- stratification and the grounding association ------------------------------------


def _feature(
    group_id: str,
    *,
    score: float,
    loss: float,
    all_valid: bool = True,
    triggers: int = 1,
    gold: int = 1,
    cross: int = 0,
    valid_members: int | None = None,
) -> GroupFeature:
    return GroupFeature(
        group_id=group_id,
        score=score,
        loss=loss,
        all_valid=all_valid,
        triggers=triggers,
        gold_arguments=gold,
        cross_sentence=cross,
        valid_members=triggers if valid_members is None else valid_members,
        content_members=triggers if valid_members is None else valid_members,
    )


def test_stratify_reports_the_never_acceptable_groups_as_their_own_stratum() -> None:
    features = [
        _feature("a", score=1.0, loss=0.0),
        _feature("b", score=0.5, loss=0.9, all_valid=False),
        _feature("c", score=0.2, loss=0.8, all_valid=False),
    ]
    out = stratify(features, alpha=0.2, accepted=frozenset({"a"}))
    never = out["never_acceptable"]
    assert isinstance(never, dict)
    assert never["not_all_valid"]["groups"] == 2
    assert never["all_valid"]["groups"] == 1


def test_acceptance_lift_is_one_when_acceptances_fall_where_chance_would_put_them() -> None:
    """Two strata of equal size, one acceptance in each: neither stratum is favoured."""

    features = [
        _feature("a", score=1.0, loss=0.0, cross=0),
        _feature("b", score=0.9, loss=0.0, cross=0),
        _feature("c", score=0.8, loss=0.0, cross=1),
        _feature("d", score=0.7, loss=0.0, cross=1),
    ]
    out = stratify(features, alpha=0.2, accepted=frozenset({"a", "c"}))
    strata = out["cross_sentence"]
    assert isinstance(strata, dict)
    assert strata["0"]["acceptance_lift"] == pytest.approx(1.0)
    assert strata["1"]["acceptance_lift"] == pytest.approx(1.0)


def test_stratify_leaves_acceptance_lift_undefined_when_nothing_was_accepted() -> None:
    out = stratify([_feature("a", score=1.0, loss=0.9)], alpha=0.2, accepted=frozenset())
    strata = out["cross_sentence"]
    assert isinstance(strata, dict)
    assert strata["0"]["acceptance_lift"] is None


def test_grounding_association_isolates_the_fully_grounded_cell() -> None:
    """The cell the §3.2 wording turns on: groups whose every member parsed and stayed in the
    source text, and whose loss is nonetheless far above alpha."""

    features = [
        _feature("a", score=1.0, loss=0.7, triggers=2, valid_members=2),
        _feature("b", score=0.9, loss=0.6, triggers=2, valid_members=2),
        _feature("c", score=0.1, loss=1.0, triggers=2, valid_members=0),
    ]
    out = grounding_association(features)
    conditional = out["conditional_mean_loss_by_grounded_fraction"]
    assert isinstance(conditional, dict)
    assert conditional["1.00"]["groups"] == 2
    assert conditional["1.00"]["mean_loss"] == pytest.approx(0.65)
    assert conditional["0.00"]["groups"] == 1


def test_grounding_association_on_an_empty_population_reports_no_groups() -> None:
    assert grounding_association([]) == {"groups": 0}


# --- the group features are built from the group's own members -----------------------


def test_build_group_features_sums_gold_and_cross_sentence_over_group_members() -> None:
    instances = {
        "rams:d1": _instance(trigger_start=1, argument_starts=[2, 15]),
        "rams:d2": _instance(trigger_start=12, argument_starts=[13]),
    }
    data = SplitSystemData(
        system_id="qa",
        split_role="development",
        confidence_candidate="mean",
        rows=[GroupRow(group_id="g1", score=-0.1, all_valid=True, loss=0.4, document_count=2)],
        channel_by_document={"rams:d1": "valid_content_bearing", "rams:d2": "grounding_failure"},
        loss_by_document={"rams:d1": 0.3, "rams:d2": 0.5},
        score_by_document={"rams:d1": -0.1, "rams:d2": -0.2},
        valid_by_document={"rams:d1": True, "rams:d2": False},
        group_by_document={"rams:d1": "g1", "rams:d2": "g1"},
    )
    offsets = {"rams:d1": (0, 10, 20), "rams:d2": (0, 10, 20)}
    (feature,) = build_group_features(data, instances=instances, sentence_offsets=offsets)
    assert feature.triggers == 2
    assert feature.gold_arguments == 3
    assert feature.cross_sentence == 1  # d1's argument at 15 crosses; d2's at 13 does not
    assert feature.valid_members == 1
    assert feature.grounded_fraction == pytest.approx(0.5)


def test_system_readout_carries_every_indicator_and_the_headline_reads_it() -> None:
    instances = {f"rams:d{i}": _instance(1, [2]) for i in range(1, 5)}
    losses = {"rams:d1": 0.0, "rams:d2": 0.1, "rams:d3": 0.9, "rams:d4": 1.0}
    scores = {"rams:d1": -0.1, "rams:d2": -0.2, "rams:d3": -0.8, "rams:d4": -0.9}
    data = SplitSystemData(
        system_id="qa",
        split_role="development",
        confidence_candidate="mean",
        rows=[
            GroupRow(
                group_id=f"g{i}",
                score=scores[f"rams:d{i}"],
                all_valid=True,
                loss=losses[f"rams:d{i}"],
                document_count=1,
            )
            for i in range(1, 5)
        ],
        channel_by_document=dict.fromkeys(losses, "valid_content_bearing"),
        loss_by_document=losses,
        score_by_document=scores,
        valid_by_document=dict.fromkeys(losses, True),
        group_by_document={f"rams:d{i}": f"g{i}" for i in range(1, 5)},
    )
    readout = system_readout(
        data,
        build_group_features(
            data, instances=instances, sentence_offsets=dict.fromkeys(instances, (0, 10, 20))
        ),
        alpha=0.2,
    )
    discrimination = readout["discrimination"]
    assert isinstance(discrimination, dict)
    assert set(discrimination) == {"above_alpha", "any_error", "not_all_valid"}
    # Score ranks the two low-loss groups on top, so failure detection is perfect here.
    assert discrimination["above_alpha"]["auroc"] == 1.0
    # No group is invalid, so that indicator has one empty class and no AUROC.
    assert discrimination["not_all_valid"]["auroc"] is None
    assert headline(readout)["delivered"] == pytest.approx(0.5)
    assert headline(readout)["oracle_ranking"] == pytest.approx(0.5)


def test_prediction_status_literals_still_match_the_channels_grounding_relies_on() -> None:
    """``grounded_fraction`` equates "valid" with "parsed and grounded". That holds only while
    the two failure statuses are the only alternatives; a new status would silently join the
    grounded side of the ratio."""

    assert set(typing.get_args(PredictionRecord.model_fields["status"].annotation)) == {
        "valid",
        "structural_failure",
        "grounding_failure",
    }
