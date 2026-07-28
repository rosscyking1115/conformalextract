# RAMS→profiles generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested `build-profiles` pipeline that turns raw RAMS into the text-free `data/private/plan2/example_profiles.jsonl` that `prepare-data` consumes.

**Architecture:** A new pure module `src/conformalextract/profiles.py` (ontology loader, RAMS parser, frozen-template renderers, id hashing, orchestrator) plus a `build-profiles` CLI seam that loads the local Qwen tokenizer and ephemerally extracts the RAMS archive. Token counting is injected as a `Callable[[str], int]` so the core is tested with a fake counter; the real tokenizer is wired only in the CLI.

**Tech Stack:** Python 3.12, pydantic (existing `ExampleProfile`), `transformers`/`tokenizers` (CPU, tokenizer-only), Typer CLI, pytest.

## Global Constraints

- **Text-free output only.** Persisted `ExampleProfile` carries hashes + ontology labels (`event_type`, `argument_roles`) + integer counts. Grounded argument text and document tokens are used only transiently for rendering/tokenization, never written.
- **Sealed roles dropped at generation.** Emit only `train`/`development`; never emit `certification`/`final`/`shift`.
- **Aggregation-key rule.** `document_id_hash = sha256(instance_key)` (per-trigger). `group_id_hash = sha256(group_id)` is the source-doc **aggregation unit**. Never treat `document_id_hash` as the aggregation key.
- **Render from the frozen template file** `docs/gate0/prompt-template.md` (the one `PromptManifest.zero_shot_template_sha256` hashes) — never an inline template string.
- **Fail loud** with instance key + reason tag (`bad_span`/`unknown_event`/`unknown_role`/`unknown_data_role`); no silent skips. Ontology-coverage preflight before the build. Conservation: `emitted + sealed_dropped == total`.
- **Deterministic**: argument/role order = ontology role order, ties by span start; byte-reproducible jsonl.
- Verify after each task: `uv run pytest -q`, `uv run ruff check .`, `uv run mypy src`.

---

### Task 1: Event-role ontology loader

**Files:**
- Create: `src/conformalextract/profiles.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Produces: `load_event_ontology(text: str) -> dict[str, tuple[str, ...]]` — maps event type → allowed roles in file order.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_profiles.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py::test_load_event_ontology_maps_event_to_roles_in_order -v`
Expected: FAIL with `ImportError`/`cannot import name 'load_event_ontology'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/conformalextract/profiles.py
"""Text-free RAMS -> ExampleProfile generation (build-profiles)."""

from __future__ import annotations


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_profiles.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py tests/test_profiles.py
git commit -m "feat(plan2): add RAMS event-role ontology loader (build-profiles)"
```

---

### Task 2: RAMS instance parser

**Files:**
- Modify: `src/conformalextract/profiles.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `rams_inclusive_to_half_open(start, end_inclusive) -> tuple[int, int]` from `conformalextract.data` (existing, `data.py:44`).
- Produces:
  - `RamsArgument(role: str, start: int, end: int)` — frozen dataclass, half-open span.
  - `RamsInstance(instance_key: str, source_id: str, tokens: tuple[str, ...], event_type: str, trigger_start: int, trigger_end: int, arguments: tuple[RamsArgument, ...])` — frozen dataclass, half-open spans.
  - `parse_rams_instance(record: Mapping[str, object]) -> RamsInstance`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
from conformalextract.profiles import RamsArgument, RamsInstance, parse_rams_instance

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py -k parse_rams_instance -v`
Expected: FAIL with `cannot import name 'parse_rams_instance'`.

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/conformalextract/profiles.py (update the header imports)
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

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
    for link in record.get("gold_evt_links") or []:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_profiles.py -k parse_rams_instance -v`
Expected: PASS (both parse tests).

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py tests/test_profiles.py
git commit -m "feat(plan2): add RAMS instance parser (triggers, half-open args, empty-gold)"
```

---

### Task 3: Frozen-template prompt/completion renderers

