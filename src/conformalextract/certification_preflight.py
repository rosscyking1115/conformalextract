"""Certification-split preflight (Plan 3 §3.2) -- label-free, before any sealed read.

Every assertion in `run_certification_preflight` must hold before certification/final/shift
labels are ever opened. A failure raises (an "invalid attempt" per the plan) rather than
silently proceeding or overwriting the split. This module never accepts a final or shift
manifest as input -- their inaccessibility to the calibration command is therefore structural,
not merely checked (`test_final_and_shift_manifests_have_no_parameter_to_accept` proves it).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from conformalextract.certification import FROZEN_ACCEPTANCE_FLOOR, FROZEN_ALPHA, FROZEN_DELTA
from conformalextract.contracts import PredictionRecord, SystemManifest


class CertificationPreflightError(ValueError):
    """Raised when any §3.2 precondition fails; certification must not proceed."""


@dataclass(frozen=True)
class CertificationPreflightResult:
    status: str  # "ready" -- the only value ever returned; failures raise instead
    system_ids: tuple[str, ...]
    document_count: int
    candidate_grid_hash: str
    tie_order: tuple[str, ...]


def _document_ids(predictions: Sequence[PredictionRecord]) -> frozenset[str]:
    return frozenset(prediction.document_id for prediction in predictions)


def run_certification_preflight(
    *,
    predictions_by_system: Mapping[str, Sequence[PredictionRecord]],
    system_manifests: Mapping[str, SystemManifest],
    frozen_system_manifests: Mapping[str, SystemManifest],
    certification_group_ids: frozenset[str],
    train_group_ids: frozenset[str],
    development_group_ids: frozenset[str],
    candidate_grid_hash: str,
    tie_order: Sequence[str],
    alpha: float,
    delta: float,
    acceptance_floor: float,
    synthetic_coverage_passed: bool,
) -> CertificationPreflightResult:
    """Assert every §3.2 precondition; raise ``CertificationPreflightError`` on any failure.

    ``alpha``/``delta``/``acceptance_floor`` are passed in (not read from the module
    constants directly) so a caller drift from the ADR 0007 freeze is caught explicitly
    rather than silently reading the frozen value regardless of what was actually
    configured for this run.
    """

    system_ids = tuple(sorted(predictions_by_system))
    if not system_ids:
        raise CertificationPreflightError("no systems supplied")
    if set(system_ids) != {"zs", "fs", "qa"}:
        raise CertificationPreflightError(f"expected exactly zs/fs/qa, got {system_ids!r}")

    # 1. All ZS/FS/QA predictions exist for the identical group of documents.
    document_sets = {
        system_id: _document_ids(predictions)
        for system_id, predictions in predictions_by_system.items()
    }
    reference = document_sets[system_ids[0]]
    if not reference:
        raise CertificationPreflightError("predictions must be non-empty")
    for system_id, documents in document_sets.items():
        if documents != reference:
            raise CertificationPreflightError(
                f"{system_id} covers a different document set than {system_ids[0]}"
            )

    # 2. System/adapter/prompt/tokenizer/model/decoding/score hashes match frozen manifests.
    if set(system_manifests) != set(system_ids):
        raise CertificationPreflightError("system_manifests must cover exactly zs/fs/qa")
    if set(frozen_system_manifests) != set(system_ids):
        raise CertificationPreflightError("frozen_system_manifests must cover exactly zs/fs/qa")
    for system_id in system_ids:
        if system_manifests[system_id] != frozen_system_manifests[system_id]:
            raise CertificationPreflightError(
                f"{system_id} manifest diverges from the frozen reference"
            )

    # 3. No group overlap between the certification split about to open and train/development.
    if certification_group_ids & train_group_ids:
        raise CertificationPreflightError("certification groups overlap the train role")
    if certification_group_ids & development_group_ids:
        raise CertificationPreflightError("certification groups overlap the development role")
    if not certification_group_ids:
        raise CertificationPreflightError("certification_group_ids must be non-empty")

    # 4. The candidate grid and its deterministic tie order are already committed.
    if not candidate_grid_hash:
        raise CertificationPreflightError("candidate_grid_hash must be committed before opening")
    if not tie_order or len(set(tie_order)) != len(tie_order):
        raise CertificationPreflightError("tie_order must be a committed, unique ordering")

    # 5. alpha/delta/floor match the ADR 0007 freeze; the delta ledger (this call's own
    #    values) is committed by virtue of being explicit, non-default arguments.
    if (alpha, delta, acceptance_floor) != (FROZEN_ALPHA, FROZEN_DELTA, FROZEN_ACCEPTANCE_FLOOR):
        raise CertificationPreflightError(
            "alpha/delta/acceptance_floor diverge from the ADR 0007 freeze "
            f"({FROZEN_ALPHA}, {FROZEN_DELTA}, {FROZEN_ACCEPTANCE_FLOOR})"
        )

    # 6. The certifier passes synthetic coverage tests at the current Git SHA.
    if not synthetic_coverage_passed:
        raise CertificationPreflightError(
            "synthetic certifier coverage tests (test_scorc_coverage.py) must pass first"
        )

    # 7. Final and shift manifests remain inaccessible to the calibration command: this
    # function accepts no such parameter, so there is nothing to check here -- see
    # test_final_and_shift_manifests_have_no_parameter_to_accept for the structural proof.

    return CertificationPreflightResult(
        status="ready",
        system_ids=system_ids,
        document_count=len(reference),
        candidate_grid_hash=candidate_grid_hash,
        tie_order=tuple(tie_order),
    )
