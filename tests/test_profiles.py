from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conformalextract.preparation import freeze_preparation_manifests, load_training_profiles
from conformalextract.profiles import (
    ProfileBuildSummary,
    RamsArgument,
    assert_ontology_coverage,
    build_example_profile,
    build_profiles,
    instance_hashes,
    load_event_ontology,
    load_prompt_template,
    load_role_map,
    ordered_argument_roles,
    parse_rams_instance,
    render_completion,
    render_prompt,
    write_profiles,
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
    # Canonical repo-wide document id: the "rams:" prefix matches load_rams and the
    # frozen private split (rams_roles.jsonl), so the role join shares one identity space.
    assert instance.instance_key == "rams:nw_RC00example"
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


def _instances():
    base = parse_rams_instance(RAMS_RECORD)
    from dataclasses import replace
    return [
        replace(base, instance_key="k_train"),
        replace(base, instance_key="k_dev"),
        replace(base, instance_key="k_cert"),
    ]


def test_build_profiles_emits_training_roles_and_drops_sealed() -> None:
    role_map = {
        "k_train": ("g1", "train"),
        "k_dev": ("g1", "development"),
        "k_cert": ("g2", "certification"),
    }
    profiles, summary = build_profiles(
        instances=_instances(), role_map=role_map, ontology=ONTOLOGY, template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    assert {p.data_role for p in profiles} == {"train", "development"}
    assert summary == ProfileBuildSummary(emitted=2, sealed_dropped=1, total=3)


def test_build_profiles_conservation_holds_on_join() -> None:
    role_map = {
        "k_train": ("g1", "train"),
        "k_dev": ("g1", "development"),
        "k_cert": ("g2", "final"),
    }
    _, summary = build_profiles(
        instances=_instances(), role_map=role_map, ontology=ONTOLOGY, template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    assert summary.emitted + summary.sealed_dropped == summary.total == 3


def test_ontology_coverage_preflight_fails_on_missing_event() -> None:
    with pytest.raises(ValueError, match="unknown_event"):
        assert_ontology_coverage(_instances(), {})


def test_load_role_map_parses_group_and_role(tmp_path: Path) -> None:
    path = tmp_path / "roles.jsonl"
    path.write_text(
        '{"document_id":"k1","group_id":"g1","role":"train","schema_version":"1"}\n'
        '{"document_id":"k2","group_id":"g1","role":"certification","schema_version":"1"}\n',
        encoding="utf-8",
    )
    role_map = load_role_map(path)
    assert role_map["k1"] == ("g1", "train")
    assert role_map["k2"] == ("g1", "certification")


def test_write_then_reload_profiles_roundtrips(tmp_path: Path) -> None:
    role_map = {
        "k_train": ("g1", "train"),
        "k_dev": ("g1", "development"),
        "k_cert": ("g2", "final"),
    }
    profiles, _ = build_profiles(
        instances=_instances(),
        role_map=role_map,
        ontology=ONTOLOGY,
        template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    output = tmp_path / "example_profiles.jsonl"
    write_profiles(profiles, output)
    reloaded = load_training_profiles(output)  # existing consumer-side loader
    assert len(reloaded) == 2
    with pytest.raises(FileExistsError):
        write_profiles(profiles, output)


def test_generated_profiles_are_accepted_by_prepare_data(tmp_path: Path) -> None:
    role_map = {"k_train": ("g1", "train"), "k_dev": ("g2", "development")}
    from dataclasses import replace
    base = parse_rams_instance(RAMS_RECORD)
    instances = [replace(base, instance_key="k_train"), replace(base, instance_key="k_dev")]
    profiles, _ = build_profiles(
        instances=instances, role_map=role_map, ontology=ONTOLOGY, template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    profiles_path = tmp_path / "example_profiles.jsonl"
    write_profiles(profiles, profiles_path)

    # minimal companion inputs (see tests/test_preparation.py for the fixture shapes)
    split = tmp_path / "split.jsonl"
    split.write_text(
        '{"document_id":"k_train","group_id":"g1","role":"train"}\n'
        '{"document_id":"k_dev","group_id":"g2","role":"development"}\n',
        encoding="utf-8",
    )
    sources = tmp_path / "sources.json"
    sources.write_text(
        '{"schema_version":"1","sources":[{"schema_version":"1","source_id":"RAMS-1.0c",'
        '"url":"https://example.test/rams.tar.gz","revision":"1.0c","sha256":"' + "a" * 64 + '",'
        '"restricted_text":true,"redistribution":"blocked"}]}',
        encoding="utf-8",
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("PROMPT", encoding="utf-8")
    demos = tmp_path / "demos.jsonl"
    demos.write_text("DEMOS", encoding="utf-8")
    model_config = tmp_path / "model.json"
    model_config.write_text(
        '{"model_id":"Qwen/Qwen3-4B-Instruct-2507","model_revision":"' + "c" * 40 + '",'
        '"initial_context_tokens":2048,"context_ladder":[2048,2560,3072,3584,4096],'
        '"decoding":{"max_new_tokens":512}}',
        encoding="utf-8",
    )

    hashes = freeze_preparation_manifests(
        profiles_path=profiles_path, split_assignment_path=split, source_contract_path=sources,
        prompt_template_path=prompt, demonstrations_path=demos, model_config_path=model_config,
        output_dir=tmp_path / "manifests",
    )
    assert set(hashes) == {
        "source", "split", "trainer", "prompt", "mask", "context_window", "lineage",
    }


def _demo_pool():
    from dataclasses import replace

    base = parse_rams_instance(RAMS_RECORD)  # 2 arguments -> multi-argument
    empty = parse_rams_instance({**RAMS_RECORD, "gold_evt_links": []})
    single = replace(base, arguments=base.arguments[:1])
    return {
        "k_multi_a": replace(base, instance_key="k_multi_a"),
        "k_multi_b": replace(base, instance_key="k_multi_b"),
        "k_empty_a": replace(empty, instance_key="k_empty_a"),
        "k_empty_dev": replace(empty, instance_key="k_empty_dev"),
        "k_single": replace(single, instance_key="k_single"),
    }


def _demo_role_map():
    return {
        "k_multi_a": ("g1", "train"),
        "k_multi_b": ("g2", "train"),
        "k_empty_a": ("g3", "train"),
        "k_empty_dev": ("g4", "development"),
        "k_single": ("g5", "train"),
    }


def test_fs_demonstrations_pick_train_only_multi_and_empty_by_lowest_hash() -> None:
    from conformalextract.profiles import select_fs_demonstrations

    pool = _demo_pool()
    multi, empty = select_fs_demonstrations(list(pool.values()), _demo_role_map())

    assert len(multi.arguments) >= 2
    assert empty.arguments == ()
    # Lexicographically-lowest example hash within each category.
    expected_multi = min(
        ("k_multi_a", "k_multi_b"),
        key=lambda k: hashlib.sha256(f"{k}#example".encode()).hexdigest(),
    )
    assert multi.instance_key == expected_multi
    # The development empty-gold instance is never eligible.
    assert empty.instance_key == "k_empty_a"


def test_fs_demonstrations_are_deterministic_under_input_order() -> None:
    from conformalextract.profiles import select_fs_demonstrations

    pool = list(_demo_pool().values())
    first = select_fs_demonstrations(pool, _demo_role_map())
    second = select_fs_demonstrations(list(reversed(pool)), _demo_role_map())
    assert (first[0].instance_key, first[1].instance_key) == (
        second[0].instance_key,
        second[1].instance_key,
    )


def test_fs_demonstrations_fail_loud_when_a_category_is_missing() -> None:
    from conformalextract.profiles import select_fs_demonstrations

    pool = _demo_pool()
    only_multi = [pool["k_multi_a"], pool["k_single"]]
    with pytest.raises(ValueError, match="empty-gold"):
        select_fs_demonstrations(only_multi, _demo_role_map())


def test_render_and_write_demonstrations_roundtrip(tmp_path: Path) -> None:
    import json as json_module

    from conformalextract.profiles import (
        render_demonstrations,
        select_fs_demonstrations,
        write_demonstrations,
    )
    from conformalextract.training import build_system_configs

    pair = select_fs_demonstrations(list(_demo_pool().values()), _demo_role_map())
    demos = render_demonstrations(pair, ontology=ONTOLOGY, template=TEMPLATE)

    assert len(demos) == 2
    ids = tuple(demo.demonstration_id for demo in demos)
    assert len(set(ids)) == 2
    # IDs satisfy the frozen FS system contract.
    systems = build_system_configs(fs_demonstration_ids=(ids[0], ids[1]))
    assert systems[1].family == "FS"
    # Prompts/completions are rendered from the frozen template pipeline.
    assert "Event type: conflict.attack.n/a" in demos[0].prompt
    assert json_module.loads(demos[1].completion) == {"arguments": []}

    output = tmp_path / "fs_demonstrations.jsonl"
    write_demonstrations(demos, output)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert set(json_module.loads(lines[0])) == {"demonstration_id", "prompt", "completion"}
    with pytest.raises(FileExistsError):
        write_demonstrations(demos, output)
