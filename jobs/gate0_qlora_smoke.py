# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "accelerate==1.14.0",
#   "bitsandbytes==0.49.2",
#   "huggingface-hub==0.36.2",
#   "numpy==2.5.1",
#   "peft==0.19.1",
#   "safetensors==0.8.0",
#   "torch==2.13.0",
#   "transformers==4.57.6",
# ]
# ///
"""Synthetic, restricted-text-free QLoRA save/reload smoke for Hugging Face Jobs."""

from __future__ import annotations

import argparse
import base64
import gc
import hashlib
import importlib.metadata
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import torch
from huggingface_hub import CommitOperationAdd, HfApi
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ADAPTER_DIR = Path("/tmp/conformalextract-gate0-adapter")
EVIDENCE_PATH = "gate0/qlora_smoke.v1.json"


def load_base():  # type: ignore[no-untyped-def]
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    return AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )


def adapter_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if item.is_file():
            result[item.relative_to(path).as_posix()] = hashlib.sha256(
                item.read_bytes()
            ).hexdigest()
    return result


def parameter_dtype_counts(model) -> dict[str, int]:  # type: ignore[no-untyped-def]
    counts: dict[str, int] = {}
    for parameter in model.parameters():
        name = str(parameter.dtype)
        counts[name] = counts.get(name, 0) + parameter.numel()
    return counts


def generation_evidence(model, tokenizer) -> dict[str, object]:  # type: ignore[no-untyped-def]
    model.eval()
    model.config.use_cache = True
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    prompt = 'Return JSON only: {"arguments":[]}'
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            do_sample=False,
            num_beams=1,
            max_new_tokens=4,
        )
    completion = generated[0, inputs["input_ids"].shape[1] :].detach().cpu().numpy().tobytes()
    return {
        "generated_token_count": int(generated.shape[1] - inputs["input_ids"].shape[1]),
        "generated_token_sha256": hashlib.sha256(completion).hexdigest(),
        "gradient_checkpointing": bool(model.is_gradient_checkpointing),
        "parameter_dtype_counts": parameter_dtype_counts(model),
        "use_cache": bool(model.config.use_cache),
    }


def reload_smoke(adapter_dir: Path) -> None:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    prepared_base = prepare_model_for_kbit_training(
        load_base(), use_gradient_checkpointing=False
    )
    model = PeftModel.from_pretrained(prepared_base, adapter_dir)
    model.gradient_checkpointing_disable()
    generation = generation_evidence(model, tokenizer)
    print(
        "RELOAD_EVIDENCE="
        + json.dumps(
            {
                "revision": REVISION,
                **generation,
                "adapter_hashes": adapter_hashes(adapter_dir),
                "fresh_process": True,
            },
            sort_keys=True,
        )
    )


def persist_report(report: dict[str, object], repo_id: str) -> dict[str, str]:
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    api = HfApi()
    repo_info = api.dataset_info(repo_id)
    if repo_info.private is not True:
        raise RuntimeError("Gate 0F evidence repository must already exist and be private")
    if api.file_exists(
        repo_id=repo_id,
        filename=EVIDENCE_PATH,
        repo_type="dataset",
        revision=repo_info.sha,
    ):
        raise RuntimeError(f"evidence path already exists: {EVIDENCE_PATH}")
    commit = api.create_commit(
        repo_id=repo_id,
        repo_type="dataset",
        operations=[
            CommitOperationAdd(path_in_repo=EVIDENCE_PATH, path_or_fileobj=io.BytesIO(data))
        ],
        commit_message="evidence: persist Gate 0F QLoRA smoke",
        parent_commit=repo_info.sha,
    )
    return {
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "hub_commit_oid": commit.oid,
    }


