"""Strict parser and grounding validator for generated compact JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from conformalextract.contracts import Argument, EventFrame, Span
from conformalextract.evaluation import normalize_text


class _GeneratedArgument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    role: str
    start: int
    end: int
    text: str


class _GeneratedOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    arguments: list[_GeneratedArgument]


@dataclass(frozen=True)
class ParseResult:
    status: Literal["valid", "structural_failure", "grounding_failure"]
    frame: EventFrame | None
    reason: str | None
    confidence: float


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_contradiction")
        result[key] = value
    return result


def parse_generated_frame(
    raw_output: str,
    *,
    document_id: str,
    event_type: str,
    trigger: Span,
    allowed_roles: set[str],
    document_tokens: list[str],
    confidence: float,
) -> ParseResult:
    """Parse exact JSON and require token-span text to round trip to the source tokens."""

    if not raw_output.strip():
        return ParseResult("structural_failure", None, "generation_empty", float("-inf"))
    try:
        decoded = json.loads(raw_output, object_pairs_hook=_reject_duplicate_keys)
        output = _GeneratedOutput.model_validate(decoded)
    except json.JSONDecodeError:
        return ParseResult("structural_failure", None, "invalid_json", float("-inf"))
    except ValidationError:
        return ParseResult("structural_failure", None, "schema_violation", float("-inf"))
    except ValueError as error:
        reason = (
            "duplicate_contradiction" if str(error) == "duplicate_contradiction" else "invalid_json"
        )
        return ParseResult("structural_failure", None, reason, float("-inf"))

    arguments: list[Argument] = []
    for generated in output.arguments:
        if generated.role not in allowed_roles:
            return ParseResult("structural_failure", None, "unknown_role", float("-inf"))
        if generated.start < 0 or generated.end <= generated.start:
            return ParseResult("structural_failure", None, "invalid_span", float("-inf"))
        if generated.end > len(document_tokens):
            return ParseResult("structural_failure", None, "invalid_span", float("-inf"))
        grounded = " ".join(document_tokens[generated.start : generated.end])
        if normalize_text(generated.text) != normalize_text(grounded):
            return ParseResult("grounding_failure", None, "ungrounded_span", float("-inf"))
        arguments.append(
            Argument(
                role=generated.role,
                span=Span(start=generated.start, end=generated.end, text=grounded),
            )
        )
    frame = EventFrame(
        document_id=document_id,
        event_type=event_type,
        trigger=trigger,
        arguments=arguments,
    )
    return ParseResult("valid", frame, None, confidence)
