from __future__ import annotations

import json
from pathlib import Path

import pytest

from conformalextract.preparation import (
    ExampleProfile,
    choose_context_window,
    freeze_preparation_manifests,
    load_training_profiles,
)


def _profile(
    identifier: str,
    *,
    role: str = "train",
    event_type: str = "Conflict.Attack",
    argument_role: str = "Attacker",
    prompt_tokens: int = 100,
    completion_tokens: int = 20,
) -> ExampleProfile:
    return ExampleProfile(
        example_id_hash=identifier * 64,
        document_id_hash=("d" + identifier) * 32,
        group_id_hash=(identifier.upper() * 64),
        frame_id_hash=("f" + identifier) * 32,
        data_role=role,
        event_type=event_type,
        argument_roles=(argument_role,),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_masked_tokens=prompt_tokens,
        completion_supervised_tokens=completion_tokens,
    )


def test_context_window_uses_initial_rung_when_exclusions_are_within_policy() -> None:
    profiles = [_profile(str(index % 10)) for index in range(100)]
    profiles[-5:] = [
        _profile(character, prompt_tokens=2049, completion_tokens=20)
        for character in ("a", "b", "c", "d", "e")
    ]

    decision = choose_context_window(profiles)

    assert decision.selected_input_tokens == 2048
    assert decision.max_output_tokens == 512
    assert decision.overall_exclusion_rate == 0.05
    assert not decision.context_changed


def test_context_window_raises_for_a_role_slice_and_requires_smoke_rerun() -> None:
    profiles = [_profile(str(index % 10), argument_role="Victim") for index in range(90)]
    profiles.extend(
        _profile(str(index % 10), argument_role="Place", prompt_tokens=2300)
        for index in range(10)
    )

    decision = choose_context_window(profiles)

    assert decision.selected_input_tokens == 2560
    assert decision.policy_satisfied
    assert decision.context_changed
    assert decision.smoke_rerun_required


def test_training_profiles_refuse_sealed_roles(tmp_path: Path) -> None:
    profile_path = tmp_path / "profiles.jsonl"
    record = _profile("f", role="final").model_dump(mode="json")
    profile_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="sealed role"):
        load_training_profiles(profile_path)


def test_profiles_represent_empty_gold_and_multi_role_trigger_frames() -> None:
    empty = ExampleProfile(
        example_id_hash="a" * 64,
        document_id_hash="b" * 64,
        group_id_hash="c" * 64,
        frame_id_hash="d" * 64,
        data_role="train",
        event_type="Conflict.Attack",
        argument_roles=(),
        prompt_tokens=100,
        completion_tokens=4,
        prompt_masked_tokens=100,
        completion_supervised_tokens=4,
    )
    multi = empty.model_copy(update={"argument_roles": ("Attacker", "Victim")})

    assert empty.argument_roles == ()
    assert multi.argument_roles == ("Attacker", "Victim")


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_preparation_freezes_seven_text_free_role_bound_manifests(tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles.jsonl"
    profiles = [_profile("1"), _profile("2", role="development")]
    profiles_path.write_text(
        "".join(json.dumps(profile.model_dump(mode="json")) + "\n" for profile in profiles),
        encoding="utf-8",
    )
    split_path = tmp_path / "split.jsonl"
    split_path.write_text(
        "".join(
            json.dumps(record) + "\n"
            for record in (
                {"document_id": "private-train-id", "group_id": "g1", "role": "train"},
                {"document_id": "private-dev-id", "group_id": "g2", "role": "development"},
                {"document_id": "private-final-id", "group_id": "g3", "role": "final"},
            )
        ),
        encoding="utf-8",
    )
    source_contract = tmp_path / "sources.json"
    _write_json(
        source_contract,
        {
            "schema_version": "1",
            "sources": [
                {
                    "source_id": "RAMS-1.0c",
                    "url": "https://example.test/official-rams.tar.gz",
                    "revision": "1.0c",
                    "sha256": "a" * 64,
                    "restricted_text": True,
                    "redistribution": "blocked",
                }
            ],
        },
    )
    prompt_path = tmp_path / "prompt.txt"
    prompt_path.write_text("PRIVATE PROMPT CONTENT", encoding="utf-8")
    demonstrations_path = tmp_path / "demos.jsonl"
    demonstrations_path.write_text("PRIVATE DEMONSTRATION CONTENT", encoding="utf-8")
    model_config = tmp_path / "model.json"
    _write_json(
        model_config,
        {
            "model_id": "Qwen/Qwen3-4B-Instruct-2507",
            "model_revision": "c" * 40,
            "initial_context_tokens": 2048,
            "context_ladder": [2048, 2560, 3072, 3584, 4096],
            "decoding": {"max_new_tokens": 512},
        },
    )

    hashes = freeze_preparation_manifests(
        profiles_path=profiles_path,
        split_assignment_path=split_path,
        source_contract_path=source_contract,
        prompt_template_path=prompt_path,
        demonstrations_path=demonstrations_path,
        model_config_path=model_config,
        output_dir=tmp_path / "manifests",
    )

    assert set(hashes) == {
        "source",
        "split",
        "trainer",
        "prompt",
        "mask",
        "context_window",
        "lineage",
    }
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (tmp_path / "manifests").iterdir()
    ]
    assert len({record["analysis_id"] for record in records}) == 1
    serialized = json.dumps(records)
    assert "PRIVATE PROMPT CONTENT" not in serialized
    assert "PRIVATE DEMONSTRATION CONTENT" not in serialized
    assert "private-final-id" not in serialized
    source = json.loads((tmp_path / "manifests" / "source_manifest.json").read_text())
    assert source["local_raw_upload_forbidden"]
    assert source["sources"][0]["sha256"] == "a" * 64
