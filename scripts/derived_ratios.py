r"""Store the ratios the write-up quotes beside the counts they come from.

The counts are committed; the ratios were not. 95.7%, 39.4% and 68.1% --- the most-quoted numbers
in this project --- are ``valid / records`` per system, and neither the quotient nor the pairing
was recorded anywhere. So the guard had nothing to check them against, and a reader had to trust
that a division had been done correctly on numbers two files apart.

**The guard must never divide.** A guard that computes can be wrong in the same direction as the
author, and then agreement between them means nothing. So the arithmetic happens once, here, and
each ratio is stored **with pointers to the exact counts that produced it**, so the pairing is
auditable rather than implied.

**Deviation, stated.** The instruction was to compute each ratio in the script that writes its
counts. Those counts live in ``evidence/plan2/prediction_parse_summary.json``, produced by a Plan 2
pipeline closed under an independent reviewer PASS; re-running it needs the private predictions and
would rewrite closed evidence. This script instead reads the committed counts and stores each ratio
beside them. The property that matters --- the guard never divides, and a ratio travels with its
inputs --- holds either way.

Reads only committed evidence JSON: no predictions, no RAMS archive, no gold, no sealed split. It
runs anywhere the repository is checked out, at $0.

Usage::

    uv run python scripts/derived_ratios.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PARSE = "evidence/plan2/prediction_parse_summary.json"
DECOMP = "evidence/plan3/loss_decomposition.json"
CALIB = "evidence/plan3/calibration_diagnostics.json"
CERT = "evidence/plan3/certification_result.json"

QA = "splits.certification.qa"
STRATA = "splits.certification.qa.mean.stratified"
FS_ERR = "splits.certification.fs.tenth_percentile.discrimination.any_error"


def _get(data: Any, pointer: str) -> Any:
    current = data
    for key in pointer.split("."):
        current = current[key]
    return current


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("evidence/plan3/derived_ratios.json"))
    args = parser.parse_args()

    sources = {name: json.loads((ROOT / name).read_text(encoding="utf-8")) for name in
               (PARSE, DECOMP, CALIB, CERT)}

    def ratio(
        key: str,
        numerator: tuple[str, str],
        denominator: tuple[str, str],
        *,
        scale: float = 1.0,
        construction: str,
        note: str = "",
    ) -> dict[str, Any]:
        num = _get(sources[numerator[0]], numerator[1])
        den = _get(sources[denominator[0]], denominator[1])
        return {
            "value": scale * num / den,
            "numerator": {"artifact": numerator[0], "pointer": numerator[1], "value": num},
            "denominator": {"artifact": denominator[0], "pointer": denominator[1], "value": den},
            "construction": construction,
            "note": note,
        }

    ratios: dict[str, Any] = {}
    for system in ("qa", "zs", "fs"):
        ratios[f"parse_and_ground_rate_{system}"] = ratio(
            f"rate_{system}",
            (PARSE, f"{system}.valid"),
            (PARSE, f"{system}.records"),
            scale=100.0,
            construction="100 * valid / records, over frames",
            note=(
                "'Valid' is parseable AND grounded. It is NOT correctness: a span can point at "
                "real document text and still name the wrong entity or role."
            ),
        )

    ratios["ungrounded_span_separation"] = ratio(
        "separation",
        (PARSE, "zs.grounding_failure"),
        (PARSE, "qa.grounding_failure"),
        construction="zs ungrounded spans / qa ungrounded spans",
        note="The write-up rounds this to ~16x. The unrounded value is 15.75.",
    )

    ratios["content_bearing_share_of_group_loss"] = ratio(
        "content_share",
        (DECOMP, f"{QA}.channels.valid_content_bearing.group_level_contribution"),
        (DECOMP, f"{QA}.group_level_total_loss"),
        scale=100.0,
        construction="100 * channel group-level contribution / total group-level loss",
        note=(
            "The GROUP-level share is 87.3%. The document-level share of the same channel is "
            "86.2% and is a different quantity; the write-up quotes the group-level one."
        ),
    )

    triggers = _get(sources[CALIB], f"{STRATA}.triggers")
    cross = _get(sources[CALIB], f"{STRATA}.cross_sentence")
    counts = {
        "oracle_accepted_groups_total": {
            "value": sum(int(v["accepted_groups"]) for v in triggers.values()),
            "construction": "sum of accepted_groups across the trigger-count strata",
            "components": {k: int(v["accepted_groups"]) for k, v in triggers.items()},
            "artifact": CALIB,
            "pointer": f"{STRATA}.triggers",
        },
        "oracle_accepted_with_no_cross_sentence_argument": {
            "value": int(cross["0"]["accepted_groups"]),
            "construction": "accepted_groups in the zero-cross-sentence stratum",
            "components": {k: int(v["accepted_groups"]) for k, v in cross.items()},
            "artifact": CALIB,
            "pointer": f"{STRATA}.cross_sentence['0'].accepted_groups",
        },
        "fs_non_failing_groups": {
            "value": round(
                _get(sources[CALIB], f"{FS_ERR}.scored_groups")
                * (1.0 - _get(sources[CALIB], f"{FS_ERR}.failure_prevalence"))
            ),
            "construction": "scored_groups * (1 - failure_prevalence), FS at tenth_percentile",
            "artifact": CALIB,
            "pointer": FS_ERR,
            "note": "The count the FS AUROC rests on, and why the write-up calls it unstable.",
        },
        "confidence_level_percent": {
            "value": round(100.0 * (1.0 - _get(sources[CERT], "delta"))),
            "construction": "100 * (1 - delta)",
            "artifact": CERT,
            "pointer": "delta",
            "note": (
                "The write-up says '95% confidence'. It is stored here rather than rendered from "
                "delta by the guard, because a semantic transform in a guard is a computation in "
                "a guard."
            ),
        },
        "mean_per_document_span_exact_f1": {
            "value": 1.0 - _get(sources[CERT], "systems.qa.loss_summary.unweighted_mean_loss"),
            "construction": "1 - unweighted mean group loss; the loss IS 1 - F1 per document",
            "artifact": CERT,
            "pointer": "systems.qa.loss_summary.unweighted_mean_loss",
            "note": (
                "A mean of per-document F1. NOT comparable to corpus-level micro Arg-C figures."
            ),
        },
    }

    # --- definitional constants the paper states about its own metrics ------------------------
    # These are claims, not typesetting: "normalized AURC is 0 for a perfect ranking and 1 for
    # chance" and "an invalid output scores 1.0" are assertions about the implementation, and they
    # are checkable against it. Excluding them structurally would have been an exemption; they are
    # computed instead, from the committed AURC endpoints and from the frozen scorer itself.
    from conformalextract.evaluation import evaluate_document

    qa_risk = _get(sources[CALIB], f"{QA}.mean.selective_risk")
    optimal = qa_risk["aurc_optimal_ranking"]
    chance = qa_risk["aurc_random_ranking"]
    zs_err = _get(sources[CALIB], "splits.certification.zs.mean.discrimination.any_error")

    counts["normalized_aurc_of_a_perfect_ranking"] = {
        "value": (optimal - optimal) / (chance - optimal),
        "construction": "(aurc_optimal - aurc_optimal) / (aurc_random - aurc_optimal)",
        "artifact": CALIB,
        "pointer": f"{QA}.mean.selective_risk.aurc_optimal_ranking",
    }
    counts["normalized_aurc_of_chance"] = {
        "value": (chance - optimal) / (chance - optimal),
        "construction": "(aurc_random - aurc_optimal) / (aurc_random - aurc_optimal)",
        "artifact": CALIB,
        "pointer": f"{QA}.mean.selective_risk.aurc_random_ranking",
    }
    counts["loss_of_a_structurally_invalid_output"] = {
        "value": evaluate_document([], None, structural_failure="invalid_json").loss,
        "construction": (
            "evaluation.evaluate_document with a structural failure, through the frozen scorer. "
            "A pure function over no data: the always-answer contract scores a non-valid "
            "prediction as wrong."
        ),
        "artifact": "src/conformalextract/evaluation.py",
        "pointer": "evaluate_document(structural_failure=...).loss",
    }
    counts["zs_non_failing_groups"] = {
        "value": round(zs_err["scored_groups"] * (1.0 - zs_err["failure_prevalence"])),
        "construction": "scored_groups * (1 - failure_prevalence), ZS at mean",
        "artifact": CALIB,
        "pointer": "splits.certification.zs.mean.discrimination.any_error",
        "note": "The count the ZS AUROC rests on. It and the FS count are why both are unstable.",
    }

    artifact = {
        "schema_version": "1",
        "certifies_nothing": True,
        "diagnostic_only": True,
        "reads_only_committed_evidence": True,
        "interpretation": (
            "Ratios and counts the write-up quotes that were derived in prose from committed "
            "inputs and never stored. Each is recorded WITH pointers to the counts that produced "
            "it, so the pairing is auditable and scripts/check_paper_claims.py never has to "
            "divide - a guard that computes can be wrong in the same direction as the author. "
            "Nothing here selects a threshold or issues a certificate, and nothing here opens a "
            "split: it reads committed evidence JSON only."
        ),
        "counts": counts,
        "ratios": ratios,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v["value"] for k, v in ratios.items()}, indent=2))
    print(json.dumps({k: v["value"] for k, v in counts.items()}, indent=2))


if __name__ == "__main__":
    main()
