from __future__ import annotations

from conformalextract.certification import (
    certified_acceptance,
    compare_certified_acceptance,
)
from conformalextract.contracts import CertificationResult


def _decisions(qa: float | None, zs: float | None, fs: float | None, gain: float = 0.05):
    return compare_certified_acceptance(qa=qa, zs=zs, fs=fs, material_gain=gain)


def test_h1_supported_only_with_a_material_gain_over_zero_shot() -> None:
    h1, _ = _decisions(qa=0.60, zs=0.50, fs=0.50)
    assert h1.hypothesis == "H1"
    assert h1.comparison == "QA_vs_ZS"
    assert h1.outcome == "supported"


def test_h1_not_supported_when_gain_is_below_material_threshold() -> None:
    h1, _ = _decisions(qa=0.56, zs=0.55, fs=0.55)
    assert h1.outcome == "no_material_gain"


def test_qa_feasible_and_baseline_infeasible_is_a_boundary_crossing() -> None:
    h1, h2 = _decisions(qa=0.40, zs=None, fs=None)
    assert h1.outcome == "boundary_crossing"
    assert h2.outcome == "boundary_crossing"
    # No invented numerical difference from an infeasible baseline.
    assert h1.baseline_acceptance is None


def test_qa_infeasible_against_a_feasible_baseline_is_adaptation_harm() -> None:
    h1, _ = _decisions(qa=None, zs=0.50, fs=0.40)
    assert h1.outcome == "qa_infeasible"
    assert h1.qa_acceptance is None


def test_all_systems_infeasible_reports_both_infeasible() -> None:
    h1, h2 = _decisions(qa=None, zs=None, fs=None)
    assert h1.outcome == "both_infeasible"
    assert h2.outcome == "both_infeasible"


def test_h2_applies_the_same_rule_against_few_shot() -> None:
    _, h2 = _decisions(qa=0.60, zs=0.40, fs=0.58)
    assert h2.hypothesis == "H2"
    assert h2.comparison == "QA_vs_FS"
    # QA over FS is only 0.02 -> not material even though H1 (vs ZS) is supported.
    assert h2.outcome == "no_material_gain"


def test_certified_acceptance_extracts_only_from_feasible_results() -> None:
    feasible = CertificationResult(
        method="scorc-joint-finite-grid",
        status="certified",
        feasible=True,
        n_total=2000,
        n_accepted=1200,
        risk_upper=0.2,
        acceptance_lower=0.55,
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
    )
    infeasible = feasible.model_copy(
        update={"status": "infeasible", "feasible": False, "acceptance_lower": 0.0}
    )
    assert certified_acceptance(feasible) == 0.55
    assert certified_acceptance(infeasible) is None