**Files:**
- Modify: `src/conformalextract/profiles.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `RamsInstance` (Task 2), ontology dict (Task 1).
- Produces:
  - `load_prompt_template(path: Path) -> str` — extracts the fenced template body from `docs/gate0/prompt-template.md`.
  - `render_prompt(template: str, instance: RamsInstance, allowed_roles: tuple[str, ...]) -> str`.
  - `render_completion(instance: RamsInstance, allowed_roles: tuple[str, ...]) -> str` — deterministic (ontology role order, ties by span start).
  - `ordered_argument_roles(instance: RamsInstance, allowed_roles: tuple[str, ...]) -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
import json

from conformalextract.profiles import (
    ordered_argument_roles,
    render_completion,
    render_prompt,
)

TEMPLATE = (
    "Event type: {event_type}\n"
    "Trigger token span [start, end): {trigger_start}, {trigger_end}\n"
    "Allowed roles: {allowed_roles_json}\n"
    "Document tokens: {numbered_tokens_json}\n"
    'Return: {"arguments":[]}\n'  # literal JSON braces must survive rendering
)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py -k render -v`
Expected: FAIL with `cannot import name 'render_prompt'`.

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/conformalextract/profiles.py (add Path to imports: from pathlib import Path; import json)


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
    rank = {role: index for index, role in enumerate(allowed_roles)}
    ordered = sorted(instance.arguments, key=lambda arg: (rank.get(arg.role, len(rank)), arg.start))
    return tuple(arg.role for arg in ordered)


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_profiles.py -k render -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py tests/test_profiles.py
git commit -m "feat(plan2): render prompts from frozen template + deterministic completions"
```

---

### Task 4: Id hashing + single-profile builder

**Files:**
- Modify: `src/conformalextract/profiles.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `RamsInstance`, ontology dict, template str, `render_prompt`/`render_completion`, `ExampleProfile` from `conformalextract.preparation`.
- Produces:
  - `instance_hashes(instance_key: str, group_id: str) -> tuple[str, str, str, str]` returning `(example_id_hash, document_id_hash, group_id_hash, frame_id_hash)`.
  - `build_example_profile(instance: RamsInstance, *, data_role: str, group_id: str, ontology: Mapping[str, tuple[str, ...]], template: str, count_tokens: Callable[[str], int]) -> ExampleProfile`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
import hashlib

from conformalextract.profiles import build_example_profile, instance_hashes

ONTOLOGY = {"conflict.attack.n/a": ("attacker", "target", "instrument", "place")}


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
```

(Add `import pytest` at the top of the test file if not already present.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py -k "hashes or build_example_profile" -v`
Expected: FAIL with `cannot import name 'instance_hashes'`.

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/conformalextract/profiles.py (add: import hashlib; from collections.abc import Callable;
#   from conformalextract.preparation import ExampleProfile)


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
    data_role: str,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_profiles.py -k "hashes or build_example_profile" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py tests/test_profiles.py
git commit -m "feat(plan2): id hashing + single ExampleProfile builder (text-free, validated)"
```

---

### Task 5: Orchestrator — preflight, sealed-drop, conservation

**Files:**
- Modify: `src/conformalextract/profiles.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: everything above; `TRAINING_ROLES` from `conformalextract.preparation`.
- Produces:
  - `SEALED_ROLES: frozenset[str]` = `{"certification", "final", "shift"}`.
  - `ProfileBuildSummary(emitted: int, sealed_dropped: int, total: int)` — frozen dataclass.
  - `assert_ontology_coverage(instances: Sequence[RamsInstance], ontology: Mapping[str, tuple[str, ...]]) -> None`.
  - `build_profiles(*, instances: Sequence[RamsInstance], role_map: Mapping[str, tuple[str, str]], ontology: Mapping[str, tuple[str, ...]], template: str, count_tokens: Callable[[str], int]) -> tuple[list[ExampleProfile], ProfileBuildSummary]` where `role_map[instance_key] = (group_id, data_role)`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
from conformalextract.profiles import (
    ProfileBuildSummary,
    assert_ontology_coverage,
    build_profiles,
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
    role_map = {"k_train": ("g1", "train"), "k_dev": ("g1", "development"), "k_cert": ("g2", "final")}
    _, summary = build_profiles(
        instances=_instances(), role_map=role_map, ontology=ONTOLOGY, template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    assert summary.emitted + summary.sealed_dropped == summary.total == 3


def test_ontology_coverage_preflight_fails_on_missing_event() -> None:
    with pytest.raises(ValueError, match="unknown_event"):
        assert_ontology_coverage(_instances(), {})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py -k "build_profiles or coverage" -v`
Expected: FAIL with `cannot import name 'build_profiles'`.

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/conformalextract/profiles.py (import: from conformalextract.preparation import ExampleProfile, TRAINING_ROLES)

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
                instance, data_role=data_role, group_id=group_id, ontology=ontology,
                template=template, count_tokens=count_tokens,
            )
        )
    summary = ProfileBuildSummary(
        emitted=len(profiles), sealed_dropped=sealed_dropped, total=len(instances)
    )
    if summary.emitted + summary.sealed_dropped != summary.total:
        raise ValueError("conservation failed: emitted + sealed_dropped != total")
    return profiles, summary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_profiles.py -k "build_profiles or coverage" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py tests/test_profiles.py
