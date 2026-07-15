"""Typed canonical records shared across all plans."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictRecord(BaseModel):
    """Base record with stable, strict serialization behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"


class Span(StrictRecord):
    """Half-open token span after NFC and newline normalization."""

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str

    @model_validator(mode="after")
    def validate_interval(self) -> Span:
        if self.end <= self.start:
            raise ValueError("span must be a non-empty half-open interval")
        return self


class Argument(StrictRecord):
    role: NonEmpty
    span: Span

    @model_validator(mode="after")
    def require_grounded_text(self) -> Argument:
        if not self.span.text:
            raise ValueError("argument span must carry grounded text")
        return self


class EventFrame(StrictRecord):
    document_id: NonEmpty
    event_type: NonEmpty
    trigger: Span
    arguments: list[Argument] = Field(default_factory=list)


class PredictionRecord(StrictRecord):
    prediction_id: NonEmpty
    document_id: NonEmpty
    system_id: NonEmpty
    prompt_hash: NonEmpty
    raw_output: str
    frames: list[EventFrame] = Field(default_factory=list)
    confidence: float
    status: Literal["valid", "structural_failure", "grounding_failure"]
    failure_reason: str | None = None


class SystemManifest(StrictRecord):
    system_id: NonEmpty
    family: Literal["ZS", "FS", "QA"]
    model_id: NonEmpty
    model_revision: NonEmpty
    tokenizer_revision: NonEmpty
    prompt_hash: NonEmpty
    decoding: dict[str, Any]
    artifact_hashes: dict[str, NonEmpty] = Field(default_factory=dict)


class AnalysisLock(StrictRecord):
    analysis_id: NonEmpty
    git_commit: NonEmpty
    environment_hash: NonEmpty
    input_hashes: dict[str, NonEmpty]
    config_hash: NonEmpty
    status: Literal["locked"] = "locked"


class CertificationResult(StrictRecord):
    method: NonEmpty
    feasible: bool
    n_total: int = Field(ge=0)
    n_accepted: int = Field(ge=0)
    empirical_risk: float | None = Field(default=None, ge=0, le=1)
    risk_upper: float = Field(ge=0, le=1)
    acceptance_lower: float = Field(ge=0, le=1)
    alpha: float = Field(gt=0, lt=1)
    acceptance_floor: float = Field(ge=0, le=1)
    delta: float = Field(gt=0, lt=1)
    reasons: list[str] = Field(default_factory=list)


class ClaimLedger(StrictRecord):
    ledger_id: NonEmpty
    analysis_id: NonEmpty
    claims: list[dict[str, Any]]


class EvidenceManifest(StrictRecord):
    evidence_id: NonEmpty
    analysis_id: NonEmpty
    artifact_hashes: dict[str, NonEmpty]
    gate_status: dict[str, Literal["pass", "fail", "unchecked"]]
