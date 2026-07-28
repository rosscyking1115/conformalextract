from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from conformalextract.training import (
    LabelAccessPurpose,
    LabelAccessRequest,
    build_label_access_log,
)


def _request(role: str, purpose: LabelAccessPurpose, tag: str = "0") -> LabelAccessRequest:
    return LabelAccessRequest(
        data_role=role,
        document_id_hash=hashlib.sha256(tag.encode()).hexdigest(),
        purpose=purpose,
    )


def test_developmental_and_training_access_builds_a_verifiable_hash_chain() -> None:
    requests = (
        _request("train", LabelAccessPurpose.SFT, "a"),
        _request("train", LabelAccessPurpose.GENERATION, "b"),
        _request("development", LabelAccessPurpose.DEVELOPMENT_SELECTION, "c"),
    )

    log = build_label_access_log(requests)

    assert [entry.data_role for entry in log.entries] == ["train", "train", "development"]
    # Each entry hash is chained to its predecessor, so no entry hash repeats and the
    # head advances with every access.
    assert len({entry.entry_hash for entry in log.entries}) == 3
    assert log.head_hash == log.entries[-1].entry_hash
    assert log.verify() is True


def test_sealed_gold_is_unreachable_for_any_training_purpose() -> None:
    for sealed in ("certification", "final", "shift"):
        for purpose in LabelAccessPurpose:
            with pytest.raises(ValueError, match="sealed"):
                build_label_access_log((_request(sealed, purpose),))


def test_sealed_role_is_unrepresentable_outside_the_declared_vocabulary() -> None:
    with pytest.raises(ValidationError):
        LabelAccessRequest(
            data_role="test",
            document_id_hash="a" * 64,
            purpose=LabelAccessPurpose.SFT,
        )


def test_development_gold_is_limited_to_development_selection() -> None:
    for forbidden in (LabelAccessPurpose.SFT, LabelAccessPurpose.GENERATION):
        with pytest.raises(ValueError, match="development"):
            build_label_access_log((_request("development", forbidden),))


def test_tampering_with_a_recorded_role_breaks_chain_verification() -> None:
    log = build_label_access_log((_request("train", LabelAccessPurpose.SFT),))
    tampered = log.model_copy(
        update={
            "entries": (log.entries[0].model_copy(update={"data_role": "development"}),),
        }
    )

    assert log.verify() is True
    assert tampered.verify() is False


def test_access_log_carries_only_hashes_and_enumerated_facts() -> None:
    log = build_label_access_log((_request("train", LabelAccessPurpose.SFT, "grounded text"),))
    serialized = log.model_dump_json()

    assert "grounded text" not in serialized
    assert log.entries[0].document_id_hash == hashlib.sha256(b"grounded text").hexdigest()
