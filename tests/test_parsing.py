from __future__ import annotations

from conformalextract.contracts import Span
from conformalextract.data import half_open_to_rams_inclusive, rams_inclusive_to_half_open
from conformalextract.parsing import parse_generated_frame


def _parse(raw: str):  # type: ignore[no-untyped-def]
    return parse_generated_frame(
        raw,
        document_id="d",
        event_type="Conflict.Attack",
        trigger=Span(start=1, end=2, text="attacked"),
        allowed_roles={"Attacker", "Target"},
        document_tokens=["Alice", "attacked", "Bob"],
        confidence=-0.2,
    )


def test_valid_empty_and_grounded_outputs() -> None:
    assert _parse('{"arguments":[]}').status == "valid"
    result = _parse('{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Alice"}]}')
    assert result.status == "valid"
    assert result.frame is not None
    assert result.frame.arguments[0].span.end == 1


def test_parser_rejects_repairs_unknown_roles_and_ungrounded_text() -> None:
    assert _parse('```json\n{"arguments":[]}\n```').reason == "invalid_json"
    assert _parse('{"arguments":[],"arguments":[]}').reason == "duplicate_contradiction"
    assert (
        _parse('{"arguments":[{"role":"Place","start":0,"end":1,"text":"Alice"}]}').reason
        == "unknown_role"
    )
    assert (
        _parse('{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Bob"}]}').reason
        == "ungrounded_span"
    )


def test_rams_offset_conversion_round_trips() -> None:
    assert rams_inclusive_to_half_open(4, 7) == (4, 8)
    assert half_open_to_rams_inclusive(*rams_inclusive_to_half_open(4, 7)) == (4, 7)
