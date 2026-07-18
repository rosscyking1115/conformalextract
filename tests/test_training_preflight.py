from __future__ import annotations

import pytest
from pydantic import ValidationError

from conformalextract.training import (
    MODEL_REVISION,
    TrainingConfig,
    TrainingRuntimeConfig,
    validate_training_preflight,
)


def _runtime(**overrides: object) -> TrainingRuntimeConfig:
    kwargs: dict[str, object] = {
        "max_length": 2048,
        "learning_rate": 2e-4,
        "pad_token_set": True,
        "tokenizer_revision": MODEL_REVISION,
    }
    kwargs.update(overrides)
    return TrainingRuntimeConfig(**kwargs)  # type: ignore[arg-type]


def test_consistent_runtime_and_config_pass_preflight() -> None:
    validate_training_preflight(_runtime(), TrainingConfig())


def test_max_length_below_the_context_rung_is_rejected() -> None:
    # The TRL SFTConfig.max_length default of 1024 silently truncates document-level inputs.
    with pytest.raises(ValueError, match="max_length"):
        validate_training_preflight(_runtime(max_length=1024), TrainingConfig())


def test_learning_rate_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="learning_rate"):
        validate_training_preflight(_runtime(learning_rate=1e-4), TrainingConfig())


def test_unset_pad_token_is_rejected() -> None:
    with pytest.raises(ValueError, match="pad_token"):
        validate_training_preflight(_runtime(pad_token_set=False), TrainingConfig())


def test_tokenizer_revision_must_match_the_pinned_model_revision() -> None:
    with pytest.raises(ValueError, match="tokenizer revision"):
        validate_training_preflight(_runtime(tokenizer_revision="a" * 40), TrainingConfig())


def test_runtime_config_pins_the_silent_failure_traps() -> None:
    # use_cache/gradient_checkpointing/use_reentrant/packing/completion_only are pinned by
    # the model, so a wrong value cannot even be constructed.
    for field, bad in (
        ("use_cache", True),
        ("gradient_checkpointing", False),
        ("use_reentrant", True),
        ("packing", True),
        ("completion_only", False),
    ):
        with pytest.raises(ValidationError):
            _runtime(**{field: bad})


def test_r1_context_rung_is_accepted_when_config_moves_with_it() -> None:
    # R1 may move to a higher ladder rung; preflight must track the config, not a constant.
    adjusted = TrainingConfig(context_tokens=2560, learning_rate=1e-4)
    validate_training_preflight(
        _runtime(max_length=2560, learning_rate=1e-4), adjusted
    )
