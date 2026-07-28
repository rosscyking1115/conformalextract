from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from conformalextract.analysis_pipeline import (
    AnalysisStage,
    StageArtifact,
    append_stage,
    authorize_stage,
    next_stage,
)

VERSION = "plan3-analysis-v1"


def _artifact(stage: AnalysisStage, completed: tuple[StageArtifact, ...]) -> StageArtifact:
    return append_stage(
        stage,
        analysis_version=VERSION,
        artifact_sha256=hashlib.sha256(stage.value.encode()).hexdigest(),
        completed=completed,
    )


def test_pipeline_runs_stages_in_the_frozen_order() -> None:
    completed: tuple[StageArtifact, ...] = ()
    for stage in AnalysisStage:
        assert next_stage(completed) is stage
        completed = (*completed, _artifact(stage, completed))
    assert next_stage(completed) is None


def test_build_grid_is_authorized_first_and_certify_is_not() -> None:
    authorize_stage(AnalysisStage.BUILD_GRID, analysis_version=VERSION, completed=())
    with pytest.raises(ValueError, match="out of order"):
        authorize_stage(AnalysisStage.CERTIFY, analysis_version=VERSION, completed=())


def test_certify_requires_the_build_grid_artifact_first() -> None:
    grid = _artifact(AnalysisStage.BUILD_GRID, ())
    authorize_stage(AnalysisStage.CERTIFY, analysis_version=VERSION, completed=(grid,))
    with pytest.raises(ValueError, match="out of order"):
        authorize_stage(
            AnalysisStage.EVALUATE_FINAL, analysis_version=VERSION, completed=(grid,)
        )


def test_stages_from_a_different_analysis_version_are_rejected() -> None:
    grid = _artifact(AnalysisStage.BUILD_GRID, ())
    with pytest.raises(ValueError, match="analysis version"):
        authorize_stage(AnalysisStage.CERTIFY, analysis_version="other-version", completed=(grid,))


def test_a_tampered_prerequisite_hash_breaks_the_chain() -> None:
    grid = _artifact(AnalysisStage.BUILD_GRID, ())
    certify = _artifact(AnalysisStage.CERTIFY, (grid,))
    tampered_grid = grid.model_copy(update={"artifact_sha256": "b" * 64})

    with pytest.raises(ValueError, match="prerequisite"):
        authorize_stage(
            AnalysisStage.EVALUATE_FINAL,
            analysis_version=VERSION,
            completed=(tampered_grid, certify),
        )


def test_append_stage_rejects_an_out_of_order_append() -> None:
    with pytest.raises(ValueError, match="out of order"):
        append_stage(
            AnalysisStage.CERTIFY,
            analysis_version=VERSION,
            artifact_sha256="a" * 64,
            completed=(),
        )


def test_stage_artifact_requires_a_valid_sha256() -> None:
    with pytest.raises(ValidationError):
        StageArtifact(
            stage=AnalysisStage.BUILD_GRID,
            analysis_version=VERSION,
            artifact_sha256="not-a-hash",
            prerequisite_sha256=None,
        )
