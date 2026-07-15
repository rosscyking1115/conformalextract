"""Canonical immutable artifact and label-access logging utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_json(path: Path, value: Any) -> str:
    """Write canonical JSON once and return its SHA-256 digest."""

    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(value)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        raise FileExistsError(f"refusing to overwrite frozen artifact: {path}") from None
    return sha256_bytes(data)


def freeze_jsonl(path: Path, records: list[dict[str, Any]]) -> str:
    """Write canonical JSON Lines once and return the complete file digest."""

    path.parent.mkdir(parents=True, exist_ok=True)
    data = b"".join(canonical_json_bytes(record) for record in records)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        raise FileExistsError(f"refusing to overwrite frozen artifact: {path}") from None
    return sha256_bytes(data)


def _record_hash(record: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(record))


def append_access_event(path: Path, *, actor: str, label_role: str, purpose: str) -> str:
    """Append a hash-linked event without recording secret or label content."""

    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = "0" * 64
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            previous_hash = str(json.loads(lines[-1])["event_hash"])
    payload = {
        "actor": actor,
        "label_role": label_role,
        "previous_hash": previous_hash,
        "purpose": purpose,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    event_hash = _record_hash(payload)
    record = {**payload, "event_hash": event_hash}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return event_hash


def verify_hash_chain(path: Path) -> bool:
    previous_hash = "0" * 64
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        event_hash = record.pop("event_hash", None)
        if record.get("previous_hash") != previous_hash or event_hash != _record_hash(record):
            return False
        previous_hash = event_hash
    return True
