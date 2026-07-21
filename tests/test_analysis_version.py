from __future__ import annotations

import pytest

from conformalextract.analysis_version import build_analysis_lock, certification_config_hash
from conformalextract.certification import FROZEN_ALPHA


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "prediction_manifests": {"zs": "hz", "fs": "hf", "qa": "hq"},
        "data_group_split_hashes": {"split_assignment": "hs", "lineage": "hl"},
        "evaluator_loss_score_hash": "he",
        "candidate_grid_hash": "hg",
        "delta_ledger_hash": "hd",
        "git_commit": "abc1234",
        "environment_hash": "henv",
        "config_hash": certification_config_hash(),
    }
    kwargs.update(overrides)
    return kwargs


def test_build_analysis_lock_is_deterministic() -> None:
    """§13.3: serial/parallel execution must produce identical JSON."""
    first = build_analysis_lock(**_valid_kwargs())  # type: ignore[arg-type]
    second = build_analysis_lock(**_valid_kwargs())  # type: ignore[arg-type]
    assert first == second
    assert first.analysis_id == second.analysis_id
    assert first.status == "locked"


def test_any_changed_input_produces_a_different_analysis_id() -> None:
    """§13.2: any change creates a new version, so different versions never collide."""
    base = build_analysis_lock(**_valid_kwargs())
    changed_manifests = {"zs": "DIFFERENT", "fs": "hf", "qa": "hq"}
    variants = [
        build_analysis_lock(**_valid_kwargs(prediction_manifests=changed_manifests)),
        build_analysis_lock(**_valid_kwargs(candidate_grid_hash="DIFFERENT")),
        build_analysis_lock(**_valid_kwargs(delta_ledger_hash="DIFFERENT")),
        build_analysis_lock(**_valid_kwargs(git_commit="DIFFERENT")),
        build_analysis_lock(**_valid_kwargs(environment_hash="DIFFERENT")),
        build_analysis_lock(**_valid_kwargs(config_hash="DIFFERENT")),
    ]
    ids = {base.analysis_id} | {variant.analysis_id for variant in variants}
    assert len(ids) == len(variants) + 1  # every variant is genuinely distinct


def test_missing_or_incomplete_prediction_manifests_rejected() -> None:
    with pytest.raises(ValueError, match="exactly zs/fs/qa"):
        build_analysis_lock(**_valid_kwargs(prediction_manifests={"zs": "hz", "fs": "hf"}))
    with pytest.raises(ValueError, match="must be non-empty"):
        build_analysis_lock(
            **_valid_kwargs(prediction_manifests={"zs": "", "fs": "hf", "qa": "hq"})
        )


def test_empty_hash_inputs_are_rejected_not_silently_absent() -> None:
    """An empty string must not collapse into the same hash as a missing input."""
    for field in (
        "evaluator_loss_score_hash",
        "candidate_grid_hash",
        "delta_ledger_hash",
        "git_commit",
        "environment_hash",
        "config_hash",
    ):
        with pytest.raises(ValueError, match="non-empty"):
            build_analysis_lock(**_valid_kwargs(**{field: ""}))


def test_empty_data_group_split_hashes_rejected() -> None:
    with pytest.raises(ValueError, match="data_group_split_hashes"):
        build_analysis_lock(**_valid_kwargs(data_group_split_hashes={}))
    with pytest.raises(ValueError, match="data_group_split_hashes"):
        build_analysis_lock(**_valid_kwargs(data_group_split_hashes={"a": ""}))


def test_certification_config_hash_reflects_the_adr_0007_freeze_by_default() -> None:
    frozen = certification_config_hash()
    drifted = certification_config_hash(alpha=0.10)
    assert frozen != drifted
    # Passing the frozen value explicitly reproduces the default exactly.
    assert certification_config_hash(alpha=FROZEN_ALPHA) == frozen
