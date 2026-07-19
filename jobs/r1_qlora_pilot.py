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
"""R1 QLoRA pilot for ConformalExtract (Plan 2) — ephemeral, label-isolated, text-free.

Purpose: prove a real learning signal on the frozen contract before R2 commits the full
budget. Downloads official RAMS ephemerally (checksum-verified), renders train/development
examples from the frozen prompt template, DELETES the raw source before model load, trains
a rank-16 NF4 QLoRA adapter on a train-role subset, measures development loss before/after
(development gold used only for this selection measurement), and persists ONLY the adapter,
aggregate metrics, and a hash-chained label-access summary to the private evidence Dataset.
No source text, no gold text, and no generations are persisted or printed.
"""

from __future__ import annotations

import gc
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import torch
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
RAMS_URL = "https://nlp.jhu.edu/rams/RAMS_1.0c.tar.gz"
RAMS_SHA256 = "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54"
EVIDENCE_REPO = "rosscyking/conformalextract-evidence"
ROLES_PATH = "plan2/rams_roles.jsonl"
ROLES_SHA256 = "17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3"
ANALYSIS_ID = "plan2prep-f3f2f7a938061a92b2cb"
EVIDENCE_PATH = "plan2/r1_pilot.v1.json"
ADAPTER_PREFIX = "plan2/r1/adapter"

CONTEXT_TOKENS = 6144  # ADR 0003 selected rung (frozen context_window manifest)
MAX_OUTPUT_TOKENS = 512
LEARNING_RATE = 2e-4
SEED = 42
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
GRAD_ACCUM = 16
TRAIN_SUBSET = 512
DEV_SUBSET = 128

WORKSPACE = Path("/tmp/ce-r1")
RAW_DIR = WORKSPACE / "raw"
ADAPTER_DIR = WORKSPACE / "adapter"
GENESIS = hashlib.sha256(b"conformalextract/label-access/v1").hexdigest()

TEMPLATE = """You extract grounded event arguments for one given trigger.

Event type: {event_type}
Trigger token span [start, end): {trigger_start}, {trigger_end}
Allowed roles: {allowed_roles_json}
Document tokens: {numbered_tokens_json}

Return one JSON object only:
{"arguments":[{"role":"<allowed role>","start":0,"end":1,"text":"<exact token text>"}]}

Use half-open token spans. Copy grounded text exactly. Do not infer an ungrounded argument.
When no argument is present return {"arguments":[]}.
"""

_ROLE_RE = re.compile(r"^evt\d+arg\d+(.+)$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_verified(url: str, expected_sha256: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:  # frozen official URL only
        data = response.read()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise RuntimeError(f"checksum mismatch for {url}: {digest}")
    destination.write_bytes(data)


def load_roles() -> dict[str, str]:
    """Download the metadata-only role assignment and verify the frozen hash."""

    path = hf_hub_download(
        repo_id=EVIDENCE_REPO, filename=ROLES_PATH, repo_type="dataset"
    )
    data = Path(path).read_bytes()
    if sha256_bytes(data) != ROLES_SHA256:
        raise RuntimeError("role assignment hash does not match the frozen split manifest")
    roles: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        record = json.loads(line)
        roles[str(record["document_id"])] = str(record["role"])
    return roles


def parse_ontology(text: str) -> dict[str, list[str]]:
    ontology: dict[str, list[str]] = {}
    for line in text.splitlines():
        parts = line.split()
        if parts:
            ontology[parts[0]] = [parts[i] for i in range(1, len(parts), 2)]
    return ontology


def render_example(record: dict, ontology: dict[str, list[str]]) -> tuple[str, str, str]:
    instance_key = f"rams:{record['doc_key']}"
    tokens = [str(token) for sentence in record["sentences"] for token in sentence]
    trig = record["evt_triggers"][0]
    trigger_start, trigger_end = int(trig[0]), int(trig[1]) + 1
    event_type = str(trig[2][0][0])
    allowed = ontology[event_type]
    arguments = []
    for link in record.get("gold_evt_links") or []:
        (_, _), (arg_start, arg_end), link_role = link
        match = _ROLE_RE.match(str(link_role))
        if match is None:
            raise RuntimeError(f"unparseable role for {instance_key}")
        arguments.append(
            {
                "role": match.group(1),
                "start": int(arg_start),
                "end": int(arg_end) + 1,
                "text": " ".join(tokens[int(arg_start) : int(arg_end) + 1]),
            }
        )
    rank = {role: index for index, role in enumerate(allowed)}
    arguments.sort(key=lambda item: (rank.get(item["role"], len(rank)), item["start"]))
    numbered = [{"i": i, "t": token} for i, token in enumerate(tokens)]
    prompt = TEMPLATE
    for placeholder, value in (
        ("{event_type}", event_type),
        ("{trigger_start}", str(trigger_start)),
        ("{trigger_end}", str(trigger_end)),
        ("{allowed_roles_json}", json.dumps(allowed)),
        ("{numbered_tokens_json}", json.dumps(numbered)),
    ):
        prompt = prompt.replace(placeholder, value)
    completion = (
        '{"arguments":[]}'
        if not arguments
        else json.dumps({"arguments": arguments}, separators=(",", ":"))
    )
    return instance_key, prompt, completion


def materialize_examples(
    roles: dict[str, str],
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]], int]:
    """Download+verify RAMS, render train/dev examples, DELETE raw before returning."""

    archive = RAW_DIR / "RAMS_1.0c.tar.gz"
    fetch_verified(RAMS_URL, RAMS_SHA256, archive)
    train: list[tuple[str, str, str]] = []
    development: list[tuple[str, str, str]] = []
    skipped_roleless = 0
    with tarfile.open(archive, "r:gz") as tar:
        member = tar.extractfile("RAMS_1.0c/scorer/event_role_multiplicities.txt")
        if member is None:
            raise RuntimeError("ontology missing from RAMS archive")
        ontology = parse_ontology(member.read().decode("utf-8"))
        for split in ("train", "dev", "test"):
            handle = tar.extractfile(f"RAMS_1.0c/data/{split}.jsonlines")
            if handle is None:
                continue
            for line in io.TextIOWrapper(handle, encoding="utf-8"):
                if not line.strip():
                    continue
                record = json.loads(line)
                key = f"rams:{record['doc_key']}"
                role = roles.get(key)
                if role is None:
                    skipped_roleless += 1
                    continue
                if role == "train":
                    train.append(render_example(record, ontology))
                elif role == "development":
                    development.append(render_example(record, ontology))
                # certification/final/shift: sealed - never rendered, never read further.
    shutil.rmtree(RAW_DIR)  # delete raw archive + extraction BEFORE any model work
    return train, development, skipped_roleless


