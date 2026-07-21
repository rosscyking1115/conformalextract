"""Parse generated predictions into grounded records under the ADR 0006 extraction policy.

Consumes the per-arm prediction JSONL produced by ``jobs/plan2_prediction_generation.py`` and
applies the frozen parser to every frame, validating each argument span against the source
document tokens. **Gold labels are never read here** — grounding validates against source text,
so this step is safe for every split including the sealed ones.

Reviewer condition C3: empty-argument frames are counted as a first-class category. An empty
frame is structurally valid *and* grounds trivially, so it reaches acceptance as a contentless
prediction; reporting it inside a single "valid" number would conflate saying nothing with
extracting correctly.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from conformalextract.contracts import PredictionRecord, Span
from conformalextract.parsing import parse_generated_frame
from conformalextract.profiles import RamsInstance

CONFIDENCE_CANDIDATES = ("mean", "tenth_percentile", "minimum")


@dataclass(frozen=True)
class ArmSummary:
    """Text-free, committable summary of one system's parsed predictions."""

    system_id: str
    records: int
    context_overflow: int
    structural_failure: int
    grounding_failure: int
    valid: int
    valid_empty: int
    valid_content_bearing: int
    failure_reasons: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "system_id": self.system_id,
            "records": self.records,
            "context_overflow": self.context_overflow,
            "structural_failure": self.structural_failure,
            "grounding_failure": self.grounding_failure,
            "valid": self.valid,
            "valid_empty": self.valid_empty,
            "valid_content_bearing": self.valid_content_bearing,
            "failure_reasons": dict(sorted(self.failure_reasons.items())),
        }


@dataclass(frozen=True)
class DocumentContext:
    """Everything needed to ground a generated frame — source tokens only, never gold."""

    tokens: tuple[str, ...]
    event_type: str
    trigger_start: int
    trigger_end: int
    allowed_roles: frozenset[str]


def build_document_contexts(
    instances: Sequence[RamsInstance], ontology: Mapping[str, Sequence[str]]
) -> dict[str, DocumentContext]:
    """Index RAMS instances by canonical id, taking source tokens and the trigger only.

    ``instance.arguments`` (gold) is deliberately not touched: grounding is a round-trip
    against the document text, so no label access is required or performed.
    """

    contexts: dict[str, DocumentContext] = {}
    for instance in instances:
        allowed = ontology.get(instance.event_type)
        if allowed is None:
            raise ValueError(f"unknown_event {instance.event_type!r}")
        contexts[instance.instance_key] = DocumentContext(
            tokens=tuple(instance.tokens),
            event_type=instance.event_type,
            trigger_start=instance.trigger_start,
            trigger_end=instance.trigger_end,
            allowed_roles=frozenset(str(role) for role in allowed),
        )
    return contexts


def _confidence(record: Mapping[str, object], candidate: str) -> float:
    candidates = record.get("confidence_candidates")
    if not isinstance(candidates, Mapping):
        return float("-inf")  # empty generation: no transition log probabilities
    return float(candidates[candidate])


def parse_arm(
    records: Sequence[Mapping[str, object]],
    contexts: Mapping[str, DocumentContext],
    *,
    confidence_candidate: str = "mean",
) -> tuple[list[PredictionRecord], ArmSummary]:
    """Parse one system's records under the ADR 0006 policy, returning records and a summary.

    ``confidence_candidate`` selects which predeclared score is carried on the record; the
    operative candidate is not chosen until Plan 3 calibration, so all three remain available
    in the source artifact and this only sets what the typed record carries.
    """

    if confidence_candidate not in CONFIDENCE_CANDIDATES:
        raise ValueError(f"unknown confidence candidate: {confidence_candidate!r}")

    parsed: list[PredictionRecord] = []
    counts = {"structural_failure": 0, "grounding_failure": 0, "valid": 0}
    reasons: dict[str, int] = {}
    overflow = valid_empty = valid_content = 0
    system_id = str(records[0]["system_id"]) if records else "unknown"

    for record in records:
        instance_key = str(record["instance_key"])
        context = contexts.get(instance_key)
        if context is None:
            raise ValueError(f"no source document for {instance_key}")

        if str(record["status_hint"]) == "context_overflow":
            # Never generated: an explicit failure, not a silent exclusion.
            overflow += 1
            counts["structural_failure"] += 1
            reasons["context_overflow"] = reasons.get("context_overflow", 0) + 1
            parsed.append(
                PredictionRecord(
                    prediction_id=f"{system_id}:{instance_key}",
                    document_id=instance_key,
                    system_id=system_id,
                    prompt_hash=str(record["prompt_sha256"]),
                    raw_output="",
                    frames=[],
                    confidence=float("-inf"),
                    status="structural_failure",
                    failure_reason="context_overflow",
                )
            )
            continue

        trigger = Span(
            start=context.trigger_start,
            end=context.trigger_end,
            text=" ".join(context.tokens[context.trigger_start : context.trigger_end]),
        )
        result = parse_generated_frame(
            str(record["raw_output"]),
            document_id=instance_key,
            event_type=context.event_type,
            trigger=trigger,
            allowed_roles=set(context.allowed_roles),
            document_tokens=list(context.tokens),
            confidence=_confidence(record, confidence_candidate),
            extract_first_object=True,  # ADR 0006, applied uniformly to every arm
        )
        counts[result.status] += 1
        if result.reason:
            reasons[result.reason] = reasons.get(result.reason, 0) + 1
        if result.status == "valid" and result.frame is not None:
            if result.frame.arguments:
                valid_content += 1
            else:
                valid_empty += 1
        parsed.append(
            PredictionRecord(
                prediction_id=f"{system_id}:{instance_key}",
                document_id=instance_key,
                system_id=system_id,
                prompt_hash=str(record["prompt_sha256"]),
                raw_output=str(record["raw_output"]),
                frames=[result.frame] if result.frame is not None else [],
                confidence=result.confidence,
                status=result.status,
                failure_reason=result.reason,
            )
        )

    summary = ArmSummary(
        system_id=system_id,
        records=len(records),
        context_overflow=overflow,
        structural_failure=counts["structural_failure"],
        grounding_failure=counts["grounding_failure"],
        valid=counts["valid"],
        valid_empty=valid_empty,
        valid_content_bearing=valid_content,
        failure_reasons=reasons,
    )
    return parsed, summary


def read_prediction_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
