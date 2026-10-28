"""ADR 0011 re-analysis: the alpha-free curve, loss channels and the grounding oracle."""

from __future__ import annotations

import typing
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from conformalextract.certification_run import (
    GroupRow,
    SealedRoleError,
    build_certification_access_log,
    risk_coverage_curve,
    risk_coverage_frontier,
)
from conformalextract.contracts import Argument, EventFrame, PredictionRecord, Span
from conformalextract.development_gate import document_loss
from conformalextract.reanalysis import (
    CONTENT_CHANNEL,
    LOSS_CHANNELS,
    SplitSystemData,
    access_block,
    assert_reanalysis_role,
    certification_access_for,
    decompose_losses,
    grounding_oracle_comparison,
    load_split_system_data,
    loss_channel,
    mean_loss_ceiling,
)

# --- the curve is the frontier, read at one height -----------------------------------


def _rows(losses: list[float], scores: list[float] | None = None) -> list[GroupRow]:
    scores = scores if scores is not None else [-float(i) for i in range(len(losses))]
    return [
        GroupRow(group_id=f"g{i:04d}", score=scores[i], all_valid=True, loss=loss, document_count=1)
        for i, loss in enumerate(losses)
    ]


# No deadline: this failed intermittently only under concurrent GPU load and never alone, which
# is Hypothesis's 200 ms default deadline tripping, not a numerical difference.
@settings(deadline=None)
@given(
    losses=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=40),
    alpha=st.floats(min_value=0.0, max_value=1.0),
)
def test_curve_read_at_alpha_reproduces_the_frontier(losses: list[float], alpha: float) -> None:
    """The sweep must be a re-reading of the committed object, not a second statistic."""

    rows = _rows(losses)
    curve = risk_coverage_curve(rows)
    frontier = risk_coverage_frontier(rows, alpha=alpha, acceptance_floor=0.20)
    assert curve.max_acceptance_within(alpha) == pytest.approx(
        frontier.max_acceptance_within_alpha
    )


def test_alpha_star_inverts_max_acceptance() -> None:
    """alpha_star(c) is the smallest alpha at which coverage c is reachable."""

    rows = _rows([0.0, 0.0, 1.0, 1.0, 1.0])
    curve = risk_coverage_curve(rows)
    alpha_star = curve.alpha_star(0.40)
    assert alpha_star is not None
    assert curve.max_acceptance_within(alpha_star) >= 0.40
    # Anything strictly below it cannot reach that coverage.
    assert curve.max_acceptance_within(alpha_star - 1e-9) < 0.40


def test_alpha_star_is_correct_on_a_non_monotone_curve() -> None:
    """Min over reachable, not the first crossing -- the two must actually differ here."""

    # Running risk: 0.0, 0.5, 0.667, 0.5, 0.4, 0.333 -- rises then falls, so the cheapest way
    # to reach 50% coverage is a LATER, larger prefix than the first one that reaches it.
    rows = _rows([0.0, 1.0, 1.0, 0.0, 0.0, 0.0])
    curve = risk_coverage_curve(rows)
    assert curve.running_risk[2] == pytest.approx(2 / 3)  # first prefix reaching 50% coverage
    assert curve.alpha_star(0.50) == pytest.approx(1 / 3)  # ... but 1/3 suffices
    # A first-crossing implementation would return 2/3 here; guard against that regression.
    assert curve.alpha_star(0.50) < curve.running_risk[2]
    assert curve.max_acceptance_within(1 / 3) >= 0.50


def test_unreachable_coverage_has_no_alpha_star() -> None:
    rows = [
        GroupRow(group_id="g0", score=-1.0, all_valid=True, loss=0.0, document_count=1),
        GroupRow(group_id="g1", score=-2.0, all_valid=False, loss=0.0, document_count=1),
    ]
    curve = risk_coverage_curve(rows)
    assert curve.alpha_star(0.80) is None  # only one of two groups is ever eligible


def test_empty_curve_is_safe() -> None:
    curve = risk_coverage_curve([])
    assert curve.max_acceptance_within(0.20) == 0.0
    assert curve.alpha_star(0.20) is None


# --- loss channels --------------------------------------------------------------------


def _prediction(status: str, arguments: list[Argument]) -> PredictionRecord:
    return PredictionRecord(
        prediction_id="p",
        document_id="d",
        system_id="qa",
        prompt_hash="h",
        raw_output="",
        frames=[
            EventFrame(
                document_id="d",
                event_type="Conflict.Attack",
                trigger=Span(start=1, end=2, text="attacked"),
                arguments=arguments,
            )
        ],
        confidence=-0.5,
        status=status,  # type: ignore[arg-type]
    )


