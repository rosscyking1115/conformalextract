from __future__ import annotations

import pytest
from pydantic import ValidationError

from conformalextract.contracts import EventFrame, Span
from conformalextract.training import (
    FrameGeneration,
    FrozenTrainingSource,
    RunStage,
    TrainingConfig,
    TrainingJobContract,
    TrainingRoleManifest,
    TrainingRunLedger,
    TrainingRunRecord,
    aggregate_document_prediction,
    build_system_configs,
    choose_pretraining_context,
    completion_only_labels,
    validate_stage_config,
)


def test_training_config_pins_shared_qwen_stack() -> None:
    config = TrainingConfig()

    assert config.model_id == "Qwen/Qwen3-4B-Instruct-2507"
    assert config.model_revision == "cdbee75f17c01a7cc42f958dc650907174af0554"
    assert config.quantization.model_dump() == {
        "load_in_4bit": True,
        "quant_type": "nf4",
        "compute_dtype": "bfloat16",
        "double_quantization": True,
    }
    assert config.lora.model_dump() == {
        "rank": 16,
        "alpha": 32,
        "dropout": 0.05,
        "target_modules": "all-linear",
    }
    assert config.seed == 42
    assert config.batch_size == 1
    assert config.gradient_accumulation_steps == 16
    assert config.gradient_checkpointing is True
    assert config.completion_only is True
    assert config.bf16 is True
    assert config.learning_rate == 2e-4
    assert config.context_tokens == 2048
    assert config.output_tokens == 512


def test_system_configs_share_inference_stack_and_freeze_family_differences() -> None:
    systems = build_system_configs(fs_demonstration_ids=("demo-b", "demo-a"))

    assert [system.family for system in systems] == ["ZS", "FS", "QA"]
    assert {system.model_id for system in systems} == {"Qwen/Qwen3-4B-Instruct-2507"}
    assert {system.model_revision for system in systems} == {
        "cdbee75f17c01a7cc42f958dc650907174af0554"
    }
    assert {system.decoding.do_sample for system in systems} == {False}
    assert {system.decoding.num_beams for system in systems} == {1}
    assert {system.decoding.max_new_tokens for system in systems} == {512}
    assert systems[0].demonstration_ids == ()
    assert systems[1].demonstration_ids == ("demo-a", "demo-b")
    assert systems[2].adapter_required is True


def test_r1_adjustments_require_evidence_and_stay_on_approved_ladders() -> None:
    adjusted = TrainingConfig(
        learning_rate=1e-4,
        batch_size=2,
        gradient_accumulation_steps=8,
        context_tokens=2560,
    )

    validate_stage_config(
        RunStage.R1,
        adjusted,
        compatibility_evidence_id="oom-r0-20260717",
    )
    with pytest.raises(ValueError, match="compatibility evidence"):
        validate_stage_config(RunStage.R1, adjusted)
    with pytest.raises(ValueError, match="approved learning-rate set"):
        validate_stage_config(
            RunStage.R1,
            TrainingConfig(learning_rate=3e-4),
            compatibility_evidence_id="loss-r0-20260717",
        )
    with pytest.raises(ValueError, match="context ladder"):
        validate_stage_config(
            RunStage.R1,
            TrainingConfig(context_tokens=2304),
            compatibility_evidence_id="length-r0-20260717",
        )


def test_pretraining_context_uses_lowest_passing_512_token_increment() -> None:
    selected = choose_pretraining_context(
        {
            2048: (0.06, {"Conflict.Attack/Attacker": 0.08}),
            2560: (0.04, {"Conflict.Attack/Attacker": 0.10}),
            3072: (0.01, {"Conflict.Attack/Attacker": 0.02}),
        }
    )

    assert selected == 2560


def test_r2_must_exactly_inherit_frozen_r1_config() -> None:
    selected_r1 = TrainingConfig(
        learning_rate=1e-4,
        batch_size=2,
        gradient_accumulation_steps=8,
        context_tokens=2560,
    )

    validate_stage_config(RunStage.R2, selected_r1, frozen_r1_config=selected_r1)
    with pytest.raises(ValueError, match="exact frozen R1 config"):
        validate_stage_config(
            RunStage.R2,
            selected_r1.model_copy(update={"learning_rate": 5e-5}),
            frozen_r1_config=selected_r1,
        )


def test_completion_only_labels_mask_every_prompt_token() -> None:
    labels = completion_only_labels((101, 102, 201, 202), prompt_token_count=2)

    assert labels == (-100, -100, 201, 202)
    with pytest.raises(ValueError, match="at least one completion token"):
        completion_only_labels((101, 102), prompt_token_count=2)


