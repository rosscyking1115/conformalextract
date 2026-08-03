from __future__ import annotations

import pytest

from conformalextract.certification_run import (
    GroupRow,
    SealedRoleError,
    aggregate_to_groups,
    build_certification_access_log,
    certification_artifact,
    certify_system,
    group_accepted,
    loss_summaries,
    risk_coverage_frontier,
    run_certification,
    size_distribution,
)

# --- ADR 0009 group aggregation ------------------------------------------------------


def _aggregation_inputs() -> dict[str, object]:
    return {
        "document_ids": ["d1", "d2", "d3"],
        "group_by_document": {"d1": "g1", "d2": "g1", "d3": "g2"},
        "score_by_document": {"d1": -0.1, "d2": -0.9, "d3": -0.2},
        "valid_by_document": {"d1": True, "d2": True, "d3": True},
        "loss_by_document": {"d1": 0.0, "d2": 1.0, "d3": 0.5},
    }


def test_group_score_is_the_minimum_member_and_loss_is_the_mean() -> None:
    rows = aggregate_to_groups(**_aggregation_inputs())  # type: ignore[arg-type]
    by_id = {row.group_id: row for row in rows}
    assert by_id["g1"].score == pytest.approx(-0.9)  # worst member, not the best
    assert by_id["g1"].loss == pytest.approx(0.5)  # mean of 0.0 and 1.0
    assert by_id["g1"].document_count == 2
    assert by_id["g2"].score == pytest.approx(-0.2)
    assert by_id["g2"].document_count == 1


def test_a_group_is_invalid_if_any_member_is_invalid() -> None:
    inputs = _aggregation_inputs()
    inputs["valid_by_document"] = {"d1": True, "d2": False, "d3": True}  # type: ignore[index]
    rows = aggregate_to_groups(**inputs)  # type: ignore[arg-type]
    by_id = {row.group_id: row for row in rows}
    assert by_id["g1"].all_valid is False
    assert by_id["g2"].all_valid is True


def test_near_duplicates_cannot_manufacture_acceptance() -> None:
    """One easy member must not carry a group over the threshold."""
    rows = aggregate_to_groups(**_aggregation_inputs())  # type: ignore[arg-type]
    g1 = next(row for row in rows if row.group_id == "g1")
    assert group_accepted(g1, -0.5) is False  # min is -0.9, so -0.5 is not cleared
    assert group_accepted(g1, -1.0) is True


def test_aggregation_is_deterministic_in_group_id_order() -> None:
    first = aggregate_to_groups(**_aggregation_inputs())  # type: ignore[arg-type]
    inputs = _aggregation_inputs()
    inputs["document_ids"] = ["d3", "d2", "d1"]  # type: ignore[index]
    second = aggregate_to_groups(**inputs)  # type: ignore[arg-type]
    assert [row.group_id for row in first] == [row.group_id for row in second]
    assert first == second


def test_missing_group_or_out_of_range_loss_fails_loudly() -> None:
    inputs = _aggregation_inputs()
    inputs["group_by_document"] = {"d1": "g1", "d2": "g1"}  # type: ignore[index]
    with pytest.raises(ValueError, match="no group assignment"):
        aggregate_to_groups(**inputs)  # type: ignore[arg-type]
    inputs = _aggregation_inputs()
    inputs["loss_by_document"] = {"d1": 0.0, "d2": 1.5, "d3": 0.5}  # type: ignore[index]
    with pytest.raises(ValueError, match="out-of-range document loss"):
        aggregate_to_groups(**inputs)  # type: ignore[arg-type]


# --- sealed-label access -------------------------------------------------------------


def test_access_log_permits_certification_and_verifies() -> None:
    log = build_certification_access_log(["d1", "d2"])
    assert log.document_count == 2
    assert log.verify() is True


def test_final_and_shift_are_unreachable_from_certification() -> None:
    """Opening the certification split must not become a foothold for the others."""
    for role in ("final", "shift", "train", "development"):
        with pytest.raises(SealedRoleError, match="unreachable"):
            build_certification_access_log(["d1"], data_role=role)


def test_tampering_with_the_access_chain_is_detected() -> None:
    log = build_certification_access_log(["d1", "d2"])
    tampered = type(log)(
        entries=(log.entries[0],), head_hash=log.head_hash, document_count=1
    )
    assert tampered.verify() is False


# --- certification behaviour (§7.2, §13.3) -------------------------------------------


def _rows(n: int, loss: float, score: float = 0.0) -> list[GroupRow]:
    return [
        GroupRow(group_id=f"g{i:04d}", score=score, all_valid=True, loss=loss, document_count=1)
        for i in range(n)
    ]