def test_channels_follow_the_parse_arm_predicate() -> None:
    argument = Argument(role="victim", span=Span(start=3, end=4, text="Clinton"))
    assert loss_channel(_prediction("valid", [argument])) == CONTENT_CHANNEL
    assert loss_channel(_prediction("valid", [])) == "valid_empty"
    assert loss_channel(_prediction("grounding_failure", [argument])) == "grounding_failure"
    assert loss_channel(_prediction("structural_failure", [])) == "structural_failure"


def test_every_channel_is_declared() -> None:
    assert set(LOSS_CHANNELS) == {
        "structural_failure",
        "grounding_failure",
        "valid_empty",
        CONTENT_CHANNEL,
    }


# --- the decomposition is exact at both levels ----------------------------------------


def _decomposition_inputs() -> dict[str, dict[str, object]]:
    return {
        "channel_by_document": {
            "d1": CONTENT_CHANNEL,
            "d2": "grounding_failure",
            "d3": "valid_empty",
            "d4": CONTENT_CHANNEL,
            "d5": "structural_failure",
        },
        "loss_by_document": {"d1": 0.25, "d2": 1.0, "d3": 1.0, "d4": 0.0, "d5": 1.0},
        # g1 has three members and g2 two, so the two aggregation levels genuinely differ.
        "group_by_document": {"d1": "g1", "d2": "g1", "d3": "g1", "d4": "g2", "d5": "g2"},
    }


def test_channel_contributions_sum_to_both_totals() -> None:
    decomposition = decompose_losses("qa", **_decomposition_inputs())  # type: ignore[arg-type]
    document_sum = sum(c.document_level_contribution for c in decomposition.channels.values())
    group_sum = sum(c.group_level_contribution for c in decomposition.channels.values())
    assert document_sum == pytest.approx(decomposition.document_level_total)
    assert group_sum == pytest.approx(decomposition.group_level_total)


def test_group_level_total_is_the_unweighted_mean_of_group_means() -> None:
    """The certificate bounds this quantity (ADR 0009), so the decomposition must target it."""

    decomposition = decompose_losses("qa", **_decomposition_inputs())  # type: ignore[arg-type]
    g1 = (0.25 + 1.0 + 1.0) / 3  # three members
    g2 = (0.0 + 1.0) / 2  # two members
    assert decomposition.group_level_total == pytest.approx((g1 + g2) / 2)  # 0.625
    # ... and it is NOT the document mean, which is what a reader naturally hears.
    assert decomposition.document_level_total == pytest.approx(3.25 / 5)  # 0.65
    assert decomposition.total_gap == pytest.approx(-0.025)


def test_only_the_non_valid_channels_are_forced_to_loss_one() -> None:
    """document_loss forces 1.0 on non-valid records; an empty record is scored normally."""

    argument = Argument(role="victim", span=Span(start=3, end=4, text="Clinton"))
    gold = [
        EventFrame(
            document_id="d",
            event_type="Conflict.Attack",
            trigger=Span(start=1, end=2, text="attacked"),
            arguments=[argument],
        )
    ]
    # A grounding failure is forced to 1.0 even though its frames look right.
    assert document_loss(gold, _prediction("grounding_failure", [argument])) == pytest.approx(1.0)
    # An empty-but-valid record is scored: wrong against non-empty gold ...
    assert document_loss(gold, _prediction("valid", [])) == pytest.approx(1.0)
    # ... but correct against empty gold, so the channel is NOT forced.
    empty_gold = [
        EventFrame(
            document_id="d",
            event_type="Conflict.Attack",
            trigger=Span(start=1, end=2, text="attacked"),
            arguments=[],
        )
    ]
    assert document_loss(empty_gold, _prediction("valid", [])) == pytest.approx(0.0)
    assert loss_channel(_prediction("valid", [])) == "valid_empty"


def test_channel_means_are_read_from_the_losses_supplied() -> None:
    decomposition = decompose_losses("qa", **_decomposition_inputs())  # type: ignore[arg-type]
    for channel in ("structural_failure", "grounding_failure", "valid_empty"):
        assert decomposition.channels[channel].mean_loss_within_channel == pytest.approx(1.0)
    assert decomposition.channels[CONTENT_CHANNEL].mean_loss_within_channel == pytest.approx(0.125)


def test_decomposition_fails_loudly_on_a_document_without_a_channel() -> None:
    inputs = _decomposition_inputs()
    del inputs["channel_by_document"]["d3"]  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="lack a channel or group"):
        decompose_losses("qa", **inputs)  # type: ignore[arg-type]


# --- the arithmetic ceiling that carries the baselines' result (reviewer R5) -----------


