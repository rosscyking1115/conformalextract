"""Empirical coverage validation for the SCoRC certifier (gate G1d).

Mirrors the frontier validation practice (arXiv 2606.08517 / 2606.29054): over many
resplits of a synthetic data-generating process with KNOWN population selected risk,
the certified selector's chosen policy must almost never have true selected risk above
alpha, and a negative control shows that a naive accept-all (max-acceptance) policy —
which the certificate refuses — genuinely violates alpha.
"""

from __future__ import annotations

import math

import numpy as np

from conformalextract.certification import scorc_certificate, scorc_minimum_n

# Population: score X ~ U(0,1); document loss is Bernoulli with a step hazard that is
# high below 0.3 and low above. A threshold tau accepts documents with X >= tau.
THRESHOLDS = (0.0, 0.1, 0.2, 0.3, 0.5)
IDS = [f"tau={t}" for t in THRESHOLDS]
ALPHA = 0.20
FLOOR = 0.20
DELTA = 0.05
HIGH, LOW, CUT = 0.9, 0.05, 0.3


def _true_selected_risk(tau: float) -> float:
    """Closed-form population selected risk E[loss | X >= tau]."""

    if tau >= CUT:
        return LOW
    frac_high = (CUT - tau) / (1.0 - tau)
    return frac_high * HIGH + (1.0 - frac_high) * LOW


def _sample(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    x = rng.uniform(0.0, 1.0, size=n)
    hazard = np.where(x < CUT, HIGH, LOW)
    loss = (rng.uniform(0.0, 1.0, size=n) < hazard).astype(float)
    accepted = np.stack([x >= t for t in THRESHOLDS], axis=1)
    losses = np.repeat(loss[:, None], len(THRESHOLDS), axis=1)
    return losses, accepted


def test_scorc_controls_risk_and_refuses_the_risk_violating_naive_policy() -> None:
    n = scorc_minimum_n(candidate_count=len(THRESHOLDS), delta=DELTA, acceptance_floor=FLOOR)
    trials = 80
    certified = 0
    coverage_violations = 0
    naive_selected_by_certifier = 0

    for seed in range(trials):
        rng = np.random.default_rng(seed)
        losses, accepted = _sample(rng, n)
        result = scorc_certificate(
            losses=losses.tolist(),
            accepted=accepted.tolist(),
            candidate_ids=IDS,
            alpha=ALPHA,
            acceptance_floor=FLOOR,
            delta=DELTA,
        )
        if result.status != "certified":
            continue
        certified += 1
        tau = THRESHOLDS[IDS.index(result.selected_candidate)]  # type: ignore[arg-type]
        if _true_selected_risk(tau) > ALPHA + 1e-9:
            coverage_violations += 1
        if result.selected_candidate == "tau=0.0":
            naive_selected_by_certifier += 1

    # The certifier must actually certify in this easy regime.
    assert certified > 0
    # Coverage: certified selections violate the risk target at most at rate delta.
    assert coverage_violations <= math.ceil(DELTA * trials)
    # Negative control: the naive accept-all policy genuinely violates alpha...
    assert _true_selected_risk(0.0) > ALPHA
    # ...and the certificate never selects it.
    assert naive_selected_by_certifier == 0


def test_scorc_never_reports_zero_risk_for_zero_acceptance() -> None:
    # A threshold that accepts nothing must be ineligible, never a zero-risk certificate.
    n = scorc_minimum_n(candidate_count=2, delta=DELTA, acceptance_floor=FLOOR)
    accepted = np.zeros((n, 2), dtype=bool)
    accepted[:, 0] = True  # first candidate accepts all; second accepts none
    losses = np.zeros((n, 2))
    result = scorc_certificate(
        losses=losses.tolist(),
        accepted=accepted.tolist(),
        candidate_ids=["accept-all", "accept-none"],
        alpha=ALPHA,
        acceptance_floor=FLOOR,
        delta=DELTA,
    )
    # The all-accept zero-loss candidate certifies; the accept-none one never wins.
    assert result.selected_candidate == "accept-all"