def chain_accesses(entries: list[tuple[str, str, str]]) -> str:
    head = GENESIS
    for data_role, document_hash, purpose in entries:
        material = json.dumps(
            {
                "previous": head,
                "data_role": data_role,
                "document_id_hash": document_hash,
                "purpose": purpose,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        head = hashlib.sha256(material).hexdigest()
    return head


def encode_example(
    tokenizer, prompt: str, completion: str
) -> tuple[torch.Tensor, torch.Tensor] | None:
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    completion_ids = tokenizer(
        completion + tokenizer.eos_token, add_special_tokens=False
    )["input_ids"]
    if len(prompt_ids) > CONTEXT_TOKENS or len(completion_ids) > MAX_OUTPUT_TOKENS:
        return None
    input_ids = torch.tensor([prompt_ids + completion_ids])
    labels = torch.tensor([[-100] * len(prompt_ids) + completion_ids])
    return input_ids, labels


def mean_dev_loss(model, tokenizer, examples, device) -> float:
    model.eval()
    total, count = 0.0, 0
    with torch.no_grad():
        for _, prompt, completion in examples:
            encoded = encode_example(tokenizer, prompt, completion)
            if encoded is None:
                continue
            input_ids, labels = (t.to(device) for t in encoded)
            loss = model(input_ids=input_ids, labels=labels).loss
            total += float(loss)
            count += 1
    model.train()
    if count == 0:
        raise RuntimeError("no development examples fit the context window")
    return total / count


def persist(report: dict, adapter_dir: Path) -> dict[str, str]:
    api = HfApi()
    info = api.dataset_info(EVIDENCE_REPO)
    if info.private is not True:
        raise RuntimeError("evidence repository must be private")
    if api.file_exists(
        repo_id=EVIDENCE_REPO, filename=EVIDENCE_PATH, repo_type="dataset",
        revision=info.sha,
    ):
        raise RuntimeError(f"evidence path already exists: {EVIDENCE_PATH}")
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    operations = [
        CommitOperationAdd(path_in_repo=EVIDENCE_PATH, path_or_fileobj=io.BytesIO(data))
    ]
    for item in sorted(adapter_dir.rglob("*")):
        if item.is_file():
            operations.append(
                CommitOperationAdd(
                    path_in_repo=f"{ADAPTER_PREFIX}/{item.relative_to(adapter_dir).as_posix()}",
                    path_or_fileobj=str(item),
                )
            )
    commit = api.create_commit(
        repo_id=EVIDENCE_REPO, repo_type="dataset", operations=operations,
        commit_message="evidence: persist R1 QLoRA pilot adapter + metrics",
        parent_commit=info.sha,
    )
    return {"artifact_sha256": sha256_bytes(data), "hub_commit_oid": commit.oid}


def main() -> None:
    started = time.monotonic()
    torch.manual_seed(SEED)
    roles = load_roles()
    train_all, dev_all, skipped_roleless = materialize_examples(roles)
    if RAW_DIR.exists():
        raise RuntimeError("raw extraction survived materialization")
    generator = torch.Generator().manual_seed(SEED)
    train_order = torch.randperm(len(train_all), generator=generator).tolist()
    dev_order = torch.randperm(len(dev_all), generator=generator).tolist()
    train_examples = [train_all[i] for i in train_order[:TRAIN_SUBSET]]
    dev_examples = [dev_all[i] for i in dev_order[:DEV_SUBSET]]

    access_head = chain_accesses(
        [("train", sha256_bytes(key.encode()), "sft_training") for key, _, _ in train_examples]
        + [
            ("development", sha256_bytes(key.encode()), "development_selection")
            for key, _, _ in dev_examples
        ]
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    assert tokenizer.pad_token_id is not None, "pad token must be set (G3)"

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=REVISION, quantization_config=quantization,
        dtype=torch.bfloat16, device_map="auto",
    )
    model.config.use_cache = False  # G3: incompatible with gradient checkpointing
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False}  # G3
    )
    model = get_peft_model(
        model,
        LoraConfig(
            r=LORA_RANK, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
            target_modules="all-linear", task_type="CAUSAL_LM",
        ),
    )
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_fraction = trainable / total_params
    assert 0.005 < trainable_fraction < 0.10, "trainable-parameter band violated (G3)"
    bad_names = [
        name for name, p in model.named_parameters() if p.requires_grad and "lora_" not in name
    ]
    if bad_names:
        raise RuntimeError("non-adapter parameters are trainable")
    device = next(model.parameters()).device

    dev_loss_before = mean_dev_loss(model, tokenizer, dev_examples, device)

    optimizer = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=LEARNING_RATE
    )
    model.train()
    losses: list[float] = []
    trained, excluded_long, step_index = 0, 0, 0
    train_started = time.monotonic()
    for _, prompt, completion in train_examples:
        encoded = encode_example(tokenizer, prompt, completion)
        if encoded is None:
            excluded_long += 1
            continue
        input_ids, labels = (t.to(device) for t in encoded)
        loss = model(input_ids=input_ids, labels=labels).loss
        if not torch.isfinite(loss):
            raise RuntimeError("non-finite training loss")
        (loss / GRAD_ACCUM).backward()
        losses.append(float(loss))
        trained += 1
        if trained % GRAD_ACCUM == 0:
            optimizer.step()
            optimizer.zero_grad()
            step_index += 1
    if trained % GRAD_ACCUM:
        optimizer.step()
        optimizer.zero_grad()
        step_index += 1
    train_seconds = time.monotonic() - train_started

    dev_loss_after = mean_dev_loss(model, tokenizer, dev_examples, device)

    model.config.use_cache = True
    model.save_pretrained(ADAPTER_DIR, safe_serialization=True)
    adapter_hashes = {
        item.relative_to(ADAPTER_DIR).as_posix(): sha256_bytes(item.read_bytes())
        for item in sorted(ADAPTER_DIR.rglob("*"))
        if item.is_file()
    }
    if "adapter_model.safetensors" not in adapter_hashes:
        raise RuntimeError("adapter was not saved as safetensors")

    learning_signal = dev_loss_after < dev_loss_before
    quarter = max(1, len(losses) // 4)
    report = {
        "schema_version": "1",
        "status": "pass" if learning_signal else "revise",
        "r1_pilot_pass": learning_signal,
        "analysis_id": ANALYSIS_ID,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "seed": SEED,
        "context_tokens": CONTEXT_TOKENS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "learning_rate": LEARNING_RATE,
        "lora": {"rank": LORA_RANK, "alpha": LORA_ALPHA, "dropout": LORA_DROPOUT,
                 "target_modules": "all-linear"},
        "quantization": "nf4-4bit-double-quant-bf16",
        "gradient_accumulation": GRAD_ACCUM,
        "counts": {
            "train_pool": len(train_all),
            "development_pool": len(dev_all),
            "train_subset": len(train_examples),
            "dev_subset": len(dev_examples),
            "trained_examples": trained,
            "excluded_over_context": excluded_long,
            "optimizer_steps": step_index,
            "skipped_roleless_instances": skipped_roleless,
        },
        "train_loss_first_quarter": sum(losses[:quarter]) / quarter,
        "train_loss_last_quarter": sum(losses[-quarter:]) / quarter,
        "dev_loss_before": dev_loss_before,
        "dev_loss_after": dev_loss_after,
        "dev_loss_delta": dev_loss_after - dev_loss_before,
        "learning_signal": learning_signal,
        "label_access": {
            "head_hash": access_head,
            "train_sft_reads": len(train_examples),
            "development_selection_reads": len(dev_examples),
            "sealed_reads": 0,
        },
        "raw_deleted_before_model_load": True,
        "adapter_hashes": adapter_hashes,
        "train_seconds": train_seconds,
        "seconds_per_trained_example": train_seconds / max(1, trained),
        "gpu": torch.cuda.get_device_name(0),
        "duration_seconds": time.monotonic() - started,
        "estimated_cost_usd": (time.monotonic() - started) / 3600.0 * 1.80,
        "python": sys.version.split()[0],
        "torch": torch.__version__,
    }
    print(
        "R1_PILOT_REPORT="
        + json.dumps(
            {k: v for k, v in report.items() if k != "adapter_hashes"}, sort_keys=True
        ),
        flush=True,
    )
    del model, optimizer
    gc.collect()
    torch.cuda.empty_cache()
    persistence = persist(report, ADAPTER_DIR)
    print(json.dumps({"persisted": persistence, "status": report["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
