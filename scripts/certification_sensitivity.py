r"""Emit the sensitivity quantities the write-up quotes, each stamped with its configuration.

**Why this script exists.** Five times in this project's preparation a number was computed in a
shell at one configuration and written into prose naming another, and every one erred in the
direction that flattered the result. The most recent was an acceptance lower bound quoted as
0.2017 "at the run's three-candidate allocation" when that allocation gives 0.198390 --- below the
floor, which reverses the sentence it was supporting.

``claims.verify_ledger`` cannot catch that. It checks that a claim's cited evidence **paths exist
and are git-tracked**; it never opens the file, never compares a number, and never sees a
configuration. So a prose figure computed nowhere passes the publication gate unchanged.

This script is the narrow fix: every quantity below is emitted **together with the configuration
that produced it** --- the delta, its allocation, the candidate count, and the n. A reader can then
check not only that a number is right but that it answers the question the prose asks of it.

**Diagnostic only.** No threshold is selected, no certificate is issued, the frozen alpha = 0.20 is
untouched, and no sealed split is opened: the loader is the re-analysis loader, so
``assert_reanalysis_role`` refuses ``final``/``shift`` before a file is opened. $0.

Usage::

    uv run python scripts/certification_sensitivity.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta

from conformalextract.calibration import auroc
from conformalextract.certification import (
    FROZEN_ACCEPTANCE_FLOOR,
    FROZEN_ALPHA,
    FROZEN_DELTA,
    largest_scorc_grid,
    scorc_certificate,
    scorc_minimum_n,
)
from conformalextract.reanalysis import load_split_system_data

#: The frozen run's own allocation, read off the committed certification result rather than
#: assumed: three systems share delta, so each gets delta/3, and each system's grid holds three
#: candidates. Both divisions apply. Quoting one without the other is exactly the error this
#: script exists to prevent.
SYSTEMS = 3
CANDIDATES_PER_SYSTEM = 3
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260802


def _clopper_pearson_lower(k: int, n: int, alpha_cp: float) -> float:
    """The certifier's own acceptance lower bound, at whatever tail mass it is handed."""

    return 0.0 if k == 0 else float(beta.ppf(alpha_cp, k, n - k + 1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="qa")
    parser.add_argument("--candidate", default="mean")
    parser.add_argument(
        "--predictions-dir", type=Path, default=Path("data/private/plan2/predictions")
    )
    parser.add_argument("--rams-archive", type=Path, default=Path("data/raw/rams/RAMS_1.0c.tar.gz"))
    parser.add_argument(
        "--role-map", type=Path, default=Path("data/private/splits/rams_roles.jsonl")
    )
    parser.add_argument(
        "--development-gate",
        type=Path,
        default=Path("evidence/plan2/development_gate_summary.json"),
    )
    parser.add_argument(
        "--out", type=Path, default=Path("evidence/plan3/certification_sensitivity.json")
    )
    args = parser.parse_args()

    from conformalextract.cli import _reanalysis_inputs

    instances, contexts, assignments, gold_frames, _gate = _reanalysis_inputs(
        args.rams_archive, args.role_map, args.development_gate
    )
    groups = {
        str(a["document_id"]): str(a["group_id"])
        for a in assignments
        if a["role"] == "certification"
    }
    data = load_split_system_data(
        split_role="certification",
        system_id=args.system,
        confidence_candidate=args.candidate,
        predictions_path=args.predictions_dir / f"{args.system}.v1.jsonl",
        contexts=contexts,
        instances=instances,
        group_by_document=groups,
        gold_frames=gold_frames,
    )

    rows = data.rows
    n_rows = len(rows)
    losses = np.asarray([r.loss for r in rows], dtype=np.float64)
    scores = np.asarray([r.score for r in rows], dtype=np.float64)
    finite = np.isfinite(scores)
    eligible = np.asarray([r.all_valid for r in rows]) & finite
    order = np.argsort(np.where(eligible, losses, np.inf))
    n_eligible = int(eligible.sum())

    running = np.cumsum(losses[order]) / np.arange(1, n_rows + 1)
    within = np.flatnonzero(running[:n_eligible] <= FROZEN_ALPHA)
    k_oracle = int(within[-1]) + 1 if within.size else 0

    # --- the acceptance lower bound, at EVERY allocation anyone might mean -------------------
    allocations = {
        "single_candidate_full_delta": {
            "delta": FROZEN_DELTA,
            "candidate_count": 1,
            "note": (
                "What scorc_certificate itself prints for a one-candidate verification run. "
                "Correct FOR THAT RUN and for nothing else."
            ),
        },
        "three_candidates_full_delta": {
            "delta": FROZEN_DELTA,
            "candidate_count": CANDIDATES_PER_SYSTEM,
            "note": (
                "NOT a configuration this project ever ran. Recorded because a draft quoted its "
                "value, 0.2017, while naming the frozen allocation. It omits the per-system "
                "delta/3 division."
            ),
        },
        "frozen_run_three_candidates_delta_over_three": {
            "delta": FROZEN_DELTA / SYSTEMS,
            "candidate_count": CANDIDATES_PER_SYSTEM,
            "note": (
                "THE FROZEN CONFIGURATION, per evidence/plan3/certification_result.json: three "
                "systems share delta so each gets delta/3, and each grid holds three candidates. "
                "Both divisions apply."
            ),
        },
    }
    acceptance_bound: dict[str, object] = {}
    for name, cfg in allocations.items():
        alpha_cp = float(cfg["delta"]) / (16.0 * int(cfg["candidate_count"]))
        lcb = _clopper_pearson_lower(k_oracle, n_rows, alpha_cp)
        smallest = next(
            (
                k
                for k in range(1, n_eligible + 1)
                if _clopper_pearson_lower(k, n_rows, alpha_cp) >= FROZEN_ACCEPTANCE_FLOOR
            ),
            None,
        )
        acceptance_bound[name] = {
            **cfg,
            "clopper_pearson_tail_mass": alpha_cp,
            "n": n_rows,
            "k_at_oracle_prefix": k_oracle,
            "acceptance_lower_bound": lcb,
            "clears_acceptance_floor": bool(lcb >= FROZEN_ACCEPTANCE_FLOOR),
            "smallest_k_clearing_floor": smallest,
            "margin_in_groups": None if smallest is None else k_oracle - smallest,
        }

    # --- the empirical-Bernstein verification, through the certifier itself -------------------
    eb_probe = []
    for k in (139, 279, k_oracle, 559):
        accepted = np.zeros((n_rows, 1), dtype=bool)
        accepted[order[:k], 0] = True
        result = scorc_certificate(
            losses=losses[:, None],
            accepted=accepted,
            candidate_ids=["oracle"],
            alpha=FROZEN_ALPHA,
            acceptance_floor=FROZEN_ACCEPTANCE_FLOOR,
            delta=FROZEN_DELTA,
        )
        eb_probe.append(
            {
                "k": k,
                "coverage": k / n_rows,
                "status": result.status,
                "feasible": result.feasible,
                "reasons": list(result.reasons),
                "acceptance_lower": result.acceptance_lower,
            }
        )

    # --- the AUROC interval -------------------------------------------------------------------
    failure = losses[finite] > 0.0
    subset = scores[finite]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        idx = rng.integers(0, subset.size, subset.size)
        value = auroc(subset[idx], failure[idx])
        if value is not None:
            draws.append(value)
    low, high = (float(x) for x in np.percentile(draws, [2.5, 97.5]))

    required = {
        c: scorc_minimum_n(
            candidate_count=c,
            delta=FROZEN_DELTA / SYSTEMS,
            acceptance_floor=FROZEN_ACCEPTANCE_FLOOR,
        )
        for c in (1, 2, 3, 4, 9)
    }

    artifact = {
        "schema_version": "1",
        "diagnostic_only": True,
        "certifies_nothing": True,
        "interpretation": (
            "Sensitivity quantities the write-up quotes, each stamped with the configuration that "
            "produced it. Written because claims.verify_ledger checks only that a claim's cited "
            "evidence paths exist and are tracked - it never opens the file, compares a number, or "
            "sees a configuration - so a prose figure computed at the wrong allocation passes the "
            "publication gate unchanged. That is how an acceptance lower bound of 0.2017 was "
            "quoted against the frozen allocation, which gives 0.198390 and does NOT clear the "
            "floor. Every figure here names its delta, its allocation, its candidate count and its "
            "n. Nothing here selects a threshold or certifies anything."
        ),
        "frozen": {
            "alpha": FROZEN_ALPHA,
            "delta": FROZEN_DELTA,
            "acceptance_floor": FROZEN_ACCEPTANCE_FLOOR,
            "systems": SYSTEMS,
            "candidates_per_system": CANDIDATES_PER_SYSTEM,
        },
        "population": {
            "rows_passed_to_certifier": n_rows,
            "scorable_finite_score": int(finite.sum()),
            "eligible_all_valid_and_finite": n_eligible,
            "unscorable_groups": int((~finite).sum()),
            "note": (
                "The precondition is checked against the ROW COUNT. Unscorable groups remain rows, "
                "so n stays at rows_passed_to_certifier however many of them cannot be ranked."
            ),
        },
        "acceptance_lower_bound_by_allocation": acceptance_bound,
        "empirical_bernstein_probe": {
            "construction": "scorc_certificate, one pre-chosen oracle candidate, no multiplicity",
            "delta": FROZEN_DELTA,
            "candidate_count": 1,
            "results": eb_probe,
        },
        "auroc_interval": {
            "indicator": "any_error",
            "point": auroc(subset, failure),
            "ci_lower": low,
            "ci_upper": high,
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
            "scored_groups": int(finite.sum()),
            "non_failing_groups": int((~failure).sum()),
        },
        "grid_capacity": {
            "delta_allocation": FROZEN_DELTA / SYSTEMS,
            "required_n_by_candidate_count": required,
            "largest_grid_at_rows": largest_scorc_grid(
                independent_documents=n_rows,
                delta=FROZEN_DELTA / SYSTEMS,
                acceptance_floor=FROZEN_ACCEPTANCE_FLOOR,
            ),
            "note": (
                "The frozen three-candidate grid is the largest this corpus admits at delta/3: a "
                "fourth candidate requires more groups than the split holds. This states 'at the "
                "edge' without expressing it as a margin in groups, which the row/scorable "
                "distinction makes ambiguous."
            ),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
