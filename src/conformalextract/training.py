"""Pure, typed contracts for the paid Plan 2 training pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from enum import StrEnum
from typing import Annotated, Final, Literal, cast, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

from conformalextract.contracts import EventFrame, PredictionRecord

# PEP 586 forbids float and non-literal names inside ``Literal[...]``; the shared
# model identity is pinned with explicit ``Literal`` aliases whose defaults are the
# ``Final`` constants below, and single-value floats are pinned with equal bounds.
MODEL_ID: Final = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION: Final = "cdbee75f17c01a7cc42f958dc650907174af0554"
ModelId = Literal["Qwen/Qwen3-4B-Instruct-2507"]
ModelRevision = Literal["cdbee75f17c01a7cc42f958dc650907174af0554"]
APPROVED_LEARNING_RATES = frozenset({2e-4, 1e-4, 5e-5})
CONTEXT_LADDER = (2048, 2560, 3072, 3584, 4096)


class FrozenModel(BaseModel):
    """Strict immutable base for configuration records."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RunStage(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"


Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class FrozenTrainingSource(FrozenModel):
    """One official source downloaded and verified inside an ephemeral job."""

    source_url: HttpUrl
    source_sha256: Sha256
    source_revision: str = Field(min_length=1)
    licence_review_id: str = Field(min_length=1)


class TrainingRoleManifest(FrozenModel):
    """Metadata-only allow-list; there is deliberately no generic label-path field."""

    manifest_sha256: Sha256
    train_document_ids: tuple[str, ...]
    development_document_ids: tuple[str, ...]
    contains_source_text: Literal[False] = False

    @field_validator("train_document_ids", "development_document_ids", mode="before")
    @classmethod
    def sort_ids(cls, value: object) -> object:
        if isinstance(value, (list, tuple)):
            return tuple(sorted(str(item) for item in value))
        return value

    @model_validator(mode="after")
    def validate_roles(self) -> TrainingRoleManifest:
        train = set(self.train_document_ids)
        development = set(self.development_document_ids)
        if not train or not development:
            raise ValueError("training and development role allow-lists must both be non-empty")
        if train & development:
            raise ValueError("training and development document IDs must be disjoint")
        return self


DataRole = Literal["train", "development", "certification", "final", "shift"]
SEALED_LABEL_ROLES = frozenset({"certification", "final", "shift"})
_LABEL_ACCESS_GENESIS = hashlib.sha256(b"conformalextract/label-access/v1").hexdigest()


class LabelAccessPurpose(StrEnum):
    SFT = "sft_training"
    GENERATION = "prediction_generation"
    DEVELOPMENT_SELECTION = "development_selection"


class LabelAccessRequest(FrozenModel):
    """A single request to read gold for one hashed, text-free document."""

    data_role: DataRole
    document_id_hash: Sha256
    purpose: LabelAccessPurpose


def _authorize_label_access(request: LabelAccessRequest) -> None:
    """Raise unless a gold read is permitted before any model is loaded."""

    if request.data_role in SEALED_LABEL_ROLES:
        raise ValueError(
            f"sealed gold role {request.data_role!r} is unreachable during training"
        )
    if (
        request.data_role == "development"
        and request.purpose is not LabelAccessPurpose.DEVELOPMENT_SELECTION
    ):
        raise ValueError(
            "development gold is limited to development selection, not SFT or generation"
        )