def test_the_mean_loss_ceiling_matches_a_brute_force_search() -> None:
    """mu <= alpha*c + (1-c) must really be the largest mean that can reach coverage c."""

    alpha, coverage = 0.20, 0.20
    ceiling = mean_loss_ceiling(alpha=alpha, acceptance_floor=coverage)
    assert ceiling == pytest.approx(0.84)

    size, keep = 100, 20
    # At the ceiling, concentrating all the "goodness" in the kept prefix exactly attains alpha.
    best_possible = (ceiling * size - (size - keep) * 1.0) / keep
    assert best_possible == pytest.approx(alpha)
    # A hair above the ceiling, no arrangement of losses can keep the best 20% within alpha.
    worse = ((ceiling + 0.01) * size - (size - keep) * 1.0) / keep
    assert worse > alpha


def test_a_population_above_the_ceiling_cannot_reach_the_floor_by_any_ordering() -> None:
    """The claim the baselines rest on, tested against the curve rather than asserted."""

    ceiling = mean_loss_ceiling(alpha=0.20, acceptance_floor=0.20)
    # Mean loss 0.95 > 0.84: every ordering, including the best-case one, must fail.
    losses = [0.0] * 5 + [1.0] * 95
    assert sum(losses) / len(losses) > ceiling
    for arrangement in (losses, list(reversed(losses)), sorted(losses)):
        curve = risk_coverage_curve(_rows(arrangement))
        assert curve.max_acceptance_within(0.20) < 0.20


# --- the grounding-oracle counterfactual ----------------------------------------------


def _split_data(
    *, channels: dict[str, str], losses: dict[str, float], scores: dict[str, float]
) -> SplitSystemData:
    from conformalextract.certification_run import aggregate_to_groups

    groups = {document_id: f"grp-{document_id}" for document_id in losses}
    valid = {d: channels[d] not in ("structural_failure", "grounding_failure") for d in losses}
    rows = aggregate_to_groups(
        document_ids=sorted(losses),
        group_by_document=groups,
        score_by_document=scores,
        valid_by_document=valid,
        loss_by_document=losses,
    )
    return SplitSystemData(
        system_id="zs",
        split_role="development",
        confidence_candidate="mean",
        rows=rows,
        channel_by_document=channels,
        loss_by_document=losses,
        score_by_document=scores,
        valid_by_document=valid,
        group_by_document=groups,
    )


def test_grounding_oracle_does_not_rescue_a_system_that_is_wrong_when_it_grounds() -> None:
    """The claim: removing the grounding deficit moves the frontier by nothing."""

    channels = {"d1": CONTENT_CHANNEL, "d2": "grounding_failure", "d3": "grounding_failure"}
    data = _split_data(
        channels=channels,
        losses={"d1": 0.9, "d2": 1.0, "d3": 1.0},
        scores={"d1": -0.1, "d2": -0.2, "d3": -0.3},
    )
    comparison = grounding_oracle_comparison(data, alpha=0.20, acceptance_floor=0.20)
    assert comparison.floor_reachable_unconditionally is False
    # Even scored as if grounding were perfect, on its own restricted population, the one
    # content-bearing document is still wrong -- so the floor stays out of reach.
    assert comparison.floor_reachable_under_grounding_oracle is False
    assert comparison.frontier_movement == pytest.approx(0.0)


def test_grounding_oracle_does_rescue_a_system_that_is_right_when_it_grounds() -> None:
    """The counterfactual must be able to return the other answer, or it proves nothing."""

    channels = {"d1": CONTENT_CHANNEL, "d2": "grounding_failure", "d3": "grounding_failure"}
    data = _split_data(
        channels=channels,
        losses={"d1": 0.0, "d2": 1.0, "d3": 1.0},
        scores={"d1": -0.1, "d2": -0.2, "d3": -0.3},
    )
    comparison = grounding_oracle_comparison(data, alpha=0.20, acceptance_floor=0.20)
    assert comparison.conditional_max_acceptance == pytest.approx(1.0)
    assert comparison.floor_reachable_under_grounding_oracle is True
    assert comparison.conditional_groups == 1  # restricted population, not the original 3


# --- sealed-access discipline ----------------------------------------------------------


def test_development_reads_are_not_chained_and_disclose_no_certification_access() -> None:
    assert certification_access_for("development", ["d1"]) is None
    assert access_block(None) == {
        "certification_gold_read": False,
        "final_reads": 0,
        "shift_reads": 0,
    }


def test_certification_reads_are_chained_and_verify() -> None:
    log = certification_access_for("certification", ["d2", "d1"])
    assert log is not None
    assert log.document_count == 2
    assert log.verify() is True
    block = access_block(log)
    assert block["certification_gold_read"] is True
    assert block["verified"] is True
    assert block["final_reads"] == 0
    assert block["shift_reads"] == 0


