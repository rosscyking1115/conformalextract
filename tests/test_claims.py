from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from conformalextract.claims import (
    Claim,
    ClaimLedger,
    ClaimStatus,
    load_ledger,
    render_surface,
    unresolved_evidence,
    verify_ledger,
)

ROOT = Path(__file__).parents[1]
LEDGER = ROOT / "evidence" / "plan4" / "claim_ledger.json"


def _claim(**overrides: object) -> Claim:
    fields: dict[str, object] = {
        "claim_id": "CX-TEST-01",
        "wording": "A statement supported by its evidence.",
        "status": ClaimStatus.VERIFIED,
        "scope": "in-domain",
        "evidence": ("README.md",),
        "method": "a frozen procedure",
        "limitations": ("scoped to the frozen stack",),
        "surfaces": ("report",),
        "verified_by": "reviewer 2026-07-22",
    }
    fields.update(overrides)
    return Claim(**fields)  # type: ignore[arg-type]


# --- enforcement rules ---------------------------------------------------------------


def test_planned_and_failed_claims_cannot_reach_a_public_surface() -> None:
    """§3.4: `planned` is never written as achieved; failed evidence is not a result."""
    for status in (ClaimStatus.PLANNED, ClaimStatus.FAILED):
        with pytest.raises(ValidationError, match="may not appear on a public surface"):
            _claim(status=status)
        # ...but the same claim is fine with no surfaces.
        assert _claim(status=status, surfaces=()).status is status


def test_public_claims_must_carry_their_limitations() -> None:
    with pytest.raises(ValidationError, match="must carry the limitations"):
        _claim(limitations=())
    assert _claim(limitations=(), surfaces=()).surfaces == ()


@pytest.mark.parametrize(
    "wording",
    [
        "Our system achieves state-of-the-art extraction.",
        "This peer-reviewed result shows the effect.",
        "The adapter reaches 95.7% correct on RAMS.",
        "We report grounding accuracy of 96%.",
        "The results show QLoRA doesn't work for extraction.",
        "A laxer alpha would certify the adapted system.",
        "QLoRA delivers a certified margin over zero-shot.",
        "The pipeline is production-grade.",
    ],
)
def test_forbidden_wordings_are_rejected(wording: str) -> None:
    """The reviewer's boundaries, enforced as code so inattention cannot publish them."""
    with pytest.raises(ValidationError, match="forbidden wording"):
        _claim(wording=wording)


def test_unknown_surface_and_malformed_id_are_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown surfaces"):
        _claim(surfaces=("billboard",))
    with pytest.raises(ValidationError, match="claim_id must look like"):
        _claim(claim_id="h1-primary")


def test_duplicate_claim_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate claim ids"):
        ClaimLedger(ledger_id="l", analysis_id="a", claims=(_claim(), _claim()))


def test_evidence_must_resolve_on_disk() -> None:
    ledger = ClaimLedger(
        ledger_id="l",
        analysis_id="a",
        claims=(_claim(evidence=("docs/does-not-exist.md",)),),
    )
    missing = unresolved_evidence(ledger, root=ROOT)
    assert missing == {"CX-TEST-01": ["docs/does-not-exist.md"]}
    assert verify_ledger(ledger, root=ROOT)["ok"] is False


def test_evidence_anchors_resolve_to_the_underlying_file() -> None:
    ledger = ClaimLedger(
        ledger_id="l", analysis_id="a", claims=(_claim(evidence=("README.md#section",)),)
    )
    assert unresolved_evidence(ledger, root=ROOT) == {}


# --- the real ledger -----------------------------------------------------------------


def test_committed_ledger_is_valid_and_fully_evidenced() -> None:
    report = verify_ledger(load_ledger(LEDGER), root=ROOT)
    assert report["ok"] is True, report["unresolved_evidence"]
    assert report["claims"] >= 10


def test_the_null_is_recorded_and_reaches_the_abstract() -> None:
    """§8.2: a null that is the principal result belongs in the abstract."""
    ledger = load_ledger(LEDGER)
    h1 = next(c for c in ledger.claims if c.claim_id == "CX-H1-PRIMARY")
    assert h1.status is ClaimStatus.INFEASIBLE
    assert "abstract" in h1.surfaces


def test_the_grounding_win_never_travels_without_the_null() -> None:
    """The reviewer's central boundary: 95.7% must not be quotable on its own."""
    ledger = load_ledger(LEDGER)
    grounding = next(c for c in ledger.claims if c.claim_id == "CX-GROUNDING-01")
    joined = " ".join(grounding.limitations)
    assert "NOT correct" in joined
    assert "did NOT translate into a certified selective guarantee" in joined
    # It must not be quotable in isolation on a CV, slide or abstract.
    for surface in ("CV", "slide", "abstract"):
        assert surface not in grounding.surfaces


def test_unrun_work_is_never_publishable() -> None:
    ledger = load_ledger(LEDGER)
    for claim_id in ("CX-SHIFT-01", "CX-REPRO-CPU-01"):
        claim = next(c for c in ledger.claims if c.claim_id == claim_id)
        assert claim.status is ClaimStatus.PLANNED
        assert claim.surfaces == ()


def test_render_surface_emits_approved_wording_with_limitations() -> None:
    rendered = render_surface(load_ledger(LEDGER), "README")
    assert "[CX-H1-PRIMARY]" in rendered
    assert "_Limitation:_" in rendered
