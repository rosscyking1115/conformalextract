from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (ROOT / "jobs" / "r2_qlora_full.py").read_text(encoding="utf-8")


def test_r2_job_pins_the_gate0f_proven_training_stack() -> None:
    for dependency in (
        '"accelerate==1.14.0"',
        '"bitsandbytes==0.49.2"',
        '"huggingface-hub==0.36.2"',
        '"peft==0.19.1"',
        '"torch==2.13.0"',
        '"transformers==4.57.6"',
    ):
        assert dependency in SCRIPT


def test_r2_job_constants_match_the_frozen_manifests_and_approvals() -> None:
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

    assert f'REVISION = "{trainer["model_revision"]}"' in SCRIPT
    assert f"CONTEXT_TOKENS = {context['decision']['selected_input_tokens']}" in SCRIPT
    assert f"LORA_RANK = {trainer['lora_rank']}" in SCRIPT
    assert f"LORA_ALPHA = {trainer['lora_alpha']}" in SCRIPT
    assert f"GRAD_ACCUM = {trainer['gradient_accumulation']}" in SCRIPT
    assert f"SEED = {trainer['seed']}" in SCRIPT
    assert "LEARNING_RATE = 2e-4" in SCRIPT
    assert f'ROLES_SHA256 = "{lineage["input_hashes"]["split_assignment"]}"' in SCRIPT
    assert f'ANALYSIS_ID = "{lineage["analysis_id"]}"' in SCRIPT
    # Ross-approved 2-epoch, dev-selected design.
    assert "EPOCHS = 2" in SCRIPT
    assert "selected_epoch = min(" in SCRIPT
    assert "dev_losses[e]" in SCRIPT


def test_r2_job_enforces_isolation_raw_deletion_and_two_copies() -> None:
    assert 'if role == "train":' in SCRIPT
    assert 'elif role == "development":' in SCRIPT
    assert '"sealed_reads": 0' in SCRIPT
    assert "shutil.rmtree(RAW_DIR)" in SCRIPT
    assert SCRIPT.index("shutil.rmtree(RAW_DIR)") < SCRIPT.index(
        "AutoModelForCausalLM.from_pretrained"
    )
    assert "raw extraction survived materialization" in SCRIPT
    # Two checked adapter copies to two distinct private repos.
    assert 'ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"' in SCRIPT
    assert "copy_a_commit_oid" in SCRIPT
    assert "copy_b_commit_oid" in SCRIPT
    assert SCRIPT.count("private is not True") == 2
    # Fresh-process reload equivalence (Gate 0F pattern).
    assert "--reload-check" in SCRIPT
    assert "RELOAD_TOKEN_HASH=" in SCRIPT
    assert "reload_equivalence" in SCRIPT


def test_r2_job_report_is_text_free() -> None:
    report_section = SCRIPT.split("report = {", maxsplit=1)[1].split("R2_REPORT=")[0]
    for banned in ('"prompt"', '"completion"', '"raw_output"', '"sentences"'):
        assert banned not in report_section