git commit -m "feat(plan2): profiles orchestrator with ontology preflight + conservation"
```

---

### Task 6: CLI `build-profiles` + tokenizer + archive extraction + end-to-end

**Files:**
- Modify: `src/conformalextract/profiles.py` (loaders for archive + roles + tokenizer counter)
- Modify: `src/conformalextract/cli.py` (add `build-profiles` command)
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: all of the above.
- Produces:
  - `load_role_map(path: Path) -> dict[str, tuple[str, str]]` — from `rams_roles.jsonl` (`document_id -> (group_id, role)`).
  - `read_rams_instances(archive: Path) -> list[RamsInstance]` — extract `RAMS_1.0c/data/*.jsonlines` to a temp dir, parse, delete temp.
  - `read_ontology(archive: Path) -> dict[str, tuple[str, ...]]` — read `RAMS_1.0c/scorer/event_role_multiplicities.txt` from the archive.
  - `qwen_token_counter(tokenizer_dir: Path) -> Callable[[str], int]`.
  - `write_profiles(profiles: Sequence[ExampleProfile], output: Path) -> None` — refuse overwrite; one JSON per line.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
from pathlib import Path

from conformalextract.preparation import load_training_profiles
from conformalextract.profiles import load_role_map, write_profiles


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
    role_map = {"k_train": ("g1", "train"), "k_dev": ("g1", "development"), "k_cert": ("g2", "final")}
    profiles, _ = build_profiles(
        instances=_instances(), role_map=role_map, ontology=ONTOLOGY, template=TEMPLATE,
        count_tokens=lambda text: len(text.split()),
    )
    output = tmp_path / "example_profiles.jsonl"
    write_profiles(profiles, output)
    reloaded = load_training_profiles(output)  # existing consumer-side loader
    assert len(reloaded) == 2
    with pytest.raises(FileExistsError):
        write_profiles(profiles, output)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profiles.py -k "role_map or roundtrips" -v`
Expected: FAIL with `cannot import name 'load_role_map'`.

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/conformalextract/profiles.py (imports: import tarfile, tempfile; from collections.abc import Iterator)


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

    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
    return lambda text: len(tokenizer(text, add_special_tokens=False)["input_ids"])


def write_profiles(profiles: Sequence[ExampleProfile], output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for profile in profiles:
            handle.write(profile.model_dump_json() + "\n")
```

```python
# add to src/conformalextract/cli.py (near the prepare-data command)
@app.command("build-profiles")
def build_profiles_command(
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    roles: Annotated[Path, typer.Option()] = Path("data/private/splits/rams_roles.jsonl"),
    tokenizer_dir: Annotated[Path, typer.Option()] = Path("data/private/qwen-metadata"),
    prompt_template: Annotated[Path, typer.Option()] = Path("docs/gate0/prompt-template.md"),
    output: Annotated[Path, typer.Option()] = Path("data/private/plan2/example_profiles.jsonl"),
) -> None:
    """Generate the text-free example_profiles.jsonl from raw RAMS (CPU, no upload)."""

    from conformalextract.profiles import (
        build_profiles,
        load_prompt_template,
        load_role_map,
        qwen_token_counter,
        read_ontology,
        read_rams_instances,
        write_profiles,
    )

    instances = read_rams_instances(rams_archive)
    ontology = read_ontology(rams_archive)
    role_map = load_role_map(roles)
    template = load_prompt_template(prompt_template)
    profiles, summary = build_profiles(
        instances=instances, role_map=role_map, ontology=ontology, template=template,
        count_tokens=qwen_token_counter(tokenizer_dir),
    )
    write_profiles(profiles, output)
    typer.echo(
        json.dumps(
            {"output": str(output), "emitted": summary.emitted,
             "sealed_dropped": summary.sealed_dropped, "total": summary.total},
            sort_keys=True,
        )
    )
```

- [ ] **Step 4: Run test to verify it passes + full gates**

Run: `uv run pytest tests/test_profiles.py -q && uv run ruff check . && uv run mypy src`
Expected: all pass. Confirm `data/private/**` stays git-ignored (`git status --short` shows no data files).

- [ ] **Step 5: Commit**

```bash
git add src/conformalextract/profiles.py src/conformalextract/cli.py tests/test_profiles.py
git commit -m "feat(plan2): build-profiles CLI (archive extract, tokenizer counts, roundtrip)"
```

---

### Task 7: End-to-end — generated profiles feed `freeze_preparation_manifests`

**Files:**
- Test: `tests/test_profiles.py`

**Interfaces:**
- Consumes: `build_profiles`, `write_profiles`; `freeze_preparation_manifests` from `conformalextract.preparation`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_profiles.py
from conformalextract.preparation import freeze_preparation_manifests


def test_generated_profiles_are_accepted_by_prepare_data(tmp_path: Path) -> None:
    # NOTE (fixed during execution): k_dev must be in its own group — one group may
    # not span two roles (the leakage control _split_summary enforces).
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
    prompt = tmp_path / "prompt.txt"; prompt.write_text("PROMPT", encoding="utf-8")
    demos = tmp_path / "demos.jsonl"; demos.write_text("DEMOS", encoding="utf-8")
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
    assert set(hashes) == {"source", "split", "trainer", "prompt", "mask", "context_window", "lineage"}
```

- [ ] **Step 2: Run test to verify it fails, then passes**

Run: `uv run pytest tests/test_profiles.py::test_generated_profiles_are_accepted_by_prepare_data -v`
Expected: PASS (all upstream tasks make it pass; if the mask invariant or a field mismatches, fix in the relevant earlier task).

- [ ] **Step 3: Full gates + commit**

```bash
uv run pytest -q && uv run ruff check . && uv run mypy src
git add tests/test_profiles.py
git commit -m "test(plan2): end-to-end generated profiles accepted by prepare-data"
```

---

## Self-Review

**Spec coverage:** ontology loader (T1), parser incl. empty-gold/multi-role (T2), frozen-template render + deterministic order (T3), hashing incl. disjoint-suffix + aggregation-key note in Global Constraints (T4), single builder + text-free + fail-loud reasons (T4), orchestrator + preflight + sealed-drop + conservation (T5), CLI + tokenizer + archive extract + roundtrip (T6), end-to-end freeze (T7). Privacy invariant covered by the text-free assertion (T4) + roundtrip staying in `data/private` (git-ignored). All spec sections map to a task.

**Placeholder scan:** no TBD/TODO; every code step shows complete code and exact run commands.

**Type consistency:** `RamsInstance`/`RamsArgument` fields, `instance_hashes` 4-tuple order `(example, document, group, frame)`, `role_map[key] = (group_id, data_role)`, and `count_tokens: Callable[[str], int]` are used identically across T2–T7.

## Notes for the implementer
- The real `build-profiles` run (on restricted RAMS) is a **local CPU** step the user runs; it writes only to git-ignored `data/private/`. Do not commit any generated `example_profiles.jsonl`.
- Multi-role/empty-gold are exercised by `RAMS_RECORD` (two roles) and the empty-gold variant; add a 0-arg and a same-role-twice fixture if extending.
- `render_completion`'s `text` field uses whitespace-joined tokens; if RAMS spans need exact detokenization later, that is a separate, out-of-scope refinement (it only affects the transient completion string, never persisted output).
