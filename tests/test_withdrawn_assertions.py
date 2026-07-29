"""A withdrawn assertion must not survive in prose, and the search is for the words.

When `CX-GROUNDING-ORTHOGONAL-01` was narrowed on 2026-07-29, the retired attribution was still
live in **three publication surfaces the ledger has no knowledge of** — `README.md`, the write-up
draft, and a generated appendix. `verify-claims` was green throughout, because it validates the
ledger and resolves evidence paths; it has no view of prose that copied a claim's words.

**So this test searches for the assertion, not the claim ID.** A copy carries the wording and
usually drops the identifier, which is exactly why a claim-ID-based check cannot find it — the
same shape as `tests/test_doc_references.py`'s citation check missing prose that cites nothing.

The two halves are deliberately different in kind, as elsewhere in this suite:

- **A gate:** no tracked prose contains a retired phrasing outside the named exemptions.
- **A guard on the gate:** every exemption still contains its phrase, so the list shrinks when it
  should and cannot rot into a blanket.

Scope, stated because a check reported wider than it runs is this repository's recurring defect:
this searches **tracked** files with prose-bearing suffixes. It is a literal phrase match after
whitespace normalisation, so a *paraphrase* of a withdrawn assertion passes. Catching paraphrase is
natural-language work and is not attempted; reconciling a reworded claim against its copies stays a
reviewer's job, which `REVIEW.md` records as a check.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "evidence" / "withdrawn_assertions.json"

PROSE_SUFFIXES = frozenset({".md", ".json", ".txt", ".py", ".toml"})


def _register() -> list[dict[str, object]]:
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    assertions = data["assertions"]
    assert isinstance(assertions, list)
    return assertions


def _flat(text: str) -> str:
    """Collapse whitespace so a phrase still matches across a line wrap.

    `tests/test_gate_state.py` learned this the expensive way: its first version matched raw text
    and missed the one file that provoked it, because the phrase was wrapped across two lines.
    """

    return " ".join(text.split())


def _tracked_prose() -> list[str]:
    listing = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if listing.returncode != 0:  # pragma: no cover - only outside a git checkout
        pytest.skip("not a git checkout")
    return [f for f in listing.stdout.split() if Path(f).suffix.lower() in PROSE_SUFFIXES]


def test_the_register_is_populated_and_the_scan_reaches_files() -> None:
    """Guard the guard: an empty register or an empty file list passes everything below."""

    assert _register(), "evidence/withdrawn_assertions.json lists no assertions"
    assert len(_tracked_prose()) > 50


@pytest.mark.parametrize("entry", _register(), ids=lambda e: str(e["id"]))
def test_a_withdrawn_assertion_survives_only_where_named(entry: dict[str, object]) -> None:
    phrase = str(entry["phrase"])
    permitted = entry["permitted_in"]
    assert isinstance(permitted, dict)
    needle = _flat(phrase)

    offenders: list[str] = []
    for relative in _tracked_prose():
        if relative in permitted:
            continue
        text = (ROOT / relative).read_text(encoding="utf-8", errors="replace")
        if needle in _flat(text):
            offenders.append(relative)

    assert not offenders, (
        f"withdrawn assertion {phrase!r} (retired from {entry['withdrawn_from']} on "
        f"{entry['withdrawn_on']}) still appears in: {offenders}.\n"
        f"Why it was withdrawn: {entry['why_withdrawn']}\n"
        f"Reword those files, or add each to permitted_in with the reason it must carry the "
        f"words — historical record, or quoting the phrase in order to report it withdrawn."
    )


@pytest.mark.parametrize("entry", _register(), ids=lambda e: str(e["id"]))
def test_every_exemption_still_earns_its_place(entry: dict[str, object]) -> None:
    phrase = _flat(str(entry["phrase"]))
    permitted = entry["permitted_in"]
    assert isinstance(permitted, dict)
    for relative, reason in permitted.items():
        path = ROOT / relative
        assert path.exists(), f"permitted_in names a file that does not exist: {relative}"
        text = path.read_text(encoding="utf-8", errors="replace")
        assert phrase in _flat(text), (
            f"{relative} no longer contains the withdrawn phrase — remove the exemption. "
            f"({reason})"
        )