def _chain_label_hash(previous: str, request: LabelAccessRequest) -> str:
    material = json.dumps(
        {
            "previous": previous,
            "data_role": request.data_role,
            "document_id_hash": request.document_id_hash,
            "purpose": request.purpose.value,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(material).hexdigest()


class LabelAccessEntry(FrozenModel):
    """One tamper-evident record of a permitted gold read."""

    data_role: DataRole
    document_id_hash: Sha256
    purpose: LabelAccessPurpose
    entry_hash: Sha256


class LabelAccessLog(FrozenModel):
    """Hash-linked, text-free audit chain over every training gold read."""

    genesis_hash: Sha256 = _LABEL_ACCESS_GENESIS
    entries: tuple[LabelAccessEntry, ...] = ()
    head_hash: Sha256 = _LABEL_ACCESS_GENESIS

    def verify(self) -> bool:
        """Recompute the chain and confirm every read was and remains authorized."""

        previous = self.genesis_hash
        for entry in self.entries:
            request = LabelAccessRequest(
                data_role=entry.data_role,
                document_id_hash=entry.document_id_hash,
                purpose=entry.purpose,
            )
            try:
                _authorize_label_access(request)
            except ValueError:
                return False
            expected = _chain_label_hash(previous, request)
            if expected != entry.entry_hash:
                return False
            previous = expected
        return previous == self.head_hash


def build_label_access_log(requests: Sequence[LabelAccessRequest]) -> LabelAccessLog:
    """Authorize each gold read and append it to a tamper-evident hash chain."""

    previous = _LABEL_ACCESS_GENESIS
    entries: list[LabelAccessEntry] = []
    for request in requests:
        _authorize_label_access(request)
        entry_hash = _chain_label_hash(previous, request)
        entries.append(
            LabelAccessEntry(
                data_role=request.data_role,
                document_id_hash=request.document_id_hash,
                purpose=request.purpose,
                entry_hash=entry_hash,
            )
        )
        previous = entry_hash
    return LabelAccessLog(entries=tuple(entries), head_hash=previous)


PersistedArtifactKind = Literal[
    "adapter_copy_a",
    "adapter_copy_b",
    "label_free_prediction_manifest",
    "lineage_manifest",
    "trackio_json",
]


class TrainingJobContract(FrozenModel):
    """A bounded paid job whose input/output vocabulary excludes sealed labels."""

    stage: RunStage
    source: FrozenTrainingSource
    roles: TrainingRoleManifest
    hourly_rate_usd: float = Field(gt=0)
    max_runtime_minutes: int = Field(gt=0, le=360)
    download_strategy: Literal["ephemeral_verified_official_source"] = (
        "ephemeral_verified_official_source"
    )
    persisted_artifact_kinds: tuple[PersistedArtifactKind, ...] = (
        "adapter_copy_a",
        "adapter_copy_b",
        "label_free_prediction_manifest",
        "lineage_manifest",
        "trackio_json",
    )

    @property
    def maximum_cost_usd(self) -> float:
        return self.hourly_rate_usd * self.max_runtime_minutes / 60


ALLOWED_UPLOAD_KINDS = frozenset(get_args(PersistedArtifactKind))


class MaterializationStep(FrozenModel):
    """One ordered action a remote job takes on ephemeral, official data."""

    action: Literal[
        "download",
        "verify_checksum",
        "extract",
        "materialize_input",
        "delete_raw",
        "launch",
    ]
    target: str = Field(min_length=1)
    detail: str = ""


class EphemeralMaterializationPlan(FrozenModel):
    """Ordered, allowlisted plan proving a job never uploads local raw data."""

    source: FrozenTrainingSource
    workspace: str = Field(min_length=1)
    steps: tuple[MaterializationStep, ...]
    upload_artifact_kinds: tuple[PersistedArtifactKind, ...]
    raw_retained: bool = False
    uploads_are_label_free: bool = True


def plan_ephemeral_materialization(
    source: FrozenTrainingSource,
    *,
    workspace: str,
    raw_archive_name: str,
    allowed_inputs: tuple[str, ...],
    upload_artifact_kinds: tuple[str, ...],
) -> EphemeralMaterializationPlan:
    """Build the download → verify → delete-raw → launch plan for one ephemeral job.

    The remote job downloads the official source into an ephemeral workspace, verifies
    the frozen checksum, materialises only the allowlisted inputs, deletes every raw
    archive and extraction, and launches with explicit allowlisted paths. Uploads are
    restricted to label-free artifact kinds so raw text, sealed labels, and predictions
    with recoverable text can never leave the container.
    """

    if not workspace.startswith("/"):
        raise ValueError("ephemeral workspace must be an absolute in-container path")
    if not raw_archive_name.strip():
        raise ValueError("the official raw archive must be named")
    if not allowed_inputs:
        raise ValueError("at least one allowlisted input must be materialized")
    forbidden = tuple(
        kind for kind in upload_artifact_kinds if kind not in ALLOWED_UPLOAD_KINDS
    )
    if forbidden:
        raise ValueError(
            f"refusing to upload non-label-free artifacts: {', '.join(sorted(forbidden))}"
        )

    raw_dir = f"{workspace}/raw"
    archive_path = f"{raw_dir}/{raw_archive_name}"
    inputs_dir = f"{workspace}/inputs"
    input_paths = tuple(f"{inputs_dir}/{name}" for name in allowed_inputs)

    steps: list[MaterializationStep] = [
        MaterializationStep(
            action="download",
            target=str(source.source_url),
            detail=f"ephemeral official download to {archive_path}",
        ),
        MaterializationStep(
            action="verify_checksum",
            target=archive_path,
            detail=f"require sha256 {source.source_sha256} before use",
        ),
        MaterializationStep(
            action="extract",
            target=raw_dir,
            detail=f"extract {archive_path} under {raw_dir}",
        ),
    ]
    steps.extend(
        MaterializationStep(
            action="materialize_input",
            target=path,
            detail=f"copy allowlisted {name} to {path}",
        )
        for name, path in zip(allowed_inputs, input_paths, strict=True)
    )
    steps.append(
        MaterializationStep(
            action="delete_raw",
            target=raw_dir,
            detail=f"delete raw archive {archive_path} and extraction {raw_dir}",
        )
    )
    steps.append(
        MaterializationStep(
            action="launch",
            target=workspace,
            detail="launch with explicit allowlisted inputs: " + ", ".join(input_paths),
        )
    )
    return EphemeralMaterializationPlan(
        source=source,
        workspace=workspace,
        steps=tuple(steps),
        upload_artifact_kinds=cast(
            "tuple[PersistedArtifactKind, ...]", tuple(upload_artifact_kinds)
        ),
    )


class FrameGeneration(FrozenModel):
    """One trigger-level generation before whole-document aggregation."""

    generation_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    system_id: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=1)
    raw_output: str
    frame: EventFrame | None = None
    confidence: float
    status: Literal["valid", "structural_failure", "grounding_failure"]
    failure_reason: str | None = None

    @model_validator(mode="after")
    def validate_frame_status(self) -> FrameGeneration:
        if self.status == "valid" and self.frame is None:
            raise ValueError("valid trigger generation requires an event frame")
        if self.frame is not None and self.frame.document_id != self.document_id:
            raise ValueError("trigger frame document ID does not match generation")
        return self


def aggregate_document_prediction(
    generations: tuple[FrameGeneration, ...],
) -> PredictionRecord:
    """Aggregate all trigger generations under the whole-document policy."""

    if not generations:
        raise ValueError("at least one trigger generation is required")
    first = generations[0]
    binding = {(item.document_id, item.system_id, item.prompt_hash) for item in generations}
    if len(binding) != 1:
        raise ValueError("all trigger generations must share document, system, and prompt")
    failures = [item for item in generations if item.status != "valid"]
    if any(item.status == "structural_failure" for item in failures):
        status: Literal["valid", "structural_failure", "grounding_failure"] = (
            "structural_failure"
        )
    elif failures:
        status = "grounding_failure"
    else:
        status = "valid"
    frames = [item.frame for item in generations if item.frame is not None]
    raw_output = json.dumps(
        [item.raw_output for item in generations],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    id_material = "\n".join(item.generation_id for item in generations).encode()
    reasons = sorted(
        {item.failure_reason for item in failures if item.failure_reason is not None}
    )
    return PredictionRecord(
        prediction_id=hashlib.sha256(id_material).hexdigest(),
        document_id=first.document_id,
        system_id=first.system_id,
        prompt_hash=first.prompt_hash,
        raw_output=raw_output,
        frames=frames,
        confidence=min(item.confidence for item in generations)
        if status == "valid"
        else float("-inf"),
        status=status,
        failure_reason=";".join(reasons) if reasons else None,
    )
class TrainingRunRecord(FrozenModel):
    stage: RunStage
    status: Literal["pass", "failed"]
    actual_cost_usd: float = Field(ge=0)
    failure_code: str | None = None
    recoverable: bool = False


class TrainingRunLedger(FrozenModel):
    """Authoritative cost and stage-order guard for R0 through optional R3."""

    aggregate_cap_usd: float = Field(default=25.0, ge=25.0, le=25.0)
    prior_spend_usd: float = Field(default=0.0, ge=0)
    records: tuple[TrainingRunRecord, ...] = ()

    @property
    def spent_usd(self) -> float:
        return self.prior_spend_usd + sum(item.actual_cost_usd for item in self.records)

    def authorize(
        self,
        stage: RunStage,
        *,
        estimated_cost_usd: float,
        predeclared_recoverable_failures: frozenset[str] = frozenset(),
    ) -> None:
        """Raise unless a proposed job is ordered, predeclared, and affordable."""

        if estimated_cost_usd <= 0:
            raise ValueError("estimated job cost must be positive")
        if self.spent_usd + estimated_cost_usd > self.aggregate_cap_usd:
            raise ValueError("estimated aggregate spend exceeds the authorized $25 cap")
        by_stage = {record.stage: record for record in self.records}
        if stage is RunStage.R0:
            if self.records:
                raise ValueError("R0 is only authorized as the first Plan 2 run")
            return
        if by_stage.get(RunStage.R0) is None or by_stage[RunStage.R0].status != "pass":
            raise ValueError("R0 must pass before R1")
        if stage is RunStage.R1:
            return
        if by_stage.get(RunStage.R1) is None or by_stage[RunStage.R1].status != "pass":
            raise ValueError("R1 must pass before R2")
        if stage is RunStage.R2:
            return
        failed_r2 = by_stage.get(RunStage.R2)
        if (
            failed_r2 is None
            or failed_r2.status != "failed"
            or not failed_r2.recoverable
            or failed_r2.failure_code not in predeclared_recoverable_failures
        ):
            raise ValueError("R3 requires an R2 predeclared recoverable failure")
class QuantizationConfig(FrozenModel):
    load_in_4bit: Literal[True] = True
    quant_type: Literal["nf4"] = "nf4"
    compute_dtype: Literal["bfloat16"] = "bfloat16"
    double_quantization: Literal[True] = True


class LoraTrainingConfig(FrozenModel):
    rank: Literal[16] = 16
    alpha: Literal[32] = 32
    dropout: float = Field(default=0.05, ge=0.05, le=0.05)
    target_modules: Literal["all-linear"] = "all-linear"


class TrainingConfig(FrozenModel):
    """The locked shared Qwen/QLoRA training contract."""

    model_id: ModelId = MODEL_ID
    model_revision: ModelRevision = MODEL_REVISION
    quantization: QuantizationConfig = QuantizationConfig()
    lora: LoraTrainingConfig = LoraTrainingConfig()
    seed: Literal[42] = 42
    learning_rate: float = 2e-4
    batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=16, ge=1)
    context_tokens: int = 2048
    output_tokens: Literal[512] = 512
    gradient_checkpointing: Literal[True] = True
    completion_only: Literal[True] = True
    bf16: Literal[True] = True


def validate_stage_config(
    stage: RunStage,
    config: TrainingConfig,
    *,
    compatibility_evidence_id: str | None = None,
    base_config: TrainingConfig | None = None,
    frozen_r1_config: TrainingConfig | None = None,
) -> None:
    """Enforce pretraining context selection, R1 tuning, and R2/R3 replay."""

    if config.learning_rate not in APPROVED_LEARNING_RATES:
        raise ValueError("learning rate is outside the approved learning-rate set")
    if config.context_tokens not in CONTEXT_LADDER:
        raise ValueError("context tokens are outside the approved context ladder")
    baseline = base_config or TrainingConfig()
    if stage in (RunStage.R2, RunStage.R3):
        if frozen_r1_config is None or config != frozen_r1_config:
            raise ValueError("R2/R3 must use the exact frozen R1 config")
        return
    changed = any(
        (
            config.learning_rate != baseline.learning_rate,
            config.batch_size != baseline.batch_size,
            config.gradient_accumulation_steps != baseline.gradient_accumulation_steps,
            config.context_tokens != baseline.context_tokens,
        )
    )
    if changed and stage is RunStage.R0:
        raise ValueError("only R1 may use approved compatibility adjustments")
    if changed and not compatibility_evidence_id:
        raise ValueError("R1 adjustments require a compatibility evidence ID")


def choose_pretraining_context(
    exclusion_rates: dict[int, tuple[float, dict[str, float]]],
) -> int:
    """Choose the lowest measured ladder step meeting global and slice limits."""

    measured = [tokens for tokens in CONTEXT_LADDER if tokens in exclusion_rates]
    if not measured or measured[0] != CONTEXT_LADDER[0]:
        raise ValueError("context evidence must begin at 2048 tokens")
    for tokens in measured:
        overall, by_slice = exclusion_rates[tokens]
        if not 0 <= overall <= 1 or any(not 0 <= rate <= 1 for rate in by_slice.values()):
            raise ValueError("exclusion rates must be within [0, 1]")
        if overall <= 0.05 and all(rate <= 0.10 for rate in by_slice.values()):
            return tokens
    if measured[-1] != CONTEXT_LADDER[-1]:
        raise ValueError("more context-ladder evidence is required")
    return CONTEXT_LADDER[-1]


def completion_only_labels(
    input_ids: tuple[int, ...], *, prompt_token_count: int
) -> tuple[int, ...]:
    """Create causal-LM labels that exclude every prompt token from loss."""

    if prompt_token_count < 0 or prompt_token_count >= len(input_ids):
        raise ValueError("training record must contain at least one completion token")
    return (-100,) * prompt_token_count + input_ids[prompt_token_count:]


class DecodingConfig(FrozenModel):
    do_sample: Literal[False] = False
    num_beams: Literal[1] = 1
    max_new_tokens: Literal[512] = 512


class TrainingSystemConfig(FrozenModel):
    family: Literal["ZS", "FS", "QA"]
    model_id: ModelId = MODEL_ID
    model_revision: ModelRevision = MODEL_REVISION
    decoding: DecodingConfig = DecodingConfig()
    demonstration_ids: tuple[str, ...] = ()
    adapter_required: bool = False


def build_system_configs(
    *, fs_demonstration_ids: tuple[str, str]
) -> tuple[TrainingSystemConfig, ...]:
    """Build the three frozen families with deterministic two-shot ordering."""

    demos = tuple(sorted(fs_demonstration_ids))
    if len(set(demos)) != 2 or any(not item.strip() for item in demos):
        raise ValueError("FS requires exactly two distinct non-empty demonstration IDs")
    return (
        TrainingSystemConfig(family="ZS"),
        TrainingSystemConfig(family="FS", demonstration_ids=demos),
        TrainingSystemConfig(family="QA", adapter_required=True),
    )
