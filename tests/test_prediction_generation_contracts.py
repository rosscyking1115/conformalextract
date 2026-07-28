from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (ROOT / "jobs" / "plan2_prediction_generation.py").read_text(encoding="utf-8")
R2_SCRIPT = (ROOT / "jobs" / "r2_qlora_full.py").read_text(encoding="utf-8")


def _block(script: str, start: str, end: str) -> str:
    return script.split(start, maxsplit=1)[1].split(end, maxsplit=1)[0]


def test_prediction_job_pins_the_frozen_model_and_selected_adapter() -> None:
    assert 'MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"' in SCRIPT
    assert 'REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"' in SCRIPT
    assert 'ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"' in SCRIPT
    # THE dev-selected R2 adapter (copy B commit) - the QA system under test.
    assert 'ADAPTER_REVISION = "edd69373be3d46ae2a982e555f4ec9549491e8e4"' in SCRIPT
    assert "snapshot_download(ADAPTER_REPO, revision=ADAPTER_REVISION)" in SCRIPT


def test_prediction_job_constants_match_the_frozen_manifests() -> None:
    lineage = json.loads(
        (ROOT / "manifests" / "plan2" / "lineage_manifest.json").read_text(encoding="utf-8")
    )
    split = json.loads(
        (ROOT / "manifests" / "plan2" / "split_manifest.json").read_text(encoding="utf-8")
    )
    prompt = json.loads(
        (ROOT / "manifests" / "plan2" / "prompt_manifest.json").read_text(encoding="utf-8")
    )
    context = json.loads(
        (ROOT / "manifests" / "plan2" / "context_window_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert f'ANALYSIS_ID = "{lineage["analysis_id"]}"' in SCRIPT
    assert f'ROLES_SHA256 = "{lineage["input_hashes"]["split_assignment"]}"' in SCRIPT
    assert f'DEMOS_SHA256 = "{prompt["two_shot_demonstrations_sha256"]}"' in SCRIPT
    assert f"CONTEXT_TOKENS = {context['decision']['selected_input_tokens']}" in SCRIPT
    counts = split["role_document_counts"]
    for role in ("train", "development", "certification", "final"):
        assert f'"{role}": {counts[role]},' in SCRIPT
    assert sum(counts.values()) == 9124


def test_prediction_job_uses_the_g2b_decided_output_cap_and_greedy_decoding() -> None:
    # G2b evidence decision: 256 cap (>1.5x measured real max of 162) - not 512.
    assert "MAX_NEW_TOKENS = 256" in SCRIPT
    assert "temperature=0.0" in SCRIPT
    assert "max_tokens=MAX_NEW_TOKENS" in SCRIPT
    assert "logprobs=1" in SCRIPT
    # FS worst case measured at 9,249 prompt tokens; the model window must cover it.
    assert "MAX_MODEL_LEN = 9728" in SCRIPT
    assert "fs_worst_case + MAX_NEW_TOKENS > MAX_MODEL_LEN" in SCRIPT


def test_prediction_job_reuses_the_r2_frozen_prompt_template_verbatim() -> None:
    template = _block(SCRIPT, 'TEMPLATE = """', '"""')
    r2_template = _block(R2_SCRIPT, 'TEMPLATE = """', '"""')
    assert template == r2_template


def test_prediction_job_reuses_the_g2b_proven_serving_recipe() -> None:
    assert 'os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")' in SCRIPT
    assert 'quantization="bitsandbytes"' in SCRIPT
    assert "enforce_eager=True" in SCRIPT
    assert "enable_lora=True" in SCRIPT
    assert "max_lora_rank=16" in SCRIPT
    # Token prompts as dicts (the R0-proven vLLM 0.25.x calling convention).
    assert '{"prompt_token_ids": item["prompt_token_ids"]}' in SCRIPT
    assert '"vllm==0.25.1"' in SCRIPT


def test_prediction_job_never_reads_gold_links_or_sealed_labels() -> None:
    # Prompts need triggers + sentences only; gold links must be absent from the script.
    assert "gold_evt_links" not in SCRIPT
    assert '"gold_links_read": 0' in SCRIPT
    assert '"sealed_reads": 0' in SCRIPT


def test_prediction_job_deletes_raw_before_model_load_and_verifies_downloads() -> None:
    assert "shutil.rmtree(RAW_DIR)" in SCRIPT
    assert SCRIPT.index("shutil.rmtree(RAW_DIR)") < SCRIPT.index("LLM(")
    assert "raw extraction survived materialization" in SCRIPT
    assert "checksum mismatch" in SCRIPT
    assert "hash mismatch for frozen artifact" in SCRIPT
    # Both frozen inputs arrive hash-verified from the private evidence repo.
    assert 'ROLES_PATH = "plan2/rams_roles.jsonl"' in SCRIPT
    assert 'DEMOS_PATH = "plan2/fs_demonstrations.jsonl"' in SCRIPT


def test_prediction_job_gives_overflow_frames_explicit_records_in_all_systems() -> None:
    # The context rung was chosen on train+dev; sealed-split prompts may overflow.
    # They must appear as explicit context_overflow records, never silent exclusions,
    # and the same frames overflow in all three systems (identical comparison sets).
    assert '"context_overflow"' in SCRIPT
    assert "record count is not the full frame set" in SCRIPT
    assert "role counts diverge from the frozen split manifest" in SCRIPT
    fs_block = _block(SCRIPT, "def system_inputs", "def generate_arm")
    assert "live_frames" in fs_block  # FS runs on the same non-overflow set as ZS/QA


def test_prediction_job_persists_per_arm_to_the_private_evidence_repo_only() -> None:
    # ADR 0005: predictions with recoverable text go to the private evidence Dataset.
    assert 'EVIDENCE_REPO = "rosscyking/conformalextract-evidence"' in SCRIPT
    assert 'PREDICTIONS_PREFIX = "plan2/predictions"' in SCRIPT
    assert SCRIPT.count("private is not True") == 2  # arm persist + report persist
    assert "predictions path already exists" in SCRIPT  # never overwrite an arm
    assert "arm_already_persisted" in SCRIPT  # skip-if-exists resume semantics
    assert "parent_commit=info.sha" in SCRIPT


def test_prediction_job_runs_the_fresh_process_parsed_output_probe() -> None:
    assert "--probe" in SCRIPT
    assert "PROBE_OUTPUTS=" in SCRIPT
    assert "parsed_output_agreement" in SCRIPT
    assert "PROBE_SIZE = 12" in SCRIPT
    # The probe draws from the train split only - zero sealed-split concern.
    assert 'frame["role"] == "train"' in SCRIPT
    # Fresh process reuses the R2 training-stack quantization exactly.
    assert 'bnb_4bit_quant_type="nf4"' in SCRIPT
    assert "bnb_4bit_use_double_quant=True" in SCRIPT


def test_prediction_job_records_confidence_candidates_from_transition_logprobs() -> None:
    # The three predeclared candidates; empty output encodes as null (-inf downstream).
    for candidate in ('"mean"', '"tenth_percentile"', '"minimum"'):
        assert candidate in SCRIPT
    assert "transition log probabilities must be finite" in SCRIPT
    assert "logprob stream does not align with generated tokens" in SCRIPT


def test_prediction_job_report_is_text_free() -> None:
    report_section = _block(SCRIPT, "report = {", "PRED_REPORT=")
    for banned in ('"prompt"', '"raw_output"', '"sentences"', "raw_by_key"):
        assert banned not in report_section
    assert '"estimated_cost_usd"' in SCRIPT
    assert "HOURLY_RATE_USD = 0.80" in SCRIPT  # l4x1


def test_prediction_job_has_a_runtime_guard_between_arms() -> None:
    assert "MAX_ELAPSED_HOURS_BEFORE_NEXT_ARM = 12.0" in SCRIPT
    assert "time guard at" in SCRIPT
    assert '"partial"' in SCRIPT
