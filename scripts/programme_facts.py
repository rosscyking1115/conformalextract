r"""Programme facts whose inputs are committed as PROSE, computed here and stored with provenance.

Four figures the write-up quotes --- the serving-stack parity, the two abstain/extract flip rates,
and the cost band --- resolved to no artifact when the paper-scoped guard first ran. A search of
``evidence/*.json`` found nothing, and that search was reported as a verdict. It was wrong: the
inputs are all committed, in **Markdown**. The population was the error, not the query.

So this script does two separable things and keeps them separable:

* **Transcribes** the counts from the committed documents that record them, carrying the document
  path and the sentence each was read from. A transcription is not a computation and does not
  pretend to be one --- same discipline as ``evidence/plan4/external_citations.json``.
* **Computes** the derived figures from those counts, and stores each beside the counts that
  produced it, so ``scripts/check_paper_claims.py`` never has to divide.

The Wilson interval is **recomputed** from the transcribed counts rather than transcribed, because
that is a check on the transcription: if the recomputed interval disagreed with the one the probe
document states, one of the two would be wrong and this script would say so.

Reads committed Markdown and writes JSON. No predictions, no gold, no split of any kind, $0.

Usage::

    uv run python scripts/programme_facts.py
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = "docs/plan2/serving-equivalence-probe-result.md"
COST_ADR = "docs/adr/0012-cost-claim-evidence-correction.md"

Z_95 = 1.959963984540054


def wilson(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval, recomputed as a check on the transcribed one."""

    proportion = successes / total
    denominator = 1.0 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    half = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total))
        / denominator
    )
    return 100.0 * (centre - half), 100.0 * (centre + half)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("evidence/plan4/programme_facts.json"))
    args = parser.parse_args()

    # --- transcribed inputs, each with the document and sentence it was read from -------------
    agreed, tested = 259, 300
    flips = 4
    tightened_denominator = 225  # top-75% of the 300 tested frames

    lower, upper = wilson(agreed, tested)
    stated_interval = (81.98, 89.76)
    interval_agrees = (
        abs(lower - stated_interval[0]) < 0.05 and abs(upper - stated_interval[1]) < 0.05
    )

    serving: dict[str, Any] = {
        "parsed_output_agreement_percent": {
            "value": 100.0 * agreed / tested,
            "numerator": agreed,
            "denominator": tested,
            "construction": "100 * agreeing frames / frames tested, greedy decoding, probe v2",
            "source_document": PROBE,
            "source_quote": "| **v2 (authoritative)** | ... | **300** | **86.33% (259/300)** |",
        },
        "wilson_interval_95_percent": {
            "lower": lower,
            "upper": upper,
            "z": Z_95,
            "construction": "Wilson score interval on 259/300, RECOMPUTED as a check",
            "stated_in_document": list(stated_interval),
            "agrees_with_document": interval_agrees,
        },
        "abstain_extract_flips": {
            "value": flips,
            "of_frames_tested": tested,
            "source_document": PROBE,
            "source_quote": "The 4 `empty_vs_nonempty` flips are the sharpest concern",
        },
        "flip_rate_at_full_acceptance_percent": {
            "value": 100.0 * flips / tested,
            "numerator": flips,
            "denominator": tested,
            "construction": "100 * flips / frames tested, at 100% acceptance",
        },
        "flip_rate_at_top_75_percent_acceptance": {
            "value": 100.0 * flips / tightened_denominator,
            "numerator": flips,
            "denominator": tightened_denominator,
            "construction": "100 * flips / top-75% of frames tested",
            "note": (
                "THE SAME FOUR FLIPS, over a smaller denominator. This and the full-acceptance "
                "rate are not two draws from one measurement and must not be printed as a "
                "dash-joined band: that reads as a confidence interval, which is a claim about "
                "sampling uncertainty that neither figure supports. The flips concentrate under "
                "tightening because they cluster mid-distribution."
            ),
        },
    }

    # --- the cost band, and why it is a band --------------------------------------------------
    plan2_subtotal = 18.33
    gate0_total = 0.2008
    r0_including_gate0 = 0.149
    r0_excluding_gate0 = 0.35

    cost = {
        "recorded_components": {
            "plan2_subtotal_usd": plan2_subtotal,
            "gate0_per_job_artifact_usd": gate0_total,
            "sum_usd": plan2_subtotal + gate0_total,
            "source_document": COST_ADR,
            "note": (
                "Gate 0 has a genuine per-job artifact "
                "(evidence/gate0/hf_jobs_submission_attempts.json, summing to 0.2008, the exact "
                "figure training.REMAINING_BUDGET_USD subtracts from the cap). Plan 2's eight "
                "jobs are recorded as PROSE in launch briefs and result documents."
            ),
        },
        "recovered_by_differencing": {
            "job": "6a5bcee6bee6ee1cf4ecfe08 R0 inference benchmark",
            "why": (
                "Its cost was never written down per-job. It falls out of four running totals by "
                "subtraction, and two independently written documents agree to the tenth of a "
                "cent -- but the running totals admit two readings, depending on whether "
                "'of $24.7992' includes Gate 0. Nothing in the repository settles which was meant."
            ),
            "reading_running_totals_include_gate0_usd": r0_including_gate0,
            "reading_running_totals_exclude_gate0_usd": r0_excluding_gate0,
        },
        "band_usd": {
            "lower": plan2_subtotal + gate0_total + r0_including_gate0,
            "upper": plan2_subtotal + gate0_total + r0_excluding_gate0,
            "construction": "recorded components plus the differenced job, under each reading",
            "why_a_band": (
                "THERE IS NO SINGLE SPEND LEDGER. The total is assembled by a reader from a "
                "per-job artifact plus eight prose records, and one job is recovered by "
                "differencing running totals that admit two readings. Picking an endpoint would "
                "be choosing the convenient one, and for a claim measured against a fixed ceiling "
                "the low endpoint is the convenient one. The absence of a ledger is the reason "
                "this is a band; manufacturing a ledger would hide that."
            ),
            "ceiling_usd": 25.0,
            "authorised_remaining_at_plan2_start_usd": 24.7992,
        },
        "basis": "price x measured duration, not a billing statement",
    }

    # --- the serving stack's quantisation width, which the paper names in every scope note -----
    # The gate-0 smoke artifact records the MODE (load_in_4bit, quant_type nf4) rather than the
    # numeral, so the width is derived from it here with both flags pinned as configuration.
    # "4-bit" is a stated property of the frozen stack, so it is backed rather than excluded --
    # a structural rule that swallowed it would also swallow "top-75%", which is a real threshold.
    smoke = json.loads((ROOT / "evidence/gate0/qlora_smoke.v1.json").read_text(encoding="utf-8"))
    quantisation = {
        "bits": 4 if smoke["quantization"]["load_in_4bit"] else None,
        "construction": "load_in_4bit implies a 4-bit width; quant_type nf4 names the format",
        "load_in_4bit": smoke["quantization"]["load_in_4bit"],
        "quant_type": smoke["quantization"]["quant_type"],
        "compute_dtype": smoke["quantization"]["compute_dtype"],
        "source_artifact": "evidence/gate0/qlora_smoke.v1.json",
    }

    artifact = {
        "schema_version": "1",
        "serving_stack_quantisation": quantisation,
        "cost_usd_to_produce": 0.0,
        "reads_only_committed_documents": True,
        "certifies_nothing": True,
        "diagnostic_only": True,
        "interpretation": (
            "Figures whose inputs are committed as prose rather than as JSON. Transcription and "
            "computation are kept separate: the counts are transcribed with the document and "
            "sentence they came from, and the derived values are computed here and stored beside "
            "those counts so no guard has to divide. An earlier search of evidence/*.json "
            "concluded these figures were untraceable; the search population was the error, and "
            "the conclusion was reported before the population was stated."
        ),
        "serving_equivalence_probe": serving,
        "programme_cost": cost,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"parity {100 * agreed / tested:.2f}%  wilson [{lower:.2f}, {upper:.2f}]")
    print(f"  recomputed interval agrees with the probe document: {interval_agrees}")
    print(f"flips {100 * flips / tested:.2f}% at full acceptance, "
          f"{100 * flips / tightened_denominator:.2f}% at top-75%")
    print(f"cost band ${cost['band_usd']['lower']:.4f} - ${cost['band_usd']['upper']:.4f}")


if __name__ == "__main__":
    main()
