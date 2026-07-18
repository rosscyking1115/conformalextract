from __future__ import annotations

import pytest

from conformalextract.certification import (
    base_risk_feasibility,
    max_feasible_acceptance,
    minimum_abstention,
)


def test_no_forced_abstention_when_base_risk_within_target() -> None:
    assert minimum_abstention(base_risk=0.15, alpha=0.20) == 0.0
    assert max_feasible_acceptance(base_risk=0.15, alpha=0.20) == 1.0


def test_impossibility_bound_matches_the_closed_form() -> None:
    # (mu - alpha) / (1 - alpha); mu=0.50, alpha=0.20 -> 0.30/0.80 = 0.375.
    assert minimum_abstention(base_risk=0.50, alpha=0.20) == pytest.approx(0.375)
    assert max_feasible_acceptance(base_risk=0.50, alpha=0.20) == pytest.approx(0.625)
    # mu=0.55, alpha=0.20 -> 0.35/0.80 = 0.4375.
    assert minimum_abstention(base_risk=0.55, alpha=0.20) == pytest.approx(0.4375)


def test_bounds_reject_out_of_range_inputs() -> None:
    with pytest.raises(ValueError):
        minimum_abstention(base_risk=1.2, alpha=0.20)
    with pytest.raises(ValueError):
        minimum_abstention(base_risk=0.5, alpha=0.0)
    with pytest.raises(ValueError):
        minimum_abstention(base_risk=0.5, alpha=1.0)


def test_feasibility_report_uses_conservative_upper_base_risk() -> None:
    # Always-answer document losses; empirical mean = 0.5.
    losses = [0.0, 1.0] * 50  # 100 docs, mean 0.5
    report = base_risk_feasibility(
        losses, alpha=0.20, acceptance_floor=0.20, failure_probability=0.05
    )

    assert report.base_risk == pytest.approx(0.5)
    # The conservative (upper) base risk exceeds the point estimate.
    assert report.base_risk_upper > report.base_risk
    # Forced abstention is computed from the conservative upper base risk.
    assert report.minimum_abstention == pytest.approx(
        minimum_abstention(base_risk=report.base_risk_upper, alpha=0.20)
    )
    assert report.max_feasible_acceptance == pytest.approx(1.0 - report.minimum_abstention)
    # 0.5 base risk still leaves head-room above a 0.20 floor.
    assert report.floor_reachable is True
    assert report.verdict in {"answerable", "marginal"}


def test_feasibility_report_flags_a_near_vacuous_target() -> None:
    # Base risk ~0.9 with a 0.5 floor: forced abstention is so large that no
    # policy can meet the floor, so the certificate is near-vacuous at this alpha.
    losses = [1.0] * 90 + [0.0] * 10  # mean 0.9
    report = base_risk_feasibility(
        losses, alpha=0.20, acceptance_floor=0.50, failure_probability=0.05
    )

    assert report.floor_reachable is False
    assert report.verdict == "near_vacuous"


def test_feasibility_report_requires_bounded_losses() -> None:
    with pytest.raises(ValueError):
        base_risk_feasibility([0.0, 1.5], alpha=0.2, acceptance_floor=0.2)
    with pytest.raises(ValueError):
        base_risk_feasibility([], alpha=0.2, acceptance_floor=0.2)
