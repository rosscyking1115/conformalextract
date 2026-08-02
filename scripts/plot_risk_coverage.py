r"""Draw the write-up's risk-coverage figure: three curves, three ways of failing.

The figure is the paper's argument in one panel. All three curves cover the same population and
differ only in how it is ranked and whether a confidence bound is applied:

* **score-ranked, empirical** -- accept best-scoring groups first, the curve the certifier sweeps;
* **loss-optimal, empirical** -- accept lowest-loss groups first, what a perfect ranking reaches;
* **loss-optimal, certified** -- the same perfect ranking, required to keep its Hoeffding UPPER
  bound within alpha. This is the only one of the three that licenses the word "certified".

Where each crosses the alpha rule is the acceptance it supports: 0.0201, 0.2357 and 0.1139 for the
QLoRA system. **The third is below the acceptance floor**, which is why the figure was redrawn on
2026-08-02: its first version showed only the first two, and an independent review found the paper
reading the empirical oracle as if it were certifiable and concluding the floor "was reachable".
It was not. The distance between curves 1 and 2 is the ranking's; the distance between 2 and 3 is
the finite-sample penalty's; and no curve clears the floor.

**Not part of the certified path.** matplotlib is a `docs` extra, nothing under ``src/`` imports it,
and no test depends on this script. It selects no threshold, issues no certificate and writes no
artifact that any claim cites -- it only redraws committed evidence.

**Reads the guarded loader, not a private re-derivation.** Curves come from
``reanalysis.load_split_system_data``, the same path the certifier and the three ADR 0011 commands
use, so ``assert_reanalysis_role`` refuses ``final``/``shift`` before a file is opened. The
certified curve uses ``certification.hoeffding_upper`` rather than a second implementation of the
bound. The script then **cross-checks its own score curve against the committed**
``alpha_frontier.json`` and refuses to draw on mismatch.

Usage::

    uv run --extra docs python scripts/plot_risk_coverage.py
    uv run --extra docs python scripts/plot_risk_coverage.py --system fs --out fig/fs.pdf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from conformalextract.calibration import CERTIFIED_DELTA
from conformalextract.certification import (
    FROZEN_ACCEPTANCE_FLOOR,
    FROZEN_ALPHA,
    hoeffding_upper,
)
from conformalextract.certification_run import GroupRow
from conformalextract.reanalysis import (
    SYSTEM_IDS,
    load_split_system_data,
)

#: Okabe--Ito, the standard colourblind-safe qualitative palette. Chosen over the default
#: blue/red pair because a paper figure gets printed: under deuteranopia and protanopia a
#: saturated red darkens toward the blue, and the two solid lines were previously separated by
#: HUE ALONE.
SCORE_COLOUR = "#D55E00"  # vermillion
ORACLE_COLOUR = "#0072B2"  # blue

#: Every series also differs in DASH PATTERN, so the figure survives greyscale printing and
#: photocopying with no information lost. The two oracle curves deliberately share a hue -- they
#: are the same ranking under two treatments -- and are separated by pattern; the measured score
#: differs in both. Redundant encoding, per the skill's accessibility guidance.
SCORE_STYLE = "-"
ORACLE_EMPIRICAL_STYLE = (0, (5, 2))
ORACLE_CERTIFIED_STYLE = (0, (3, 1.5, 1, 1.5))

#: Set explicitly rather than inherited, so the figure renders identically on any machine and does
#: not silently change if a matplotlibrc appears.
FONT_SIZES = {
    "font.size": 7,
    "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6,
}

#: Tolerance for the cross-check against the committed frontier artifact. The artifact stores
#: down-sampled curve points as JSON doubles, so exact equality is the wrong test; anything looser
#: than this would stop the check from catching a real disagreement.
CROSS_CHECK_TOLERANCE = 1e-9


def _curves(
    rows: list[GroupRow],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Coverage, score-ranked risk, loss-optimal risk, and the certified loss-optimal bound.

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
    optimal = np.sort(losses)
    certified = np.array(
        [hoeffding_upper(list(optimal[:k]), CERTIFIED_DELTA) for k in range(1, optimal.size + 1)]
    )
    return coverage, np.cumsum(losses) / n, np.cumsum(optimal) / n, certified


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


def _write_greyscale_proof(png: Path) -> None:
    """Desaturate the exported PNG so the dash patterns can be checked without colour.

    A paper figure gets printed and photocopied. Rather than assert that the encoding is
    redundant, this produces the artefact that shows it -- written beside the PNG, not into the
    paper, and never committed.
    """

    from matplotlib import image as mpimg

    rgba = mpimg.imread(png)
    # Rec. 601 luma, the standard perceptual weighting; a plain channel mean would misrepresent
    # how a vermillion and a blue of similar lightness actually print.
    grey = rgba[..., 0] * 0.299 + rgba[..., 1] * 0.587 + rgba[..., 2] * 0.114
    out = png.with_name(png.stem + "-greyscale.png")
    mpimg.imsave(out, grey, cmap="gray", vmin=0.0, vmax=1.0)
    print(json.dumps({"greyscale_proof": str(out)}, sort_keys=True))


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
    parser.add_argument(
        "--greyscale-check",
        action="store_true",
        help="also write a desaturated proof, to confirm the curves separate without colour.",
    )
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

    coverage, scored, optimal, certified = _curves(data.rows)
    _cross_check(args.system, coverage, scored, args.frontier)

    delivered = _crossing(coverage, scored, FROZEN_ALPHA)
    attainable = _crossing(coverage, optimal, FROZEN_ALPHA)
    certifiable = _crossing(coverage, certified, FROZEN_ALPHA)

    plt.rcParams.update(FONT_SIZES)
    # constrained_layout rather than tight_layout: it reserves space for the legend and the
    # annotations as it lays out, instead of shrinking the axes afterwards.
    # SINGLE-COLUMN geometry (3.3 in is the ACL column width), not a full-width figure*.
    # Measured, not preferred: as a figure* spanning both columns this panel cost about seven
    # column-inches of page budget and pushed the Conclusion onto a fifth page. In one column it
    # costs under two. Type is set correspondingly small; at this size the figure is included at
    # its natural width with no further scaling, so these point sizes are what the reader sees.
    fig, ax = plt.subplots(figsize=(3.3, 2.2), constrained_layout=True)
    ax.plot(
        coverage,
        optimal,
        color=ORACLE_COLOUR,
        ls=ORACLE_EMPIRICAL_STYLE,
        lw=1.8,
        label="loss-optimal ranking, empirical",
    )
    ax.plot(
        coverage,
        certified,
        color=ORACLE_COLOUR,
        ls=ORACLE_CERTIFIED_STYLE,
        lw=1.8,
        label="loss-optimal ranking, certified ($\\delta$/3)",
    )
    ax.plot(
        coverage,
        scored,
        color=SCORE_COLOUR,
        ls=SCORE_STYLE,
        lw=2.0,
        label=f"score-ranked ({candidate} logprob)",
    )

    ax.axhline(FROZEN_ALPHA, color="0.35", ls="--", lw=1.0)
    ax.axvline(FROZEN_ACCEPTANCE_FLOOR, color="0.35", ls=":", lw=1.0)
    ax.annotate(
        f"$\\alpha$ = {FROZEN_ALPHA:g}",
        xy=(0.78, FROZEN_ALPHA),
        xytext=(0, 4),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=8,
        color="0.25",
    )
    ax.annotate(
        f"floor {FROZEN_ACCEPTANCE_FLOOR:g}",
        xy=(FROZEN_ACCEPTANCE_FLOOR, 0.97),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=8,
        color="0.25",
        rotation=90,
    )

    # Three crossings, and the point of the panel is that NONE of them reaches the floor line.
    for x, colour in (
        (delivered, SCORE_COLOUR),
        (certifiable, ORACLE_COLOUR),
        (attainable, ORACLE_COLOUR),
    ):
        ax.plot([x], [FROZEN_ALPHA], marker="o", ms=5, color=colour, zorder=5)
    for x, text, colour, dy in (
        # Staggered: the first two crossings sit close together on x, so a single row of labels
        # collides once the figure is scaled into a two-column page.
        (delivered, f"{delivered:.3f}", SCORE_COLOUR, -10),
        (certifiable, f"{certifiable:.3f}", ORACLE_COLOUR, -19),
        (attainable, f"{attainable:.3f}", ORACLE_COLOUR, -10),
    ):
        ax.annotate(
            text,
            xy=(x, FROZEN_ALPHA),
            xytext=(3, dy),
            textcoords="offset points",
            fontsize=8,
            color=colour,
            ha="left",
        )
    # The two gap figures used to be drawn here as an arrow plus a caption. Removed: in a
    # shorter, full-width panel they crowded the x-axis, and a derived number belongs in the
    # figure caption anyway, where it can be stated in words. The three crossings stay, because
    # those are read off the axes.

    ax.set_xlabel("coverage (share of all groups accepted)")
    ax.set_ylabel("risk among accepted groups")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.28),
        ncol=1,
        fontsize=6,
        frameon=False,
        handlelength=2.4,
    )
    ax.spines[["top", "right"]].set_visible(False)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # PDF is the one the paper includes: vector, so it stays sharp at any zoom and carries no dpi.
    fig.savefig(args.out, bbox_inches="tight")
    # PNG is for review and for anything that cannot take a PDF. 300 dpi and an explicit white
    # facecolor, so it does not come out transparent-on-black in a dark viewer.
    fig.savefig(args.out.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white")
    if args.greyscale_check:
        _write_greyscale_proof(args.out.with_suffix(".png"))
    plt.close(fig)
    print(
        json.dumps(
            {
                "out": str(args.out),
                "system": args.system,
                "confidence_candidate": candidate,
                "delivered_at_alpha_empirical": delivered,
                "attainable_empirical": attainable,
                "attainable_certified": certifiable,
                "gap_ranking": attainable - delivered,
                "gap_finite_sample": attainable - certifiable,
                # Named precisely, because "a curve clears the floor" is the ambiguity that
                # produced the refuted claim: the EMPIRICAL oracle does and the certified one
                # does not, and only the second bears on whether anything could be certified.
                "empirical_oracle_clears_floor": bool(attainable >= FROZEN_ACCEPTANCE_FLOOR),
                "certified_oracle_clears_floor": bool(certifiable >= FROZEN_ACCEPTANCE_FLOOR),
                "cross_check": f"agrees with {args.frontier}",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
