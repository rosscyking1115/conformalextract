"""Text-free RAMS -> ExampleProfile generation (build-profiles)."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from conformalextract.data import rams_inclusive_to_half_open
from conformalextract.preparation import TRAINING_ROLES, DataRole, ExampleProfile

_ROLE_RE = re.compile(r"^evt\d+arg\d+(.+)$")


def _parse_role(link_role: str) -> str:
    match = _ROLE_RE.match(link_role)
    if match is None:
        raise ValueError(f"unparseable RAMS role string: {link_role!r}")
    return match.group(1)


@dataclass(frozen=True)
class RamsArgument:
    role: str
    start: int
    end: int


@dataclass(frozen=True)
class RamsInstance:
    instance_key: str
    source_id: str
    tokens: tuple[str, ...]
    event_type: str
    trigger_start: int
    trigger_end: int
    arguments: tuple[RamsArgument, ...]


def load_event_ontology(text: str) -> dict[str, tuple[str, ...]]:
    """Parse ``event_role_multiplicities.txt`` into event type -> allowed roles.

    Each line is ``<event_type> <role> <mult> <role> <mult> ...``; roles keep file order.
    """

    ontology: dict[str, tuple[str, ...]] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        event_type = parts[0]
        roles = tuple(parts[i] for i in range(1, len(parts), 2))
        ontology[event_type] = roles
    return ontology


def parse_rams_instance(record: Mapping[str, object]) -> RamsInstance:
    """Parse one RAMS ``.jsonlines`` record into a half-open-span instance."""

    # Canonical repo-wide id: prefix the raw doc_key exactly as load_rams does, so the
    # instance key joins the frozen private split (rams_roles.jsonl) in one identity space.
    instance_key = f"rams:{record['doc_key']}"
    sentences = record["sentences"]
    if not isinstance(sentences, Sequence):
        raise ValueError(f"RAMS sentences must be a sequence: {instance_key}")
    tokens = tuple(str(token) for sentence in sentences for token in sentence)
    triggers = record["evt_triggers"]
    if not isinstance(triggers, Sequence) or not triggers:
        raise ValueError(f"RAMS instance has no trigger: {instance_key}")
    trig = triggers[0]
    trigger_start, trigger_end = rams_inclusive_to_half_open(int(trig[0]), int(trig[1]))
    event_type = str(trig[2][0][0])
    arguments: list[RamsArgument] = []
    for link in cast(list[Any], record.get("gold_evt_links") or []):
        (_, _), (arg_start, arg_end), link_role = link
        start, end = rams_inclusive_to_half_open(int(arg_start), int(arg_end))
        arguments.append(RamsArgument(role=_parse_role(str(link_role)), start=start, end=end))
    return RamsInstance(
        instance_key=instance_key,
        source_id=str(record.get("source_url") or instance_key),
        tokens=tokens,
        event_type=event_type,
        trigger_start=trigger_start,
        trigger_end=trigger_end,
        arguments=tuple(arguments),
    )


def load_prompt_template(path: Path) -> str:
    """Return the fenced ```text template body from the frozen prompt-template file."""

    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip().startswith("```")) + 1
        end = next(i for i in range(start, len(lines)) if lines[i].strip().startswith("```"))
    except StopIteration as error:
        raise ValueError("prompt template file has no fenced code block") from error
    return "\n".join(lines[start:end]) + "\n"


