# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "vllm==0.25.1",
#   "numpy",
# ]
# ///
"""R0 inference-throughput benchmark for ConformalExtract (DRAFT — not yet launched).

Measures vLLM batched-generation throughput for Qwen3-4B on the *real RAMS prompt-length
distribution* so the full-programme generation cost can be forecast against the remaining
$24.7992 Hugging Face Jobs cap BEFORE committing to R1/R2 + full prediction generation.

Text-free by construction: it generates from RANDOM token prompts whose *lengths* match the
frozen RAMS distribution (token counts are metadata, not source text). It never reads,
downloads, or uploads raw RAMS/WikiEvents text, sealed labels, or predictions. It persists /
prints only aggregate throughput metrics.

Design follows the 2026-07-18 frontier check (docs/frontier-check/findings.md, cluster C):
1x Nvidia L4 ($0.80/hr); vLLM continuous batching (not padded transformers .generate());
benchmark at the true length distribution; report total + output tokens/sec and items/hour.
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

# The slim uv image has the CUDA runtime but no toolkit (nvcc). vLLM auto-enables the
# flashinfer sampler when flashinfer is installed, and flashinfer JIT-compiles its kernels
# at runtime (needs nvcc). Force the native PyTorch sampler so no runtime compilation occurs.
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"


def sample_prompt_lengths(
    rng: np.random.Generator, *, count: int, mean: int, low: int, high: int
) -> list[int]:
    """Draw input-token lengths matched to the frozen RAMS distribution (clipped)."""

    raw = rng.normal(loc=mean, scale=(high - low) / 4.0, size=count)
    return [int(min(high, max(low, round(value)))) for value in raw]


def build_random_token_prompts(
    lengths: list[int], vocab_size: int, rng: np.random.Generator
) -> list[list[int]]:
    """Random in-vocab token-id prompts of the given lengths — no natural-language text."""

    return [rng.integers(0, vocab_size, size=length).tolist() for length in lengths]


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    # Imported here so --dry-run works without a GPU/vLLM install.
    from vllm import LLM, SamplingParams

    rng = np.random.default_rng(args.seed)
    llm = LLM(
        model=MODEL_ID,
        revision=MODEL_REVISION,
        dtype="bfloat16",
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        # The slim uv image ships the CUDA runtime but not the toolkit (nvcc), which
        # vLLM's torch.compile path needs. Eager mode skips compilation entirely and
        # yields a conservative throughput floor for the cost forecast.
        enforce_eager=True,
    )
    vocab_size = llm.get_tokenizer().vocab_size
    lengths = sample_prompt_lengths(
        rng, count=args.num_prompts, mean=args.mean_input, low=args.min_input, high=args.max_input
    )
    prompt_token_ids = build_random_token_prompts(lengths, vocab_size, rng)
    # vLLM 0.25.x takes token-id prompts positionally as prompt dicts, not a kwarg.
    token_prompts = [{"prompt_token_ids": ids} for ids in prompt_token_ids]
    sampling = SamplingParams(temperature=0.0, max_tokens=args.max_output)

    started = time.monotonic()
    outputs = llm.generate(token_prompts, sampling_params=sampling)
    elapsed = time.monotonic() - started

    input_tokens = int(sum(lengths))
    output_tokens = int(sum(len(o.outputs[0].token_ids) for o in outputs))
    total_tokens = input_tokens + output_tokens
    items_per_hour = args.num_prompts / elapsed * 3600.0
    return {
        "schema_version": "1",
        "status": "benchmark",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "flavor": args.flavor,
        "hourly_rate_usd": args.hourly_rate_usd,
        "num_prompts": args.num_prompts,
        "input_token_distribution": {
            "mean": args.mean_input, "min": args.min_input, "max": args.max_input,
            "measured_mean": input_tokens / args.num_prompts,
        },
        "max_output_tokens": args.max_output,
        "measured_output_tokens_total": output_tokens,
        "measured_output_tokens_mean": output_tokens / args.num_prompts,
        "elapsed_seconds": elapsed,
        "aggregate_tokens_per_second": total_tokens / elapsed,
        "output_tokens_per_second": output_tokens / elapsed,
        "items_per_hour": items_per_hour,
        "cost_per_1m_tokens_usd": args.hourly_rate_usd / (total_tokens / elapsed * 3600.0 / 1e6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ConformalExtract R0 inference benchmark")
    parser.add_argument("--num-prompts", type=int, default=256)
    parser.add_argument("--mean-input", type=int, default=1500)
    parser.add_argument("--min-input", type=int, default=512)
    parser.add_argument("--max-input", type=int, default=4096)
    parser.add_argument("--max-output", type=int, default=512)
    parser.add_argument("--max-model-len", type=int, default=4608)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    parser.add_argument("--flavor", default="l4x1")
    parser.add_argument("--hourly-rate-usd", type=float, default=0.80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate args without loading vLLM."
    )
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({"status": "dry_run_ok", "flavor": args.flavor}, sort_keys=True))
        return
    report = run_benchmark(args)
    print("R0_BENCHMARK_REPORT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
