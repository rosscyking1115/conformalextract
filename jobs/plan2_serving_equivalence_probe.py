# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "accelerate==1.14.0",
#   "bitsandbytes==0.49.2",
#   "huggingface-hub==0.36.2",
#   "peft==0.19.1",
#   "torch==2.13.0",
#   "transformers==4.57.6",
# ]
# ///
"""Serving-equivalence probe: vLLM-served QA output vs the training stack, on real prompts.

Reviewer-required control (decision 2 of evidence/plan2/reviewer_record.extraction-policy.json).
The Plan 2 evidence base is entirely vLLM-generated text from which a first JSON object is now
extracted, so a serving-stack perturbation would infect both the structural and grounding
numbers. R2 proved fresh-process *reload* equivalence only; this closes *parsed-output* parity.

Fixes the OOM that crashed the in-run probe: this job loads NOTHING but transformers+peft, with
no vLLM engine anywhere in the process, so the 4-bit model has the whole card.

Method: ephemerally re-render the frozen ZS prompts from a checksum-verified RAMS download,
assert each re-rendered prompt's sha256 matches the saved QA record (proving prompt reproduction
is faithful before anything is compared), greedily regenerate on the training stack, then compare
against the served output under the adopted first-object extraction policy. Train split only.
Raw is deleted before model load; the report is aggregate and text-free.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import tarfile
import time
import urllib.request
from pathlib import Path

import torch
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download, snapshot_download
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"
ADAPTER_REVISION = "edd69373be3d46ae2a982e555f4ec9549491e8e4"  # R2 copy B commit
RAMS_URL = "https://nlp.jhu.edu/rams/RAMS_1.0c.tar.gz"
RAMS_SHA256 = "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54"
EVIDENCE_REPO = "rosscyking/conformalextract-evidence"
ROLES_PATH = "plan2/rams_roles.jsonl"
ROLES_SHA256 = "17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3"
QA_PREDICTIONS_PATH = "plan2/predictions/qa.v1.jsonl"
QA_PREDICTIONS_SHA256 = "036f8f08dcbe7587c19def951f81e62e4be0a5de1485b406c64514d03bf721f3"
ANALYSIS_ID = "plan2prep-f3f2f7a938061a92b2cb"
REPORT_PATH = "plan2/serving_equivalence_probe.v1.json"

CONTEXT_TOKENS = 6144
MAX_NEW_TOKENS = 256  # identical to the generation run
PROBE_SIZE = 24
PROBE_PROMPT_CAP = 4096
HOURLY_RATE_USD = 0.80  # l4x1

WORKSPACE = Path("/tmp/ce-probe")
RAW_DIR = WORKSPACE / "raw"

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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def first_balanced_object(text: str) -> str | None:
    """Adopted extraction policy (ADR 0006 / reviewer condition C2).

    Single pass from index 0 tracking JSON string and escape state globally, so a brace
    inside a string literal can never open or close an object.
    """

    depth = 0
    in_string = False
    escaped = False
    start = None
    for index, character in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            if depth == 0:
                start = index
            depth += 1
        elif character == "}":
            if depth:
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : index + 1]
    return None


def fetch_verified(url: str, expected_sha256: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:  # frozen official URL only
        data = response.read()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise RuntimeError(f"checksum mismatch for {url}: {digest}")
    destination.write_bytes(data)


def load_verified_evidence_file(filename: str, expected_sha256: str) -> bytes:
    path = hf_hub_download(repo_id=EVIDENCE_REPO, filename=filename, repo_type="dataset")
    data = Path(path).read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise RuntimeError(f"hash mismatch for frozen artifact {filename}")
    return data


def parse_ontology(text: str) -> dict[str, list[str]]:
    ontology: dict[str, list[str]] = {}
    for line in text.splitlines():
        parts = line.split()
        if parts:
            ontology[parts[0]] = [parts[i] for i in range(1, len(parts), 2)]
    return ontology


def render_zs_prompt(record: dict, ontology: dict[str, list[str]]) -> dict:
    """Byte-identical to the generation job's renderer (triggers + tokens only)."""

    instance_key = f"rams:{record['doc_key']}"
    tokens = [str(token) for sentence in record["sentences"] for token in sentence]
    trig = record["evt_triggers"][0]
    trigger_start, trigger_end = int(trig[0]), int(trig[1]) + 1
    event_type = str(trig[2][0][0])
    allowed = ontology[event_type]
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
    return {"instance_key": instance_key, "prompt": prompt}


