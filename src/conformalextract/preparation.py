"""Plan 2 data-role boundaries and text-free preparation manifests."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from conformalextract.artifacts import (
    canonical_json_bytes,
    freeze_json,
    sha256_bytes,
    sha256_file,
)
from conformalextract.contracts import NonEmpty, StrictRecord

DataRole = Literal["train", "development", "certification", "final", "shift"]
TRAINING_ROLES = frozenset({"train", "development"})


class ExampleProfile(StrictRecord):
    """Text-free token and masking facts for one private prepared example."""

    example_id_hash: NonEmpty
    document_id_hash: NonEmpty
    group_id_hash: NonEmpty
    frame_id_hash: NonEmpty
    data_role: DataRole
    event_type: NonEmpty
    argument_roles: tuple[NonEmpty, ...] = ()
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    prompt_masked_tokens: int = Field(ge=0)
    completion_supervised_tokens: int = Field(ge=0)


class ContextWindowDecision(StrictRecord):
    selected_input_tokens: int = Field(ge=1)
    max_output_tokens: int = Field(ge=1)
    overall_exclusion_rate: float = Field(ge=0, le=1)
    slice_exclusion_rates: dict[str, float]
    excluded_examples: int = Field(ge=0)
    total_examples: int = Field(ge=0)
    context_changed: bool
    smoke_rerun_required: bool
    policy_satisfied: bool


class SourceDownload(StrictRecord):
    source_id: NonEmpty
    url: NonEmpty
    revision: NonEmpty
    sha256: NonEmpty
    restricted_text: Literal[True] = True
    redistribution: Literal["blocked"] = "blocked"


class SourceContract(StrictRecord):
    sources: list[SourceDownload]


class PreparationManifest(StrictRecord):
    analysis_id: NonEmpty


class SourceManifest(PreparationManifest):
    sources: list[SourceDownload]
    transport: Literal["ephemeral_official_download"] = "ephemeral_official_download"
    verify_sha256_before_use: Literal[True] = True
    local_raw_upload_forbidden: Literal[True] = True
    restricted_text_persistence: Literal["private_ephemeral_only"] = "private_ephemeral_only"


class SplitManifest(PreparationManifest):
    assignment_sha256: NonEmpty
    role_document_counts: dict[str, int]
    role_group_counts: dict[str, int]
    grouping_algorithm: Literal["source-id+normalized-sha256+word-fivegram-minhash"] = (
        "source-id+normalized-sha256+word-fivegram-minhash"
    )
    minhash_seed: Literal[42] = 42
    minhash_permutations: Literal[128] = 128
    near_duplicate_jaccard: Literal[0.9] = 0.9
    split_seed: Literal[42] = 42
    split_proportions: dict[str, float] = Field(
        default_factory=lambda: {
            "train": 0.45,
            "development": 0.10,
            "certification": 0.35,
            "final": 0.10,
        }
    )
    group_leakage: Literal[False] = False
    assignment_contains_text: Literal[False] = False


class TrainerManifest(PreparationManifest):
    model_id: NonEmpty
    model_revision: NonEmpty
    role_bound_profile_sha256: NonEmpty
    allowed_label_roles: tuple[Literal["train", "development"], ...] = (
        "train",
        "development",
    )
    forbidden_label_roles: tuple[Literal["certification", "final", "shift"], ...] = (
        "certification",
        "final",
        "shift",
    )
    frame_unit: Literal["one_given_trigger"] = "one_given_trigger"
    prediction_aggregation: Literal["whole_document"] = "whole_document"
    quantization: Literal["nf4-4bit-double-quant-bf16"] = "nf4-4bit-double-quant-bf16"
    lora_rank: Literal[16] = 16
    lora_alpha: Literal[32] = 32
    lora_dropout: Literal[0.05] = 0.05
    lora_targets: Literal["all-linear"] = "all-linear"
    completion_only: Literal[True] = True
    seed: Literal[42] = 42
    batch_size: Literal[1] = 1
    gradient_accumulation: Literal[16] = 16
    gradient_checkpointing: Literal[True] = True
    initial_learning_rate: Literal[0.0002] = 0.0002
    r1_learning_rate_choices: tuple[float, ...] = (0.0002, 0.0001, 0.00005)
    context_policy_phase: Literal["pre_training_and_r0"] = "pre_training_and_r0"
    r1_context_change_reason: Literal["demonstrated_compatibility_only"] = (
        "demonstrated_compatibility_only"
    )


class PromptManifest(PreparationManifest):
    zero_shot_template_sha256: NonEmpty
    two_shot_demonstrations_sha256: NonEmpty
    deterministic_serialization: Literal[True] = True
    empty_output: Literal['{"arguments":[]}'] = '{"arguments":[]}'


class MaskManifest(PreparationManifest):
    profile_sha256: NonEmpty
    completion_only: Literal[True] = True
    prompt_tokens: int = Field(ge=0)
    prompt_masked_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    completion_supervised_tokens: int = Field(ge=0)
    violations: Literal[0] = 0


class ContextWindowManifest(PreparationManifest):
    decision: ContextWindowDecision
    policy_phase: Literal["pre_training_and_r0"] = "pre_training_and_r0"
    r1_adjustment_scope: Literal["compatibility_problem_only"] = "compatibility_problem_only"


class LineageManifest(PreparationManifest):
    manifest_hashes: dict[str, NonEmpty]
    input_hashes: dict[str, NonEmpty]
    contains_source_text: Literal[False] = False
    contains_sealed_labels: Literal[False] = False


def load_training_profiles(path: Path) -> list[ExampleProfile]:
    """Load only metadata profiles that are legal inputs to training preparation."""

    profiles: list[ExampleProfile] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                profile = ExampleProfile.model_validate_json(line)
            except ValueError as error:
                raise ValueError(f"invalid metadata profile at {path.name}:{line_number}") from error
            if profile.data_role not in TRAINING_ROLES:
                raise ValueError(
                    f"sealed role {profile.data_role!r} is forbidden in training profiles"
                )
            profiles.append(profile)
    if not profiles:
        raise ValueError("training profile file must not be empty")
    return profiles


def _context_rates(
    profiles: Sequence[ExampleProfile], *, input_tokens: int, output_tokens: int
) -> tuple[int, float, dict[str, float]]:
    excluded = [
        profile
        for profile in profiles
        if profile.prompt_tokens > input_tokens or profile.completion_tokens > output_tokens
    ]
    def slices(profile: ExampleProfile) -> tuple[str, ...]:
        roles = profile.argument_roles or ("<EMPTY>",)
        return tuple(f"{profile.event_type}::{role}" for role in roles)

    total_by_slice = Counter(key for profile in profiles for key in slices(profile))
    excluded_by_slice = Counter(key for profile in excluded for key in slices(profile))
    rates = {
        key: excluded_by_slice[key] / count for key, count in sorted(total_by_slice.items())
    }
    overall = len(excluded) / len(profiles) if profiles else 0.0
    return len(excluded), overall, rates


def choose_context_window(
    profiles: Sequence[ExampleProfile],
    *,
    ladder: Sequence[int] = (2048, 2560, 3072, 3584, 4096),
    max_output_tokens: int = 512,
    overall_limit: float = 0.05,
    slice_limit: float = 0.10,
) -> ContextWindowDecision:
    """Choose the lowest rung satisfying the predeclared exclusion policy."""

    if not ladder or any(rung <= 0 for rung in ladder):
        raise ValueError("context ladder must contain positive token counts")
    if tuple(ladder) != tuple(sorted(set(ladder))):
        raise ValueError("context ladder must be strictly increasing")

    selected: tuple[int, int, float, dict[str, float]] | None = None
    for rung in ladder:
        excluded, overall, rates = _context_rates(
            profiles, input_tokens=rung, output_tokens=max_output_tokens
        )
        selected = (rung, excluded, overall, rates)
        if overall <= overall_limit and all(rate <= slice_limit for rate in rates.values()):
            break
    assert selected is not None
    rung, excluded, overall, rates = selected
    changed = rung != ladder[0]
    policy_satisfied = overall <= overall_limit and all(
        rate <= slice_limit for rate in rates.values()
    )
    return ContextWindowDecision(
        selected_input_tokens=rung,
        max_output_tokens=max_output_tokens,
        overall_exclusion_rate=overall,
        slice_exclusion_rates=rates,
        excluded_examples=excluded,
        total_examples=len(profiles),
        context_changed=changed,
        smoke_rerun_required=changed,
        policy_satisfied=policy_satisfied,
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _split_summary(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    role_documents: Counter[str] = Counter()
    role_groups: dict[str, set[str]] = {}
    group_role: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected split object at {path.name}:{line_number}")
            if set(value) - {"schema_version", "document_id", "group_id", "role"}:
                raise ValueError(f"split assignment contains forbidden fields at line {line_number}")
            role = str(value.get("role"))
            group = str(value.get("group_id"))
            if role not in {"train", "development", "certification", "final", "shift"}:
                raise ValueError(f"invalid data role at {path.name}:{line_number}")
            previous = group_role.setdefault(group, role)
            if previous != role:
                raise ValueError(f"duplicate group crosses roles: {group}")
            role_documents[role] += 1
            role_groups.setdefault(role, set()).add(group)
    return dict(sorted(role_documents.items())), {
        role: len(groups) for role, groups in sorted(role_groups.items())
    }


def _manifest_payload(record: StrictRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def freeze_preparation_manifests(
    *,
    profiles_path: Path,
    split_assignment_path: Path,
    source_contract_path: Path,
    prompt_template_path: Path,
    demonstrations_path: Path,
    model_config_path: Path,
    output_dir: Path,
) -> dict[str, str]:
    """Freeze the seven compact Plan 2 manifests without copying restricted content."""

    profiles = load_training_profiles(profiles_path)
    source_contract = SourceContract.model_validate_json(
        source_contract_path.read_text(encoding="utf-8")
    )
    if not source_contract.sources:
        raise ValueError("at least one official source download is required")
    model_config = _load_json_object(model_config_path)
    role_document_counts, role_group_counts = _split_summary(split_assignment_path)
    input_hashes = {
        "profiles": sha256_file(profiles_path),
        "split_assignment": sha256_file(split_assignment_path),
        "source_contract": sha256_file(source_contract_path),
        "prompt_template": sha256_file(prompt_template_path),
        "two_shot_demonstrations": sha256_file(demonstrations_path),
        "model_config": sha256_file(model_config_path),
    }
    analysis_id = "plan2prep-" + sha256_bytes(canonical_json_bytes(input_hashes))[:20]
    decision = choose_context_window(
        profiles,
        ladder=tuple(int(value) for value in model_config["context_ladder"]),
        max_output_tokens=int(model_config["decoding"]["max_new_tokens"]),
    )
    if not decision.policy_satisfied:
        raise ValueError("context exclusions exceed policy at the maximum context rung")
    prompt_tokens = sum(profile.prompt_tokens for profile in profiles)
    masked_prompt_tokens = sum(profile.prompt_masked_tokens for profile in profiles)
    completion_tokens = sum(profile.completion_tokens for profile in profiles)
    supervised_completion_tokens = sum(
        profile.completion_supervised_tokens for profile in profiles
    )
    if prompt_tokens != masked_prompt_tokens or completion_tokens != supervised_completion_tokens:
        raise ValueError("completion-only masking profile contains a violation")

    records: dict[str, PreparationManifest] = {
        "source": SourceManifest(
            analysis_id=analysis_id,
            sources=source_contract.sources,
        ),
        "split": SplitManifest(
            analysis_id=analysis_id,
            assignment_sha256=input_hashes["split_assignment"],
            role_document_counts=role_document_counts,
            role_group_counts=role_group_counts,
        ),
        "trainer": TrainerManifest(
            analysis_id=analysis_id,
            model_id=str(model_config["model_id"]),
            model_revision=str(model_config["model_revision"]),
            role_bound_profile_sha256=input_hashes["profiles"],
        ),
        "prompt": PromptManifest(
            analysis_id=analysis_id,
            zero_shot_template_sha256=input_hashes["prompt_template"],
            two_shot_demonstrations_sha256=input_hashes["two_shot_demonstrations"],
        ),
        "mask": MaskManifest(
            analysis_id=analysis_id,
            profile_sha256=input_hashes["profiles"],
            prompt_tokens=prompt_tokens,
            prompt_masked_tokens=masked_prompt_tokens,
            completion_tokens=completion_tokens,
            completion_supervised_tokens=supervised_completion_tokens,
        ),
        "context_window": ContextWindowManifest(
            analysis_id=analysis_id,
            decision=decision,
        ),
    }
    filenames = {
        "source": "source_manifest.json",
        "split": "split_manifest.json",
        "trainer": "trainer_manifest.json",
        "prompt": "prompt_manifest.json",
        "mask": "mask_manifest.json",
        "context_window": "context_window_manifest.json",
        "lineage": "lineage_manifest.json",
    }
    if any((output_dir / filename).exists() for filename in filenames.values()):
        raise FileExistsError(f"refusing to overwrite preparation manifests in {output_dir}")
    hashes: dict[str, str] = {}
    for name, record in records.items():
        hashes[name] = freeze_json(output_dir / filenames[name], _manifest_payload(record))
    lineage = LineageManifest(
        analysis_id=analysis_id,
        manifest_hashes=hashes,
        input_hashes=input_hashes,
    )
    hashes["lineage"] = freeze_json(
        output_dir / filenames["lineage"], _manifest_payload(lineage)
    )
    return hashes
