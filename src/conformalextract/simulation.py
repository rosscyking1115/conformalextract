"""Deterministic grouped Monte Carlo checks for certificate implementations."""

from __future__ import annotations

from typing import Literal, TypedDict

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


RegimeName = Literal["easy_nonmonotone", "boundary", "unsafe", "low_acceptance"]


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


def simulate_nine_candidate_grid(
    *,
    regime: RegimeName,
    replicates: int,
    seed: int,
) -> RegimeResult:
    """Exercise adaptive selection across the complete nine-candidate global family."""

    candidate_count = 9
    n = scorc_minimum_n(candidate_count=candidate_count, delta=0.05, acceptance_floor=0.2)
    generator = np.random.default_rng(np.random.SeedSequence(seed))
    if regime == "low_acceptance":
        thresholds = np.linspace(0.81, 0.97, candidate_count)
    else:
        thresholds = np.linspace(0.0, 0.8, candidate_count)
    integration_scores = np.linspace(0.0, 1.0, 200_001)

    def probabilities(scores: np.ndarray) -> np.ndarray:
        if regime == "easy_nonmonotone":
            return 0.05 + 0.25 * np.exp(-(((scores - 0.5) / 0.08) ** 2))
        if regime == "boundary":
            return np.full_like(scores, 0.205)
        if regime == "unsafe":
            return np.full_like(scores, 0.24)
        return np.full_like(scores, 0.05)

    integration_probabilities = probabilities(integration_scores)
    true_acceptances = 1.0 - thresholds
    true_risks = np.asarray(
        [
            float(np.mean(integration_probabilities[integration_scores >= threshold]))
            for threshold in thresholds
        ]
    )
    certified = 0
    violations = 0
    for _ in range(replicates):
        scores = generator.random(n)
        accepted = scores[:, None] >= thresholds[None, :]
        document_losses = (generator.random(n) < probabilities(scores)).astype(np.float64)
        losses = np.repeat(document_losses[:, None], candidate_count, axis=1)
        result = scorc_certificate(
            losses=losses.tolist(),
            accepted=accepted.tolist(),
            candidate_ids=[f"candidate-{index}" for index in range(candidate_count)],
            alpha=0.2,
            acceptance_floor=0.2,
            delta=0.05,
        )
        if result.feasible:
            certified += 1
            assert result.selected_candidate is not None
            selected = int(result.selected_candidate.rsplit("-", maxsplit=1)[1])
            if true_risks[selected] > 0.2 or true_acceptances[selected] < 0.2:
                violations += 1
    return {
        "true_risk": float(np.max(true_risks)),
        "true_acceptance": float(np.min(true_acceptances)),
        "certified_runs": certified,
        "violations": violations,
        "violation_rate": violations / replicates,
        "violation_upper_99": _binomial_upper_99(violations, replicates),
    }


def run_gate0_simulations_v2(*, replicates: int = 2000, seed: int = 20260715) -> dict[str, object]:
    """Nine-candidate adaptive, boundary, non-monotone, and low-acceptance validation."""

    names: tuple[RegimeName, ...] = (
        "easy_nonmonotone",
        "boundary",
        "unsafe",
        "low_acceptance",
    )
    regimes = {
        name: simulate_nine_candidate_grid(regime=name, replicates=replicates, seed=seed + index)
        for index, name in enumerate(names)
    }
    coverage_pass = all(regime["violation_upper_99"] <= 0.07 for regime in regimes.values())
    return {
        "schema_version": "2",
        "replicates": replicates,
        "seed": seed,
        "candidate_count": 9,
        "adaptive_post_selection": True,
        "statistical_unit": "independent duplicate/source group",
        "delta": 0.05,
        "one_sided_99_tolerance": 0.02,
        "regimes": regimes,
        "coverage_pass": coverage_pass,
    }