def test_final_and_shift_remain_unreachable_from_the_reanalysis() -> None:
    """The re-analysis inherits the certifier's genesis, so no other role can be chained."""

    for role in ("final", "shift", "train", "development"):
        with pytest.raises(SealedRoleError):
            build_certification_access_log(["d1"], data_role=role)


# --- reviewer ruling R1: the role guard the sealed splits actually depend on ------------


def test_the_role_guard_is_an_allowlist_not_a_denylist() -> None:
    for role in ("development", "certification"):
        assert_reanalysis_role(role)  # permitted: must not raise
    for role in ("final", "shift", "train", "", "Certification", "certification "):
        with pytest.raises(SealedRoleError):
            assert_reanalysis_role(role)


def test_a_sealed_role_is_refused_before_any_gold_is_opened() -> None:
    """The failure mode this closes: read `final`, then attest `final_reads: 0`."""

    with pytest.raises(SealedRoleError, match="sealed split"):
        load_split_system_data(
            split_role="final",
            system_id="qa",
            confidence_candidate="mean",
            # Paths that would raise FileNotFoundError if the guard let execution reach them,
            # so a passing test proves the guard fired FIRST, before any file was touched.
            predictions_path=Path("does-not-exist/qa.v1.jsonl"),
            contexts={},
            instances={},
            group_by_document={},
            gold_frames=lambda instance: [],
        )


def test_an_unauthorised_role_cannot_be_disclosed_as_no_access() -> None:
    """certification_access_for must raise on a sealed role, not return None."""

    for role in ("final", "shift"):
        with pytest.raises(SealedRoleError):
            certification_access_for(role, ["d1"])


def _role_reading_commands() -> list[str]:
    """Every CLI command taking a split-role LIST, discovered rather than listed.

    A hardcoded list would let a NEW unguarded command pass silently until someone remembered
    to extend it -- which is the failure this guard exists to prevent, one level up.

    Selected on the annotation, not the parameter name: ``build-profiles`` and
    ``freeze-demonstrations`` also take ``--roles``, but theirs is a ``Path`` to a role-map
    file, not a comma-separated list of splits to open. Matching on the name alone pulls them
    in and the sealed-role test becomes a test that a filename does not exist.
    """

    import inspect

    from conformalextract.cli import app

    names = []
    for command in app.registered_commands:
        callback = command.callback
        if callback is None:  # pragma: no cover - every command here has one
            continue
        # eval_str resolves the annotation to an object: cli.py uses postponed annotations, so
        # without it every annotation is a string and the type test silently matches nothing.
        parameter = inspect.signature(callback, eval_str=True).parameters.get("roles")
        if parameter is None:
            continue
        # Annotated[str, typer.Option(...)] -> the split-role list; Annotated[Path, ...] -> a file.
        annotation = typing.get_args(parameter.annotation)
        if annotation and annotation[0] is str:
            names.append(command.name or callback.__name__.replace("_", "-"))
    return names


def test_the_role_reading_commands_are_discovered() -> None:
    """Guard the guard: if discovery silently returns nothing, the tests below prove nothing."""

    discovered = set(_role_reading_commands())
    assert discovered == {
        "risk-coverage-diagnostic",
        "alpha-frontier",
        "loss-decomposition",
        "calibration-diagnostics",
    }, (
        "a command taking a split-role list appeared or vanished; if it is new it must be "
        "guarded, and if it is a Path-typed --roles it must not be selected here"
    )


@pytest.mark.parametrize("command", _role_reading_commands())
@pytest.mark.parametrize("sealed", ["final", "shift"])
def test_every_split_reading_command_refuses_a_sealed_role(command: str, sealed: str) -> None:
    """Driven end-to-end through the CLI, so delegation to a guarded helper still counts.

    ``risk-coverage-diagnostic`` predates ADR 0011 and carried the same hole; the guarantee has
    to hold for every command that accepts ``--roles``, not just the new ones, which is why the
    list is introspected. These run without the private RAMS archive or predictions present, so
    a pass means the guard fired rather than a missing-file error being mistaken for a refusal.
    """

    from typer.testing import CliRunner

    from conformalextract.cli import app

    result = CliRunner().invoke(app, [command, "--roles", sealed])
    assert result.exit_code != 0
    assert isinstance(result.exception, SealedRoleError)
    assert sealed in str(result.exception)


@pytest.mark.parametrize("command", _role_reading_commands())
def test_a_sealed_role_is_refused_even_when_paired_with_a_permitted_one(command: str) -> None:
    """`--roles development,final` must not process development and then stop."""

    from typer.testing import CliRunner

    from conformalextract.cli import app

    result = CliRunner().invoke(app, [command, "--roles", "development,final"])
    assert isinstance(result.exception, SealedRoleError)
