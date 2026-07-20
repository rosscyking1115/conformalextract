# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "vllm==0.25.1",
#   "numpy",
#   "bitsandbytes==0.49.2",
#   "peft==0.19.1",
# ]
# ///
"""Plan 2 prediction generation: ZS/FS/QA x 9,124 RAMS trigger frames on the frozen stack.

Renders zero-shot prompts from an ephemeral, checksum-verified RAMS download using only
``evt_triggers`` + ``sentences`` (gold links are never read; sealed labels never touched),
composes FS prompts by prepending the two frozen demonstrations, and generates greedily on
the G2b-proven vLLM bitsandbytes 4-bit path (QA adds the pinned R2 adapter as a LoRA
request). Frames whose zero-shot prompt exceeds the frozen 6,144-token rung get explicit
``context_overflow`` records in ALL three systems - identical comparison sets, no silent
exclusion. Each arm's predictions persist to the private evidence Dataset as soon as the
arm completes (skip-if-exists gives resume semantics); a fresh-process transformers+peft
probe then checks parsed-output agreement with the served QA arm. The printed report is
aggregate and text-free.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import numpy as np

os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ADAPTER_REPO = "rosscyking/conformalextract-qwen3-4b-qlora"
ADAPTER_REVISION = "edd69373be3d46ae2a982e555f4ec9549491e8e4"  # R2 copy B commit
RAMS_URL = "https://nlp.jhu.edu/rams/RAMS_1.0c.tar.gz"
RAMS_SHA256 = "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54"
EVIDENCE_REPO = "rosscyking/conformalextract-evidence"
ROLES_PATH = "plan2/rams_roles.jsonl"
ROLES_SHA256 = "17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3"
DEMOS_PATH = "plan2/fs_demonstrations.jsonl"
DEMOS_SHA256 = "879baed7be15c487d50d6032cb5ec728203c45c8add20d113a2a47ef62b97008"
ANALYSIS_ID = "plan2prep-f3f2f7a938061a92b2cb"
PREDICTIONS_PREFIX = "plan2/predictions"  # ADR 0005: private evidence Dataset only
REPORT_PATH_PATTERN = "plan2/predictions/report.v{version}.json"  # attempts never overwrite

SYSTEMS = ("zs", "fs", "qa")
EXPECTED_ROLE_COUNTS = {
    "train": 4068,
    "development": 933,
    "certification": 3152,
    "final": 971,
}  # frozen split manifest; total 9,124
CONTEXT_TOKENS = 6144  # ADR 0003 selected rung
MAX_NEW_TOKENS = 256  # G2b decision: >1.5x the measured real max (162), restores headroom
MAX_MODEL_LEN = 9728  # covers measured FS worst case 9,249 prompt tokens + 256 output
PROBE_SIZE = 12
PROBE_PROMPT_CAP = 4096  # keep the single-item transformers probe fast
MAX_ELAPSED_HOURS_BEFORE_NEXT_ARM = 12.0
HOURLY_RATE_USD = 0.80  # l4x1
SEED = 42

WORKSPACE = Path("/tmp/ce-predict")
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


def fetch_verified(url: str, expected_sha256: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:  # frozen official URL only
        data = response.read()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise RuntimeError(f"checksum mismatch for {url}: {digest}")
    destination.write_bytes(data)


def load_verified_evidence_file(filename: str, expected_sha256: str) -> bytes:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(repo_id=EVIDENCE_REPO, filename=filename, repo_type="dataset")
    data = Path(path).read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise RuntimeError(f"hash mismatch for frozen artifact {filename}")
    return data


def load_roles() -> dict[str, str]:
    roles: dict[str, str] = {}
    for line in load_verified_evidence_file(ROLES_PATH, ROLES_SHA256).decode("utf-8").splitlines():
        record = json.loads(line)
        roles[str(record["document_id"])] = str(record["role"])
    return roles


def load_demonstrations() -> list[dict[str, str]]:
    rows = [
        json.loads(line)
        for line in load_verified_evidence_file(DEMOS_PATH, DEMOS_SHA256)
        .decode("utf-8")
        .splitlines()
        if line.strip()
    ]
    if len(rows) != 2:
        raise RuntimeError("expected exactly two frozen FS demonstrations")
    return rows


def compose_fs_prefix(demonstrations: list[dict[str, str]]) -> str:
    """Frozen FS composition rule: demo prompt + gold completion pairs, file order."""

    return "".join(f"{demo['prompt']}\n{demo['completion']}\n\n" for demo in demonstrations)


def parse_ontology(text: str) -> dict[str, list[str]]:
    ontology: dict[str, list[str]] = {}
    for line in text.splitlines():
        parts = line.split()
        if parts:
            ontology[parts[0]] = [parts[i] for i in range(1, len(parts), 2)]
    return ontology


def render_zs_prompt(record: dict, ontology: dict[str, list[str]]) -> dict:
    """Render the frozen zero-shot prompt from triggers + tokens only (no gold access)."""

    instance_key = f"rams:{record['doc_key']}"
    if len(record["evt_triggers"]) != 1:
        raise RuntimeError(f"expected exactly one trigger for {instance_key}")
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
    return {
        "instance_key": instance_key,
        "event_type": event_type,
        "trigger_start": trigger_start,
        "trigger_end": trigger_end,
        "prompt": prompt,
    }


def materialize_frames(roles: dict[str, str]) -> list[dict]:
    """Ephemeral RAMS download -> ZS prompts for every role-assigned frame; raw deleted."""

    archive = RAW_DIR / "RAMS_1.0c.tar.gz"
    fetch_verified(RAMS_URL, RAMS_SHA256, archive)
    frames: list[dict] = []
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
                if role is None:
                    continue
                rendered = render_zs_prompt(record, ontology)
                rendered["role"] = role
                frames.append(rendered)
    shutil.rmtree(RAW_DIR)  # delete raw archive + extraction BEFORE any model work
    observed = {role: 0 for role in EXPECTED_ROLE_COUNTS}
    for frame in frames:
        observed[frame["role"]] += 1
    if observed != EXPECTED_ROLE_COUNTS:
        raise RuntimeError(f"role counts diverge from the frozen split manifest: {observed}")
    frames.sort(key=lambda frame: frame["instance_key"])
    return frames


def confidence_candidates(transitions: list[float]) -> dict[str, float] | None:
    """The three predeclared higher-is-better candidates; null encodes -inf (JSON-safe)."""

    if not transitions:
        return None
    array = np.asarray(transitions, dtype=np.float64)
    if not np.isfinite(array).all():
        raise RuntimeError("transition log probabilities must be finite")
    return {
        "mean": float(np.mean(array)),
        "tenth_percentile": float(np.quantile(array, 0.1)),
        "minimum": float(np.min(array)),
    }


def chosen_transition_logprobs(output) -> list[float]:
    token_ids = list(output.token_ids)
    logprob_maps = output.logprobs or []
    if len(logprob_maps) != len(token_ids):
        raise RuntimeError("logprob stream does not align with generated tokens")
    return [
        float(step[token_id].logprob)
        for token_id, step in zip(token_ids, logprob_maps, strict=True)
    ]


def arm_records(system_id: str, generated: list[dict], overflow: list[dict]) -> list[dict]:
    records = []
    for item in generated:
        records.append(
            {
                "schema_version": "1",
                "analysis_id": ANALYSIS_ID,
                "system_id": system_id,
                "instance_key": item["instance_key"],
                "role": item["role"],
                "event_type": item["event_type"],
                "trigger_start": item["trigger_start"],
                "trigger_end": item["trigger_end"],
                "prompt_sha256": item["prompt_sha256"],
                "prompt_tokens": item["prompt_tokens"],
                "status_hint": "generated",
                "raw_output": item["raw_output"],
                "output_tokens": item["output_tokens"],
                "finish_reason": item["finish_reason"],
                "confidence_candidates": item["confidence_candidates"],
            }
        )
    for item in overflow:
        records.append(
            {
                "schema_version": "1",
                "analysis_id": ANALYSIS_ID,
                "system_id": system_id,
                "instance_key": item["instance_key"],
                "role": item["role"],
                "event_type": item["event_type"],
                "trigger_start": item["trigger_start"],
                "trigger_end": item["trigger_end"],
                "prompt_sha256": item["prompt_sha256"],
                "prompt_tokens": item["prompt_tokens"],
                "status_hint": "context_overflow",
                "raw_output": "",
                "output_tokens": 0,
                "finish_reason": "context_overflow",
                "confidence_candidates": None,
            }
        )
    records.sort(key=lambda record: record["instance_key"])
    if len(records) != sum(EXPECTED_ROLE_COUNTS.values()):
        raise RuntimeError(f"{system_id}: record count is not the full frame set")
    return records


def persist_arm(system_id: str, records: list[dict]) -> str:
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    info = api.dataset_info(EVIDENCE_REPO)
    if info.private is not True:
        raise RuntimeError("evidence repository must be private")
    path_in_repo = f"{PREDICTIONS_PREFIX}/{system_id}.v1.jsonl"
    if api.file_exists(
        repo_id=EVIDENCE_REPO, filename=path_in_repo, repo_type="dataset", revision=info.sha
    ):
        raise RuntimeError(f"predictions path already exists: {path_in_repo}")
    payload = "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records
    ).encode("utf-8")
    commit = api.create_commit(
        repo_id=EVIDENCE_REPO,
        repo_type="dataset",
        operations=[
            CommitOperationAdd(path_in_repo=path_in_repo, path_or_fileobj=io.BytesIO(payload))
        ],
        commit_message=f"evidence: plan2 {system_id} predictions",
        parent_commit=info.sha,
    )
    print(
        json.dumps(
            {
                "persisted_arm": system_id,
                "path": path_in_repo,
                "records": len(records),
                "sha256": sha256_bytes(payload),
                "commit_oid": commit.oid,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return commit.oid


def arm_already_persisted(system_id: str) -> bool:
    from huggingface_hub import HfApi

    return HfApi().file_exists(
        repo_id=EVIDENCE_REPO,
        filename=f"{PREDICTIONS_PREFIX}/{system_id}.v1.jsonl",
        repo_type="dataset",
    )


def summarize_arm(records: list[dict], elapsed: float) -> dict:
    output_tokens = [r["output_tokens"] for r in records if r["status_hint"] == "generated"]
    decodable = 0
    empty = 0
    for record in records:
        if record["status_hint"] != "generated":
            continue
        if not record["raw_output"].strip():
            empty += 1
            continue
        try:
            json.loads(record["raw_output"])
            decodable += 1
        except json.JSONDecodeError:
            pass
    lengths = np.asarray(output_tokens, dtype=np.float64)
    return {
        "records": len(records),
        "generated": len(output_tokens),
        "context_overflow": len(records) - len(output_tokens),
        "empty_output": empty,
        "json_decodable": decodable,
        "elapsed_seconds": elapsed,
        "items_per_hour": len(output_tokens) / elapsed * 3600.0 if elapsed > 0 else None,
        "output_tokens": {
            "mean": float(np.mean(lengths)) if len(lengths) else None,
            "p95": float(np.quantile(lengths, 0.95)) if len(lengths) else None,
            "max": int(np.max(lengths)) if len(lengths) else None,
        },
        "hit_output_cap": int(np.sum(lengths >= MAX_NEW_TOKENS)) if len(lengths) else 0,
    }


def run_probe(probe_items: list[dict], vllm_outputs: dict[str, str], adapter_path: str) -> dict:
    """Fresh-process transformers+peft regeneration; parsed-output agreement with vLLM."""

    probe_file = WORKSPACE / "probe_prompts.json"
    probe_file.write_text(
        json.dumps(
            [{"instance_key": p["instance_key"], "prompt": p["prompt"]} for p in probe_items]
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--probe",
            str(probe_file),
            "--adapter-path",
            adapter_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    line = next(
        line for line in completed.stdout.splitlines() if line.startswith("PROBE_OUTPUTS=")
    )
    fresh_outputs: dict[str, str] = json.loads(line.removeprefix("PROBE_OUTPUTS="))

    def canonical(raw: str) -> str:
        try:
            return json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":"))
        except json.JSONDecodeError:
            return "UNPARSEABLE:" + raw.strip()

    agree = sum(
        1
        for key in fresh_outputs
        if canonical(fresh_outputs[key]) == canonical(vllm_outputs[key])
    )
    return {
        "probe_size": len(fresh_outputs),
        "parsed_output_agreement": agree,
        "parsed_output_agreement_rate": agree / len(fresh_outputs),
    }


def probe_subprocess(probe_file: Path, adapter_path: str) -> None:
    """Child process: transformers+peft 4-bit greedy generation on the probe prompts."""

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

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
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    model.config.use_cache = True
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    outputs: dict[str, str] = {}
    for item in json.loads(probe_file.read_text(encoding="utf-8")):
        inputs = tokenizer(item["prompt"], return_tensors="pt").to(
            next(model.parameters()).device
        )
        with torch.no_grad():
            generated = model.generate(
                **inputs, do_sample=False, num_beams=1, max_new_tokens=MAX_NEW_TOKENS
            )
        outputs[item["instance_key"]] = tokenizer.decode(
            generated[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
    print("PROBE_OUTPUTS=" + json.dumps(outputs, sort_keys=True), flush=True)


def persist_report(report: dict) -> tuple[str, str]:
    """Write the report to the first free version slot; resumed attempts never overwrite."""

    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    info = api.dataset_info(EVIDENCE_REPO)
    if info.private is not True:
        raise RuntimeError("evidence repository must be private")
    path = next(
        candidate
        for candidate in (REPORT_PATH_PATTERN.format(version=v) for v in range(1, 10))
        if not api.file_exists(
            repo_id=EVIDENCE_REPO, filename=candidate, repo_type="dataset", revision=info.sha
        )
    )
    data = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    commit = api.create_commit(
        repo_id=EVIDENCE_REPO,
        repo_type="dataset",
        operations=[CommitOperationAdd(path_in_repo=path, path_or_fileobj=io.BytesIO(data))],
        commit_message="evidence: plan2 prediction-generation report",
        parent_commit=info.sha,
    )
    return commit.oid, path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--adapter-path", type=str)
    arguments = parser.parse_args()
    if arguments.probe:
        probe_subprocess(arguments.probe, arguments.adapter_path)
        return

    started = time.monotonic()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    roles = load_roles()
    demonstrations = load_demonstrations()
    fs_prefix = compose_fs_prefix(demonstrations)
    frames = materialize_frames(roles)
    if RAW_DIR.exists():
        raise RuntimeError("raw extraction survived materialization")

    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    fs_prefix_ids = tokenizer(fs_prefix, add_special_tokens=False)["input_ids"]
    for frame in frames:
        prompt_ids = tokenizer(frame["prompt"], add_special_tokens=True)["input_ids"]
        frame["prompt_token_ids"] = prompt_ids
        frame["prompt_tokens"] = len(prompt_ids)
        frame["overflow"] = len(prompt_ids) > CONTEXT_TOKENS
    overflow_frames = [frame for frame in frames if frame["overflow"]]
    live_frames = [frame for frame in frames if not frame["overflow"]]
    fs_worst_case = max(frame["prompt_tokens"] for frame in live_frames) + len(fs_prefix_ids)
    if fs_worst_case + MAX_NEW_TOKENS > MAX_MODEL_LEN:
        raise RuntimeError(f"FS worst case {fs_worst_case} breaches max_model_len (G3)")

    adapter_path = snapshot_download(ADAPTER_REPO, revision=ADAPTER_REVISION)
    llm = LLM(
        model=MODEL_ID,
        revision=REVISION,
        quantization="bitsandbytes",
        dtype="bfloat16",
        gpu_memory_utilization=0.90,
        max_model_len=MAX_MODEL_LEN,
        enforce_eager=True,
        enable_lora=True,
        max_lora_rank=16,
        seed=SEED,
    )
    sampling = SamplingParams(temperature=0.0, max_tokens=MAX_NEW_TOKENS, logprobs=1)
    lora = LoRARequest("qa", 1, adapter_path)

    def system_inputs(system_id: str) -> list[dict]:
        if system_id == "fs":
            items = []
            for frame in live_frames:
                ids = fs_prefix_ids + list(frame["prompt_token_ids"])
                items.append({**frame, "prompt_token_ids": ids, "prompt_tokens": len(ids)})
            return items
        return live_frames

    def generate_arm(system_id: str) -> tuple[list[dict], dict[str, str], float]:
        items = system_inputs(system_id)
        prompts = [{"prompt_token_ids": item["prompt_token_ids"]} for item in items]
        arm_started = time.monotonic()
        outputs = llm.generate(
            prompts,
            sampling_params=sampling,
            lora_request=lora if system_id == "qa" else None,
        )
        elapsed = time.monotonic() - arm_started
        generated: list[dict] = []
        raw_by_key: dict[str, str] = {}
        for item, request_output in zip(items, outputs, strict=True):
            completion = request_output.outputs[0]
            transitions = chosen_transition_logprobs(completion)
            raw_by_key[item["instance_key"]] = completion.text
            generated.append(
                {
                    "instance_key": item["instance_key"],
                    "role": item["role"],
                    "event_type": item["event_type"],
                    "trigger_start": item["trigger_start"],
                    "trigger_end": item["trigger_end"],
                    "prompt_sha256": sha256_bytes(
                        json.dumps(item["prompt_token_ids"]).encode()
                    ),
                    "prompt_tokens": item["prompt_tokens"],
                    "raw_output": completion.text,
                    "output_tokens": len(completion.token_ids),
                    "finish_reason": str(completion.finish_reason),
                    "confidence_candidates": confidence_candidates(transitions),
                }
            )
        return generated, raw_by_key, elapsed

    overflow_records = [
        {
            "instance_key": frame["instance_key"],
            "role": frame["role"],
            "event_type": frame["event_type"],
            "trigger_start": frame["trigger_start"],
            "trigger_end": frame["trigger_end"],
            "prompt_sha256": sha256_bytes(json.dumps(frame["prompt_token_ids"]).encode()),
            "prompt_tokens": frame["prompt_tokens"],
        }
        for frame in overflow_frames
    ]

    arm_summaries: dict[str, dict] = {}
    arm_commits: dict[str, str] = {}
    qa_raw_by_key: dict[str, str] = {}
    completed_arms = 0
    for system_id in SYSTEMS:
        if arm_already_persisted(system_id):
            arm_summaries[system_id] = {"skipped": "already persisted (resume)"}
            completed_arms += 1
            continue
        elapsed_hours = (time.monotonic() - started) / 3600.0
        if elapsed_hours > MAX_ELAPSED_HOURS_BEFORE_NEXT_ARM:
            arm_summaries[system_id] = {"skipped": f"time guard at {elapsed_hours:.2f}h"}
            continue
        generated, raw_by_key, elapsed = generate_arm(system_id)
        if system_id == "qa":
            qa_raw_by_key = raw_by_key
        records = arm_records(system_id, generated, overflow_records)
        arm_commits[system_id] = persist_arm(system_id, records)
        arm_summaries[system_id] = summarize_arm(records, elapsed)
        completed_arms += 1

    probe_result: dict | None = None
    if qa_raw_by_key:
        probe_pool = sorted(
            (
                frame
                for frame in live_frames
                if frame["role"] == "train" and frame["prompt_tokens"] <= PROBE_PROMPT_CAP
            ),
            key=lambda frame: hashlib.sha256(frame["instance_key"].encode()).hexdigest(),
        )[:PROBE_SIZE]
        probe_result = run_probe(
            probe_pool,
            {frame["instance_key"]: qa_raw_by_key[frame["instance_key"]] for frame in probe_pool},
            adapter_path,
        )

    report = {
        "schema_version": "1",
        "status": "complete" if completed_arms == len(SYSTEMS) else "partial",
        "analysis_id": ANALYSIS_ID,
        "model_id": MODEL_ID,
        "model_revision": REVISION,
        "adapter_repo": ADAPTER_REPO,
        "adapter_revision": ADAPTER_REVISION,
        "systems": list(SYSTEMS),
        "decoding": {
            "temperature": 0.0,
            "max_new_tokens": MAX_NEW_TOKENS,
            "logprobs": 1,
            "seed": SEED,
        },
        "context_tokens": CONTEXT_TOKENS,
        "max_model_len": MAX_MODEL_LEN,
        "fs_prefix_tokens": len(fs_prefix_ids),
        "frame_counts": EXPECTED_ROLE_COUNTS,
        "context_overflow_frames": len(overflow_frames),
        "arms": arm_summaries,
        "arm_commits": arm_commits,
        "probe": probe_result,
        "label_access": {"gold_links_read": 0, "sealed_reads": 0},
        "raw_deleted_before_model_load": True,
        "duration_seconds": time.monotonic() - started,
        "estimated_cost_usd": (time.monotonic() - started) / 3600.0 * HOURLY_RATE_USD,
    }
    print("PRED_REPORT=" + json.dumps(report, sort_keys=True), flush=True)
    report_commit, report_path = persist_report(report)
    print(
        json.dumps(
            {
                "report_commit_oid": report_commit,
                "report_path": report_path,
                "status": report["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
