from __future__ import annotations

import json
from pathlib import Path

import pytest

from conformalextract.artifacts import (
    append_access_event,
    freeze_json,
    freeze_jsonl,
    sha256_file,
    verify_hash_chain,
)


def test_freeze_json_is_canonical_and_refuses_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "artifact.json"
    digest = freeze_json(target, {"b": 2, "a": 1})
    assert target.read_text(encoding="utf-8") == '{"a":1,"b":2}\n'
    assert digest == sha256_file(target)
    with pytest.raises(FileExistsError):
        freeze_json(target, {"a": 1})


def test_access_log_is_hash_linked(tmp_path: Path) -> None:
    log = tmp_path / "access.jsonl"
    append_access_event(log, actor="test", label_role="certification", purpose="unit-test")
    append_access_event(log, actor="test", label_role="final", purpose="unit-test")
    assert verify_hash_chain(log)
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    records[0]["purpose"] = "tampered"
    log.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    assert not verify_hash_chain(log)


def test_freeze_jsonl_is_canonical_and_refuses_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "records.jsonl"
    digest = freeze_jsonl(target, [{"b": 2, "a": 1}, {"c": 3}])
    assert target.read_text(encoding="utf-8") == '{"a":1,"b":2}\n{"c":3}\n'
    assert digest == sha256_file(target)
    with pytest.raises(FileExistsError):
        freeze_jsonl(target, [])