def main() -> None:
    started = time.monotonic()
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    roles: dict[str, str] = {}
    for line in load_verified_evidence_file(ROLES_PATH, ROLES_SHA256).decode("utf-8").splitlines():
        record = json.loads(line)
        roles[str(record["document_id"])] = str(record["role"])

    served: dict[str, dict] = {}
    qa_bytes = load_verified_evidence_file(QA_PREDICTIONS_PATH, QA_PREDICTIONS_SHA256)
    for line in qa_bytes.decode("utf-8").splitlines():
        record = json.loads(line)
        served[record["instance_key"]] = record

    archive = RAW_DIR / "RAMS_1.0c.tar.gz"
    fetch_verified(RAMS_URL, RAMS_SHA256, archive)
    rendered: dict[str, str] = {}
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
                # Train split only: the probe never touches a sealed-split document.
                if roles.get(f"rams:{record['doc_key']}") != "train":
                    continue
                item = render_zs_prompt(record, ontology)
                rendered[item["instance_key"]] = item["prompt"]
    shutil.rmtree(RAW_DIR)  # delete raw BEFORE any model work
    if RAW_DIR.exists():
        raise RuntimeError("raw extraction survived materialization")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    candidates = []
    for instance_key, prompt in rendered.items():
        record = served.get(instance_key)
        if record is None or record["status_hint"] != "generated":
            continue
        prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
        if len(prompt_ids) > PROBE_PROMPT_CAP:
            continue
        candidates.append((instance_key, prompt, prompt_ids, record))
    candidates.sort(key=lambda item: hashlib.sha256(item[0].encode()).hexdigest())
    selected = candidates[:PROBE_SIZE]
    if len(selected) < PROBE_SIZE:
        raise RuntimeError(f"only {len(selected)} probe candidates available")

    # Integrity gate: the re-rendered prompt must hash to what the generation run recorded.
    prompt_hash_matches = 0
    for _key, _, prompt_ids, record in selected:
        if sha256_bytes(json.dumps(prompt_ids).encode()) == record["prompt_sha256"]:
            prompt_hash_matches += 1
    if prompt_hash_matches != len(selected):
        raise RuntimeError(
            f"prompt reproduction mismatch: {prompt_hash_matches}/{len(selected)} hashes agree"
        )

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
    adapter_path = snapshot_download(ADAPTER_REPO, revision=ADAPTER_REVISION)
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    model.config.use_cache = True
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    device = next(model.parameters()).device

    exact_raw = 0
    extracted_equal = 0
    both_extractable = 0
    served_extractable = 0
    output_lengths: list[int] = []
    for _key, _prompt, prompt_ids, record in selected:
        inputs = torch.tensor([prompt_ids]).to(device)
        with torch.no_grad():
            generated = model.generate(
                input_ids=inputs, attention_mask=torch.ones_like(inputs),
                do_sample=False, num_beams=1, max_new_tokens=MAX_NEW_TOKENS,
            )
        completion = tokenizer.decode(
            generated[0, inputs.shape[1] :], skip_special_tokens=True
        )
        output_lengths.append(int(generated.shape[1] - inputs.shape[1]))
        if completion == record["raw_output"]:
            exact_raw += 1
        local_object = first_balanced_object(completion)
        served_object = first_balanced_object(record["raw_output"])
        if served_object is not None:
            served_extractable += 1
        if local_object is None or served_object is None:
            continue
        both_extractable += 1
        try:
            if json.loads(local_object) == json.loads(served_object):
                extracted_equal += 1
        except json.JSONDecodeError:
            pass

    report = {
        "schema_version": "1",
        "status": "probe",
        "analysis_id": ANALYSIS_ID,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "adapter_repo": ADAPTER_REPO,
        "adapter_revision": ADAPTER_REVISION,
        "compared_against": QA_PREDICTIONS_PATH,
        "compared_against_sha256": QA_PREDICTIONS_SHA256,
        "serving_stack": "vllm==0.25.1 bitsandbytes 4bit + LoRA (generation run)",
        "local_stack": "transformers==4.57.6 + peft==0.19.1, nf4 4bit double-quant bf16",
        "probe_size": len(selected),
        "split_used": "train",
        "decoding": {"greedy": True, "max_new_tokens": MAX_NEW_TOKENS},
        "prompt_sha256_matches": prompt_hash_matches,
        "served_extractable": served_extractable,
        "both_extractable": both_extractable,
        "exact_raw_string_matches": exact_raw,
        "parsed_output_agreement": extracted_equal,
        "parsed_output_agreement_rate": (
            extracted_equal / both_extractable if both_extractable else None
        ),
        "local_output_tokens": {
            "mean": sum(output_lengths) / len(output_lengths),
            "max": max(output_lengths),
        },
        "label_access": {"gold_links_read": 0, "sealed_reads": 0},
        "raw_deleted_before_model_load": True,
        "gpu": torch.cuda.get_device_name(0),
        "duration_seconds": time.monotonic() - started,
        "estimated_cost_usd": (time.monotonic() - started) / 3600.0 * HOURLY_RATE_USD,
    }
    print("PROBE_REPORT=" + json.dumps(report, sort_keys=True), flush=True)

    api = HfApi()
    info = api.dataset_info(EVIDENCE_REPO)
    if info.private is not True:
        raise RuntimeError("evidence repository must be private")
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    commit = api.create_commit(
        repo_id=EVIDENCE_REPO,
        repo_type="dataset",
        operations=[CommitOperationAdd(path_in_repo=REPORT_PATH, path_or_fileobj=io.BytesIO(data))],
        commit_message="evidence: plan2 serving-equivalence probe",
        parent_commit=info.sha,
    )
    print(json.dumps({"report_commit_oid": commit.oid, "path": REPORT_PATH}, sort_keys=True))


if __name__ == "__main__":
    main()
