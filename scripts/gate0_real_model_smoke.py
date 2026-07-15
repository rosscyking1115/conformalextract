"""Run the real pinned Qwen Gate 0E smoke on 20 deterministic RAMS development records."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
DEV_PATH = Path("data/raw/rams/RAMS_1.0c/data/dev.jsonlines")
ONTOLOGY_PATH = Path("data/raw/rams/RAMS_1.0c/scorer/event_role_multiplicities.txt")
CACHE_DIR = Path("data/private/hf-cache")
OUTPUT_PATH = Path("evidence/gate0/model_score_smoke.v3.json")
ROLE_PATTERN = re.compile(r"^evt\d+arg\d+(.+)$")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_ontology() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in ONTOLOGY_PATH.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        result[fields[0]] = fields[1::2]
    return result


def load_examples() -> list[dict[str, Any]]:
    records = [json.loads(line) for line in DEV_PATH.read_text(encoding="utf-8").splitlines()]
    records.sort(key=lambda record: hashlib.sha256(str(record["doc_key"]).encode()).hexdigest())
    return records[:20]


def make_prompt(record: dict[str, Any], roles: list[str]) -> str:
    tokens = [token for sentence in record["sentences"] for token in sentence]
    trigger = record["evt_triggers"][0]
    event_type = trigger[2][0][0]
    return (
        "You extract grounded event arguments for one given trigger.\n"
        f"Event type: {event_type}\n"
        f"Trigger token span [start, end): {trigger[0]}, {trigger[1] + 1}\n"
        f"Allowed roles: {json.dumps(roles, separators=(',', ':'))}\n"
        f"Document tokens: {json.dumps(list(enumerate(tokens)), separators=(',', ':'))}\n"
        "Return one JSON object only with this schema: "
        '{"arguments":[{"role":"<allowed role>","start":0,"end":1,'
        '"text":"<exact token text>"}]}. '
        "Use half-open token spans. Copy grounded text exactly. Do not infer ungrounded text. "
        'When no argument is present return {"arguments":[]}.'
    )


def parse_arguments(
    raw: str, tokens: list[str], roles: set[str]
) -> tuple[str, Counter[tuple[str, int, int]]]:
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return "invalid_json", Counter()
    if not isinstance(decoded, dict) or set(decoded) != {"arguments"}:
        return "schema_violation", Counter()
    arguments = decoded["arguments"]
    if not isinstance(arguments, list):
        return "schema_violation", Counter()
    result: Counter[tuple[str, int, int]] = Counter()
    for item in arguments:
        if not isinstance(item, dict) or set(item) != {"role", "start", "end", "text"}:
            return "schema_violation", Counter()
        role, start, end, text = item["role"], item["start"], item["end"], item["text"]
        if role not in roles:
            return "unknown_role", Counter()
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or not 0 <= start < end <= len(tokens)
        ):
            return "invalid_span", Counter()
        if not isinstance(text, str) or text != " ".join(tokens[start:end]):
            return "ungrounded_span", Counter()
        result[(role, start, end)] += 1
    return "valid", result


def gold_arguments(record: dict[str, Any]) -> Counter[tuple[str, int, int]]:
    result: Counter[tuple[str, int, int]] = Counter()
    for link in record["gold_evt_links"]:
        match = ROLE_PATTERN.match(link[2])
        if match is None:
            raise ValueError("unexpected RAMS role encoding")
        result[(match.group(1), link[1][0], link[1][1] + 1)] += 1
    return result


def document_loss(
    gold: Counter[tuple[str, int, int]], predicted: Counter[tuple[str, int, int]]
) -> float:
    true_positives = sum((gold & predicted).values())
    gold_count = sum(gold.values())
    prediction_count = sum(predicted.values())
    if gold_count == 0 and prediction_count == 0:
        return 0.0
    if true_positives == 0:
        return 1.0
    precision = true_positives / prediction_count
    recall = true_positives / gold_count
    return 1.0 - 2.0 * precision * recall / (precision + recall)


def risk_coverage_auc(scores: list[float], losses: list[float]) -> float:
    order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
    ordered_losses = np.asarray([losses[index] for index in order])
    risks = np.cumsum(ordered_losses) / np.arange(1, len(losses) + 1)
    coverage = np.arange(1, len(losses) + 1) / len(losses)
    return float(np.trapezoid(np.r_[risks[0], risks], np.r_[0.0, coverage]))


def generate_one(model: Any, tokenizer: Any, prompt: str) -> tuple[list[int], list[float], str]:
    messages = [{"role": "user", "content": prompt}]
    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
    ).to(model.device)
    attention_mask = torch.ones_like(input_ids)
    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            num_beams=1,
            max_new_tokens=64,
            return_dict_in_generate=True,
            output_scores=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output.sequences[0, input_ids.shape[1] :]
    transition = model.compute_transition_scores(
        output.sequences, output.scores, normalize_logits=True
    )[0]
    token_ids = [int(value) for value in generated.detach().cpu()]
    scores = [float(value) for value in transition.detach().cpu()]
    if len(token_ids) != len(scores):
        raise RuntimeError("generated-token and transition-score alignment failed")
    return token_ids, scores, tokenizer.decode(generated, skip_special_tokens=True)


def main() -> None:
    started = time.monotonic()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the real model smoke")
    ontology = load_ontology()
    examples = load_examples()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION, cache_dir=CACHE_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        cache_dir=CACHE_DIR,
        dtype=torch.bfloat16,
        device_map="auto",
        max_memory={0: "5GiB", "cpu": "24GiB"},
    )
    model.eval()
    evidence_records: list[dict[str, Any]] = []
    determinism_pass = True
    score_values: dict[str, list[float]] = {
        "mean": [],
        "tenth_percentile": [],
        "minimum": [],
    }
    losses: list[float] = []
    for index, record in enumerate(examples):
        event_type = record["evt_triggers"][0][2][0][0]
        roles = ontology[event_type]
        tokens = [token for sentence in record["sentences"] for token in sentence]
        prompt = make_prompt(record, roles)
        token_ids, transition_scores, raw_output = generate_one(model, tokenizer, prompt)
        status, predicted = parse_arguments(raw_output, tokens, set(roles))
        loss = 1.0 if status != "valid" else document_loss(gold_arguments(record), predicted)
        losses.append(loss)
        if status == "valid" and transition_scores:
            candidates = {
                "mean": float(np.mean(transition_scores)),
                "tenth_percentile": float(np.quantile(transition_scores, 0.1)),
                "minimum": float(np.min(transition_scores)),
            }
        else:
            candidates = dict.fromkeys(score_values, -1e9)
        for name, value in candidates.items():
            score_values[name].append(float(value))
        if index < 3:
            repeated_ids, repeated_scores, _ = generate_one(model, tokenizer, prompt)
            determinism_pass &= token_ids == repeated_ids and np.allclose(
                transition_scores, repeated_scores, rtol=0.0, atol=0.0
            )
        evidence_records.append(
            {
                "doc_key_sha256": hashlib.sha256(str(record["doc_key"]).encode()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "output_sha256": hashlib.sha256(raw_output.encode()).hexdigest(),
                "generated_token_count": len(token_ids),
                "transition_score_count": len(transition_scores),
                "status": status,
                "loss": loss,
                "scores": None if status != "valid" else candidates,
            }
        )
    auc = {name: risk_coverage_auc(values, losses) for name, values in score_values.items()}
    tie_order = ("mean", "tenth_percentile", "minimum")
    selected = min(tie_order, key=lambda name: (auc[name], tie_order.index(name)))
    report = {
        "schema_version": "3",
        "status": "pass" if determinism_pass else "fail",
        "gate0e_pass": determinism_pass,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "real_development_generations": len(examples),
        "restricted_source_text_in_evidence": False,
        "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": 64},
        "load_mode": "BF16 with explicit GPU/CPU offload; NF4 compatibility is Gate 0F",
        "completion_only_transition_alignment": all(
            record["generated_token_count"] == record["transition_score_count"]
            for record in evidence_records
        ),
        "determinism_repeated_examples": 3,
        "determinism_pass": determinism_pass,
        "confidence_auc": auc,
        "selected_confidence": selected,
        "confidence_selection_data_role": "development only",
        "structural_failure_count": sum(record["status"] != "valid" for record in evidence_records),
        "records": evidence_records,
        "runtime": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "accelerate": importlib.metadata.version("accelerate"),
            "bitsandbytes": importlib.metadata.version("bitsandbytes"),
            "gpu": torch.cuda.get_device_name(0),
        },
        "duration_seconds": time.monotonic() - started,
    }
    if not math.isfinite(report["duration_seconds"]):
        raise RuntimeError("invalid runtime duration")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with OUTPUT_PATH.open("xb") as handle:
        handle.write(data)
    print(json.dumps({"output": str(OUTPUT_PATH), "sha256": hashlib.sha256(data).hexdigest()}))
    if not report["gate0e_pass"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
