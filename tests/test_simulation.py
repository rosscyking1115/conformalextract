from __future__ import annotations

from conformalextract.simulation import run_gate0_simulations, run_gate0_simulations_v2


def test_simulation_report_is_deterministic() -> None:
    first = run_gate0_simulations(replicates=20, seed=42)
    second = run_gate0_simulations(replicates=20, seed=42)
    assert first == second
    assert first["statistical_unit"] == "independent duplicate/source group"


def test_nine_candidate_simulation_report_is_deterministic() -> None:
    first = run_gate0_simulations_v2(replicates=5, seed=20260715)
    second = run_gate0_simulations_v2(replicates=5, seed=20260715)
    assert first == second
    assert first["candidate_count"] == 9
    assert first["adaptive_post_selection"] is True
