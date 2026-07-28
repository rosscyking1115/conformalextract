"""Ordered, hash-gated Plan 3 analysis-pipeline governance (plan sections 13.1/13.2).

The five Plan 3 commands must run in a fixed order, each consuming the immutable artifact
of the stage before it, and all bound to one analysis version. This module encodes that
mechanism as pure contracts: authorization refuses out-of-order execution, a broken
prerequisite hash chain, or a version mismatch, so a later stage can never silently run
against stale or foreign inputs.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from conformalextract.contracts import NonEmpty

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class AnalysisStage(StrEnum):
    BUILD_GRID = "build_grid"
    CERTIFY = "certify"
    EVALUATE_FINAL = "evaluate_final"
    EVALUATE_SHIFT = "evaluate_shift"
    RENDER_REPORT = "render_report"


STAGE_ORDER: tuple[AnalysisStage, ...] = tuple(AnalysisStage)


class StageArtifact(BaseModel):
    """One completed stage, hash-linked to the immutable artifact of the prior stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: AnalysisStage
    analysis_version: NonEmpty
    artifact_sha256: Sha256
    prerequisite_sha256: Sha256 | None = None


def next_stage(completed: tuple[StageArtifact, ...]) -> AnalysisStage | None:
    """Return the next stage to run, or ``None`` when the pipeline is complete."""

    return STAGE_ORDER[len(completed)] if len(completed) < len(STAGE_ORDER) else None


def authorize_stage(
    stage: AnalysisStage,
    *,
    analysis_version: str,
    completed: tuple[StageArtifact, ...],
) -> None:
    """Raise unless ``stage`` is the next stage over a valid completed prefix.

    Validates that the completed stages form the exact ordered prefix, share the requested
    analysis version, and chain by prerequisite hash, then that ``stage`` is the next stage.
    """

    previous_hash: str | None = None
    for index, artifact in enumerate(completed):
        if index >= len(STAGE_ORDER) or artifact.stage is not STAGE_ORDER[index]:
            raise ValueError("completed stages are out of order")
        if artifact.analysis_version != analysis_version:
            raise ValueError("completed stage has a different analysis version")
        if artifact.prerequisite_sha256 != previous_hash:
            raise ValueError("prerequisite hash chain is broken")
        previous_hash = artifact.artifact_sha256
    expected = next_stage(completed)
    if stage is not expected:
        raise ValueError(f"stage {stage.value!r} is out of order")


def append_stage(
    stage: AnalysisStage,
    *,
    analysis_version: str,
    artifact_sha256: str,
    completed: tuple[StageArtifact, ...],
) -> StageArtifact:
    """Authorize ``stage`` then append its immutable, hash-linked artifact record."""

    authorize_stage(stage, analysis_version=analysis_version, completed=completed)
    previous_hash = completed[-1].artifact_sha256 if completed else None
    return StageArtifact(
        stage=stage,
        analysis_version=analysis_version,
        artifact_sha256=artifact_sha256,
        prerequisite_sha256=previous_hash,
    )
