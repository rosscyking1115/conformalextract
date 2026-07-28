# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "vllm==0.25.1",
#   "numpy",
#   "bitsandbytes==0.49.2",
#   "peft==0.19.1",
# ]
# ///
"""G2b serving benchmark: the frozen 4-bit inference stack, with and without the QA adapter.

The R0 throughput was measured on the bf16 base; the frozen contract serves all three systems
on the 4-bit stack, and the QA system additionally loads the trained LoRA adapter. This job
measures items/hour for (a) 4-bit base (ZS/FS proxy) and (b) 4-bit base + QA adapter, on the
real prompt-length distribution, preferring vLLM's bitsandbytes path and falling back to a
length-sorted transformers batch measurement if the vLLM path fails. Text-free (random in-vocab
tokens at real lengths); nothing persisted; report is aggregate metrics via logs only.
"""

from __future__ import annotations

import json
import os
import time
import traceback

import numpy as np

os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"
ADAPTER_REVISION = "edd69373be3d46ae2a982e555f4ec9549491e8e4"  # R2 copy B commit
NUM_PROMPTS = 96
MEAN_INPUT, MIN_INPUT, MAX_INPUT = 2000, 512, 6144
MAX_OUTPUT = 512
MAX_MODEL_LEN = 6656
HOURLY_RATE_USD = 0.80  # l4x1
SEED = 42


def sample_lengths(rng: np.random.Generator, count: int) -> list[int]:
    raw = rng.normal(loc=MEAN_INPUT, scale=(MAX_INPUT - MIN_INPUT) / 4.0, size=count)
    return [int(min(MAX_INPUT, max(MIN_INPUT, round(value)))) for value in raw]


def random_token_prompts(vocab_size: int, rng: np.random.Generator) -> list[list[int]]:
    return [
        rng.integers(0, vocab_size, size=length).tolist()
        for length in sample_lengths(rng, NUM_PROMPTS)
    ]


def arm_metrics(name: str, elapsed: float, prompts: int, output_tokens: int) -> dict:
    return {
        f"{name}_elapsed_seconds": elapsed,
        f"{name}_items_per_hour": prompts / elapsed * 3600.0,
        f"{name}_output_tokens_per_second": output_tokens / elapsed,
    }


def run_vllm() -> dict:
    from huggingface_hub import snapshot_download
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    adapter_path = snapshot_download(ADAPTER_REPO, revision=ADAPTER_REVISION)
    llm = LLM(
        model=MODEL_ID,
        revision=MODEL_REVISION,
        quantization="bitsandbytes",
        dtype="bfloat16",
        gpu_memory_utilization=0.90,
        max_model_len=MAX_MODEL_LEN,
        enforce_eager=True,
        enable_lora=True,
        max_lora_rank=16,
    )
    rng = np.random.default_rng(SEED)
    vocab_size = llm.get_tokenizer().vocab_size
    prompts = [
        {"prompt_token_ids": ids} for ids in random_token_prompts(vocab_size, rng)
    ]
    sampling = SamplingParams(temperature=0.0, max_tokens=MAX_OUTPUT)

    started = time.monotonic()
    base_out = llm.generate(prompts, sampling_params=sampling)
    base_elapsed = time.monotonic() - started
    base_tokens = sum(len(o.outputs[0].token_ids) for o in base_out)

    lora = LoRARequest("qa", 1, adapter_path)
    started = time.monotonic()
    qa_out = llm.generate(prompts, sampling_params=sampling, lora_request=lora)
    qa_elapsed = time.monotonic() - started
    qa_tokens = sum(len(o.outputs[0].token_ids) for o in qa_out)

    return {
        "path_used": "vllm_bitsandbytes",
        **arm_metrics("base_4bit", base_elapsed, NUM_PROMPTS, base_tokens),
        **arm_metrics("qa_4bit_lora", qa_elapsed, NUM_PROMPTS, qa_tokens),
    }


def run_transformers_fallback() -> dict:
    import torch
    from huggingface_hub import snapshot_download
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    sample = 24  # smaller sample; extrapolated
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, quantization_config=quantization,
        dtype=torch.bfloat16, device_map="auto",
    )
    model.config.use_cache = True
    rng = np.random.default_rng(SEED)
    prompt_ids = random_token_prompts(tokenizer.vocab_size, rng)[:sample]
    prompt_ids.sort(key=len)  # length-sorted batching to cut padding waste

    def measure(m) -> tuple[float, int]:
        started = time.monotonic()
        tokens = 0
        batch_size = 4
        for index in range(0, sample, batch_size):
            batch = prompt_ids[index : index + batch_size]
            longest = max(len(ids) for ids in batch)
            padded = torch.tensor(
                [[tokenizer.pad_token_id] * (longest - len(ids)) + ids for ids in batch]
            ).to(m.device)
            attention = (padded != tokenizer.pad_token_id).long()
            with torch.no_grad():
                out = m.generate(
                    input_ids=padded, attention_mask=attention,
                    do_sample=False, num_beams=1, max_new_tokens=MAX_OUTPUT,
                )
            tokens += int(out.shape[0] * (out.shape[1] - padded.shape[1]))
        return time.monotonic() - started, tokens

    base_elapsed, base_tokens = measure(model)
    adapter_path = snapshot_download(ADAPTER_REPO, revision=ADAPTER_REVISION)
    model = PeftModel.from_pretrained(model, adapter_path)
    qa_elapsed, qa_tokens = measure(model)
    return {
        "path_used": "transformers_fallback",
        **arm_metrics("base_4bit", base_elapsed, sample, base_tokens),
        **arm_metrics("qa_4bit_lora", qa_elapsed, sample, qa_tokens),
    }


def main() -> None:
    started = time.monotonic()
    try:
        result = run_vllm()
        vllm_error = None
    except Exception:  # fall back to the proven transformers stack, record why
        vllm_error = traceback.format_exc().splitlines()[-1][:300]
        result = run_transformers_fallback()
    report = {
        "schema_version": "1",
        "status": "benchmark",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "adapter_repo": ADAPTER_REPO,
        "adapter_revision": ADAPTER_REVISION,
        "num_prompts": NUM_PROMPTS,
        "input_distribution": {"mean": MEAN_INPUT, "min": MIN_INPUT, "max": MAX_INPUT},
        "max_output_tokens": MAX_OUTPUT,
        "vllm_error": vllm_error,
        **result,
        "duration_seconds": time.monotonic() - started,
        "estimated_cost_usd": (time.monotonic() - started) / 3600.0 * HOURLY_RATE_USD,
    }
    print("G2B_BENCHMARK_REPORT=" + json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