def train_smoke(evidence_repo: str) -> None:
    started = time.monotonic()
    torch.manual_seed(42)
    if ADAPTER_DIR.exists():
        raise RuntimeError(f"refusing to overwrite adapter directory: {ADAPTER_DIR}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    tokenizer.pad_token = tokenizer.eos_token
    model = prepare_model_for_kbit_training(
        load_base(), use_gradient_checkpointing=True
    )
    model = get_peft_model(
        model,
        LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules="all-linear",
            task_type="CAUSAL_LM",
        ),
    )
    prompt = "Extract arguments as JSON. Synthetic tokens: alpha attacked beta.\nAnswer:"
    completion = '{"arguments":[{"role":"Attacker","start":0,"end":1,"text":"alpha"}]}'
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    completion_ids = tokenizer(completion + tokenizer.eos_token, add_special_tokens=False)[
        "input_ids"
    ]
    input_ids = torch.tensor([prompt_ids + completion_ids], device=model.device)
    labels = torch.tensor([[-100] * len(prompt_ids) + completion_ids], device=model.device)
    attention_mask = torch.ones_like(input_ids)
    model.train()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=2e-4)
    output = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
    if not torch.isfinite(output.loss):
        raise RuntimeError("non-finite smoke loss")
    output.loss.backward()
    trainable_parameters = [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]
    trainable_names = [name for name, _ in trainable_parameters]
    if not trainable_names or any("lora_" not in name for name in trainable_names):
        raise RuntimeError("non-adapter parameters are trainable")
    gradients = [parameter.grad for _, parameter in trainable_parameters]
    if not gradients or any(gradient is None for gradient in gradients):
        raise RuntimeError("missing adapter gradients")
    finite_gradients = all(
        torch.isfinite(gradient).all().item()
        for gradient in gradients
        if gradient is not None
    )
    if not finite_gradients:
        raise RuntimeError("non-finite adapter gradients")
    optimizer.step()
    loss_value = float(output.loss.detach().cpu())
    model.gradient_checkpointing_disable()
    model.config.use_cache = True
    model.save_pretrained(ADAPTER_DIR, safe_serialization=True)
    saved_hashes = adapter_hashes(ADAPTER_DIR)
    if "adapter_model.safetensors" not in saved_hashes:
        raise RuntimeError("adapter was not saved as safetensors")
    before_reload = generation_evidence(model, tokenizer)
    trainable = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    train_evidence = {
        "revision": REVISION,
        "loss": loss_value,
        "trainable_parameters": trainable,
        "only_adapter_parameters_trainable": True,
        "all_trainable_gradients_present": True,
        "all_trainable_gradients_finite": True,
        "one_gradient_step": True,
        "adapter_hashes": saved_hashes,
        "completion_only_mask": True,
        "prompt_token_count": len(prompt_ids),
        "completion_token_count": len(completion_ids),
        "before_reload": before_reload,
    }
    del model, optimizer, output
    gc.collect()
    torch.cuda.empty_cache()
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--reload", str(ADAPTER_DIR)],
        check=True,
        capture_output=True,
        text=True,
    )
    line = next(
        value for value in completed.stdout.splitlines() if value.startswith("RELOAD_EVIDENCE=")
    )
    reload_evidence = json.loads(line.removeprefix("RELOAD_EVIDENCE="))
    if reload_evidence["adapter_hashes"] != saved_hashes:
        raise RuntimeError("fresh-process adapter hashes changed")
    if int(reload_evidence["generated_token_count"]) <= 0:
        raise RuntimeError("fresh-process reload did not generate tokens")
    greedy_completion_equivalence = (
        before_reload["generated_token_sha256"] == reload_evidence["generated_token_sha256"]
    )
    diagnostic: dict[str, object] = {
        "schema_version": "1",
        "status": "diagnostic",
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "synthetic_text_only": True,
        "adapter_hashes_equal": reload_evidence["adapter_hashes"] == saved_hashes,
        "before_reload": before_reload,
        "reload": reload_evidence,
        "greedy_completion_equivalence": greedy_completion_equivalence,
        "reload_base_prepared_for_kbit": True,
    }
    diagnostic_bytes = (
        json.dumps(diagnostic, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    print(
        "GATE0F_DIAGNOSTIC_B64=" + base64.b64encode(diagnostic_bytes).decode(),
        flush=True,
    )
    if not greedy_completion_equivalence:
        raise RuntimeError("fresh-process adapter reload changed the greedy completion")
    report: dict[str, object] = {
        "schema_version": "1",
        "status": "pass",
        "gate0f_pass": True,
        "synthetic_text_only": True,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "seed": 42,
        "quantization": {
            "load_in_4bit": True,
            "quant_type": "nf4",
            "compute_dtype": "bfloat16",
            "double_quantization": True,
        },
        "lora": {
            "rank": 16,
            "alpha": 32,
            "dropout": 0.05,
            "target_modules": "all-linear",
        },
        "optimizer": {"name": "AdamW", "learning_rate": 2e-4},
        "train": train_evidence,
        "reload": reload_evidence,
        "greedy_completion_equivalence": True,
        "runtime": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "accelerate": importlib.metadata.version("accelerate"),
            "bitsandbytes": importlib.metadata.version("bitsandbytes"),
            "peft": importlib.metadata.version("peft"),
            "safetensors": importlib.metadata.version("safetensors"),
            "gpu": torch.cuda.get_device_name(0),
        },
        "duration_seconds": time.monotonic() - started,
    }
    report_bytes = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    print("GATE0F_REPORT_B64=" + base64.b64encode(report_bytes).decode(), flush=True)
    persistence = persist_report(report, evidence_repo)
    print(
        json.dumps(
            {
                "evidence_repo": evidence_repo,
                "evidence_path": EVIDENCE_PATH,
                **persistence,
                "status": "pass",
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=Path)
    parser.add_argument("--evidence-repo", default="rosscyking/conformalextract-evidence")
    arguments = parser.parse_args()
    if arguments.reload:
        reload_smoke(arguments.reload)
    else:
        train_smoke(arguments.evidence_repo)


if __name__ == "__main__":
    main()
