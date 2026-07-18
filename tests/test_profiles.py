from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conformalextract.profiles import (
    RamsArgument,
    build_example_profile,
    instance_hashes,
    load_event_ontology,
    load_prompt_template,
    ordered_argument_roles,
    parse_rams_instance,
    render_completion,
    render_prompt,
)

ONTOLOGY_TEXT = (
    "life.die.deathcausedbyviolentevents killer 1 victim 1 place 1\n"
    "conflict.attack.n/a attacker 1 target 1 instrument 1 place 1\n"
)


def test_load_event_ontology_maps_event_to_roles_in_order() -> None:
    ontology = load_event_ontology(ONTOLOGY_TEXT)
    assert ontology["life.die.deathcausedbyviolentevents"] == ("killer", "victim", "place")
    assert ontology["conflict.attack.n/a"] == ("attacker", "target", "instrument", "place")


RAMS_RECORD = {
    "doc_key": "nw_RC00example",
    "source_url": "http://example.test/article",
    "sentences": [["Alpha", "attacked", "Beta"], ["in", "Gamma", "yesterday"]],
    "evt_triggers": [[1, 1, [["conflict.attack.n/a", 1.0]]]],
    "gold_evt_links": [
        [[1, 1], [0, 0], "evt001arg01attacker"],
        [[1, 1], [2, 2], "evt001arg02target"],
    ],
}


def test_parse_rams_instance_extracts_trigger_and_half_open_arguments() -> None:
    instance = parse_rams_instance(RAMS_RECORD)
    assert instance.instance_key == "nw_RC00example"
    assert instance.source_id == "http://example.test/article"
    assert instance.tokens == ("Alpha", "attacked", "Beta", "in", "Gamma", "yesterday")
    assert instance.event_type == "conflict.attack.n/a"
    assert (instance.trigger_start, instance.trigger_end) == (1, 2)  # inclusive 1,1 -> half-open
    assert instance.arguments == (
        RamsArgument(role="attacker", start=0, end=1),
        RamsArgument(role="target", start=2, end=3),
    )


def test_parse_rams_instance_supports_empty_gold() -> None:
    record = {**RAMS_RECORD, "gold_evt_links": []}
    assert parse_rams_instance(record).arguments == ()


TEMPLATE = (
    "Event type: {event_type}\n"
    "Trigger token span [start, end): {trigger_start}, {trigger_end}\n"
    "Allowed roles: {allowed_roles_json}\n"
    "Document tokens: {numbered_tokens_json}\n"
    'Return: {"arguments":[]}\n'  # literal JSON braces must survive rendering
)

ONTOLOGY = {"conflict.attack.n/a": ("attacker", "target", "instrument", "place")}


def test_render_prompt_fills_placeholders_and_keeps_literal_json() -> None:
    instance = parse_rams_instance(RAMS_RECORD)
    prompt = render_prompt(TEMPLATE, instance, ("attacker", "target", "instrument", "place"))
    assert "Event type: conflict.attack.n/a" in prompt
    assert "[start, end): 1, 2" in prompt
    assert '["attacker", "target", "instrument", "place"]' in prompt
    assert '"arguments":[]' in prompt  # literal example untouched
    assert '"Alpha"' in prompt  # numbered tokens present


def test_render_completion_is_deterministic_in_ontology_order() -> None:
    instance = parse_rams_instance(RAMS_RECORD)  # attacker@0, target@2
    allowed = ("attacker", "target", "instrument", "place")
    completion = render_completion(instance, allowed)
    payload = json.loads(completion)
    assert [a["role"] for a in payload["arguments"]] == ["attacker", "target"]
    assert payload["arguments"][0] == {"role": "attacker", "start": 0, "end": 1, "text": "Alpha"}
    assert ordered_argument_roles(instance, allowed) == ("attacker", "target")


def test_render_completion_empty_gold() -> None:
    instance = parse_rams_instance({**RAMS_RECORD, "gold_evt_links": []})
    assert render_completion(instance, ("attacker",)) == '{"arguments":[]}'


def test_load_prompt_template_extracts_the_frozen_fenced_body() -> None:
    template = load_prompt_template(Path("docs/gate0/prompt-template.md"))
    for placeholder in (
        "{event_type}", "{trigger_start}", "{trigger_end}",
        "{allowed_roles_json}", "{numbered_tokens_json}",
    ):
        assert placeholder in template
    assert '{"arguments":[]}' in template  # literal JSON example survives extraction


def test_load_prompt_template_fails_loud_without_a_fence(tmp_path: Path) -> None:
    bare = tmp_path / "no-fence.md"
    bare.write_text("just prose, no code fence\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fenced"):
        load_prompt_template(bare)


def test_instance_hashes_are_deterministic_and_suffix_disjoint() -> None:
    a = instance_hashes("k1", "g1")
    b = instance_hashes("k1", "g1")
    example, document, group, frame = a
    assert a == b
    assert example != frame  # disjoint-by-suffix
    assert document == hashlib.sha256(b"k1").hexdigest()
    assert group == hashlib.sha256(b"g1").hexdigest()


def test_build_example_profile_counts_and_is_text_free() -> None:
    instance = parse_rams_instance(RAMS_RECORD)
    profile = build_example_profile(
        instance,
        data_role="train",
        group_id="g1",
        ontology=ONTOLOGY,
        template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),  # fake counter
    )
    assert profile.data_role == "train"
    assert profile.event_type == "conflict.attack.n/a"
    assert profile.argument_roles == ("attacker", "target")
    # completion-only masking invariant
    assert profile.prompt_masked_tokens == profile.prompt_tokens
    assert profile.completion_supervised_tokens == profile.completion_tokens
    # text-free: no source token appears in the serialized profile
    assert "Alpha" not in profile.model_dump_json()


def test_build_example_profile_rejects_unknown_event() -> None:
    instance = parse_rams_instance(RAMS_RECORD)
    with pytest.raises(ValueError, match="unknown_event"):
        build_example_profile(
            instance, data_role="train", group_id="g1", ontology={}, template=TEMPLATE,
            count_tokens=lambda text: len(text.split()),
        )
