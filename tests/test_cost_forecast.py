from __future__ import annotations

import pytest

from conformalextract.training import (
    REMAINING_BUDGET_USD,
    InferenceBenchmark,
    StageDemand,
    forecast_whole_programme,
)

# A slow, single-item schedule: no padding waste but no parallelism either.
NAIVE_UNBATCHED = InferenceBenchmark(batch_size=1, items_per_hour=200.0, hourly_rate_usd=1.80)
# A padded-batch schedule measured on the real prompt-length distribution.
PADDED_BATCHED = InferenceBenchmark(batch_size=32, items_per_hour=4000.0, hourly_rate_usd=1.80)


def test_remaining_budget_matches_the_frozen_cap_minus_recorded_spend() -> None:
    assert REMAINING_BUDGET_USD == pytest.approx(24.7992)


def test_naive_unbatched_inference_is_declared_infeasible() -> None:
    forecast = forecast_whole_programme(
        benchmark=NAIVE_UNBATCHED,
        stages=(StageDemand(stage="predictions", items=9124, essential=True),),
        r0_cost_usd=0.60,
        upload_cost_usd=0.10,
        reserve_usd=2.00,
    )

    assert forecast.decision == "infeasible"
    assert forecast.essential_floor_usd > REMAINING_BUDGET_USD


def test_padded_batched_full_programme_that_fits_is_a_go() -> None:
    forecast = forecast_whole_programme(
        benchmark=PADDED_BATCHED,
        stages=(
            StageDemand(stage="R1", items=500),
            StageDemand(stage="R2", items=2000),
            StageDemand(stage="predictions", items=9124, essential=True),
        ),
        r0_cost_usd=0.60,
        upload_cost_usd=0.10,
        reserve_usd=2.00,
    )

    assert forecast.decision == "go"
    assert forecast.total_committed_usd <= REMAINING_BUDGET_USD
    # Every essential stage plus reserve is held within budget.
    assert forecast.essential_floor_usd <= forecast.total_committed_usd


def test_conservative_buffer_inflates_each_stage_cost() -> None:
    forecast = forecast_whole_programme(
        benchmark=PADDED_BATCHED,
        stages=(StageDemand(stage="predictions", items=4000, essential=True),),
        r0_cost_usd=0.0,
        reserve_usd=0.0,
        safety_buffer=0.20,
    )

    # 4000 items / 4000 items-per-hour = 1.0 h; 1.0 h * $1.80 * 1.20 buffer = $2.16.
    assert forecast.stage_costs_usd["predictions"] == pytest.approx(2.16)


def test_overscoped_but_essential_affordable_programme_says_stop() -> None:
    forecast = forecast_whole_programme(
        benchmark=PADDED_BATCHED,
        stages=(
            StageDemand(stage="predictions", items=9124, essential=True),
            StageDemand(stage="R2", items=1_000_000, essential=False),
        ),
        r0_cost_usd=0.60,
        upload_cost_usd=0.10,
        reserve_usd=2.00,
    )

    assert forecast.decision == "stop"
    assert forecast.essential_floor_usd <= REMAINING_BUDGET_USD
    assert forecast.total_committed_usd > REMAINING_BUDGET_USD


def test_reserve_must_fit_inside_the_budget_for_a_go() -> None:
    # Without the reserve this plan would fit; the reserve pushes it over the cap,
    # so the forecast must refuse to say go.
    forecast = forecast_whole_programme(
        benchmark=PADDED_BATCHED,
        stages=(StageDemand(stage="predictions", items=9124, essential=True),),
        r0_cost_usd=0.60,
        upload_cost_usd=0.10,
        reserve_usd=100.0,
    )

    assert forecast.decision != "go"


def test_forecast_never_reports_go_when_the_total_exceeds_budget() -> None:
    for benchmark in (NAIVE_UNBATCHED, PADDED_BATCHED):
        forecast = forecast_whole_programme(
            benchmark=benchmark,
            stages=(StageDemand(stage="predictions", items=9124, essential=True),),
            r0_cost_usd=0.60,
            upload_cost_usd=0.10,
            reserve_usd=2.00,
        )
        if forecast.total_committed_usd > REMAINING_BUDGET_USD:
            assert forecast.decision != "go"
