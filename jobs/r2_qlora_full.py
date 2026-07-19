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
"""R2 full QLoRA training for ConformalExtract (Plan 2) — 2 epochs, dev-selected checkpoint.

Trains the QA adapter on the FULL train split (2 epochs, per-epoch checkpoints), selects
exactly one checkpoint by full-development loss (the plan's sanctioned selection rule),
proves fresh-process reload equivalence on a synthetic prompt (Gate 0F pattern), and
persists the selected adapter as two checked copies — copy A to the private evidence
Dataset, copy B to the private adapter Model repo — plus one aggregate, text-free metrics
JSON. Same ephemeral-download, label-isolation, and G3 guards as the PASSed R1 pilot.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import torch
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
RAMS_URL = "https://nlp.jhu.edu/rams/RAMS_1.0c.tar.gz"
RAMS_SHA256 = "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54"
EVIDENCE_REPO = "rosscyking/conformalextract-evidence"
ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"
ROLES_PATH = "plan2/rams_roles.jsonl"
ROLES_SHA256 = "17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3"
ANALYSIS_ID = "plan2prep-f3f2f7a938061a92b2cb"
EVIDENCE_PATH = "plan2/r2_full.v1.json"
ADAPTER_PREFIX = "plan2/r2/adapter"

CONTEXT_TOKENS = 6144  # ADR 0003 selected rung (frozen context_window manifest)
MAX_OUTPUT_TOKENS = 512
LEARNING_RATE = 2e-4
SEED = 42
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
GRAD_ACCUM = 16
EPOCHS = 2  # Ross-approved 2026-07-19: two epochs, dev-selected checkpoint

WORKSPACE = Path("/tmp/ce-r2")
RAW_DIR = WORKSPACE / "raw"
GENESIS = hashlib.sha256(b"conformalextract/label-access/v1").hexdigest()
SMOKE_PROMPT = 'Return JSON only: {"arguments":[]}'

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
    path = hf_hub_download(repo_id=EVIDENCE_REPO, filename=ROLES_PATH, repo_type="dataset")
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
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    archive = RAW_DIR / "RAMS_1.0c.tar.gz"
    fetch_verified(RAMS_URL, RAMS_SHA256, archive)
    train: list[tuple[str, str, str]] = []
    development: list[tuple[str, str, str]] = []
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
                role = roles.get(f"rams:{record['doc_key']}")
                if role == "train":
                    train.append(render_example(record, ontology))
                elif role == "development":
                    development.append(render_example(record, ontology))
                # certification/final/shift: sealed - never rendered, never read further.
    shutil.rmtree(RAW_DIR)  # delete raw archive + extraction BEFORE any model work
    return train, development


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
            total += float(model(input_ids=input_ids, labels=labels).loss)
            count += 1
    model.train()
    if count == 0:
        raise RuntimeError("no development examples fit the context window")
    return total / count


def greedy_token_hash(model, tokenizer) -> str:
    """Deterministic 8-token greedy completion hash (Gate 0F equivalence pattern)."""

    model.eval()
    model.config.use_cache = True
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    inputs = tokenizer(SMOKE_PROMPT, return_tensors="pt").to(next(model.parameters()).device)
    with torch.no_grad():
        generated = model.generate(
            **inputs, do_sample=False, num_beams=1, max_new_tokens=8
        )
    completion = generated[0, inputs["input_ids"].shape[1] :].detach().cpu().numpy().tobytes()
    return hashlib.sha256(completion).hexdigest()


def reload_check(adapter_dir: Path) -> None:
    """Fresh-process path: load base + adapter, print the greedy token hash."""

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=REVISION, quantization_config=quantization,
        dtype=torch.bfloat16, device_map="auto",
    )
    base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
    model = PeftModel.from_pretrained(base, adapter_dir)
    model.gradient_checkpointing_disable()
    print("RELOAD_TOKEN_HASH=" + greedy_token_hash(model, tokenizer), flush=True)


def adapter_hashes(path: Path) -> dict[str, str]:
    return {
        item.relative_to(path).as_posix(): sha256_bytes(item.read_bytes())
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def persist(report: dict, adapter_dir: Path) -> dict[str, str]:
    api = HfApi()
    result: dict[str, str] = {}
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    evidence_info = api.dataset_info(EVIDENCE_REPO)
    if evidence_info.private is not True:
        raise RuntimeError("evidence repository must be private")
    if api.file_exists(
        repo_id=EVIDENCE_REPO, filename=EVIDENCE_PATH, repo_type="dataset",
        revision=evidence_info.sha,
    ):
        raise RuntimeError(f"evidence path already exists: {EVIDENCE_PATH}")
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
    commit_a = api.create_commit(
        repo_id=EVIDENCE_REPO, repo_type="dataset", operations=operations,
        commit_message="evidence: persist R2 selected adapter (copy A) + metrics",
        parent_commit=evidence_info.sha,
    )
    result["copy_a_commit_oid"] = commit_a.oid
    result["metrics_sha256"] = sha256_bytes(data)

    adapter_info = api.model_info(ADAPTER_REPO)
    if adapter_info.private is not True:
        raise RuntimeError("adapter repository must be private")
    copy_b_ops = [
        CommitOperationAdd(
            path_in_repo=item.relative_to(adapter_dir).as_posix(),
            path_or_fileobj=str(item),
        )
        for item in sorted(adapter_dir.rglob("*"))
        if item.is_file()
    ]
    commit_b = api.create_commit(
        repo_id=ADAPTER_REPO, repo_type="model", operations=copy_b_ops,
        commit_message="R2 selected QA adapter (copy B)",
        parent_commit=adapter_info.sha,
    )
    result["copy_b_commit_oid"] = commit_b.oid
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload-check", type=Path)
    arguments = parser.parse_args()
    if arguments.reload_check:
        reload_check(arguments.reload_check)
        return

    started = time.monotonic()
    torch.manual_seed(SEED)
    roles = load_roles()
    train_all, dev_all = materialize_examples(roles)
    if RAW_DIR.exists():
        raise RuntimeError("raw extraction survived materialization")

    access_entries = [
        ("train", sha256_bytes(key.encode()), "sft_training") for key, _, _ in train_all
    ] * EPOCHS + [
        ("development", sha256_bytes(key.encode()), "development_selection")
        for key, _, _ in dev_all
    ] * (EPOCHS + 1)
    access_head = chain_accesses(access_entries)

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
    model.config.use_cache = False  # G3
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
    assert 0.005 < trainable / total_params < 0.10, "trainable-parameter band violated (G3)"
    if [n for n, p in model.named_parameters() if p.requires_grad and "lora_" not in n]:
        raise RuntimeError("non-adapter parameters are trainable")
    device = next(model.parameters()).device

    dev_losses = [mean_dev_loss(model, tokenizer, dev_all, device)]  # epoch 0 baseline

    optimizer = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=LEARNING_RATE
    )
    generator = torch.Generator().manual_seed(SEED)
    model.train()
    epoch_stats: list[dict[str, float]] = []
    excluded_long = 0
    for epoch in range(1, EPOCHS + 1):
        order = torch.randperm(len(train_all), generator=generator).tolist()
        losses: list[float] = []
        trained = 0
        epoch_started = time.monotonic()
        for index in order:
            _, prompt, completion = train_all[index]
            encoded = encode_example(tokenizer, prompt, completion)
            if encoded is None:
                if epoch == 1:
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
        if trained % GRAD_ACCUM:
            optimizer.step()
            optimizer.zero_grad()
        dev_loss = mean_dev_loss(model, tokenizer, dev_all, device)
        dev_losses.append(dev_loss)
        quarter = max(1, len(losses) // 4)
        epoch_dir = WORKSPACE / f"epoch_{epoch}"
        model.config.use_cache = True
        model.save_pretrained(epoch_dir, safe_serialization=True)
        model.config.use_cache = False
        epoch_stats.append(
            {
                "epoch": epoch,
                "trained_examples": trained,
                "train_loss_first_quarter": sum(losses[:quarter]) / quarter,
                "train_loss_last_quarter": sum(losses[-quarter:]) / quarter,
                "dev_loss": dev_loss,
                "epoch_seconds": time.monotonic() - epoch_started,
            }
        )
        print(f"EPOCH_{epoch}_DEV_LOSS={dev_loss}", flush=True)

    selected_epoch = min(range(1, EPOCHS + 1), key=lambda e: dev_losses[e])
    selected_dir = WORKSPACE / f"epoch_{selected_epoch}"
    selected_hashes = adapter_hashes(selected_dir)
    if "adapter_model.safetensors" not in selected_hashes:
        raise RuntimeError("selected adapter was not saved as safetensors")

    # In-process greedy hash with the selected adapter loaded fresh from disk is proven
    # by the subprocess; here we take the trained model's hash only when the selected
    # epoch is the last one (weights still in memory), else rely on the subprocess pair.
    model.gradient_checkpointing_disable()
    in_process_hash = (
        greedy_token_hash(model, tokenizer) if selected_epoch == EPOCHS else None
    )

    del model, optimizer
    gc.collect()
    torch.cuda.empty_cache()

    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--reload-check", str(selected_dir)],
        check=True, capture_output=True, text=True,
    )
    reload_hash = next(
        line.removeprefix("RELOAD_TOKEN_HASH=")
        for line in completed.stdout.splitlines()
        if line.startswith("RELOAD_TOKEN_HASH=")
    )
    reload_equivalence = in_process_hash is None or reload_hash == in_process_hash

    report = {
        "schema_version": "1",
        "status": "pass" if dev_losses[selected_epoch] < dev_losses[0] else "revise",
        "r2_pass": dev_losses[selected_epoch] < dev_losses[0],
        "analysis_id": ANALYSIS_ID,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "seed": SEED,
        "epochs": EPOCHS,
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
            "excluded_over_context": excluded_long,
        },
        "dev_loss_epoch0": dev_losses[0],
        "epoch_stats": epoch_stats,
        "selected_epoch": selected_epoch,
        "selected_dev_loss": dev_losses[selected_epoch],
        "reload_token_hash": reload_hash,
        "in_process_token_hash": in_process_hash,
        "reload_equivalence": reload_equivalence,
        "label_access": {
            "head_hash": access_head,
            "train_sft_reads": len(train_all) * EPOCHS,
            "development_selection_reads": len(dev_all) * (EPOCHS + 1),
            "sealed_reads": 0,
        },
        "raw_deleted_before_model_load": True,
        "adapter_hashes": selected_hashes,
        "gpu": torch.cuda.get_device_name(0),
        "duration_seconds": time.monotonic() - started,
        "estimated_cost_usd": (time.monotonic() - started) / 3600.0 * 1.80,
        "python": sys.version.split()[0],
        "torch": torch.__version__,
    }
    print(
        "R2_REPORT="
        + json.dumps(
            {k: v for k, v in report.items() if k != "adapter_hashes"}, sort_keys=True
        ),
        flush=True,
    )
    persistence = persist(report, selected_dir)
    print(json.dumps({"persisted": persistence, "status": report["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
