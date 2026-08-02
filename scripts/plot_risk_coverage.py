r"""Draw the write-up's risk-coverage figure: what the score delivered against what was there.

The figure is the paper's argument in one panel. Two curves over the same population, differing
only in how it is ranked:

* **score-ranked** -- accept best-scoring groups first, the curve the certifier actually sweeps;
* **loss-optimal** -- accept lowest-loss groups first, what a perfect ranking would have reached.

With the alpha = 0.20 and acceptance-floor = 0.20 rules drawn in, the two cross the floor line at
0.0201 and 0.2357 for the QLoRA system, and the distance between those crossings is the finding:
the target was reachable by ranking alone and the score reached less than a tenth of it.

**Not part of the certified path.** matplotlib is a `docs` extra, nothing under ``src/`` imports it,
and no test depends on this script. It selects no threshold, issues no certificate and writes no
artifact that any claim cites -- it only redraws committed evidence.

**Reads the guarded loader, not a private re-derivation.** Curves come from
``reanalysis.load_split_system_data``, the same path the certifier and the three ADR 0011 commands
use, so ``assert_reanalysis_role`` refuses ``final``/``shift`` before a file is opened. The script
then **cross-checks its own score curve against the committed** ``alpha_frontier.json`` and refuses
to draw on mismatch, so the figure cannot quietly disagree with the artifact it illustrates.

Usage::

    uv run --extra docs python scripts/plot_risk_coverage.py
    uv run --extra docs python scripts/plot_risk_coverage.py --system fs --out fig/fs.pdf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from conformalextract.certification import FROZEN_ACCEPTANCE_FLOOR, FROZEN_ALPHA
from conformalextract.certification_run import GroupRow
from conformalextract.reanalysis import (
    SYSTEM_IDS,
    load_split_system_data,
)

#: Tolerance for the cross-check against the committed frontier artifact. The artifact stores
#: down-sampled curve points as JSON doubles, so exact equality is the wrong test; anything looser
#: than this would stop the check from catching a real disagreement.
CROSS_CHECK_TOLERANCE = 1e-9


def _curves(rows: list[GroupRow]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Coverage, score-ranked running risk, and loss-optimal running risk.

    Eligibility, sort order and the coverage denominator are the certifier's
    (``certification_run._curve_arrays``): only all-valid finitely-scored groups can be accepted,
    and coverage is a share of ALL groups so ineligible ones dilute it.
    """

    total = len(rows)
    eligible = sorted(
        (r for r in rows if r.all_valid and np.isfinite(r.score)), key=lambda r: -r.score
    )
    losses = np.asarray([r.loss for r in eligible], dtype=np.float64)
    n = np.arange(1, losses.size + 1)
    coverage = n / total
    return coverage, np.cumsum(losses) / n, np.cumsum(np.sort(losses)) / n


def _crossing(coverage: np.ndarray, risk: np.ndarray, alpha: float) -> float:
    within = np.flatnonzero(risk <= alpha)
    return float(coverage[int(within[-1])]) if within.size else 0.0