def test_run_ledger_enforces_r0_r1_r2_order_and_predeclared_r3_recovery() -> None:
    ledger = TrainingRunLedger(
        prior_spend_usd=0.20,
        records=(
            TrainingRunRecord(stage=RunStage.R0, status="pass", actual_cost_usd=0.50),
            TrainingRunRecord(stage=RunStage.R1, status="pass", actual_cost_usd=2.00),
            TrainingRunRecord(
                stage=RunStage.R2,
                status="failed",
                actual_cost_usd=10.00,
                failure_code="oom",
                recoverable=True,
            ),
        ),
    )

    ledger.authorize(
        RunStage.R3,
        estimated_cost_usd=3.00,
        predeclared_recoverable_failures=frozenset({"oom", "upload_failure"}),
    )
    with pytest.raises(ValueError, match=r"aggregate.*cap"):
        ledger.authorize(
            RunStage.R3,
            estimated_cost_usd=20.00,
            predeclared_recoverable_failures=frozenset({"oom"}),
        )
    with pytest.raises(ValueError, match="predeclared recoverable failure"):
        ledger.authorize(
            RunStage.R3,
            estimated_cost_usd=1.00,
            predeclared_recoverable_failures=frozenset({"upload_failure"}),
        )


def test_run_ledger_blocks_skipping_required_stages() -> None:
    with pytest.raises(ValueError, match="R0 must pass before R1"):
        TrainingRunLedger().authorize(RunStage.R1, estimated_cost_usd=1.00)


def test_job_inputs_download_frozen_source_and_cannot_represent_sealed_labels() -> None:
    source = FrozenTrainingSource(
        source_url="https://www.cs.jhu.edu/~paxia/rams/data/RAMS_1.0.zip",
        source_sha256="a" * 64,
        source_revision="RAMS-1.0",
        licence_review_id="gate0-rams-licence",
    )
    roles = TrainingRoleManifest(
        manifest_sha256="b" * 64,
        train_document_ids=("train-2", "train-1"),
        development_document_ids=("dev-1",),
    )
    contract = TrainingJobContract(
        stage=RunStage.R0,
        source=source,
        roles=roles,
        hourly_rate_usd=1.80,
        max_runtime_minutes=20,
    )

    assert contract.download_strategy == "ephemeral_verified_official_source"
    assert contract.roles.train_document_ids == ("train-1", "train-2")
    assert contract.roles.contains_source_text is False
    assert set(contract.persisted_artifact_kinds) == {
        "adapter_copy_a",
        "adapter_copy_b",
        "label_free_prediction_manifest",
        "lineage_manifest",
        "trackio_json",
    }
    assert contract.maximum_cost_usd == pytest.approx(0.60)
    with pytest.raises(ValidationError, match="certification_labels_path"):
        TrainingJobContract.model_validate(
            {
                **contract.model_dump(mode="json"),
                "certification_labels_path": "/sealed/certification.jsonl",
            }
        )


def test_trigger_frames_aggregate_to_one_whole_document_prediction() -> None:
    generations = (
        FrameGeneration(
            generation_id="g-1",
            document_id="doc-1",
            system_id="qa",
            prompt_hash="p" * 64,
            raw_output='{"arguments":[]}',
            frame=EventFrame(
                document_id="doc-1",
                event_type="Conflict.Attack",
                trigger=Span(start=1, end=2, text="attacked"),
            ),
            confidence=-0.2,
            status="valid",
        ),
        FrameGeneration(
            generation_id="g-2",
            document_id="doc-1",
            system_id="qa",
            prompt_hash="p" * 64,
            raw_output='{"arguments":[]}',
            frame=EventFrame(
                document_id="doc-1",
                event_type="Contact.Meet",
                trigger=Span(start=5, end=6, text="met"),
            ),
            confidence=-0.8,
            status="valid",
        ),
    )

    prediction = aggregate_document_prediction(generations)

    assert prediction.document_id == "doc-1"
    assert len(prediction.frames) == 2
    assert prediction.confidence == -0.8
    assert prediction.status == "valid"


def test_any_invalid_trigger_rejects_whole_document_at_worst_confidence() -> None:
    generations = (
        FrameGeneration(
            generation_id="g-1",
            document_id="doc-1",
            system_id="qa",
            prompt_hash="p" * 64,
            raw_output="not-json",
            confidence=-0.1,
            status="structural_failure",
            failure_reason="invalid_json",
        ),
    )

    prediction = aggregate_document_prediction(generations)

    assert prediction.status == "structural_failure"
    assert prediction.confidence == float("-inf")
    assert prediction.frames == []


def test_extended_context_ladder_reaches_6144() -> None:
    # Ross-approved 2026-07-19 (ADR 0003): ladder extended so the frozen exclusion
    # policy can be satisfied on the real RAMS token distribution.
    validate_stage_config(
        RunStage.R1,
        TrainingConfig(context_tokens=6144),
        compatibility_evidence_id="context-evidence-20260719",
    )
    selected = choose_pretraining_context(
        {
            2048: (0.30, {}),
            2560: (0.20, {}),
            3072: (0.10, {}),
            3584: (0.08, {}),
            4096: (0.009, {"conflict.attack.bombing::<EMPTY>": 1.0}),
            4608: (0.005, {"conflict.attack.bombing::<EMPTY>": 1.0}),
            5120: (0.003, {"conflict.attack.bombing::<EMPTY>": 0.5}),
            6144: (0.0014, {"transaction.transfermoney.purc::money": 0.091}),
        }
    )
    assert selected == 6144
