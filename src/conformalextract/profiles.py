"""Text-free RAMS -> ExampleProfile generation (build-profiles)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from conformalextract.data import rams_inclusive_to_half_open

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

    instance_key = str(record["doc_key"])
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
        source_id=str(record.get("source_url") or f"rams:{instance_key}"),
        tokens=tokens,
        event_type=event_type,
        trigger_start=trigger_start,
        trigger_end=trigger_end,
        arguments=tuple(arguments),
    )
