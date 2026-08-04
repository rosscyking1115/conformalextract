r"""How large a corpus this loss profile would need before a certificate exists at all.

**Why.** The abstract says the corpus "would need to be roughly 13$\times$ larger before that gap
could close". That figure closes the **risk test** only. A certificate has to clear two constraints,
and the second one behaves in a way nobody in this project had checked: the acceptance floor is
tested on a Clopper-Pearson **lower** bound, and at *exactly* the floor coverage that bound
approaches the floor from below and never reaches it, at any $n$. So the honest question is not
"how much data closes the gap" but "is there a corpus size at which a certificate exists, and what
coverage does it need".

Three things are computed, each stamped with the configuration that produced it:

1. **The convergence curve.** The acceptance lower bound at exactly 20% coverage, across corpus
   sizes. It rises monotonically toward 0.20 and stays under it. This is not an empirical accident:
   the bound is a one-sided confidence limit on a proportion whose point estimate *is* the floor, so
   it lies strictly below the floor for every finite sample. **No corpus of any size certifies at
   exactly the floor coverage.** A certificate needs coverage strictly above it.
2. **The smallest corpus that admits a certificate**, searched over both constraints jointly, and
   the coverage it requires.
3. **The k = 332 witness at the observed corpus**, which is the smallest prefix at $n = 1{,}396$
   that clears the acceptance floor, and the mean loss such a prefix could carry.

**The extrapolation, stated because it is an assumption and not a measurement.** Sizes beyond the
observed 1,396 groups hold the *loss profile* fixed: the mean loss of the best $c$-fraction is read
off the observed distribution and applied at the larger $n$. That answers "what if there were more
data like this", which is the question the abstract's sentence asks. It is not a prediction about
any real larger corpus, and a corpus with a different loss profile has a different answer.

**Diagnostic only.** Selects no threshold, issues no certificate, changes no frozen parameter. $0:
CPU over predictions and gold already on disk, on the already-open certification split; the loader
is the re-analysis loader, so ``assert_reanalysis_role`` refuses ``final``/``shift`` before a file
is opened.

Usage::

    uv run python scripts/corpus_size_requirement.py
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
    clopper_pearson_lower,
    hoeffding_upper,
)
from conformalextract.reanalysis import (
    access_block,
    certification_access_for,
    load_split_system_data,
)

SYSTEMS = 3
CANDIDATES_PER_SYSTEM = 3
CERTIFIED_DELTA = FROZEN_DELTA / SYSTEMS
#: The tail mass the certifier hands Clopper-Pearson: delta/(16 * candidates), per
#: ``certification.scorc_certificate``. Read off the code, not assumed.
CP_TAIL = CERTIFIED_DELTA / (16.0 * CANDIDATES_PER_SYSTEM)

CONVERGENCE_SIZES = (1396, 2792, 5000, 18740, 29926, 100_000, 1_000_000, 10_000_000)


def radius(k: int, delta: float) -> float:
    """The Hoeffding half-width, as ``certification.hoeffding_upper`` computes it."""

    return float(hoeffding_upper([0.0] * k, delta))


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
        "--out", type=Path, default=Path("evidence/plan3/corpus_size_requirement.json")
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
    n_observed = len(rows)
    losses = np.asarray([r.loss for r in rows], dtype=np.float64)
    scores = np.asarray([r.score for r in rows], dtype=np.float64)
    eligible = np.asarray([r.all_valid for r in rows]) & np.isfinite(scores)
    sorted_eligible = np.sort(losses[eligible])
    n_eligible = int(sorted_eligible.size)
    eligible_fraction = n_eligible / n_observed

    cumulative = np.cumsum(sorted_eligible)

    def profile_mean(coverage: float, *, interpolate: bool) -> float | None:
        """Mean loss of the best ``coverage`` fraction, read off the observed distribution.

        Coverage is a share of ALL groups, so it is converted to a share of the eligible pool
        before indexing --- ineligible groups can never be accepted at any corpus size.

        **Two treatments, because the answer depends on the choice and the choice is not a
        measurement.** ``interpolate=False`` rounds to a whole observed group; ``True`` takes a
        fractional last group. Both are defensible readings of "the same loss profile at a larger
        n", they differ by about 1.5% in the threshold below, and reporting either alone as a point
        would present a modelling decision as a finding.
        """

        position = coverage / eligible_fraction * n_eligible
        if position > n_eligible:
            return None
        if not interpolate:
            take = max(1, round(position))
            return float(sorted_eligible[:take].mean())
        whole = max(1, math.floor(position))
        total = float(cumulative[whole - 1])
        if whole < n_eligible:
            total += (position - whole) * float(sorted_eligible[whole])
        return total / max(position, 1.0)

    # --- 1. the convergence curve at EXACTLY the floor coverage --------------------------------
    convergence = []
    for n in CONVERGENCE_SIZES:
        k = round(FROZEN_ACCEPTANCE_FLOOR * n)
        lower = clopper_pearson_lower(k, n, CP_TAIL)
        convergence.append(
            {
                "n": n,
                "k_at_exactly_the_floor_coverage": k,
                "acceptance_lower_bound": lower,
                "clears_acceptance_floor": bool(lower >= FROZEN_ACCEPTANCE_FLOOR),
                "shortfall": FROZEN_ACCEPTANCE_FLOOR - lower,
            }
        )

    # --- 2. the smallest corpus admitting a certificate, over BOTH constraints -----------------
    def certifies(n: int, *, interpolate: bool) -> dict[str, Any] | None:
        """Best feasible prefix at corpus size ``n``, or None if no prefix clears both tests."""

        k_low = math.ceil(FROZEN_ACCEPTANCE_FLOOR * n)
        k_high = math.floor(eligible_fraction * n)
        for k in range(k_low, k_high + 1):
            if clopper_pearson_lower(k, n, CP_TAIL) < FROZEN_ACCEPTANCE_FLOOR:
                continue  # acceptance rises with k, so this only skips the low end
            mean = profile_mean(k / n, interpolate=interpolate)
            if mean is None:
                break
            if mean + radius(k, CERTIFIED_DELTA) <= FROZEN_ALPHA:
                return {
                    "k": k,
                    "coverage": k / n,
                    "prefix_mean_loss": mean,
                    "risk_upper_bound": mean + radius(k, CERTIFIED_DELTA),
                    "acceptance_lower_bound": clopper_pearson_lower(k, n, CP_TAIL),
                }
        return None

    def smallest_for(interpolate: bool) -> dict[str, Any] | None:
        low, high = n_observed, 2_000_000
        if certifies(high, interpolate=interpolate) is None:
            return None
        while low < high:
            mid = (low + high) // 2
            if certifies(mid, interpolate=interpolate) is None:
                low = mid + 1
            else:
                high = mid
        found = certifies(low, interpolate=interpolate) or {}
        return {"n": low, **found, "multiple_of_observed_corpus": low / n_observed}

    rounded = smallest_for(False)
    interpolated = smallest_for(True)
    smallest: dict[str, Any] = {
        "_notice": (
            "A BAND, NOT A POINT, and the reason is the reason the cost figure is a band: the "
            "endpoints differ only by a modelling choice the data does not settle. Rounding the "
            "loss profile to a whole observed group and interpolating a fractional one are both "
            "defensible readings of 'the same profile at a larger n' and they disagree by about "
            "1.5%. An independent reviewer's own derivation landed at 29,926 (21.4x), a third "
            "point in the same band. Publishing any single endpoint would present a modelling "
            "decision as a measurement, which is this project's recorded defect class."
        ),
        "profile_rounded_to_whole_group": rounded,
        "profile_interpolated": interpolated,
        "band_n": [rounded["n"], interpolated["n"]] if rounded and interpolated else None,
        "band_multiple_of_observed_corpus": (
            [rounded["multiple_of_observed_corpus"], interpolated["multiple_of_observed_corpus"]]
            if rounded and interpolated
            else None
        ),
        "what_is_robust": (
            "The ORDER of the answer, not its third significant figure: roughly 21x the observed "
            "corpus, and - unlike the withdrawn 13x - only at coverage STRICTLY ABOVE the floor. "
            "The structural fact needs no extrapolation at all and is exact: at exactly the floor "
            "coverage the acceptance lower bound is below the floor at every n."
        ),
    }

    # --- 3. the witness at the OBSERVED corpus -------------------------------------------------
    k_floor_lcb = next(
        k
        for k in range(1, n_observed + 1)
        if clopper_pearson_lower(k, n_observed, CP_TAIL) >= FROZEN_ACCEPTANCE_FLOOR
    )
    witness = {
        "k": k_floor_lcb,
        "coverage": k_floor_lcb / n_observed,
        "acceptance_lower_bound": clopper_pearson_lower(k_floor_lcb, n_observed, CP_TAIL),
        "hoeffding_radius": radius(k_floor_lcb, CERTIFIED_DELTA),
        "mean_loss_a_certifying_prefix_may_carry": (
            FROZEN_ALPHA - radius(k_floor_lcb, CERTIFIED_DELTA)
        ),
        "observed_prefix_mean_loss": profile_mean(
            k_floor_lcb / n_observed, interpolate=False
        ),
        "note": (
            "The smallest prefix at the observed corpus that clears the ACCEPTANCE floor on its "
            "Clopper-Pearson lower bound. A witness for 'some model could certify here' must clear "
            "BOTH tests, so it must be stated at this k and this ceiling - not at the 20%-coverage "
            "prefix, which clears the risk test and fails acceptance at 0.16566."
        ),
    }
    witness["exists_a_certifying_model"] = bool(
        witness["mean_loss_a_certifying_prefix_may_carry"] > 0.0
        and witness["acceptance_lower_bound"] >= FROZEN_ACCEPTANCE_FLOOR
    )

    artifact = {
        "schema_version": "1",
        "alpha": FROZEN_ALPHA,
        "acceptance_floor": FROZEN_ACCEPTANCE_FLOOR,
        "delta": FROZEN_DELTA,
        "delta_allocation": CERTIFIED_DELTA,
        "clopper_pearson_tail_mass": CP_TAIL,
        "candidates_per_system": CANDIDATES_PER_SYSTEM,
        "systems_sharing_delta": SYSTEMS,
        "system": args.system,
        "confidence_candidate": args.candidate,
        "observed_n": n_observed,
        "observed_eligible": n_eligible,
        "risk_construction": "hoeffding_upper at delta/3",
        "acceptance_construction": "clopper_pearson_lower at delta/(16 * candidates)",
        "certifies_nothing": True,
        "diagnostic_only": True,
        "cost_usd": 0.0,
        "extrapolation_assumption": (
            "Corpus sizes beyond the observed 1,396 hold the LOSS PROFILE fixed: the mean loss of "
            "the best c-fraction is read off the observed distribution and applied at the larger "
            "n. This answers 'what if there were more data like this', which is the question the "
            "write-up's sentence asks. It is NOT a prediction about any real larger corpus, and a "
            "corpus with a different loss profile has a different answer."
        ),
        "interpretation": (
            "The write-up said the corpus would need to be roughly 13x larger before the gap could "
            "close. That closes the RISK test only. The acceptance floor is tested on a "
            "Clopper-Pearson LOWER bound, and at exactly the floor coverage that bound approaches "
            "the floor from below and never reaches it at any n - so NO corpus of any size "
            "certifies at exactly 20% coverage, and a certificate requires coverage strictly "
            "above the floor. The smallest corpus admitting one, and the coverage it needs, are "
            "computed here over BOTH constraints jointly."
        ),
        "certification_access": access_block(
            certification_access_for("certification", sorted(groups))
        ),
        "acceptance_lower_bound_at_exactly_the_floor_coverage": convergence,
        "smallest_corpus_admitting_a_certificate": smallest,
        "witness_at_the_observed_corpus": witness,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("convergence at exactly 20% coverage:")
    for row in convergence:
        print(f"  n={row['n']:>10}  lower={row['acceptance_lower_bound']:.5f}"
              f"  clears={row['clears_acceptance_floor']}")
    print("\nsmallest corpus admitting a certificate (BAND):",
          smallest["band_n"], smallest["band_multiple_of_observed_corpus"])
    print("\nwitness at the observed corpus:", json.dumps(witness, indent=2))


if __name__ == "__main__":
    main()
