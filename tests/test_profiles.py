from __future__ import annotations

from conformalextract.profiles import load_event_ontology

ONTOLOGY_TEXT = (
    "life.die.deathcausedbyviolentevents killer 1 victim 1 place 1\n"
    "conflict.attack.n/a attacker 1 target 1 instrument 1 place 1\n"
)


def test_load_event_ontology_maps_event_to_roles_in_order() -> None:
    ontology = load_event_ontology(ONTOLOGY_TEXT)
    assert ontology["life.die.deathcausedbyviolentevents"] == ("killer", "victim", "place")
    assert ontology["conflict.attack.n/a"] == ("attacker", "target", "instrument", "place")
