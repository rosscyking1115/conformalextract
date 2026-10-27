"""Post-execution hardening of ``certify`` (independent review 2026-10-27, findings B1-B3).

The certificate was produced once, on 2026-07-22, and is immutable. Nothing here re-runs it or
changes it. What these tests pin is the command as a rerunner meets it:

- B1: the Plan 3 §3.2 preflight now runs inside ``certify`` before the archive is opened. It had
  existed only as a tested function nobody called.
- B2: ``final_reads`` / ``shift_reads`` are counted from the gold that scoring actually used,
  not written as constants.
- B3: the immutability check runs before anything else, so a rerun refuses before any read.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from conformalextract.certification_preflight import (
    CertificationPreflightError,
    run_certification_input_preflight,
)
from conformalextract.certification_run import (
    SealedRoleError,
    build_certification_access_log,
    certification_artifact,
    count_gold_reads,
    run_certification,
)
from conformalextract.threshold_grid import grid_hash_from_certifiable_thresholds

ROOT = Path(__file__).parents[1]
FROZEN_INPUTS = ROOT / "manifests" / "plan3" / "certification_inputs.json"
SYSTEMS = ("zs", "fs", "qa")


# --- B1: the label-free input preflight ------------------------------------------------------


def _frozen() -> dict[str, object]:
    return {
        "alpha": 0.20,
        "delta": 0.05,
        "acceptance_floor": 0.20,
        "role_map_sha256": "r" * 64,
        "systems": {
            s: {
                "predictions_sha256": s * 32,
                "confidence_candidate": {"zs": "mean", "fs": "tenth_percentile", "qa": "mean"}[s],
                "grid_hash": _grid_hash(s),
            }
            for s in SYSTEMS
        },
    }


THRESHOLDS: list[float | str] = ["-inf", -0.1, -0.05]


def _grid_hash(system_id: str) -> str:
    return grid_hash_from_certifiable_thresholds(system_id, THRESHOLDS)


def _grids() -> dict[str, object]:
    return {
        "delta": 0.05 / 3,
        "grids": {
            s: {"grid_hash": _grid_hash(s), "certifiable_thresholds": list(THRESHOLDS)}
            for s in SYSTEMS
        },
    }


ROLES = {
    "c1": ("certification", "g1"),
    "c2": ("certification", "g2"),
    "t1": ("train", "g3"),
    "d1": ("development", "g4"),
    "f1": ("final", "g5"),
}


def _preflight(**overrides: object) -> object:
    arguments: dict[str, object] = {
        "prediction_sha256": {s: s * 32 for s in SYSTEMS},
        "prediction_document_ids": {s: frozenset(ROLES) for s in SYSTEMS},
        "role_map_sha256": "r" * 64,
        "roles": ROLES,
        "grids": _grids(),
        "selected_candidates": {"zs": "mean", "fs": "tenth_percentile", "qa": "mean"},
        "frozen": _frozen(),
    }
    arguments.update(overrides)
    return run_certification_input_preflight(**arguments)  # type: ignore[arg-type]


def test_consistent_inputs_pass_and_report_what_was_not_checked() -> None:
    result = _preflight()
    assert result.status == "ready"  # type: ignore[attr-defined]
    assert result.certification_documents == 2  # type: ignore[attr-defined]
    # The two §3.2 bullets a run-time check cannot discharge are named, not implied.
    assert "synthetic_coverage" in result.not_checked_at_run_time  # type: ignore[attr-defined]


def test_a_prediction_file_that_is_not_the_frozen_one_refuses() -> None:
    with pytest.raises(CertificationPreflightError, match="qa predictions"):
        _preflight(prediction_sha256={"zs": "zs" * 32, "fs": "fs" * 32, "qa": "x" * 64})


def test_a_role_map_that_is_not_the_frozen_one_refuses() -> None:
    with pytest.raises(CertificationPreflightError, match="role map"):
        _preflight(role_map_sha256="0" * 64)


def test_systems_covering_different_certification_documents_refuse() -> None:
    ids = {s: frozenset(ROLES) for s in SYSTEMS}
    ids["fs"] = frozenset(ROLES) - {"c2"}
    with pytest.raises(CertificationPreflightError, match="identical"):
        _preflight(prediction_document_ids=ids)


def test_a_certification_document_no_system_predicted_refuses() -> None:
    ids = {s: frozenset(ROLES) - {"c2"} for s in SYSTEMS}
    with pytest.raises(CertificationPreflightError, match="no prediction"):
        _preflight(prediction_document_ids=ids)


def test_a_certification_group_shared_with_train_refuses() -> None:
    roles = dict(ROLES)
    roles["t1"] = ("train", "g1")  # g1 is also a certification group
    with pytest.raises(CertificationPreflightError, match="train"):
        _preflight(roles=roles)


def test_a_grid_that_is_not_the_frozen_one_refuses() -> None:
    grids = _grids()
    grids["grids"]["qa"]["grid_hash"] = "other"  # type: ignore[index]
    with pytest.raises(CertificationPreflightError, match="grid"):
        _preflight(grids=grids)


def test_thresholds_that_do_not_hash_to_the_declared_grid_refuse() -> None:
    """The declared hash matches the frozen one, but the thresholds certify would use do not."""
    grids = _grids()
    grids["grids"]["qa"]["certifiable_thresholds"] = ["-inf", -0.2, -0.05]  # type: ignore[index]
    with pytest.raises(CertificationPreflightError, match="do not hash"):
        _preflight(grids=grids)


def test_the_committed_grids_hash_to_their_declared_hashes() -> None:
    grids = json.loads((ROOT / "evidence/plan2/threshold_grids.json").read_text(encoding="utf-8"))
    for s in SYSTEMS:
        entry = grids["grids"][s]
        assert grid_hash_from_certifiable_thresholds(s, entry["certifiable_thresholds"]) == (
            entry["grid_hash"]
        )


# --- B2: counting distinct gold reads ----------------------------------------------------------


def test_gold_read_once_per_system_counts_each_document_once() -> None:
    used = ["c1", "c2"] * 3  # certify reads each document's gold once per system
    assert count_gold_reads(used, ROLES, expected_documents=2) == {"certification": 2}


def test_gold_outside_the_certification_role_refuses() -> None:
    with pytest.raises(SealedRoleError, match="outside the certification role"):
        count_gold_reads(["c1", "c2", "f1"], ROLES, expected_documents=2)


def test_gold_for_a_document_the_role_map_does_not_know_refuses() -> None:
    with pytest.raises(SealedRoleError):
        count_gold_reads(["c1", "c2", "zz"], ROLES, expected_documents=2)


def test_a_certification_count_that_differs_from_the_access_record_refuses() -> None:
    with pytest.raises(RuntimeError, match="access record covers 3"):
        count_gold_reads(["c1", "c2"], ROLES, expected_documents=3)


def test_a_threshold_order_with_duplicates_refuses() -> None:
    grids = _grids()
    grids["grids"]["zs"]["certifiable_thresholds"] = ["-inf", -0.1, -0.1]  # type: ignore[index]
    with pytest.raises(CertificationPreflightError, match="tie order"):
        _preflight(grids=grids)


def test_a_candidate_that_drifted_from_the_freeze_refuses() -> None:
    with pytest.raises(CertificationPreflightError, match="candidate"):
        _preflight(selected_candidates={"zs": "mean", "fs": "mean", "qa": "mean"})


def test_operating_point_drift_refuses() -> None:
    frozen = _frozen()
    frozen["alpha"] = 0.25
    with pytest.raises(CertificationPreflightError, match="ADR 0007"):
        _preflight(frozen=frozen)


def test_the_committed_frozen_inputs_agree_with_every_record_they_restate() -> None:
    """The manifest restates reviewed values; it must not drift from any of their homes."""
    from conformalextract.certification import (
        FROZEN_ACCEPTANCE_FLOOR,
        FROZEN_ALPHA,
        FROZEN_CONFIDENCE_CANDIDATES,
        FROZEN_DELTA,
    )

    frozen = json.loads(FROZEN_INPUTS.read_text(encoding="utf-8"))
    assert (frozen["alpha"], frozen["delta"], frozen["acceptance_floor"]) == (
        FROZEN_ALPHA,
        FROZEN_DELTA,
        FROZEN_ACCEPTANCE_FLOOR,
    )
    grids = json.loads((ROOT / "evidence/plan2/threshold_grids.json").read_text(encoding="utf-8"))
    gate = json.loads(
        (ROOT / "evidence/plan2/development_gate_summary.json").read_text(encoding="utf-8")
    )
    addendum = (
        ROOT / "docs/plan3/section-12-1-certification-only-scope-addendum-2026-07-30.md"
    ).read_text(encoding="utf-8")
    assert frozen["role_map_sha256"] in addendum
    for s in SYSTEMS:
        entry = frozen["systems"][s]
        assert entry["grid_hash"] == grids["grids"][s]["grid_hash"]
        assert entry["confidence_candidate"] == FROZEN_CONFIDENCE_CANDIDATES[s]
        assert entry["confidence_candidate"] == gate["per_system"][s]["selected_candidate"]
        row = f"`data/private/plan2/predictions/{s}.v1.jsonl` | `{entry['predictions_sha256']}`"
        assert row in addendum


# --- B2: reads are counted, not asserted -----------------------------------------------------


def _run() -> object:
    from conformalextract.certification_run import GroupRow

    rows = [
        GroupRow(group_id=f"g{i}", score=0.0, all_valid=True, loss=0.0, document_count=1)
        for i in range(50)
    ]
    return run_certification(
        rows_by_system={s: rows for s in SYSTEMS},
        thresholds_by_system={s: [float("-inf")] for s in SYSTEMS},
        candidates_by_system={"qa": "mean", "zs": "mean", "fs": "tenth_percentile"},
        delta_allocation={s: 0.05 / 3 for s in SYSTEMS},
        access_log=build_certification_access_log(["d1"]),
        alpha=0.20,
        delta=0.05,
        acceptance_floor=0.20,
        material_gain=0.05,
    )


def test_the_artifact_records_the_reads_it_is_given_not_a_constant() -> None:
    artifact = certification_artifact(
        _run(),  # type: ignore[arg-type]
        provenance={},
        gold_reads_by_role={"certification": 7, "final": 1},
    )
    access = artifact["certification_access"]
    assert isinstance(access, Mapping)
    assert access["final_reads"] == 1  # a nonzero count is reported, never masked to 0
    assert access["shift_reads"] == 0
    assert access["gold_reads_by_role"] == {"certification": 7, "final": 1}


def test_the_artifact_cannot_be_built_without_measured_reads() -> None:
    with pytest.raises(TypeError):
        certification_artifact(_run(), provenance={})  # type: ignore[arg-type,call-arg]


# --- CLI ordering: B3, then B1 before any archive read -----------------------------------------


def _forbid_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    def opened(*_: object, **__: object) -> object:
        raise AssertionError("the RAMS archive was opened")

    monkeypatch.setattr("conformalextract.profiles.read_rams_instances", opened)
    monkeypatch.setattr("conformalextract.profiles.read_ontology", opened)


def _invoke(arguments: list[str]) -> object:
    from typer.testing import CliRunner

    from conformalextract.cli import app

    return CliRunner().invoke(app, ["certify", *arguments])


def test_an_existing_result_refuses_before_any_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_archive(monkeypatch)
    result_out = tmp_path / "certification_result.json"
    result_out.write_text("{}", encoding="utf-8")
    outcome = _invoke(
        [
            "--result-out",
            str(result_out),
            "--rams-archive",
            str(tmp_path / "absent.tar.gz"),
            "--role-map",
            str(tmp_path / "absent.jsonl"),
            "--i-have-reviewer-approval",
        ]
    )
    assert isinstance(outcome.exception, RuntimeError)  # type: ignore[attr-defined]
    assert "already exists and is immutable" in str(outcome.exception)  # type: ignore[attr-defined]


def _write_inputs(tmp_path: Path, *, qa_hash_override: str | None = None) -> list[str]:
    predictions = tmp_path / "predictions"
    predictions.mkdir()
    hashes = {}
    for s in SYSTEMS:
        path = predictions / f"{s}.v1.jsonl"
        lines = [json.dumps({"instance_key": key}) for key in ("c1", "c2")]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        hashes[s] = hashlib.sha256(path.read_bytes()).hexdigest()
    role_map = tmp_path / "roles.jsonl"
    role_map.write_text(
        "\n".join(
            json.dumps({"document_id": d, "role": r, "group_id": g}) for d, (r, g) in ROLES.items()
        )
        + "\n",
        encoding="utf-8",
    )
    frozen = json.loads(FROZEN_INPUTS.read_text(encoding="utf-8"))
    frozen["role_map_sha256"] = hashlib.sha256(role_map.read_bytes()).hexdigest()
    for s in SYSTEMS:
        frozen["systems"][s]["predictions_sha256"] = hashes[s]
    if qa_hash_override is not None:
        frozen["systems"]["qa"]["predictions_sha256"] = qa_hash_override
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_text(json.dumps(frozen), encoding="utf-8")
    return [
        "--predictions-dir",
        str(predictions),
        "--role-map",
        str(role_map),
        "--frozen-inputs",
        str(frozen_path),
        "--rams-archive",
        str(tmp_path / "absent.tar.gz"),
        "--result-out",
        str(tmp_path / "out.json"),
        "--i-have-reviewer-approval",
    ]


def test_the_preflight_refuses_before_the_archive_is_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_archive(monkeypatch)
    outcome = _invoke(_write_inputs(tmp_path, qa_hash_override="0" * 64))
    assert isinstance(outcome.exception, CertificationPreflightError)  # type: ignore[attr-defined]
    assert not (tmp_path / "out.json").exists()


def test_consistent_inputs_reach_the_archive_only_after_the_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The archive guard is the first thing hit once the preflight passes."""
    _forbid_archive(monkeypatch)
    outcome = _invoke(_write_inputs(tmp_path))
    assert isinstance(outcome.exception, AssertionError)  # type: ignore[attr-defined]
    assert "archive was opened" in str(outcome.exception)  # type: ignore[attr-defined]


