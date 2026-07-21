from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (ROOT / "jobs" / "plan2_serving_equivalence_probe.py").read_text(encoding="utf-8")
GENERATION = (ROOT / "jobs" / "plan2_prediction_generation.py").read_text(encoding="utf-8")


def _block(script: str, start: str, end: str) -> str:
    return script.split(start, maxsplit=1)[1].split(end, maxsplit=1)[0]


def test_probe_never_loads_vllm_in_process() -> None:
    """The OOM fix: the child previously died because a parent vLLM engine held the card.

    'vllm' may appear in report metadata describing the generation run; what must not exist
    is a vLLM dependency or import that would reserve GPU memory in this process.
    """
    dependencies = _block(SCRIPT, "# dependencies = [", "# ]")
    assert "vllm" not in dependencies
    assert "import vllm" not in SCRIPT
    assert "from vllm" not in SCRIPT
    assert "LoRARequest" not in SCRIPT
    # Standalone job, not a subprocess spawned beside a live engine.
    assert "subprocess" not in SCRIPT


def test_probe_pins_the_same_model_adapter_and_decoding_as_the_generation_run() -> None:
    assert 'MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"' in SCRIPT
    assert 'REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"' in SCRIPT
    assert 'ADAPTER_REVISION = "edd69373be3d46ae2a982e555f4ec9549491e8e4"' in SCRIPT
    assert "MAX_NEW_TOKENS = 256" in SCRIPT
    assert "do_sample=False" in SCRIPT
    assert "num_beams=1" in SCRIPT


def test_probe_compares_against_the_hash_pinned_served_predictions() -> None:
    assert 'QA_PREDICTIONS_PATH = "plan2/predictions/qa.v1.jsonl"' in SCRIPT
    assert (
        'QA_PREDICTIONS_SHA256 = '
        '"036f8f08dcbe7587c19def951f81e62e4be0a5de1485b406c64514d03bf721f3"' in SCRIPT
    )
    assert "hash mismatch for frozen artifact" in SCRIPT


def test_probe_renders_prompts_identically_to_the_generation_run() -> None:
    assert _block(SCRIPT, 'TEMPLATE = """', '"""') == _block(GENERATION, 'TEMPLATE = """', '"""')
    # Integrity gate: re-rendered prompts must hash to what the run recorded, or abort.
    assert "prompt reproduction mismatch" in SCRIPT
    assert 'record["prompt_sha256"]' in SCRIPT


def test_probe_uses_the_adopted_c2_extraction_algorithm() -> None:
    """Reviewer condition C2: from-index-0 scan with global string/escape state."""
    body = _block(SCRIPT, "def first_balanced_object", "def fetch_verified")
    assert "for index, character in enumerate(text)" in body  # scans from 0, not from first '{'
    assert "in_string" in body and "escaped" in body
    assert "depth" in body


def test_probe_touches_only_the_train_split_and_no_gold() -> None:
    assert '!= "train"' in SCRIPT
    assert "gold_evt_links" not in SCRIPT
    assert '"gold_links_read": 0' in SCRIPT
    assert '"sealed_reads": 0' in SCRIPT


def test_probe_deletes_raw_before_model_load_and_verifies_downloads() -> None:
    assert "shutil.rmtree(RAW_DIR)" in SCRIPT
    assert SCRIPT.index("shutil.rmtree(RAW_DIR)") < SCRIPT.index(
        "AutoModelForCausalLM.from_pretrained"
    )
    assert "raw extraction survived materialization" in SCRIPT
    assert "checksum mismatch" in SCRIPT


def test_probe_report_is_text_free_and_private() -> None:
    report_section = _block(SCRIPT, "report = {", "PROBE_REPORT=")
    for banned in ('"prompt"', '"raw_output"', '"completion"', '"sentences"'):
        assert banned not in report_section
    assert "private is not True" in SCRIPT
    assert "parent_commit=info.sha" in SCRIPT


def test_probe_reports_both_strict_and_extracted_agreement() -> None:
    # Raw-string equality is the strong signal; extracted equality is the one that matters
    # for the evidence base, since the adopted policy parses the extracted object.
    assert '"exact_raw_string_matches"' in SCRIPT
    assert '"parsed_output_agreement"' in SCRIPT
    assert '"parsed_output_agreement_rate"' in SCRIPT
    # v2: n=24 gave a 95% interval of [0.69, 0.96] - too loose for the reviewer to judge.
    assert "PROBE_SIZE = 300" in SCRIPT


def test_probe_characterises_divergences_rather_than_only_counting_them() -> None:
    """A differing span and a wholly different frame differ in what they imply for risk."""
    body = _block(SCRIPT, "def characterise_divergence", "def main()")
    for category in (
        '"empty_vs_nonempty"',
        '"argument_count_differs"',
        '"different_roles"',
        '"same_roles_different_spans"',
    ):
        assert category in body
    assert '"divergence_categories"' in SCRIPT
    assert '"divergence_count"' in SCRIPT


def test_probe_persists_divergent_pairs_to_the_private_evidence_repo_only() -> None:
    """Divergent pairs carry grounded text - ADR 0005 confines them to the private repo."""
    assert 'DIVERGENCE_PATH = "plan2/serving_equivalence_divergences.v2.jsonl"' in SCRIPT
    assert "private is not True" in SCRIPT
    # Only written when there is something to write, and never overwrites v1.
    assert "if divergences:" in SCRIPT
    assert 'REPORT_PATH = "plan2/serving_equivalence_probe.v2.json"' in SCRIPT
