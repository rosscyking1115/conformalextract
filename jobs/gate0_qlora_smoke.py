# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "accelerate==1.14.0",
#   "bitsandbytes>=0.45,<1",
#   "peft==0.19.1",
#   "safetensors>=0.8,<1",
#   "torch>=2.6,<3",
#   "transformers==4.57.6",
# ]
# ///
"""Synthetic, restricted-text-free QLoRA save/reload smoke for Hugging Face Jobs."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import torch
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ADAPTER_DIR = Path("/tmp/conformalextract-gate0-adapter")


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
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )


def adapter_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if item.is_file():
            result[item.name] = hashlib.sha256(item.read_bytes()).hexdigest()
    return result


def reload_smoke(adapter_dir: Path) -> None:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    model = PeftModel.from_pretrained(load_base(), adapter_dir)
    prompt = 'Return JSON only: {"arguments":[]}'
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated = model.generate(**inputs, do_sample=False, max_new_tokens=4)
    completion = generated[0, inputs["input_ids"].shape[1] :].detach().cpu().numpy().tobytes()
    print(
        "RELOAD_EVIDENCE="
        + json.dumps(
            {
                "revision": REVISION,
                "generated_token_count": int(generated.shape[1] - inputs["input_ids"].shape[1]),
                "generated_token_sha256": hashlib.sha256(completion).hexdigest(),
                "adapter_hashes": adapter_hashes(adapter_dir),
            },
            sort_keys=True,
        )
    )


def train_smoke() -> None:
    torch.manual_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    tokenizer.pad_token = tokenizer.eos_token
    model = prepare_model_for_kbit_training(load_base())
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
    gradients = [parameter.grad for parameter in model.parameters() if parameter.requires_grad]
    if not gradients or any(gradient is None for gradient in gradients):
        raise RuntimeError("missing adapter gradients")
    optimizer.step()
    model.save_pretrained(ADAPTER_DIR, safe_serialization=True)
    trainable = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    print(
        "TRAIN_EVIDENCE="
        + json.dumps(
            {
                "revision": REVISION,
                "loss": float(output.loss.detach().cpu()),
                "trainable_parameters": trainable,
                "adapter_hashes": adapter_hashes(ADAPTER_DIR),
                "completion_only_mask": True,
            },
            sort_keys=True,
        )
    )
    del model, optimizer, output
    gc.collect()
    torch.cuda.empty_cache()
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--reload", str(ADAPTER_DIR)], check=True
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=Path)
    arguments = parser.parse_args()
    if arguments.reload:
        reload_smoke(arguments.reload)
    else:
        train_smoke()


if __name__ == "__main__":
    main()
