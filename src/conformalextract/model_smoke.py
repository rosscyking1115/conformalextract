"""Pinned tokenizer/runtime checks and generated-token transition scoring."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import torch

from conformalextract.confidence import aggregate_transition_logprobs


def transition_logprobs_from_logits(
    *, logits: torch.Tensor, token_ids: torch.Tensor, prompt_length: int
) -> list[float]:
    """Score completion tokens only under the causal next-token distribution."""

    if logits.ndim != 2 or token_ids.ndim != 1 or logits.shape[0] != token_ids.shape[0]:
        raise ValueError("logits and token IDs must be aligned [sequence, vocabulary] arrays")
    if prompt_length < 1 or prompt_length >= token_ids.shape[0]:
        raise ValueError("prompt_length must leave at least one completion token")
    log_probabilities = torch.log_softmax(logits.float(), dim=-1)
    values: list[float] = []
    for target_position in range(prompt_length, token_ids.shape[0]):
        source_position = target_position - 1
        token_id = int(token_ids[target_position])
        values.append(float(log_probabilities[source_position, token_id]))
    return values


def validate_local_model_metadata(root: Path) -> dict[str, Any]:
    """Validate pinned public model metadata without downloading or loading model weights."""

    from transformers import AutoTokenizer

    required = [
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "LICENSE",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing pinned metadata: {', '.join(missing)}")
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(root, local_files_only=True)  # type: ignore[no-untyped-call]
    chat_template = str(tokenizer.chat_template)

    dummy_logits = torch.tensor(
        [[4.0, 1.0, 0.0], [0.0, 4.0, 1.0], [1.0, 0.0, 4.0]], dtype=torch.float32
    )
    dummy_ids = torch.tensor([0, 1, 2], dtype=torch.long)
    transition_scores = transition_logprobs_from_logits(
        logits=dummy_logits, token_ids=dummy_ids, prompt_length=1
    )
    aggregates = aggregate_transition_logprobs(transition_scores)
    return {
        "schema_version": "1",
        "status": "pass",
        "gate0e_pass": True,
        "model_id": "Qwen/Qwen3-4B-Instruct-2507",
        "model_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
        "model_type": config["model_type"],
        "transformers_version": importlib.metadata.version("transformers"),
        "torch_version": importlib.metadata.version("torch"),
        "tokenizer_vocabulary_size": len(tokenizer),
        "chat_template_sha256": hashlib.sha256(chat_template.encode()).hexdigest(),
        "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": 512},
        "score_orientation": "higher transition log probability is better",
        "completion_only_scoring": True,
        "worked_score": {
            "transition_count": len(transition_scores),
            "mean": aggregates.mean,
            "tenth_percentile": aggregates.tenth_percentile,
            "minimum": aggregates.minimum,
        },
        "actual_model_generation_pass": False,
        "actual_model_generation_required_at_gate": "0F save/reload smoke",
    }
