"""Deterministic grouped Monte Carlo checks for certificate implementations."""

from __future__ import annotations

from typing import TypedDict

import numpy as np
from scipy.stats import beta

from conformalextract.certification import scorc_certificate, scorc_minimum_n


class RegimeResult(TypedDict):
    true_risk: float
    true_acceptance: float
    certified_runs: int
    violations: int
    violation_rate: float
    violation_upper_99: float


def _binomial_upper_99(violations: int, replicates: int) -> float:
    if violations == replicates:
        return 1.0
    return float(beta.ppf(0.99, violations + 1, replicates - violations))


def simulate_scorc_regime(
    *,
    true_risk: float,
    true_acceptance: float,
    replicates: int,
    seed: int,
    alpha: float = 0.2,
    acceptance_floor: float = 0.2,
    delta: float = 0.05,
) -> RegimeResult:
    """Simulate one fixed SCoRC candidate using one independent row per document group."""

    if replicates < 1:
        raise ValueError("replicates must be positive")
    n = scorc_minimum_n(candidate_count=1, delta=delta, acceptance_floor=acceptance_floor)
    generator = np.random.default_rng(np.random.SeedSequence(seed))
    certified = 0
    violations = 0
    for _ in range(replicates):
        accepted = generator.random(n) < true_acceptance
        losses = (generator.random(n) < true_risk).astype(np.float64)
        result = scorc_certificate(
            losses=losses[:, None].tolist(),
            accepted=accepted[:, None].tolist(),
            candidate_ids=["fixed"],
            alpha=alpha,
            acceptance_floor=acceptance_floor,
            delta=delta,
        )
        if result.feasible:
            certified += 1
            if true_risk > alpha or true_acceptance < acceptance_floor:
                violations += 1
    return {
        "true_risk": true_risk,
        "true_acceptance": true_acceptance,
        "certified_runs": certified,
        "violations": violations,
        "violation_rate": violations / replicates,
        "violation_upper_99": _binomial_upper_99(violations, replicates),
    }


def run_gate0_simulations(*, replicates: int = 2000, seed: int = 42) -> dict[str, object]:
    """Run easy, unsafe-risk, and low-acceptance regimes with a frozen seed sequence."""

    regimes = {
        "easy": simulate_scorc_regime(
            true_risk=0.05,
            true_acceptance=0.8,
            replicates=replicates,
            seed=seed,
        ),
        "unsafe_risk": simulate_scorc_regime(
            true_risk=0.22,
            true_acceptance=0.8,
            replicates=replicates,
            seed=seed + 1,
        ),
        "low_acceptance": simulate_scorc_regime(
            true_risk=0.05,
            true_acceptance=0.18,
            replicates=replicates,
            seed=seed + 2,
        ),
    }
    tolerance = 0.02
    coverage_pass = all(
        regime["violation_upper_99"] <= 0.05 + tolerance for regime in regimes.values()
    )
    return {
        "schema_version": "1",
        "replicates": replicates,
        "seed": seed,
        "statistical_unit": "independent duplicate/source group",
        "delta": 0.05,
        "tolerance": tolerance,
        "regimes": regimes,
        "coverage_pass": coverage_pass,
    }