def _cross_check(system: str, coverage: np.ndarray, risk: np.ndarray, frontier: Path) -> None:
    """Refuse to draw if the recomputed score curve disagrees with the committed artifact."""

    published = json.loads(frontier.read_text(encoding="utf-8"))
    samples = published["splits"]["certification"][system]["curve"]
    for point in samples:
        index = int(np.argmin(np.abs(coverage - point["coverage"])))
        if abs(float(risk[index]) - point["running_risk"]) > CROSS_CHECK_TOLERANCE:
            raise SystemExit(
                f"{system}: recomputed curve disagrees with {frontier} at coverage "
                f"{point['coverage']:.6f} (artifact {point['running_risk']:.9f}, "
                f"recomputed {float(risk[index]):.9f}). Refusing to draw a figure that "
                f"contradicts committed evidence."
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="qa", choices=SYSTEM_IDS)
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
    parser.add_argument("--frontier", type=Path, default=Path("evidence/plan3/alpha_frontier.json"))
    parser.add_argument("--out", type=Path, default=Path("docs/writeup/fig/risk-coverage-qa.pdf"))
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Imported here rather than at module scope: this pulls the CLI's shared RAMS loading path,
    # which is heavy, and the script should fail on a bad --system before paying for it.
    from conformalextract.cli import _reanalysis_inputs

    instances, contexts, assignments, gold_frames, gate = _reanalysis_inputs(
        args.rams_archive, args.role_map, args.development_gate
    )
    groups = {
        str(a["document_id"]): str(a["group_id"])
        for a in assignments
        if a["role"] == "certification"
    }
    candidate = str(gate["per_system"][args.system]["selected_candidate"])
    data = load_split_system_data(
        split_role="certification",
        system_id=args.system,
        confidence_candidate=candidate,
        predictions_path=args.predictions_dir / f"{args.system}.v1.jsonl",
        contexts=contexts,
        instances=instances,
        group_by_document=groups,
        gold_frames=gold_frames,
    )

    coverage, scored, optimal = _curves(data.rows)
    _cross_check(args.system, coverage, scored, args.frontier)

    delivered = _crossing(coverage, scored, FROZEN_ALPHA)
    attainable = _crossing(coverage, optimal, FROZEN_ALPHA)

    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    ax.plot(coverage, optimal, color="#4c72b0", lw=1.8, label="loss-optimal ranking (oracle)")
    ax.plot(coverage, scored, color="#c44e52", lw=1.8, label=f"score-ranked ({candidate} logprob)")

    ax.axhline(FROZEN_ALPHA, color="0.35", ls="--", lw=1.0)
    ax.axvline(FROZEN_ACCEPTANCE_FLOOR, color="0.35", ls=":", lw=1.0)
    ax.annotate(
        f"target risk $\\alpha$ = {FROZEN_ALPHA:g}",
        xy=(0.985, FROZEN_ALPHA),
        xytext=(0, 4),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=8,
        color="0.25",
    )
    ax.annotate(
        f"acceptance floor {FROZEN_ACCEPTANCE_FLOOR:g}",
        xy=(FROZEN_ACCEPTANCE_FLOOR, 0.97),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=8,
        color="0.25",
        rotation=90,
    )

    # The two crossings and the gap between them are the whole point of the panel, so they are
    # marked rather than left for the reader to measure off the axis.
    for x, colour in ((delivered, "#c44e52"), (attainable, "#4c72b0")):
        ax.plot([x], [FROZEN_ALPHA], marker="o", ms=5, color=colour, zorder=5)
    # Three annotations share this corner and will collide if they are not given separate bands:
    # the crossing labels sit just under the alpha rule, the arrow below them, its caption below
    # that. Measured against the drawn figure rather than guessed.
    ax.annotate(
        f"{delivered:.4f}",
        xy=(delivered, FROZEN_ALPHA),
        xytext=(3, -13),
        textcoords="offset points",
        fontsize=8,
        color="#c44e52",
        ha="left",
    )
    ax.annotate(
        f"{attainable:.4f}",
        xy=(attainable, FROZEN_ALPHA),
        xytext=(3, -13),
        textcoords="offset points",
        fontsize=8,
        color="#4c72b0",
        ha="left",
    )
    ax.annotate(
        "",
        xy=(attainable, FROZEN_ALPHA - 0.085),
        xytext=(delivered, FROZEN_ALPHA - 0.085),
        arrowprops={"arrowstyle": "<->", "color": "0.3", "lw": 0.9},
    )
    # Left-anchored at the delivered crossing, not centred on the arrow: centring pushes the
    # string past the y-axis whenever the left crossing is near zero, which is exactly the case
    # this figure exists to show.
    ax.annotate(
        f"{attainable - delivered:.3f} of acceptance lost to ranking",
        xy=(delivered, FROZEN_ALPHA - 0.105),
        ha="left",
        va="top",
        fontsize=8,
        color="0.25",
    )

    ax.set_xlabel("coverage (share of all groups accepted)")
    ax.set_ylabel("risk among accepted groups")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "system": args.system,
                "confidence_candidate": candidate,
                "delivered_at_alpha": delivered,
                "attainable_under_loss_optimal_ranking": attainable,
                "gap": attainable - delivered,
                "cross_check": f"agrees with {args.frontier}",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
