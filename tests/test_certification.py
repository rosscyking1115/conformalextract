from __future__ import annotations

import pytest

from conformalextract.certification import conservative_certificate


def test_conservative_certificate_returns_feasible_candidate() -> None:
    losses = [0.0] * 100
    accepted = [True] * 100
    result = conservative_certificate(
        losses=losses,
        accepted=accepted,
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
        family_size=1,
        min_accepted=10,
    )
    assert result.feasible
    assert result.risk_upper <= 0.2
    assert result.acceptance_lower >= 0.2


def test_conservative_certificate_is_explicitly_infeasible() -> None:
    result = conservative_certificate(
        losses=[1.0] * 20,
        accepted=[True] * 20,
        alpha=0.2,
        acceptance_floor=0.2,
        delta=0.05,
        family_size=3,
        min_accepted=10,
    )
    assert not result.feasible
    assert "risk" in result.reasons


def test_certificate_refuses_unbounded_losses() -> None:
    with pytest.raises(ValueError, match="bounded"):
        conservative_certificate(
            losses=[1.1],
            accepted=[True],
            alpha=0.2,
            acceptance_floor=0.2,
            delta=0.05,
            family_size=1,
            min_accepted=1,
        )
