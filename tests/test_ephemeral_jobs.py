from __future__ import annotations

import pytest

from conformalextract.training import (
    FrozenTrainingSource,
    plan_ephemeral_materialization,
)

SOURCE = FrozenTrainingSource(
    source_url="https://www.cs.jhu.edu/~paxia/rams/data/RAMS_1.0.zip",
    source_sha256="a" * 64,
    source_revision="RAMS-1.0",
    licence_review_id="gate0-rams-licence",
)


def _plan(**overrides: object):  # type: ignore[no-untyped-def]
    kwargs: dict[str, object] = {
        "source": SOURCE,
        "workspace": "/tmp/ce-r0",
        "raw_archive_name": "RAMS_1.0.zip",
        "allowed_inputs": ("train.jsonl", "development.jsonl"),
        "upload_artifact_kinds": ("adapter_copy_a", "lineage_manifest"),
    }
    kwargs.update(overrides)
    return plan_ephemeral_materialization(**kwargs)  # type: ignore[arg-type]


def test_plan_downloads_verifies_deletes_raw_then_launches_allowlisted_inputs() -> None:
    plan = _plan()

    assert [step.action for step in plan.steps] == [
        "download",
        "verify_checksum",
        "extract",
        "materialize_input",
        "materialize_input",
        "delete_raw",
        "launch",
    ]
    verify = next(step for step in plan.steps if step.action == "verify_checksum")
    assert SOURCE.source_sha256 in verify.detail
    launch = next(step for step in plan.steps if step.action == "launch")
    assert "/tmp/ce-r0/inputs/train.jsonl" in launch.detail
    assert "/tmp/ce-r0/inputs/development.jsonl" in launch.detail
    assert plan.raw_retained is False
    assert plan.uploads_are_label_free is True


def test_launch_never_reads_from_the_raw_extraction_directory() -> None:
    plan = _plan()

    launch = next(step for step in plan.steps if step.action == "launch")
    assert "/tmp/ce-r0/raw" not in launch.detail


def test_delete_raw_precedes_launch_and_removes_archive_and_extraction() -> None:
    plan = _plan()

    actions = [step.action for step in plan.steps]
    delete = next(step for step in plan.steps if step.action == "delete_raw")
    assert "RAMS_1.0.zip" in delete.detail
    assert "/tmp/ce-r0/raw" in delete.detail
    assert actions.index("delete_raw") < actions.index("launch")


def test_plan_refuses_to_upload_raw_or_recoverable_text() -> None:
    for forbidden in (
        "raw_source_text",
        "sealed_certification_labels",
        "grounded_prediction_text",
    ):
        with pytest.raises(ValueError, match="upload"):
            _plan(upload_artifact_kinds=("adapter_copy_a", forbidden))


def test_plan_requires_an_ephemeral_absolute_workspace() -> None:
    with pytest.raises(ValueError, match="ephemeral"):
        _plan(workspace="relative/workspace")


def test_plan_requires_at_least_one_named_input() -> None:
    with pytest.raises(ValueError, match="input"):
        _plan(allowed_inputs=())
