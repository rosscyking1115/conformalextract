from __future__ import annotations

import pytest
import torch

from conformalextract.model_smoke import transition_logprobs_from_logits


def test_transition_scores_exclude_prompt_tokens() -> None:
    logits = torch.tensor(
        [
            [0.0, 4.0, 0.0],
            [0.0, 0.0, 4.0],
            [4.0, 0.0, 0.0],
        ]
    )
    token_ids = torch.tensor([0, 1, 2])
    values = transition_logprobs_from_logits(logits=logits, token_ids=token_ids, prompt_length=1)
    assert len(values) == 2
    assert values[0] == pytest.approx(values[1], abs=1e-6)
    assert values[0] > -0.1


def test_transition_scores_reject_alignment_errors() -> None:
    with pytest.raises(ValueError, match="aligned"):
        transition_logprobs_from_logits(
            logits=torch.zeros((2, 3)), token_ids=torch.zeros(3, dtype=torch.long), prompt_length=1
        )