def test_zero_accepted_is_ineligible_not_zero_risk() -> None:
    """§7.1: pairs with zero accepted units are ineligible, never zero-risk."""
    rows = _rows(2000, loss=0.0)
    # An unreachable threshold accepts nothing.
    result = certify_system(
        "qa", rows, [float("inf")], alpha=0.20, delta_s=0.0167, acceptance_floor=0.20
    )
    assert result.feasible is False
    assert result.status != "certified"
    assert result.n_accepted == 0


def test_high_risk_system_is_infeasible_not_silently_certified() -> None:
    """§7.2: a system with no feasible candidate returns Infeasible."""
    rows = _rows(2000, loss=1.0)  # every accepted group is a total loss
    result = certify_system(
        "zs", rows, [float("-inf")], alpha=0.20, delta_s=0.0167, acceptance_floor=0.20
    )
    assert result.feasible is False
    assert result.status == "infeasible"


def test_low_risk_system_certifies_and_reports_acceptance() -> None:
    rows = _rows(2000, loss=0.0)
    result = certify_system(
        "qa", rows, [float("-inf")], alpha=0.20, delta_s=0.0167, acceptance_floor=0.20
    )
    assert result.status == "certified"
    assert result.feasible is True
    assert result.acceptance_lower > 0.20


def test_insufficient_n_reports_the_theorem_precondition() -> None:
    rows = _rows(10, loss=0.0)  # far below scorc_minimum_n
    result = certify_system(
        "qa", rows, [float("-inf")], alpha=0.20, delta_s=0.0167, acceptance_floor=0.20
    )
    assert result.status == "insufficient_n"
    assert "theorem_sample_precondition" in result.reasons


# --- H1/H2 and the pre-registered collapse -------------------------------------------


def _run(qa_loss: float, baseline_loss: float):  # type: ignore[no-untyped-def]
    rows_by_system = {
        "qa": _rows(2000, loss=qa_loss),
        "zs": _rows(2000, loss=baseline_loss),
        "fs": _rows(2000, loss=baseline_loss),
    }
    thresholds = {s: [float("-inf")] for s in rows_by_system}
    return run_certification(
        rows_by_system=rows_by_system,
        thresholds_by_system=thresholds,
        candidates_by_system={"qa": "mean", "zs": "mean", "fs": "tenth_percentile"},
        delta_allocation={"qa": 0.05 / 3, "zs": 0.05 / 3, "fs": 0.05 / 3},
        access_log=build_certification_access_log(["d1"]),
        alpha=0.20,
        delta=0.05,
        acceptance_floor=0.20,
        material_gain=0.05,
    )


def test_boundary_crossing_when_only_qa_certifies_and_collapse_is_flagged() -> None:
    run = _run(qa_loss=0.0, baseline_loss=1.0)
    assert run.systems["qa"].certified_acceptance is not None
    assert run.systems["zs"].certified_acceptance is None
    assert run.systems["fs"].certified_acceptance is None
    assert run.h1.outcome == "boundary_crossing"
    assert run.h2.outcome == "boundary_crossing"
    # Pre-registered: this is one test stated twice, and the artifact must say so.
    assert run.hypotheses_collapsed is True
    artifact = certification_artifact(run, provenance={})
    assert artifact["hypotheses"]["collapsed_to_single_test"] is True
    assert "ONE test stated twice" in artifact["hypotheses"]["collapse_note"]


def test_no_collapse_flag_when_a_baseline_also_certifies() -> None:
    run = _run(qa_loss=0.0, baseline_loss=0.0)
    assert run.hypotheses_collapsed is False
    assert certification_artifact(run, provenance={})["hypotheses"]["collapse_note"] is None


def test_delta_allocation_must_exhaust_delta() -> None:
    with pytest.raises(ValueError, match="delta allocation sums"):
        run_certification(
            rows_by_system={s: _rows(2000, 0.0) for s in ("qa", "zs", "fs")},
            thresholds_by_system={s: [float("-inf")] for s in ("qa", "zs", "fs")},
            candidates_by_system={s: "mean" for s in ("qa", "zs", "fs")},
            delta_allocation={"qa": 0.01, "zs": 0.01, "fs": 0.01},
            access_log=build_certification_access_log(["d1"]),
            alpha=0.20,
            delta=0.05,
            acceptance_floor=0.20,
            material_gain=0.05,
        )


