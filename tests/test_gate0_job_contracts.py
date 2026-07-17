from __future__ import annotations

import ast
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]


def test_gate0e_authority_requires_actual_reviewed_generation_evidence() -> None:
    authority = json.loads(
        (ROOT / "evidence" / "gate0" / "evidence_authority.json").read_text(encoding="utf-8")
    )
    evidence_path = ROOT / authority["gate0e_active_evidence"]
    evidence_bytes = evidence_path.read_bytes()
    evidence = json.loads(evidence_bytes)
    superseded = set(authority["superseded_model_evidence"])

    assert authority["gate0e_status"] == "pass_independently_reviewed"
    assert evidence["actual_model_generation_pass"] is True
    assert evidence["gate0e_pass"] is True
    assert hashlib.sha256(evidence_bytes).hexdigest() == authority["gate0e_artifact_sha256"]
    assert len(authority["gate0e_hub_commit_oid"]) == 40
    assert "evidence/gate0/model_score_smoke.v2.json" in superseded
    assert "actual_model_generation_pass" in authority["acceptance_rule"]


def test_gate0e_job_is_reproducible_private_and_text_free() -> None:
    script = (ROOT / "jobs" / "gate0_model_score_smoke.py").read_text(encoding="utf-8")

    for dependency in (
        '"accelerate==1.14.0"',
        '"huggingface-hub==0.36.2"',
        '"numpy==2.5.1"',
        '"torch==2.13.0"',
        '"transformers==4.57.6"',
    ):
        assert dependency in script
    assert "cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54" in script
    assert "private=True" in script
    assert 'repo_type="dataset"' in script
    assert 'restricted_source_text_in_evidence": False' in script
    assert '"actual_model_generation_pass": gate0e_pass' in script
    assert "GATE0E_REPORT_B64=" in script
    assert script.index("GATE0E_REPORT_B64=") < script.index("persisted_sha256 = persist_report(")
    assert "--create-evidence-repo" in script
    assert "raw_output" not in script.split("report =", maxsplit=1)[1]


def test_gate0e_job_matches_frozen_development_lock() -> None:
    script_path = ROOT / "jobs" / "gate0_model_score_smoke.py"
    manifest = json.loads(
        (ROOT / "manifests" / "gate0e-development-sample.json").read_text(encoding="utf-8")
    )
    tree = ast.parse(script_path.read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "FROZEN_DEVELOPMENT_GROUPS"
            for target in node.targets
        )
    )
    embedded = ast.literal_eval(assignment.value)
    expected = {
        record["document_id_sha256"]: record["group_id_sha256"] for record in manifest["records"]
    }

    assert manifest["data_role"] == "development"
    assert manifest["selection_sha256"] == (
        "4092e154b2581e943f2a56ea15c40103a1b98796126404fdf8f5604017b12772"
    )
    assert len(expected) == len(set(expected.values())) == 20
    assert embedded == expected


def test_gate0e_malformed_output_gets_worst_outcome() -> None:
    namespace = runpy.run_path(str(ROOT / "jobs" / "gate0_model_score_smoke.py"))
    loss, scores = namespace["assess_output"]("invalid_json", {}, {}, [-0.1])

    assert loss == 1.0
    assert all(value == float("-inf") for value in scores.values())


def test_gate0e_precreated_repository_mode_never_calls_create() -> None:
    namespace = runpy.run_path(str(ROOT / "jobs" / "gate0_model_score_smoke.py"))
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeApi:
        def create_repo(self, *args: object, **kwargs: Any) -> None:
            calls.append(("create_repo", kwargs))

        def repo_info(self, *args: object, **kwargs: Any) -> None:
            calls.append(("repo_info", kwargs))

        def upload_file(self, *args: object, **kwargs: Any) -> None:
            calls.append(("upload_file", kwargs))

    persist_report = namespace["persist_report"]
    persist_report.__globals__["HfApi"] = FakeApi
    digest = persist_report(
        b'{"status":"pass"}\n',
        "rosscyking/conformalextract-evidence",
        create_repo=False,
    )

    assert len(digest) == 64
    assert [name for name, _ in calls] == ["repo_info", "upload_file"]