# --- The retrospective: what the never-run preflight would have said --------------------------


def test_the_retrospective_preflight_passed_on_the_frozen_inputs_without_reading_gold() -> None:
    """The 2026-07-22 run had no preflight; its inputs, checked afterwards, pass it.

    Pins the artifact to the frozen manifest so the two cannot drift apart: the hashes the
    retrospective measured are the hashes the manifest freezes, and the certificate's own
    document and group counts are the ones the preflight found.
    """

    artifact = json.loads(
        (ROOT / "evidence/plan3/certification_preflight_retrospective.json").read_text(
            encoding="utf-8"
        )
    )
    frozen = json.loads(FROZEN_INPUTS.read_text(encoding="utf-8"))
    certificate = json.loads(
        (ROOT / "evidence/plan3/certification_result.json").read_text(encoding="utf-8")
    )
    assert artifact["preflight"]["status"] == "ready"
    assert artifact["certification_access"] == {"archive_opened": False, "gold_read": False}
    assert artifact["inputs_sha256"]["rams_roles.jsonl"] == frozen["role_map_sha256"]
    for s in SYSTEMS:
        expected = frozen["systems"][s]["predictions_sha256"]
        assert artifact["inputs_sha256"][f"{s}.v1.jsonl"] == expected
    assert (
        artifact["preflight"]["certification_documents"]
        == certificate["certification_access"]["documents_read"]
    )
    assert (
        artifact["preflight"]["certification_groups"] == certificate["n_certification_groups"]
    )
    assert set(artifact["preflight"]["not_checked_at_run_time"]) == {
        "synthetic_coverage",
        "system_identity_fields",
    }