def ordered_argument_roles(
    instance: RamsInstance, allowed_roles: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(arg.role for arg in _ordered_arguments(instance, allowed_roles))


def _ordered_arguments(
    instance: RamsInstance, allowed_roles: tuple[str, ...]
) -> list[RamsArgument]:
    rank = {role: index for index, role in enumerate(allowed_roles)}
    return sorted(instance.arguments, key=lambda arg: (rank.get(arg.role, len(rank)), arg.start))


def render_prompt(
    template: str, instance: RamsInstance, allowed_roles: tuple[str, ...]
) -> str:
    numbered = [{"i": i, "t": token} for i, token in enumerate(instance.tokens)]
    replacements = {
        "{event_type}": instance.event_type,
        "{trigger_start}": str(instance.trigger_start),
        "{trigger_end}": str(instance.trigger_end),
        "{allowed_roles_json}": json.dumps(list(allowed_roles)),
        "{numbered_tokens_json}": json.dumps(numbered),
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def render_completion(instance: RamsInstance, allowed_roles: tuple[str, ...]) -> str:
    if not instance.arguments:
        return '{"arguments":[]}'
    arguments = [
        {
            "role": arg.role,
            "start": arg.start,
            "end": arg.end,
            "text": " ".join(instance.tokens[arg.start : arg.end]),
        }
        for arg in _ordered_arguments(instance, allowed_roles)
    ]
    return json.dumps({"arguments": arguments}, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def instance_hashes(instance_key: str, group_id: str) -> tuple[str, str, str, str]:
    return (
        _sha256(f"{instance_key}#example"),
        _sha256(instance_key),
        _sha256(group_id),
        _sha256(f"{instance_key}#frame"),
    )


def build_example_profile(
    instance: RamsInstance,
    *,
    data_role: DataRole,
    group_id: str,
    ontology: Mapping[str, tuple[str, ...]],
    template: str,
    count_tokens: Callable[[str], int],
) -> ExampleProfile:
    allowed = ontology.get(instance.event_type)
    if allowed is None:
        raise ValueError(f"unknown_event {instance.event_type!r} for {instance.instance_key}")
    for arg in instance.arguments:
        if arg.role not in allowed:
            raise ValueError(
                f"unknown_role {arg.role!r} for {instance.event_type} ({instance.instance_key})"
            )
        if not 0 <= arg.start < arg.end <= len(instance.tokens):
            raise ValueError(f"bad_span {arg.start},{arg.end} for {instance.instance_key}")
    prompt = render_prompt(template, instance, allowed)
    completion = render_completion(instance, allowed)
    prompt_tokens = count_tokens(prompt)
    completion_tokens = count_tokens(completion)
    example_hash, document_hash, group_hash, frame_hash = instance_hashes(
        instance.instance_key, group_id
    )
    return ExampleProfile(
        example_id_hash=example_hash,
        document_id_hash=document_hash,
        group_id_hash=group_hash,
        frame_id_hash=frame_hash,
        data_role=data_role,
        event_type=instance.event_type,
        argument_roles=ordered_argument_roles(instance, allowed),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_masked_tokens=prompt_tokens,
        completion_supervised_tokens=completion_tokens,
    )


SEALED_ROLES = frozenset({"certification", "final", "shift"})


@dataclass(frozen=True)
class ProfileBuildSummary:
    emitted: int
    sealed_dropped: int
    total: int


def assert_ontology_coverage(
    instances: Sequence[RamsInstance], ontology: Mapping[str, tuple[str, ...]]
) -> None:
    for instance in instances:
        allowed = ontology.get(instance.event_type)
        if allowed is None:
            raise ValueError(f"unknown_event {instance.event_type!r} (ontology preflight)")
        for arg in instance.arguments:
            if arg.role not in allowed:
                raise ValueError(
                    f"unknown_role {arg.role!r} for {instance.event_type} (ontology preflight)"
                )


def build_profiles(
    *,
    instances: Sequence[RamsInstance],
    role_map: Mapping[str, tuple[str, str]],
    ontology: Mapping[str, tuple[str, ...]],
    template: str,
    count_tokens: Callable[[str], int],
) -> tuple[list[ExampleProfile], ProfileBuildSummary]:
    assert_ontology_coverage(instances, ontology)
    profiles: list[ExampleProfile] = []
    sealed_dropped = 0
    for instance in instances:
        binding = role_map.get(instance.instance_key)
        if binding is None:
            raise ValueError(f"no role assignment for instance {instance.instance_key}")
        group_id, data_role = binding
        if data_role in SEALED_ROLES:
            sealed_dropped += 1
            continue
        if data_role not in TRAINING_ROLES:
            raise ValueError(f"unknown_data_role {data_role!r} for {instance.instance_key}")
        profiles.append(
            build_example_profile(
                instance, data_role=cast(DataRole, data_role), group_id=group_id, ontology=ontology,
                template=template, count_tokens=count_tokens,
            )
        )
    summary = ProfileBuildSummary(
        emitted=len(profiles), sealed_dropped=sealed_dropped, total=len(instances)
    )
    if summary.emitted + summary.sealed_dropped != summary.total:
        raise ValueError("conservation failed: emitted + sealed_dropped != total")
    return profiles, summary


def load_role_map(path: Path) -> dict[str, tuple[str, str]]:
    role_map: dict[str, tuple[str, str]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            role_map[str(record["document_id"])] = (str(record["group_id"]), str(record["role"]))
    return role_map


def read_ontology(archive: Path) -> dict[str, tuple[str, ...]]:
    with tarfile.open(archive, "r:gz") as tar:
        member = tar.extractfile("RAMS_1.0c/scorer/event_role_multiplicities.txt")
        if member is None:
            raise ValueError("ontology missing from RAMS archive")
        return load_event_ontology(member.read().decode("utf-8"))


def read_rams_instances(archive: Path) -> list[RamsInstance]:
    instances: list[RamsInstance] = []
    with tarfile.open(archive, "r:gz") as tar:
        for split in ("train", "dev", "test"):
            member = tar.extractfile(f"RAMS_1.0c/data/{split}.jsonlines")
            if member is None:
                continue
            for line in member.read().decode("utf-8").splitlines():
                if line.strip():
                    instances.append(parse_rams_instance(json.loads(line)))
    return instances


def qwen_token_counter(tokenizer_dir: Path) -> Callable[[str], int]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir), local_files_only=True)  # type: ignore[no-untyped-call]
    return lambda text: len(tokenizer(text, add_special_tokens=False)["input_ids"])


def write_profiles(profiles: Sequence[ExampleProfile], output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for profile in profiles:
            handle.write(profile.model_dump_json() + "\n")
