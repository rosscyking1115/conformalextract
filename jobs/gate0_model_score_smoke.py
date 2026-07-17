# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "accelerate==1.14.0",
#   "huggingface-hub==0.36.2",
#   "numpy==2.5.1",
#   "torch==2.13.0",
#   "transformers==4.57.6",
# ]
# ///
"""Run Gate 0E on pinned Qwen and ephemeral, checksum-verified RAMS development data."""

# ruff: noqa: E501 -- frozen SHA-256 key/value pairs are intentionally unwrapped.

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
import re
import sys
import tarfile
import tempfile
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
from huggingface_hub import HfApi
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
RAMS_URL = "https://nlp.jhu.edu/rams/RAMS_1.0c.tar.gz"
RAMS_SHA256 = "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54"
EVIDENCE_PATH = "gate0/model_score_smoke.v3.json"
ROLE_PATTERN = re.compile(r"^evt\d+arg\d+(.+)$")
WORST_CONFIDENCE = float("-inf")
FROZEN_SPLIT_MANIFEST_SHA256 = "17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3"
FROZEN_DEVELOPMENT_SELECTION_SHA256 = (
    "4092e154b2581e943f2a56ea15c40103a1b98796126404fdf8f5604017b12772"
)
FROZEN_DEVELOPMENT_GROUPS = {
    "0014444ddab007937eb0f748e6b524e32fbdccf41899cd8b5ea8caf3436f08a0": "87b81152250e324332712fec5c144f1e8945b06185f6cc6e871bc6101391251f",
    "001f9e4fbf33516da41517bcb3e298b75ee458843a38ba188887aa6855678f96": "58d4c009430246b113970486fa193f1b205042c4971f1fccd426d8c5fd782b89",
    "015e0aae80d69b1db0fe97c651727c60601fd5a4d5e44e1aeebba5d66e9b10d7": "0520fddedc9651cbb8975370ad78aa0a592919b11a5e7da0a2ad2b8db479d546",
    "01c2c9512ddc70cb4a16b669b049bade55319255a7a7623aa6a169853d8b8171": "6e0a946fe98d8e6793f735e18fefb91fd4bb7e0308782c5b2b71e42307be437c",
    "025549ab347a7563686eb6dcb37b2dca74f987e27325fa107e36a6801864e98a": "7fac332429e348732feedc36b2bf48638b41490345e68ed37809210f7c6fba33",
    "027545285ed9b5d6c52c3951fa4389db92ae47ec21cbae98869fa2331a5d9f6d": "bba889c55f5b9cb54955ab8588fd9936e2cb31f698bc4d1ad865b0179df9a6fd",
    "028b9086c12c4bde55bdde92533605316657f680998fccdc8144536fd7f84c74": "0c6e6c254a935a253b22fe1f07a56819fcc095d076ad796baf5a307e2163a75b",
    "02fef2303dab72dc806b8fc1c8413d072762a3a1796d445e3878f34d45d008f5": "70e8d86cbf535fea3fae06185000345e583bfce2d419bb0c603b08ffee1ff6ba",
    "033b8c83f767f2a447e074cd08e4c01c9dcb44075aaefffe86c9b420cf7d5026": "7db42192c4cb87fd6ba9ab4f5251b49202940f9dbe56949fa354f0df62d354bc",
    "034ed9920bfa53c37dbaee59f7776574fcc8b8bc27a2caddde404b82189d5d98": "3e77618fa770b97932be7b9afa6c9f685821b208c221a90948ff1763f82a2415",
    "035d8d87a826fd9522a26e20312964979b514c60caea1c36f8ece83e391b85a4": "73ee19594dcbcaa406b9615fdcc94e5f30b767c8c06847c55c49683e5cef7d20",
    "035f9961561caac3db56e429f6ae82b4d356cb0b7424acb46d1846b844171ad8": "035f9961561caac3db56e429f6ae82b4d356cb0b7424acb46d1846b844171ad8",
    "038140e4de095a81fdcb85c042e1b6ca6b32378fbd4c92d515a5cd36d9ccd4bf": "2dcab0e178b68620f7b05bd8433e1c853806e7022bf57f955b354e58f5fe04d4",
    "03f989f4f79a75ab08d5f2026047006c0456500bf7b6d11df20d46990347bed5": "03f989f4f79a75ab08d5f2026047006c0456500bf7b6d11df20d46990347bed5",
    "04270bcd707f436ad4d611fd97b63b567a2f16ce667b1209f032d5383917cd90": "ce40da192abefc56c6c6d9debd993788bdc1e117c1c572db55b467ef567df26b",
    "04bd136e503c56dd32450f7cf8992a607addaee98f4bcfa6634489e9a3a56546": "2cf3e054c4f828c7203497733835451f1c10d9e14a6a98fe16449c513b2d3b79",
    "04ed322b70e5fbbda0b485b9e15cfba3d78c2dfb71722416c31ba953d67c13e2": "317e65d23f9835ac5918424623b54a15715994b57064a69db768ad908fd40fed",
    "06151ededa841d3566cac316728ec405bb43f8b9c7afdd807e25c057b64e3d27": "1e7079b663adf41cf5507d98902bd24ed43c1e501cc680a8e262dd648c201046",
    "061d67e0b0a46a383544c7f1de4de2865139c0b302aa6e456a02af3741ed9c61": "d9a58b5860539be1f904337e0cf977186af80badb7e0533e19d149f2043eac3a",
    "0666d1a181a96c1bd3ecda0850190a82d95cf05b113dbd888d6948c2a0d06dac": "c15da5484b46f87650d27ce32b43800b129b44347854cdf132f779c5d3516203",
}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_rams(work_dir: Path) -> Path:
    archive = work_dir / "RAMS_1.0c.tar.gz"
    urllib.request.urlretrieve(RAMS_URL, archive)
    observed_hash = sha256_file(archive)
    if observed_hash != RAMS_SHA256:
        raise RuntimeError(f"RAMS archive checksum mismatch: {observed_hash}")
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(work_dir, filter="data")
    root = work_dir / "RAMS_1.0c"
    if not root.is_dir():
        raise RuntimeError("RAMS archive did not contain the expected root")
    return root


