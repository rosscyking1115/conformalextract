from __future__ import annotations

from conformalextract.simulation import run_gate0_simulations


def test_simulation_report_is_deterministic() -> None:
    first = run_gate0_simulations(replicates=20, seed=42)
    second = run_gate0_simulations(replicates=20, seed=42)
    assert first == second
    assert first["statistical_unit"] == "independent duplicate/source group"