def test_artifact_reports_unweighted_and_size_weighted_loss(  # A2
) -> None:
    """The certificate bounds the unweighted quantity; readers hear the size-weighted one."""
    rows = [
        GroupRow(group_id="g1", score=0.0, all_valid=True, loss=1.0, document_count=1),
        GroupRow(group_id="g2", score=0.0, all_valid=True, loss=0.0, document_count=9),
    ]
    summary = loss_summaries(rows)
    assert summary["unweighted_mean_loss"] == pytest.approx(0.5)  # (1.0 + 0.0) / 2
    assert summary["size_weighted_mean_loss"] == pytest.approx(0.1)  # (1*1 + 9*0) / 10
    assert summary["gap"] == pytest.approx(0.4)


def test_size_distribution_buckets_groups(  # A3
) -> None:
    rows = [
        GroupRow(group_id=f"g{i}", score=0.0, all_valid=True, loss=0.0, document_count=size)
        for i, size in enumerate([1, 1, 2, 3, 5, 9])
    ]
    assert size_distribution(rows) == {"1": 2, "2-3": 2, "4-6": 1, "7+": 1}


def test_groups_with_an_invalid_member_cap_acceptance_before_thresholding(  # A4
) -> None:
    rows = _rows(2000, loss=0.0)
    rows[0] = GroupRow(
        group_id=rows[0].group_id, score=0.0, all_valid=False, loss=0.0, document_count=2
    )
    run = run_certification(
        rows_by_system={"qa": rows, "zs": rows, "fs": rows},
        thresholds_by_system={s: [float("-inf")] for s in ("qa", "zs", "fs")},
        candidates_by_system={s: "mean" for s in ("qa", "zs", "fs")},
        delta_allocation={s: 0.05 / 3 for s in ("qa", "zs", "fs")},
        access_log=build_certification_access_log(["d1"]),
        alpha=0.20,
        delta=0.05,
        acceptance_floor=0.20,
        material_gain=0.05,
    )
    artifact = certification_artifact(run, provenance={})
    qa = artifact["systems"]["qa"]  # type: ignore[index]
    assert qa["never_acceptable_groups"] == 1
    assert qa["acceptance_ceiling"] == pytest.approx(1999 / 2000)
    # A feasible system also reports the size mix of what it actually accepted.
    assert qa["accepted_size_distribution"] is not None


def test_risk_coverage_frontier_separates_score_failure_from_grid_artifact() -> None:
    """Half of how the certification null is reported (correction C4).

    Renamed 2026-08-03: it was ``..._separates_capability_gap_from_artifact``, which claimed more
    than the frontier can see. Penalty-free is what makes it clean evidence about the score and
    also what blinds it to the finite-sample penalty (``CX-CAPGAP-01`` cause 2).
    """
    # A perfectly separable system: the top half is loss-free, so the floor is reachable.
    separable = [
        GroupRow(group_id=f"g{i:03d}", score=float(-i), all_valid=True,
                 loss=0.0 if i < 50 else 1.0, document_count=1)
        for i in range(100)
    ]
    good = risk_coverage_frontier(separable, alpha=0.20, acceptance_floor=0.20)
    assert good.floor_reachable is True
    assert good.max_acceptance_within_alpha >= 0.20

    # A system whose score carries no signal: risk is flat at the base rate everywhere.
    uninformative = [
        GroupRow(group_id=f"g{i:03d}", score=float(-i), all_valid=True,
                 loss=1.0 if i % 2 else 0.0, document_count=1)
        for i in range(100)
    ]
    bad = risk_coverage_frontier(uninformative, alpha=0.20, acceptance_floor=0.20)
    assert bad.floor_reachable is False  # no threshold rule could rescue this


def test_risk_coverage_frontier_counts_ineligible_groups_against_coverage() -> None:
    """Invalid groups can never be accepted, so they must dilute achievable acceptance."""
    rows = [GroupRow(group_id="g0", score=0.0, all_valid=True, loss=0.0, document_count=1)]
    rows += [
        GroupRow(group_id=f"g{i}", score=0.0, all_valid=False, loss=0.0, document_count=1)
        for i in range(1, 10)
    ]
    frontier = risk_coverage_frontier(rows, alpha=0.20, acceptance_floor=0.20)
    assert frontier.eligible_groups == 1
    assert frontier.total_groups == 10
    assert frontier.max_acceptance_within_alpha == pytest.approx(0.1)  # 1/10, not 1/1
    assert frontier.floor_reachable is False


def test_artifact_is_text_free_and_records_zero_final_shift_reads() -> None:
    run = _run(qa_loss=0.0, baseline_loss=1.0)
    artifact = certification_artifact(run, provenance={"git_commit": "abc"})
    serialized = str(artifact)
    for banned in ("raw_output", "prompt", "sentences", "text"):
        assert banned not in serialized
    assert artifact["certification_access"]["final_reads"] == 0
    assert artifact["certification_access"]["shift_reads"] == 0
    assert artifact["certification_access"]["verified"] is True
