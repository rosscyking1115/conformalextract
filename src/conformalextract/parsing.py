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


def extract_first_json_object(text: str) -> str | None:
    """Return the first balanced top-level JSON object in ``text`` (ADR 0006, condition C2).

    Scans from index 0 tracking JSON string and escape state globally, so a brace inside a
    string literal can never open or close an object. Returns ``None`` when no object closes,
    which keeps cap-truncated generations as structural failures.

    This corrects two documented harness artifacts in the Plan 2 prediction run -- the ZS
    instruction-echo preamble and the FS trailing continuation (missing stop sequence) -- and
    is a strict no-op on already-bare JSON, so the untreated QA arm is not perturbed.
    """

    depth = 0
    in_string = False
    escaped = False
    start: int | None = None
    for index, character in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            if depth == 0:
                start = index
            depth += 1
        elif character == "}":
            if depth:
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : index + 1]
    return None


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
    extract_first_object: bool,
) -> ParseResult:
    """Parse exact JSON and require token-span text to round trip to the source tokens.

    ``extract_first_object`` selects the output-extraction policy and is deliberately
    **required**: every call site must state which policy it uses, so no caller can silently
    inherit the wrong one (ADR 0006, condition C7). Plan 2/3 prediction parsing passes
    ``True``; ``False`` is the pre-ADR-0006 strict behaviour, retained for comparison.
    """

    if not raw_output.strip():
        return ParseResult("structural_failure", None, "generation_empty", float("-inf"))
    candidate = raw_output
    if extract_first_object:
        extracted = extract_first_json_object(raw_output)
        if extracted is None:
            return ParseResult("structural_failure", None, "no_json_object", float("-inf"))
        candidate = extracted
    try:
        decoded = json.loads(candidate, object_pairs_hook=_reject_duplicate_keys)
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
