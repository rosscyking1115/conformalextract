from __future__ import annotations

from conformalextract.contracts import Span
from conformalextract.data import half_open_to_rams_inclusive, rams_inclusive_to_half_open
from conformalextract.parsing import extract_first_json_object, parse_generated_frame


def _parse(raw: str, *, extract: bool = False):  # type: ignore[no-untyped-def]
    return parse_generated_frame(
        raw,
        document_id="d",
        event_type="Conflict.Attack",
        trigger=Span(start=1, end=2, text="attacked"),
        allowed_roles={"Attacker", "Target"},
        document_tokens=["Alice", "attacked", "Bob"],
        confidence=-0.2,
        extract_first_object=extract,
    )


def test_valid_empty_and_grounded_outputs() -> None:
    assert _parse('{"arguments":[]}').status == "valid"
    result = _parse('{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Alice"}]}')
    assert result.status == "valid"
    assert result.frame is not None
    assert result.frame.arguments[0].span.end == 1


def test_parser_rejects_repairs_unknown_roles_and_ungrounded_text() -> None:
    # Strict mode (the pre-ADR-0006 frozen behaviour) still rejects fenced JSON.
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


# --- ADR 0006 output-extraction policy -------------------------------------------------


def test_extractor_scans_from_index_zero_with_global_string_state() -> None:
    """Condition C2: a brace inside a string literal must never open or close an object."""
    # A '{' inside a preceding string must not be treated as the object start.
    assert extract_first_json_object('"a { b" {"arguments":[]}') == '{"arguments":[]}'
    # Braces inside string values are inert.
    assert (
        extract_first_json_object('{"arguments":[{"role":"A","text":"}{"}]}')
        == '{"arguments":[{"role":"A","text":"}{"}]}'
    )
    # Escaped quotes do not terminate the string.
    assert extract_first_json_object(r'{"t":"say \"}\" now"}') == r'{"t":"say \"}\" now"}'
    # Nested objects close at the outermost brace.
    assert extract_first_json_object('{"a":{"b":{"c":1}}} trailing') == '{"a":{"b":{"c":1}}}'
    # Never-closed object is unrecoverable.
    assert extract_first_json_object('{"arguments":[{"role":"A"') is None
    assert extract_first_json_object("no object here") is None


def test_extraction_recovers_the_zs_preamble_and_fs_continuation_shapes() -> None:
    """The two real harness artifacts the policy exists to correct."""
    zs = 'Only return the JSON object, nothing else.\n\n{"arguments":[]}'
    fs = '{"arguments":[]}\n\nYou extract grounded event arguments for one given trigger.\n\n'
    assert _parse(zs).status == "structural_failure"  # strict: lost
    assert _parse(zs, extract=True).status == "valid"  # policy: recovered
    assert _parse(fs).status == "structural_failure"
    assert _parse(fs, extract=True).status == "valid"


def test_extraction_preserves_genuine_failures() -> None:
    """Cap-truncated output stays a failure; grounding and role checks still bite."""
    truncated = '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Ali'
    assert _parse(truncated, extract=True).status == "structural_failure"
    ungrounded = '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Bob"}]}'
    assert _parse(ungrounded, extract=True).reason == "ungrounded_span"
    unknown = 'noise {"arguments":[{"role":"Place","start":0,"end":1,"text":"Alice"}]}'
    assert _parse(unknown, extract=True).reason == "unknown_role"


def test_extraction_is_a_no_op_on_already_bare_json() -> None:
    """Condition C7 guard: the untreated comparator (QA) must not be perturbed.

    QA emits bare JSON, so extraction must produce byte-identical parse results. If a future
    change makes extraction alter already-bare output, this fails loudly.
    """
    for raw in (
        '{"arguments":[]}',
        '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"Alice"}]}',
        '{"arguments":[{"role":"Target","start":2,"end":3,"text":"Bob"}]}',
    ):
        assert extract_first_json_object(raw) == raw
        strict, extracted = _parse(raw), _parse(raw, extract=True)
        assert strict.status == extracted.status
        assert strict.frame == extracted.frame
        assert strict.reason == extracted.reason


def test_duplicate_key_rejection_survives_extraction() -> None:
    """Extraction must not become a laundering path around the frozen strict checks."""
    assert _parse('x {"arguments":[],"arguments":[]}', extract=True).reason == (
        "duplicate_contradiction"
    )


def test_rams_offset_conversion_round_trips() -> None:
    assert rams_inclusive_to_half_open(4, 7) == (4, 8)
    assert half_open_to_rams_inclusive(*rams_inclusive_to_half_open(4, 7)) == (4, 7)
