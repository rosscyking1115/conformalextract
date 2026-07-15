"""Conservative bounded-loss and acceptance certificate primitives."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import beta

from conformalextract.contracts import CertificationResult


def hoeffding_upper(losses: Sequence[float], failure_probability: float) -> float:
    """One-sided Hoeffding upper confidence bound for bounded losses."""

    if not losses:
        return 1.0
    mean = sum(losses) / len(losses)
    radius = math.sqrt(math.log(2.0 / failure_probability) / (2.0 * len(losses)))
    return min(1.0, mean + radius)


def scorc_minimum_n(*, candidate_count: int, delta: float, acceptance_floor: float) -> int:
    """Exact document-count precondition from the preferred joint finite-grid theorem."""

    if candidate_count < 1:
        raise ValueError("candidate_count must be positive")
    if not 0.0 < delta < 1.0 or not 0.0 < acceptance_floor <= 1.0:
        raise ValueError("delta and acceptance_floor must be probabilities")
    return math.ceil(32.0 * math.log(32.0 * candidate_count / delta) / acceptance_floor)


def largest_scorc_grid(
    *, independent_documents: int, delta: float, acceptance_floor: float, cap: int = 101
) -> int:
    """Largest theorem-eligible grid; zero means the preferred method is unavailable."""

    if independent_documents < 0 or cap < 1:
        raise ValueError("document count must be non-negative and cap positive")
    for candidate_count in range(cap, 0, -1):
        if independent_documents >= scorc_minimum_n(
            candidate_count=candidate_count,
            delta=delta,
            acceptance_floor=acceptance_floor,
        ):
            return candidate_count
    return 0


def clopper_pearson_lower(successes: int, trials: int, failure_probability: float) -> float:
    """One-sided exact lower confidence bound for a binomial proportion."""

    if trials <= 0 or successes <= 0:
        return 0.0
    if successes > trials:
        raise ValueError("successes cannot exceed trials")
    return float(beta.ppf(failure_probability, successes, trials - successes + 1))


def conservative_certificate(
    *,
    losses: Sequence[float],
    accepted: Sequence[bool],
    alpha: float,
    acceptance_floor: float,
    delta: float,
    family_size: int,
    min_accepted: int,
) -> CertificationResult:
    """Bonferroni-corrected Hoeffding/Clopper-Pearson audit for one candidate."""

    if len(losses) != len(accepted):
        raise ValueError("losses and accepted must be aligned")
    if any(loss < 0.0 or loss > 1.0 for loss in losses):
        raise ValueError("losses must be bounded in [0, 1]")
    if family_size < 1:
        raise ValueError("family_size must be positive")
    if not 0.0 < delta < 1.0:
        raise ValueError("delta must lie in (0, 1)")

    accepted_losses = [
        loss for loss, is_accepted in zip(losses, accepted, strict=True) if is_accepted
    ]
    n_total = len(losses)
    n_accepted = len(accepted_losses)
    per_bound_delta = delta / (2 * family_size)
    risk_upper = hoeffding_upper(accepted_losses, per_bound_delta)
    acceptance_lower = clopper_pearson_lower(n_accepted, n_total, per_bound_delta)
    empirical_risk = sum(accepted_losses) / n_accepted if n_accepted else None

    reasons: list[str] = []
    if n_accepted < min_accepted:
        reasons.append("accepted_count")
    if risk_upper > alpha:
        reasons.append("risk")
    if acceptance_lower < acceptance_floor:
        reasons.append("acceptance")
    return CertificationResult(
        method="hoeffding-clopper-pearson-bonferroni",
        status="certified" if not reasons else "infeasible",
        feasible=not reasons,
        n_total=n_total,
        n_accepted=n_accepted,
        empirical_risk=empirical_risk,
        risk_upper=risk_upper,
        acceptance_lower=acceptance_lower,
        alpha=alpha,
        acceptance_floor=acceptance_floor,
        delta=delta,
        reasons=reasons,
    )


def scorc_certificate(
    *,
    losses: Sequence[Sequence[float]],
    accepted: Sequence[Sequence[bool]],
    candidate_ids: Sequence[str],
    alpha: float,
    acceptance_floor: float,
    delta: float,
) -> CertificationResult:
    """Preferred simultaneous finite-grid SCoRC certificate.

    Rows are independent source-document groups and columns are frozen development candidates.
    Selection maximizes the lower confidence bound on acceptance, with frozen column order as the
    only tie break.
    """

    loss_array = np.asarray(losses, dtype=np.float64)
    accepted_array = np.asarray(accepted, dtype=np.bool_)
    if loss_array.ndim != 2 or accepted_array.shape != loss_array.shape:
        raise ValueError("losses and accepted must be aligned two-dimensional arrays")
    n, candidate_count = loss_array.shape
    if candidate_count != len(candidate_ids) or len(set(candidate_ids)) != candidate_count:
        raise ValueError("candidate IDs must be unique and aligned")
    if n < 2 or candidate_count < 1:
        raise ValueError("SCoRC requires at least two rows and one candidate")
    if np.any((loss_array < 0.0) | (loss_array > 1.0)):
        raise ValueError("losses must be bounded in [0, 1]")

    minimum_n = scorc_minimum_n(
        candidate_count=candidate_count,
        delta=delta,
        acceptance_floor=acceptance_floor,
    )
    if n < minimum_n:
        return CertificationResult(
            method="scorc-joint-finite-grid",
            status="insufficient_n",
            feasible=False,
            n_total=n,
            n_accepted=0,
            empirical_risk=None,
            risk_upper=1.0,
            acceptance_lower=0.0,
            alpha=alpha,
            acceptance_floor=acceptance_floor,
            delta=delta,
            reasons=["theorem_sample_precondition"],
            candidate_count=candidate_count,
            theorem_minimum_n=minimum_n,
        )

    z = accepted_array * (loss_array - alpha)
    z_variance = np.var(z, axis=0, ddof=1)
    risk_log = math.log(64.0 * candidate_count / delta)
    eb = (
        np.mean(z, axis=0)
        + np.sqrt(2.0 * z_variance * risk_log / n)
        + 7.0 * risk_log / (3.0 * (n - 1))
    )
    accepted_counts = np.sum(accepted_array, axis=0)
    acceptance_lower = np.asarray(
        [
            0.0 if count == 0 else beta.ppf(delta / (16.0 * candidate_count), count, n - count + 1)
            for count in accepted_counts
        ],
        dtype=np.float64,
    )
    utility = accepted_array.astype(np.float64)
    utility_variance = np.var(utility, axis=0, ddof=1)
    utility_log = math.log(8.0 * candidate_count / delta)
    utility_lower = (
        np.mean(utility, axis=0)
        - np.sqrt(2.0 * utility_variance * utility_log / n)
        - 7.0 * utility_log / (3.0 * (n - 1))
    )
    feasible_indices = [
        index
        for index in range(candidate_count)
        if eb[index] <= 0.0 and acceptance_lower[index] >= acceptance_floor
    ]
    if not feasible_indices:
        return CertificationResult(
            method="scorc-joint-finite-grid",
            status="infeasible",
            feasible=False,
            n_total=n,
            n_accepted=0,
            empirical_risk=None,
            risk_upper=1.0,
            acceptance_lower=float(np.max(acceptance_lower)),
            alpha=alpha,
            acceptance_floor=acceptance_floor,
            delta=delta,
            reasons=["no_jointly_feasible_candidate"],
            candidate_count=candidate_count,
            theorem_minimum_n=minimum_n,
        )

    selected = max(feasible_indices, key=lambda index: (utility_lower[index], -index))
    selected_losses = loss_array[accepted_array[:, selected], selected]
    empirical_risk = float(np.mean(selected_losses))
    conditional_upper = min(1.0, max(0.0, alpha + float(eb[selected]) / acceptance_lower[selected]))
    return CertificationResult(
        method="scorc-joint-finite-grid",
        status="certified",
        feasible=True,
        n_total=n,
        n_accepted=int(accepted_counts[selected]),
        empirical_risk=empirical_risk,
        risk_upper=conditional_upper,
        acceptance_lower=float(acceptance_lower[selected]),
        alpha=alpha,
        acceptance_floor=acceptance_floor,
        delta=delta,
        selected_candidate=candidate_ids[selected],
        candidate_count=candidate_count,
        theorem_minimum_n=minimum_n,
    )
