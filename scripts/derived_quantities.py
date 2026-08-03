r"""Compute the quantities the write-up derives in prose, and stamp each with its configuration.

**Why this script exists.** The first run of ``scripts/check_paper_claims.py`` --- the first guard
in this project scoped by the paper rather than by the artifacts --- found no wrong figure and no
wrong configuration. It found that **53 of 120 figures resolve to nothing**, and that the set
includes the paper's headline gap (21.6 points) and its family-wide certified acceptance (8.4%).
Those were derived in a shell, written into prose, and never stored anywhere.

That is the same shape as the five recorded quoting errors, one step earlier: a number computed at
a configuration held in someone's head. So the order is inverted here. **The figure is computed
into an artifact first, the artifact stamps the configuration, the guard verifies the paper against
it, and only then is prose corrected from the artifact.** Three consecutive prose-repair rounds
each introduced a new instance of the class being repaired; this is the alternative to a fourth.

Every quantity below carries the ``construction`` that produced it (Hoeffding radius, empirical
prefix mean, difference of two committed readings), the ``delta`` and its allocation, the candidate
count, ``n``, and where relevant the accepted-prefix length ``k``. Two quantities are emitted at
**two** prefix lengths, because the write-up is not internally consistent about which one "at the
floor" means, and picking one here would hide that rather than report it.

**Diagnostic only.** No threshold is selected, no certificate is issued, the frozen alpha = 0.20 is
untouched, and no sealed split is opened --- the loader is the re-analysis loader, so
``assert_reanalysis_role`` refuses ``final``/``shift`` before a file is opened. $0.

Usage::

    uv run python scripts/derived_quantities.py
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from conformalextract.certification import (
    FROZEN_ACCEPTANCE_FLOOR,
    FROZEN_ALPHA,
    FROZEN_DELTA,
    hoeffding_upper,
)
from conformalextract.reanalysis import (
    access_block,
    certification_access_for,
    load_split_system_data,
)

SYSTEMS = 3
CANDIDATES_PER_SYSTEM = 3

#: The per-system allocation the certified readings use: three systems share delta.
CERTIFIED_DELTA = FROZEN_DELTA / SYSTEMS
#: The family-wide Bonferroni allocation, delta/(2*9), quoted where the more conservative figure
#: is wanted. The write-up calls this "family-wide".
FAMILY_DELTA = FROZEN_DELTA / 18.0


def _radius(k: int, delta: float) -> float:
    """The Hoeffding half-width at prefix length ``k``: what the bound spends before any data."""

    return float(hoeffding_upper([0.0] * k, delta))


def _certified_acceptance(sorted_losses: np.ndarray, total: int, alpha: float, delta: float) -> int:
    """Largest accepted prefix whose Hoeffding UPPER bound stays within alpha. Returns k."""

    bounds = np.array(
        [hoeffding_upper(list(sorted_losses[:k]), delta) for k in range(1, sorted_losses.size + 1)]
    )
    within = np.flatnonzero(bounds <= alpha)
    return int(within[-1]) + 1 if within.size else 0


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
        "--out", type=Path, default=Path("evidence/plan3/derived_quantities.json")
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
    n_total = len(rows)
    losses = np.asarray([r.loss for r in rows], dtype=np.float64)
    scores = np.asarray([r.score for r in rows], dtype=np.float64)
    eligible = np.asarray([r.all_valid for r in rows]) & np.isfinite(scores)

    # The loss-optimal ordering: ineligible groups can never be accepted, so they sort last.
    optimal = np.sort(np.where(eligible, losses, np.inf))
    optimal_finite = optimal[np.isfinite(optimal)]

    # Score-ranked ordering, for the delivered readings.
    ranked = np.where(eligible, -scores, np.inf)
    score_order = np.argsort(ranked, kind="stable")
    score_losses = losses[score_order]

    running_optimal = np.cumsum(optimal) / np.arange(1, n_total + 1)
    running_scored = np.cumsum(score_losses) / np.arange(1, n_total + 1)
    n_eligible = int(eligible.sum())

    within_optimal = np.flatnonzero(running_optimal[:n_eligible] <= FROZEN_ALPHA)
    within_scored = np.flatnonzero(running_scored[:n_eligible] <= FROZEN_ALPHA)
    k_oracle = int(within_optimal[-1]) + 1 if within_optimal.size else 0
    k_delivered = int(within_scored[-1]) + 1 if within_scored.size else 0

    # "At the floor" -- the smallest prefix that MEETS the 20% acceptance floor. 0.20 x 1396 is
    # 279.2, so the floor is met at 280, not 279. Both are emitted: the write-up's 18,000/12.9x
    # reconciles at 279 while its 0.0925 is the 280 figure, and hiding that behind one choice is
    # exactly what this artifact exists to stop.
    k_floor = math.ceil(FROZEN_ACCEPTANCE_FLOOR * n_total)
    k_below = k_floor - 1

    def prefix_block(k: int, label: str) -> dict[str, Any]:
        mean_loss = float(optimal[:k].mean())
        radius = _radius(k, CERTIFIED_DELTA)
        budget = FROZEN_ALPHA - mean_loss
        required_k = math.ceil(math.log(2.0 / CERTIFIED_DELTA) / (2.0 * budget * budget))
        required_n = required_k / FROZEN_ACCEPTANCE_FLOOR
        return {
            "k": k,
            "k_definition": label,
            "coverage": k / n_total,
            "empirical_risk_of_loss_optimal_prefix": mean_loss,
            "hoeffding_radius": radius,
            "hoeffding_upper_bound": float(hoeffding_upper(list(optimal[:k]), CERTIFIED_DELTA)),
            "mean_loss_an_accepted_set_may_carry": FROZEN_ALPHA - radius,
            "radius_budget_before_the_bound_crosses_alpha": budget,
            "required_accepted_groups": required_k,
            "required_total_groups": required_n,
            "corpus_multiple": required_n / n_total,
        }

    quantities: dict[str, Any] = {
        "at_the_acceptance_floor": prefix_block(
            k_floor, "ceil(acceptance_floor * n) -- the smallest prefix that MEETS the 0.20 floor"
        ),
        "one_group_below_the_floor": prefix_block(
            k_below,
            "ceil(acceptance_floor * n) - 1 -- does NOT meet the floor. Emitted because the "
            "write-up's 18,000-group and 12.9x figures reconcile here and not at the floor.",
        ),
        "shortfalls": {
            "note": (
                "Differences between three committed acceptance readings, all over the same n. "
                "Each input is itself stamped in calibration_diagnostics.json."
            ),
            "acceptance_empirical_oracle": k_oracle / n_total,
            "acceptance_delivered_empirical": k_delivered / n_total,
            "ranking_cost": (k_oracle - k_delivered) / n_total,
            "ranking_cost_points": 100.0 * (k_oracle - k_delivered) / n_total,
        },
        "certified_acceptance_by_allocation": {},
    }

    for name, delta, allocation in (
        ("per_system", CERTIFIED_DELTA, "delta/3 -- three systems share delta"),
        ("family_wide", FAMILY_DELTA, "delta/(2*9) -- the family-wide Bonferroni allocation"),
    ):
        k_certified = _certified_acceptance(optimal_finite, n_total, FROZEN_ALPHA, delta)
        quantities["certified_acceptance_by_allocation"][name] = {
            "acceptance": k_certified / n_total,
            "k": k_certified,
            "delta": delta,
            "delta_allocation": allocation,
            "construction": "hoeffding_upper on the loss-optimal prefix",
            "n": n_total,
        }

    per_system = quantities["certified_acceptance_by_allocation"]["per_system"]["acceptance"]
    quantities["shortfalls"]["finite_sample_penalty_cost"] = k_oracle / n_total - per_system

    artifact = {
        "schema_version": "1",
        "alpha": FROZEN_ALPHA,
        "acceptance_floor": FROZEN_ACCEPTANCE_FLOOR,
        "delta": FROZEN_DELTA,
        "systems_sharing_delta": SYSTEMS,
        "candidates_per_system": CANDIDATES_PER_SYSTEM,
        "system": args.system,
        "confidence_candidate": args.candidate,
        "n": n_total,
        "eligible_groups": n_eligible,
        "certifies_nothing": True,
        "diagnostic_only": True,
        "interpretation": (
            "Quantities the write-up derives in prose rather than reading off an artifact. The "
            "first paper-scoped claims guard found 53 of 120 figures resolving to nothing, "
            "including the headline 21.6-point ranking gap and the 8.4% family-wide certified "
            "acceptance; these are those figures, computed once, in a committed script, each "
            "stamped with the construction, delta, allocation, n and prefix length that produced "
            "it. Two prefix lengths are emitted because the write-up is NOT internally consistent "
            "about which one 'at the floor' means: 0.0925 is the figure at k = 280, the smallest "
            "prefix meeting the 0.20 floor, while the 18,000-group and 12.9x extrapolation "
            "reconciles at k = 279, which does not meet it. Selecting one here would conceal that. "
            "Nothing here selects a threshold or issues a certificate."
        ),
        "certification_access": access_block(
            certification_access_for("certification", sorted(data.document_ids))
            if hasattr(data, "document_ids")
            else certification_access_for("certification", sorted(groups))
        ),
        "quantities": quantities,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(quantities, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
