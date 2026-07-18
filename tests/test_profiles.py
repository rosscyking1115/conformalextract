from __future__ import annotations

from conformalextract.profiles import (
    RamsArgument,
    load_event_ontology,
    parse_rams_instance,
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
