from __future__ import annotations

import pytest

from conformalextract.predictions import DocumentContext, parse_arm


def _context() -> dict[str, DocumentContext]:
    return {
        "rams:d1": DocumentContext(
            tokens=("Alice", "attacked", "Bob"),
            event_type="Conflict.Attack",
            trigger_start=1,
            trigger_end=2,
            allowed_roles=frozenset({"Attacker", "Target"}),
        )
    }


def _record(raw: str, *, hint: str = "generated", **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "system_id": "qa",
        "instance_key": "rams:d1",
        "status_hint": hint,
        "raw_output": raw,
        "prompt_sha256": "abc",
        "confidence_candidates": {"mean": -0.1, "tenth_percentile": -0.3, "minimum": -0.9},
    }
    record.update(overrides)
    return record


def test_parse_arm_applies_the_extraction_policy_and_grounds_spans() -> None:
    raw = 'preamble\n\n{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Alice"}]}'
    parsed, summary = parse_arm([_record(raw)], _context())
    assert summary.valid == 1
    assert summary.valid_content_bearing == 1
    assert summary.valid_empty == 0
    assert parsed[0].status == "valid"
    assert parsed[0].confidence == pytest.approx(-0.1)
    assert parsed[0].frames[0].arguments[0].span.text == "Alice"


def test_empty_frames_are_counted_separately_from_content_bearing(  # C3
) -> None:
    parsed, summary = parse_arm([_record('{"arguments":[]}')], _context())
    assert summary.valid == 1
    assert summary.valid_empty == 1
    assert summary.valid_content_bearing == 0
    assert parsed[0].status == "valid"


def test_context_overflow_becomes_an_explicit_structural_failure() -> None:
    parsed, summary = parse_arm([_record("", hint="context_overflow")], _context())
    assert summary.context_overflow == 1
    assert summary.structural_failure == 1
    assert summary.valid == 0
    assert parsed[0].failure_reason == "context_overflow"
    assert parsed[0].confidence == float("-inf")
    assert parsed[0].raw_output == ""


def test_ungrounded_span_is_a_grounding_failure_not_a_structural_one() -> None:
    raw = '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Bob"}]}'
    _, summary = parse_arm([_record(raw)], _context())
    assert summary.grounding_failure == 1
    assert summary.valid == 0
    assert summary.failure_reasons == {"ungrounded_span": 1}


def test_unparseable_generation_is_a_structural_failure() -> None:
    _, summary = parse_arm([_record("no json at all")], _context())
    assert summary.structural_failure == 1
    assert summary.failure_reasons == {"no_json_object": 1}


def test_missing_confidence_candidates_scores_negative_infinity() -> None:
    parsed, _ = parse_arm(
        [_record('{"arguments":[]}', confidence_candidates=None)], _context()
    )
    assert parsed[0].confidence == float("-inf")


def test_unknown_document_and_unknown_candidate_fail_loudly() -> None:
    with pytest.raises(ValueError, match="no source document"):
        parse_arm([_record('{"arguments":[]}', instance_key="rams:missing")], _context())
    with pytest.raises(ValueError, match="unknown confidence candidate"):
        parse_arm([_record('{"arguments":[]}')], _context(), confidence_candidate="median")


def test_summary_is_text_free() -> None:
    raw = '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Alice"}]}'
    _, summary = parse_arm([_record(raw)], _context())
    serialized = str(summary.as_dict())
    assert "Alice" not in serialized
    assert "arguments" not in serialized
