r"""Recompute false positives and false negatives per system, and store the difference beside them.

**Why.** The write-up says false positives exceed false negatives by 637 arguments, and calls that
over-generation rather than entity-naming. It is a load-bearing sentence --- it is the measurement
that replaced a withdrawn error-category attribution --- and until now it appeared in no artifact
anywhere: only in prose, a claim ledger and reviewer records. The first paper-scoped guard run
reported it unbacked.

The two counts come from ``evaluation.evaluate_document``, which the certifier itself uses, so this
is a re-read of the frozen scorer rather than a second implementation. The difference is stored
here beside the counts so that ``scripts/check_paper_claims.py`` never has to subtract: a guard
that computes can be wrong in the same direction as the author.

**Scope, stated.** Counts are over the CONTENT-BEARING channel --- documents whose prediction is
valid, grounded and carries at least one argument --- because that is the population the sentence
is about. Documents in the other three channels are excluded and counted separately, so the
denominator is visible rather than implied.

**Cost: $0.** Pure CPU over predictions and gold already on disk, on the certification and
development splits, both of which are already open. The loader is the re-analysis loader, so
``assert_reanalysis_role`` refuses ``final``/``shift`` before a file is opened. No GPU, no network,
no job submission.

Usage::

    uv run python scripts/argument_error_counts.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from conformalextract.evaluation import evaluate_document
from conformalextract.reanalysis import (
    CONTENT_CHANNEL,
    access_block,
    assert_reanalysis_role,
    certification_access_for,
    loss_channel,
)

SYSTEMS = ("zs", "fs", "qa")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="certification")
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
        "--out", type=Path, default=Path("evidence/plan3/argument_error_counts.json")
    )
    args = parser.parse_args()

    from conformalextract.cli import _reanalysis_inputs

    instances, contexts, assignments, gold_frames, _gate = _reanalysis_inputs(
        args.rams_archive, args.role_map, args.development_gate
    )
    groups = {
        str(a["document_id"]): str(a["group_id"])
        for a in assignments
        if a["role"] == args.split
    }

    from conformalextract.predictions import parse_arm, read_prediction_jsonl

    # The same door to gold every re-analysis command uses, so no caller routes around it.
    assert_reanalysis_role(args.split)

    systems: dict[str, Any] = {}
    for system in SYSTEMS:
        raw = read_prediction_jsonl(args.predictions_dir / f"{system}.v1.jsonl")
        parsed, _ = parse_arm(raw, contexts, confidence_candidate=args.candidate)
        selected = [p for p in parsed if p.document_id in groups]

        false_positives = 0
        false_negatives = 0
        true_positives = 0
        documents = 0
        excluded = 0
        for record in selected:
            if loss_channel(record) != CONTENT_CHANNEL:
                excluded += 1
                continue
            # Mirrors development_gate.document_loss: content is scored only when the document
            # is valid, so a failure is never rewarded for frames it did not really produce.
            result = evaluate_document(gold_frames(instances[record.document_id]), record.frames)
            false_positives += result.false_positives
            false_negatives += result.false_negatives
            true_positives += result.true_positives
            documents += 1
        systems[system] = {
            "documents_in_content_channel": documents,
            "documents_excluded_other_channels": excluded,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "false_positive_excess": false_positives - false_negatives,
            "construction": (
                "evaluation.evaluate_document per document over the content-bearing channel; "
                "excess is false_positives - false_negatives, stored so no guard has to subtract"
            ),
        }

    artifact = {
        "schema_version": "1",
        "split": args.split,
        "confidence_candidate": args.candidate,
        "channel": CONTENT_CHANNEL,
        "certifies_nothing": True,
        "diagnostic_only": True,
        "cost_usd": 0.0,
        "interpretation": (
            "False positives against false negatives over the content-bearing channel. The excess "
            "is what licenses calling the residual loss OVER-GENERATION rather than an "
            "error-category attribution -- the wording that replaced a withdrawn claim about "
            "'naming the wrong entity'. It is descriptive: it selects no threshold, certifies "
            "nothing, and identifies no error category either. Counts come from the frozen "
            "scorer the certifier uses, not a second implementation."
        ),
        "certification_access": access_block(
            certification_access_for(args.split, sorted(groups))
        ),
        "systems": systems,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({s: v["false_positive_excess"] for s, v in systems.items()}, indent=2))


if __name__ == "__main__":
    main()
