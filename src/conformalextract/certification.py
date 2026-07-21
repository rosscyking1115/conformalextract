"""Conservative bounded-loss and acceptance certificate primitives."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from scipy.stats import beta

from conformalextract.contracts import CertificationResult

# Gate 0 freeze (ADR 0007), exercised against real development-split evidence before any
# certification/final/shift label is read. Changing any of these after certification labels
# open requires an independent review, per the general evaluation-change rule.
FROZEN_ALPHA: Final[float] = 0.20
FROZEN_DELTA: Final[float] = 0.05
FROZEN_ACCEPTANCE_FLOOR: Final[float] = 0.20
FROZEN_MATERIAL_GAIN: Final[float] = 0.05
FROZEN_BOOTSTRAP_REPLICATES: Final[int] = 2000
FROZEN_CONFIDENCE_CANDIDATE: Final[str] = "minimum"


def hoeffding_upper(losses: Sequence[float], failure_probability: float) -> float:
    """One-sided Hoeffding upper confidence bound for bounded losses."""

    if not losses:
        return 1.0
    mean = sum(losses) / len(losses)
    radius = math.sqrt(math.log(2.0 / failure_probability) / (2.0 * len(losses)))
    return min(1.0, mean + radius)


def minimum_abstention(*, base_risk: float, alpha: float) -> float:
    """Population lower bound on forced abstention when base risk exceeds the target.

    From the always-answer decomposition (plan section 6.1; arXiv 2606.29054): when
    ``base_risk > alpha`` any valid selective policy must abstain on at least
    ``(base_risk - alpha) / (1 - alpha)`` of documents. Zero otherwise.
    """

    if not 0.0 <= base_risk <= 1.0:
        raise ValueError("base_risk must lie in [0, 1]")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    if base_risk <= alpha:
        return 0.0
    return (base_risk - alpha) / (1.0 - alpha)


def max_feasible_acceptance(*, base_risk: float, alpha: float) -> float:
    """Population upper bound on any valid policy's acceptance at this base risk."""

    return 1.0 - minimum_abstention(base_risk=base_risk, alpha=alpha)


@dataclass(frozen=True)
class BaseRiskFeasibility:
    """A pre-certification, GPU-free feasibility read on one system at one target."""

    base_risk: float
    base_risk_upper: float
    alpha: float
    acceptance_floor: float
    minimum_abstention: float
    max_feasible_acceptance: float
    floor_reachable: bool
    verdict: str


def base_risk_feasibility(
    losses: Sequence[float],
    *,
    alpha: float,
    acceptance_floor: float,
    failure_probability: float = 0.05,
) -> BaseRiskFeasibility:
    """Decide whether a target is even answerable before any paid run (plan section 6.1).

    ``losses`` are the always-answer bounded document losses on development data. The
    forced-abstention floor is computed from a conservative one-sided Hoeffding upper
    bound on the base risk, so the verdict does not understate infeasibility.
    """

    if not losses:
        raise ValueError("losses must be non-empty")
    if any(loss < 0.0 or loss > 1.0 for loss in losses):
        raise ValueError("losses must be bounded in [0, 1]")

    point = sum(losses) / len(losses)
    upper = hoeffding_upper(losses, failure_probability)
    min_abstention = minimum_abstention(base_risk=upper, alpha=alpha)
    max_acceptance = 1.0 - min_abstention
    floor_reachable = max_acceptance >= acceptance_floor
    if not floor_reachable:
        verdict = "near_vacuous"
    elif upper > alpha:
        verdict = "marginal"
    else:
        verdict = "answerable"
    return BaseRiskFeasibility(
        base_risk=point,
        base_risk_upper=upper,
        alpha=alpha,
        acceptance_floor=acceptance_floor,
        minimum_abstention=min_abstention,
        max_feasible_acceptance=max_acceptance,
        floor_reachable=floor_reachable,
        verdict=verdict,
    )


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


@dataclass(frozen=True)
class HypothesisDecision:
    """One preregistered certified-acceptance comparison (plan section 8)."""

    hypothesis: str
    comparison: str
    qa_acceptance: float | None
    baseline_acceptance: float | None
    material_gain: float
    outcome: str
    detail: str


def certified_acceptance(result: CertificationResult) -> float | None:
    """The system's certified acceptance `CA_s` (acceptance LCB), or None if infeasible."""

    return result.acceptance_lower if result.feasible else None


def _decide_hypothesis(
    hypothesis: str,
    comparison: str,
    qa: float | None,
    baseline: float | None,
    material_gain: float,
) -> HypothesisDecision:
    if qa is None and baseline is None:
        outcome = "both_infeasible"
        detail = "neither QA nor the baseline is certified feasible"
    elif qa is None:
        outcome = "qa_infeasible"
        detail = "QA infeasible while the baseline is feasible (adaptation harmed certifiability)"
    elif baseline is None:
        outcome = "boundary_crossing"
        detail = "QA feasible where the baseline is infeasible; no numerical difference invented"
    elif qa - baseline >= material_gain:
        outcome = "supported"
        detail = f"CA_QA {qa:.4f} >= CA_baseline {baseline:.4f} + {material_gain:.4f}"
    else:
        outcome = "no_material_gain"
        detail = f"CA_QA {qa:.4f} - CA_baseline {baseline:.4f} < {material_gain:.4f}"
    return HypothesisDecision(
        hypothesis=hypothesis,
        comparison=comparison,
        qa_acceptance=qa,
        baseline_acceptance=baseline,
        material_gain=material_gain,
        outcome=outcome,
        detail=detail,
    )


def compare_certified_acceptance(
    *,
    qa: float | None,
    zs: float | None,
    fs: float | None,
    material_gain: float = 0.05,
) -> tuple[HypothesisDecision, HypothesisDecision]:
    """Decide H1 (QA vs zero-shot) and H2 (QA vs few-shot) on certified acceptance.

    Certified acceptance ``CA_s`` is each system's certified acceptance lower bound, or
    None when the system is infeasible. The comparison never invents a numerical
    difference against an infeasible baseline (plan section 8.2); a feasible QA over an
    infeasible baseline is a boundary crossing, and an infeasible QA against a feasible
    baseline is recorded as adaptation harm rather than a hidden failure.
    """

    if material_gain < 0.0:
        raise ValueError("material_gain must be non-negative")
    h1 = _decide_hypothesis("H1", "QA_vs_ZS", qa, zs, material_gain)
    h2 = _decide_hypothesis("H2", "QA_vs_FS", qa, fs, material_gain)
    return h1, h2
