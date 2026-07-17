from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_gate0f_job_pins_training_runtime_and_qlora_contract() -> None:
    script = (ROOT / "jobs" / "gate0_qlora_smoke.py").read_text(encoding="utf-8")

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
        assert dependency in script

    for contract in (
        'REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"',
        'bnb_4bit_quant_type="nf4"',
        "r=16",
        "lora_alpha=32",
        "lora_dropout=0.05",
        'target_modules="all-linear"',
        "lr=2e-4",
        "torch.manual_seed(42)",
        "safe_serialization=True",
        '"synthetic_text_only": True',
        '"one_gradient_step": True',
        '"all_trainable_gradients_finite": True',
        '"only_adapter_parameters_trainable": True',
        '"fresh_process": True',
        '"greedy_completion_equivalence": True',
    ):
        assert contract in script

    assert "completion_only_mask" in script


def test_gate0f_job_refuses_repo_creation_and_evidence_overwrite() -> None:
    script = (ROOT / "jobs" / "gate0_qlora_smoke.py").read_text(encoding="utf-8")

    assert "create_repo(" not in script
    assert "file_exists(" in script
    assert "private is not True" in script
    assert "parent_commit=repo_info.sha" in script
    assert "evidence path already exists" in script


def test_gate0f_job_prints_recoverable_text_free_report_before_upload() -> None:
    script = (ROOT / "jobs" / "gate0_qlora_smoke.py").read_text(encoding="utf-8")

    report_print = script.index('print("GATE0F_REPORT_B64="')
    upload = script.index("persist_report(report, evidence_repo)")
    assert report_print < upload
    assert '"prompt"' not in script
    assert '"completion"' not in script
    assert "trackio" not in script.lower()
