"""Immutable analysis-version lock (Plan 3 §13.2).

An analysis version binds every input that could change a certification result: prediction
manifests for all systems, data/group/split hashes, evaluator/loss/score hashes, the candidate
grid, certification config + delta ledger, the Git commit, and an environment lock. Any change
to any of these produces a new version; results from different versions must never be mixed in
one headline table (the ``analysis_id`` is a hash of everything below it, so this is enforced by
construction -- two versions with any differing input never collide).

The certification config (``alpha``/``delta``/``acceptance_floor``/``material_gain``/
``bootstrap_replicates``/confidence candidate) is real today (ADR 0007). The candidate grid is
not: §5.4's threshold grid has not been built yet, so its hash is accepted as a caller-supplied
input rather than computed here -- this module encodes the binding *mechanism*, not a stand-in
for an undecided grid.
"""

from __future__ import annotations

from collections.abc import Mapping

from conformalextract.artifacts import canonical_json_bytes, sha256_bytes
from conformalextract.certification import (
    FROZEN_ACCEPTANCE_FLOOR,
    FROZEN_ALPHA,
    FROZEN_BOOTSTRAP_REPLICATES,
    FROZEN_CONFIDENCE_CANDIDATES,
    FROZEN_DELTA,
    FROZEN_MATERIAL_GAIN,
)
from conformalextract.contracts import AnalysisLock

REQUIRED_INPUT_GROUPS = (
    "prediction_manifests",
    "data_group_split_hashes",
    "evaluator_loss_score_hash",
    "candidate_grid_hash",
    "delta_ledger_hash",
)


def certification_config_hash(
    *,
    alpha: float = FROZEN_ALPHA,
    delta: float = FROZEN_DELTA,
    acceptance_floor: float = FROZEN_ACCEPTANCE_FLOOR,
    material_gain: float = FROZEN_MATERIAL_GAIN,
    bootstrap_replicates: int = FROZEN_BOOTSTRAP_REPLICATES,
    confidence_candidates: Mapping[str, str] = FROZEN_CONFIDENCE_CANDIDATES,
    delta_allocation: Mapping[str, float] | None = None,
    primary_construction: str | None = None,
) -> str:
    """Hash of the frozen ADR 0007 certification config; a drift from any default changes it.

    ``confidence_candidates`` is a **per-system mapping** (reviewer Phase-A ruling 1a), never a
    scalar: the score is part of each system's own selective policy, so binding one shared value
    would encode a candidate no system deploys.

    ``delta_allocation`` (per-system δ_s) and ``primary_construction`` bind the §5.5 global
    multiplicity decision (see `docs/plan3/theorem-to-code-global-multiplicity.md`), so the
    cross-system failure-budget split cannot be swapped after the fact without producing a new
    ``analysis_id``. They are optional only because that decision is still awaiting its Gate-0
    review sign-off; ``certify`` must supply both. When supplied, the allocation must sum to
    ``delta`` -- a split that does not exhaust (or that overspends) the budget is rejected here
    rather than silently invalidating the union bound.
    """

    if set(confidence_candidates) != {"zs", "fs", "qa"}:
        raise ValueError("confidence_candidates must cover exactly zs/fs/qa")
    known = {"mean", "tenth_percentile", "minimum"}
    unknown = set(confidence_candidates.values()) - known
    if unknown:
        raise ValueError(f"unknown confidence candidate(s): {sorted(unknown)}")

    if delta_allocation is not None:
        total = sum(delta_allocation.values())
        if abs(total - delta) > 1e-12:
            raise ValueError(
                f"delta_allocation sums to {total!r}, which does not match delta {delta!r}; "
                "the cross-system union bound requires the split to exhaust exactly delta"
            )
        if any(value <= 0.0 for value in delta_allocation.values()):
            raise ValueError("every per-system delta share must be strictly positive")

    return sha256_bytes(
        canonical_json_bytes(
            {
                "alpha": alpha,
                "delta": delta,
                "acceptance_floor": acceptance_floor,
                "material_gain": material_gain,
                "bootstrap_replicates": bootstrap_replicates,
                "confidence_candidates": dict(sorted(confidence_candidates.items())),
                "delta_allocation": (
                    None
                    if delta_allocation is None
                    else dict(sorted(delta_allocation.items()))
                ),
                "primary_construction": primary_construction,
            }
        )
    )


def build_analysis_lock(
    *,
    prediction_manifests: Mapping[str, str],
    data_group_split_hashes: Mapping[str, str],
    evaluator_loss_score_hash: str,
    candidate_grid_hash: str,
    delta_ledger_hash: str,
    git_commit: str,
    environment_hash: str,
    config_hash: str,
) -> AnalysisLock:
    """Bind every §13.2 input into one immutable, hash-derived analysis version.

    Every ``*_hash`` argument must be non-empty (an absent input is a missing precondition,
    never silently treated as "no contribution" -- an empty string would collapse into the
    same hash as a genuinely-absent input, defeating the point of binding it at all).
    """

    for name, value in (
        ("evaluator_loss_score_hash", evaluator_loss_score_hash),
        ("candidate_grid_hash", candidate_grid_hash),
        ("delta_ledger_hash", delta_ledger_hash),
        ("git_commit", git_commit),
        ("environment_hash", environment_hash),
        ("config_hash", config_hash),
    ):
        if not value:
            raise ValueError(f"{name} must be non-empty")
    if not prediction_manifests:
        raise ValueError("prediction_manifests must cover at least one system")
    if set(prediction_manifests) != {"zs", "fs", "qa"}:
        raise ValueError("prediction_manifests must cover exactly zs/fs/qa")
    if any(not value for value in prediction_manifests.values()):
        raise ValueError("every prediction manifest hash must be non-empty")
    if not data_group_split_hashes or any(
        not value for value in data_group_split_hashes.values()
    ):
        raise ValueError("data_group_split_hashes must be non-empty and fully populated")

    input_hashes = {
        **{f"prediction_manifest:{system_id}": digest for system_id, digest in sorted(
            prediction_manifests.items()
        )},
        **{f"data_group_split:{key}": digest for key, digest in sorted(
            data_group_split_hashes.items()
        )},
        "evaluator_loss_score": evaluator_loss_score_hash,
        "candidate_grid": candidate_grid_hash,
        "delta_ledger": delta_ledger_hash,
    }
    analysis_id = "plan3cert-" + sha256_bytes(
        canonical_json_bytes(
            {
                **input_hashes,
                "git_commit": git_commit,
                "environment_hash": environment_hash,
                "config_hash": config_hash,
            }
        )
    )[:20]
    return AnalysisLock(
        analysis_id=analysis_id,
        git_commit=git_commit,
        environment_hash=environment_hash,
        input_hashes=input_hashes,
        config_hash=config_hash,
    )
