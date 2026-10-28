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
from conformalextract.threshold_grid import grid_hash_from_certifiable_thresholds


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


SYSTEM_IDS = ("zs", "fs", "qa")

#: The §3.2 bullets a check at run time cannot discharge, named so a passing result never reads
#: as "all seven held". Recorded on every result rather than left to a docstring.
NOT_CHECKED_AT_RUN_TIME: Mapping[str, str] = {
    "synthetic_coverage": (
        "the certifier's synthetic coverage tests are a test-suite property of the commit "
        "(tests/test_scorc_coverage.py, run by CI), not something the command re-runs"
    ),
    "system_identity_fields": (
        "model, adapter, tokenizer, prompt and decoding identity are attested through the "
        "hash of the prediction file those settings produced, not compared field by field: "
        "no per-field frozen system manifest was ever committed"
    ),
}


@dataclass(frozen=True)
class CertificationInputPreflightResult:
    status: str  # "ready" -- the only value ever returned; failures raise instead
    certification_documents: int
    certification_groups: int
    not_checked_at_run_time: Mapping[str, str]


def run_certification_input_preflight(
    *,
    prediction_sha256: Mapping[str, str],
    prediction_document_ids: Mapping[str, frozenset[str]],
    role_map_sha256: str,
    roles: Mapping[str, tuple[str, str]],
    grids: Mapping[str, object],
    selected_candidates: Mapping[str, str],
    frozen: Mapping[str, object],
) -> CertificationInputPreflightResult:
    """The §3.2 preflight over what ``certify`` actually holds, before the archive is opened.

    ``run_certification_preflight`` above states §3.2 over parsed ``PredictionRecord`` objects
    and ``SystemManifest`` pairs. ``certify`` has neither before it opens the RAMS archive --
    parsing predictions needs the source text, which shares a record with the gold -- and no
    frozen ``SystemManifest`` was ever committed. This variant checks the same preconditions on
    the inputs as files: their hashes against ``manifests/plan3/certification_inputs.json``,
    document coverage from the prediction records' keys, and role overlap from the role map.
    Everything it reads is label-free. ``roles`` maps document id to ``(role, group_id)``.
    """

    systems = frozen.get("systems")
    if not isinstance(systems, Mapping) or set(systems) != set(SYSTEM_IDS):
        raise CertificationPreflightError("frozen inputs must name exactly zs/fs/qa")
    for name in (prediction_sha256, prediction_document_ids, selected_candidates):
        if set(name) != set(SYSTEM_IDS):
            raise CertificationPreflightError("inputs must cover exactly zs/fs/qa")

    # Operating point: alpha/delta/floor as frozen by ADR 0007.
    point = (frozen.get("alpha"), frozen.get("delta"), frozen.get("acceptance_floor"))
    if point != (FROZEN_ALPHA, FROZEN_DELTA, FROZEN_ACCEPTANCE_FLOOR):
        raise CertificationPreflightError(
            f"operating point {point!r} diverges from the ADR 0007 freeze "
            f"({FROZEN_ALPHA}, {FROZEN_DELTA}, {FROZEN_ACCEPTANCE_FLOOR})"
        )

    # Input identity: each prediction file and the role map are the frozen ones.
    if role_map_sha256 != frozen.get("role_map_sha256"):
        raise CertificationPreflightError("the role map is not the frozen one")
    grid_entries = grids.get("grids")
    if not isinstance(grid_entries, Mapping):
        raise CertificationPreflightError("grids carry no per-system entries")
    for system_id in SYSTEM_IDS:
        entry = systems[system_id]
        if not isinstance(entry, Mapping):
            raise CertificationPreflightError(f"frozen entry for {system_id} is malformed")
        if prediction_sha256[system_id] != entry.get("predictions_sha256"):
            raise CertificationPreflightError(f"{system_id} predictions are not the frozen file")
        if selected_candidates[system_id] != entry.get("confidence_candidate"):
            raise CertificationPreflightError(
                f"{system_id} confidence candidate diverges from the frozen one"
            )
        grid = grid_entries.get(system_id)
        if not isinstance(grid, Mapping) or grid.get("grid_hash") != entry.get("grid_hash"):
            raise CertificationPreflightError(f"{system_id} grid is not the committed grid")
        thresholds = grid.get("certifiable_thresholds")
        if (
            not isinstance(thresholds, list)
            or not thresholds
            or len({str(t) for t in thresholds}) != len(thresholds)
        ):
            raise CertificationPreflightError(
                f"{system_id} grid has no committed, unique tie order"
            )
        # The declared hash is only evidence if it is the hash of the thresholds certify uses.
        if grid_hash_from_certifiable_thresholds(system_id, thresholds) != grid.get("grid_hash"):
            raise CertificationPreflightError(
                f"{system_id} grid's thresholds do not hash to its declared grid_hash"
            )

    # Coverage: every certification document is predicted, identically, by all three systems.
    certification = frozenset(d for d, (role, _) in roles.items() if role == "certification")
    if not certification:
        raise CertificationPreflightError("the role map assigns no certification documents")
    covered = {s: prediction_document_ids[s] & certification for s in SYSTEM_IDS}
    if len({covered[s] for s in SYSTEM_IDS}) != 1:
        raise CertificationPreflightError(
            "zs/fs/qa do not cover an identical set of certification documents"
        )
    missing = certification - covered["qa"]
    if missing:
        raise CertificationPreflightError(
            f"{len(missing)} certification document(s) have no prediction from any system"
        )

    # Separation: no certification group is shared with the train or development role.
    certification_groups = {group for role, group in roles.values() if role == "certification"}
    for other in ("train", "development"):
        shared = certification_groups & {group for role, group in roles.values() if role == other}
        if shared:
            raise CertificationPreflightError(
                f"{len(shared)} certification group(s) also appear in the {other} role"
            )

    return CertificationInputPreflightResult(
        status="ready",
        certification_documents=len(certification),
        certification_groups=len(certification_groups),
        not_checked_at_run_time=dict(NOT_CHECKED_AT_RUN_TIME),
    )
