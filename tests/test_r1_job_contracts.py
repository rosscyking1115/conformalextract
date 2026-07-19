from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (ROOT / "jobs" / "r1_qlora_pilot.py").read_text(encoding="utf-8")


def test_r1_job_pins_the_gate0f_proven_training_stack() -> None:
    for dependency in (
        '"accelerate==1.14.0"',
        '"bitsandbytes==0.49.2"',
        '"huggingface-hub==0.36.2"',
        '"numpy==2.5.1"',
        '"peft==0.19.1"',
        '"safetensors==0.8.0"',
        '"torch==2.13.0"',
        '"transformers==4.57.6"',
    ):
        assert dependency in SCRIPT


def test_r1_job_constants_match_the_frozen_manifests() -> None:
    trainer = json.loads(
        (ROOT / "manifests" / "plan2" / "trainer_manifest.json").read_text(encoding="utf-8")
    )
    context = json.loads(
        (ROOT / "manifests" / "plan2" / "context_window_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    lineage = json.loads(
        (ROOT / "manifests" / "plan2" / "lineage_manifest.json").read_text(encoding="utf-8")
    )
    sources = json.loads((ROOT / "configs" / "plan2_sources.json").read_text(encoding="utf-8"))
    rams = next(s for s in sources["sources"] if s["source_id"].startswith("RAMS"))

    assert f'REVISION = "{trainer["model_revision"]}"' in SCRIPT
    assert f"CONTEXT_TOKENS = {context['decision']['selected_input_tokens']}" in SCRIPT
    assert f"MAX_OUTPUT_TOKENS = {context['decision']['max_output_tokens']}" in SCRIPT
    assert f"LORA_RANK = {trainer['lora_rank']}" in SCRIPT
    assert f"LORA_ALPHA = {trainer['lora_alpha']}" in SCRIPT
    assert f"LORA_DROPOUT = {trainer['lora_dropout']}" in SCRIPT
    assert f"GRAD_ACCUM = {trainer['gradient_accumulation']}" in SCRIPT
    assert f"SEED = {trainer['seed']}" in SCRIPT
    assert "LEARNING_RATE = 2e-4" in SCRIPT
    assert trainer["initial_learning_rate"] == 2e-4
    assert f'RAMS_URL = "{rams["url"]}"' in SCRIPT
    assert f'RAMS_SHA256 = "{rams["sha256"]}"' in SCRIPT
    assert f'ROLES_SHA256 = "{lineage["input_hashes"]["split_assignment"]}"' in SCRIPT
    assert f'ANALYSIS_ID = "{lineage["analysis_id"]}"' in SCRIPT


def test_r1_job_enforces_label_isolation_and_raw_deletion() -> None:
    # SFT reads train only; development is read only for the selection measurement.
    assert 'if role == "train":' in SCRIPT
    assert 'elif role == "development":' in SCRIPT
    assert '"sft_training"' in SCRIPT
    assert '"development_selection"' in SCRIPT
    assert '"sealed_reads": 0' in SCRIPT
    # Raw archive + extraction deleted before any model work, and re-checked.
    assert "shutil.rmtree(RAW_DIR)" in SCRIPT
    assert SCRIPT.index("shutil.rmtree(RAW_DIR)") < SCRIPT.index(
        "AutoModelForCausalLM.from_pretrained"
    )
    assert "raw extraction survived materialization" in SCRIPT
    # No sealed role is ever rendered.
    assert "certification/final/shift: sealed" in SCRIPT


def test_r1_job_report_is_text_free_and_persistence_is_guarded() -> None:
    report_section = SCRIPT.split("report = {", maxsplit=1)[1]
    for banned in ("prompt", "completion", "raw_output", "sentences"):
        assert f'"{banned}"' not in report_section.split("R1_PILOT_REPORT=")[0]
    assert "private is not True" in SCRIPT
    assert "file_exists" in SCRIPT
    assert "parent_commit=info.sha" in SCRIPT


def test_r1_job_asserts_g3_preflight_traps() -> None:
    assert "model.config.use_cache = False" in SCRIPT
    assert '"use_reentrant": False' in SCRIPT
    assert "pad token must be set (G3)" in SCRIPT
    assert "trainable-parameter band violated (G3)" in SCRIPT
    assert "non-adapter parameters are trainable" in SCRIPT
    assert "non-finite training loss" in SCRIPT