def load_ontology(root: Path) -> dict[str, list[str]]:
    path = root / "scorer" / "event_role_multiplicities.txt"
    result: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        result[fields[0]] = fields[1::2]
    return result


def load_examples(root: Path) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for path in sorted((root / "data").glob("*.jsonlines")):
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            canonical_document_id = f"rams:{record['doc_key']}"
            document_hash = hashlib.sha256(canonical_document_id.encode()).hexdigest()
            if document_hash in FROZEN_DEVELOPMENT_GROUPS:
                record["_document_id_sha256"] = document_hash
                record["_group_id_sha256"] = FROZEN_DEVELOPMENT_GROUPS[document_hash]
                record["_nominal_rams_split"] = path.stem
                selected.append(record)
    selected.sort(key=lambda record: record["_document_id_sha256"])
    if {record["_document_id_sha256"] for record in selected} != set(FROZEN_DEVELOPMENT_GROUPS):
        raise RuntimeError("RAMS records do not exactly match the frozen development allowlist")
    if len({record["_group_id_sha256"] for record in selected}) != 20:
        raise RuntimeError("Gate 0E requires 20 distinct frozen development groups")
    return selected


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
    generated_text: str, tokens: list[str], roles: set[str]
) -> tuple[str, Counter[tuple[str, int, int]]]:
    try:
        decoded = json.loads(generated_text)
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


def assess_output(
    status: str,
    gold: Counter[tuple[str, int, int]],
    predicted: Counter[tuple[str, int, int]],
    transition_scores: list[float],
) -> tuple[float, dict[str, float]]:
    if status != "valid" or not transition_scores:
        return 1.0, {
            "mean": WORST_CONFIDENCE,
            "tenth_percentile": WORST_CONFIDENCE,
            "minimum": WORST_CONFIDENCE,
        }
    return document_loss(gold, predicted), {
        "mean": float(np.mean(transition_scores)),
        "tenth_percentile": float(np.quantile(transition_scores, 0.1)),
        "minimum": float(np.min(transition_scores)),
    }


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
            max_new_tokens=512,
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


