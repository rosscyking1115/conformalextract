from __future__ import annotations

import pytest
from pydantic import ValidationError

from conformalextract.contracts import Argument, EventFrame, Span


def test_empty_frame_serializes_with_arguments_array() -> None:
    frame = EventFrame(
        document_id="doc-1",
        event_type="Conflict.Attack",
        trigger=Span(start=1, end=2, text="attacked"),
        arguments=[],
    )

    assert frame.model_dump(mode="json")["arguments"] == []


def test_spans_are_nonempty_half_open_intervals() -> None:
    with pytest.raises(ValidationError):
        Span(start=2, end=2, text="")


def test_argument_requires_grounded_text() -> None:
    with pytest.raises(ValidationError):
        Argument(role="Attacker", span=Span(start=0, end=1, text=""))
