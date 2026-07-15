"""Conservative bounded-loss and acceptance certificate primitives."""

from __future__ import annotations

import math
from collections.abc import Sequence

from scipy.stats import beta

from conformalextract.contracts import CertificationResult


def hoeffding_upper(losses: Sequence[float], failure_probability: float) -> float:
    """One-sided Hoeffding upper confidence bound for bounded losses."""

    if not losses:
        return 1.0
    mean = sum(losses) / len(losses)
    radius = math.sqrt(math.log(1.0 / failure_probability) / (2.0 * len(losses)))
    return min(1.0, mean + radius)


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