def run_smoke(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the real model smoke")
    ontology = load_ontology(root)
    examples = load_examples(root)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        dtype=torch.bfloat16,
        device_map={"": 0},
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
        token_ids, transition_scores, generated_text = generate_one(model, tokenizer, prompt)
        status, predicted = parse_arguments(generated_text, tokens, set(roles))
        loss, candidates = assess_output(
            status, gold_arguments(record), predicted, transition_scores
        )
        losses.append(loss)
        for name, value in candidates.items():
            score_values[name].append(float(value))
        if index < 3:
            repeated_ids, repeated_scores, _ = generate_one(model, tokenizer, prompt)
            determinism_pass &= token_ids == repeated_ids and np.allclose(
                transition_scores, repeated_scores, rtol=0.0, atol=0.0
            )
        evidence_records.append(
            {
                "doc_key_sha256": record["_document_id_sha256"],
                "group_id_sha256": record["_group_id_sha256"],
                "nominal_rams_split": record["_nominal_rams_split"],
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "output_sha256": hashlib.sha256(generated_text.encode()).hexdigest(),
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
    alignment_pass = all(
        record["generated_token_count"] == record["transition_score_count"]
        for record in evidence_records
    )
    malformed_status, malformed_prediction = parse_arguments("not-json", ["token"], {"role"})
    malformed_loss, malformed_scores = assess_output(
        malformed_status, Counter(), malformed_prediction, [-0.1]
    )
    malformed_output_policy_pass = malformed_loss == 1.0 and all(
        value == WORST_CONFIDENCE for value in malformed_scores.values()
    )
    duration_seconds = time.monotonic() - started
    selection_sha256 = canonical_hash(
        [
            {
                "document_id_sha256": record["doc_key_sha256"],
                "group_id_sha256": record["group_id_sha256"],
            }
            for record in evidence_records
        ]
    )
    gate0e_pass = all(
        (
            len(evidence_records) == 20,
            selection_sha256 == FROZEN_DEVELOPMENT_SELECTION_SHA256,
            alignment_pass,
            determinism_pass,
            malformed_output_policy_pass,
            math.isfinite(duration_seconds),
            all(math.isfinite(value) for value in auc.values()),
        )
    )
    report = {
        "schema_version": "3",
        "status": "pass" if gate0e_pass else "fail",
        "gate0e_pass": gate0e_pass,
        "actual_model_generation_pass": gate0e_pass,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "source_archive_url": RAMS_URL,
        "source_archive_sha256": RAMS_SHA256,
        "source_archive_checksum_pass": True,
        "frozen_split_manifest_sha256": FROZEN_SPLIT_MANIFEST_SHA256,
        "source_text_download_persisted": False,
        "restricted_source_text_in_evidence": False,
        "real_development_generations": len(evidence_records),
        "development_selection_sha256": selection_sha256,
        "development_selection_lock_pass": (
            selection_sha256 == FROZEN_DEVELOPMENT_SELECTION_SHA256
        ),
        "development_distinct_groups": len(
            {record["group_id_sha256"] for record in evidence_records}
        ),
        "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": 512},
        "load_mode": "BF16 single-GPU",
        "completion_only_transition_alignment": alignment_pass,
        "determinism_repeated_examples": 3,
        "determinism_pass": determinism_pass,
        "malformed_output_policy": "loss=1 and confidence=-infinity",
        "malformed_output_policy_pass": malformed_output_policy_pass,
        "confidence_auc": auc,
        "provisional_confidence_ranking_winner": selected,
        "confidence_selection_status": "provisional 20-group smoke; not frozen",
        "frozen_confidence_requires": "full frozen grouped development predictions",
        "confidence_selection_data_role": "development only",
        "structural_failure_count": sum(record["status"] != "valid" for record in evidence_records),
        "records": evidence_records,
        "runtime": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "accelerate": importlib.metadata.version("accelerate"),
            "numpy": importlib.metadata.version("numpy"),
            "gpu": torch.cuda.get_device_name(0),
        },
        "duration_seconds": duration_seconds,
    }
    return report


def persist_report(report: dict[str, Any], repo_id: str) -> str:
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_file(
        path_or_fileobj=io.BytesIO(data),
        path_in_repo=EVIDENCE_PATH,
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="evidence: persist Gate 0E model-score smoke",
    )
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-repo",
        default="rosscyking/conformalextract-evidence",
        help="Private Hugging Face Dataset receiving text-free evidence.",
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="conformalextract-gate0e-") as directory:
        root = download_rams(Path(directory))
        report = run_smoke(root)
        report_sha256 = persist_report(report, args.evidence_repo)
    print(
        json.dumps(
            {
                "evidence_repo": args.evidence_repo,
                "evidence_path": EVIDENCE_PATH,
                "sha256": report_sha256,
                "status": report["status"],
            },
            sort_keys=True,
        )
    )
    if not report["gate0e_pass"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
