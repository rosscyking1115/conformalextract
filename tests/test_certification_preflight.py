from __future__ import annotations

import inspect

import pytest

from conformalextract.certification_preflight import (
    CertificationPreflightError,
    run_certification_preflight,
)
from conformalextract.contracts import PredictionRecord, SystemManifest


def _prediction(document_id: str) -> PredictionRecord:
    return PredictionRecord(
        prediction_id=f"p-{document_id}",
        document_id=document_id,
        system_id="qa",
        prompt_hash="hash",
        raw_output="{}",
        confidence=-0.1,
        status="valid",
    )


def _manifest(system_id: str, family: str, prompt_hash: str = "hash") -> SystemManifest:
    return SystemManifest(
        system_id=system_id,
        family=family,  # type: ignore[arg-type]
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        model_revision="rev",
        tokenizer_revision="rev",
        prompt_hash=prompt_hash,
        decoding={"temperature": 0.0},
    )


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    documents = [_prediction("d1"), _prediction("d2")]
    manifests = {
        "zs": _manifest("zs", "ZS"),
        "fs": _manifest("fs", "FS"),
        "qa": _manifest("qa", "QA"),
    }
    kwargs: dict[str, object] = {
        "predictions_by_system": {"zs": documents, "fs": documents, "qa": documents},
        "system_manifests": manifests,
        "frozen_system_manifests": manifests,
        "certification_group_ids": frozenset({"g1", "g2"}),
        "train_group_ids": frozenset({"g3"}),
        "development_group_ids": frozenset({"g4"}),
        "candidate_grid_hash": "abc123",
        "tie_order": ("mean", "tenth_percentile", "minimum"),
        "alpha": 0.20,
        "delta": 0.05,
        "acceptance_floor": 0.20,
        "synthetic_coverage_passed": True,
    }
    kwargs.update(overrides)
    return kwargs


def test_passes_when_every_precondition_holds() -> None:
    result = run_certification_preflight(**_valid_kwargs())  # type: ignore[arg-type]
    assert result.status == "ready"
    assert result.system_ids == ("fs", "qa", "zs")
    assert result.document_count == 2


def test_rejects_mismatched_document_sets_across_systems() -> None:
    documents = {"zs": [_prediction("d1")], "fs": [_prediction("d1")], "qa": [_prediction("d2")]}
    with pytest.raises(CertificationPreflightError, match="different document set"):
        run_certification_preflight(**_valid_kwargs(predictions_by_system=documents))  # type: ignore[arg-type]


def test_rejects_manifest_drift_from_the_frozen_reference() -> None:
    drifted = {
        "zs": _manifest("zs", "ZS"),
        "fs": _manifest("fs", "FS"),
        "qa": _manifest("qa", "QA", prompt_hash="different-hash"),
    }
    with pytest.raises(CertificationPreflightError, match="diverges from the frozen reference"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(system_manifests=drifted)
        )


def test_rejects_certification_group_overlap_with_train_or_development() -> None:
    with pytest.raises(CertificationPreflightError, match="overlap the train role"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(
                certification_group_ids=frozenset({"g1", "g3"}), train_group_ids=frozenset({"g3"})
            )
        )
    with pytest.raises(CertificationPreflightError, match="overlap the development role"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(
                certification_group_ids=frozenset({"g1", "g4"}),
                development_group_ids=frozenset({"g4"}),
            )
        )


def test_rejects_missing_grid_hash_or_degenerate_tie_order() -> None:
    with pytest.raises(CertificationPreflightError, match="candidate_grid_hash"):
        run_certification_preflight(**_valid_kwargs(candidate_grid_hash=""))  # type: ignore[arg-type]
    with pytest.raises(CertificationPreflightError, match="tie_order"):
        run_certification_preflight(**_valid_kwargs(tie_order=()))  # type: ignore[arg-type]
    with pytest.raises(CertificationPreflightError, match="tie_order"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(tie_order=("mean", "mean"))
        )


def test_rejects_alpha_delta_floor_drift_from_the_adr_0007_freeze() -> None:
    with pytest.raises(CertificationPreflightError, match="ADR 0007 freeze"):
        run_certification_preflight(**_valid_kwargs(alpha=0.10))  # type: ignore[arg-type]
    with pytest.raises(CertificationPreflightError, match="ADR 0007 freeze"):
        run_certification_preflight(**_valid_kwargs(delta=0.01))  # type: ignore[arg-type]
    with pytest.raises(CertificationPreflightError, match="ADR 0007 freeze"):
        run_certification_preflight(**_valid_kwargs(acceptance_floor=0.30))  # type: ignore[arg-type]


def test_rejects_when_synthetic_coverage_has_not_passed() -> None:
    with pytest.raises(CertificationPreflightError, match="synthetic certifier coverage"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(synthetic_coverage_passed=False)
        )


def test_final_and_shift_manifests_have_no_parameter_to_accept() -> None:
    """Structural proof of §3.2's last bullet: inaccessibility is not a runtime check that

    could be bypassed by passing a final/shift manifest in -- the function has no such
    parameter at all.
    """

    parameters = set(inspect.signature(run_certification_preflight).parameters)
    assert not any("final" in name or "shift" in name for name in parameters)


def test_rejects_empty_or_wrong_system_set() -> None:
    with pytest.raises(CertificationPreflightError, match="no systems supplied"):
        run_certification_preflight(**_valid_kwargs(predictions_by_system={}))  # type: ignore[arg-type]
    with pytest.raises(CertificationPreflightError, match="expected exactly zs/fs/qa"):
        run_certification_preflight(  # type: ignore[arg-type]
            **_valid_kwargs(
                predictions_by_system={"zs": [_prediction("d1")], "fs": [_prediction("d1")]}
            )
        )
