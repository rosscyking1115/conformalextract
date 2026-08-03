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
this walks the **filesystem** — tracked and untracked alike, see `_prose_files` for why that
distinction cost a commit — over prose-bearing suffixes. It is a literal phrase match after
normalisation, so a *paraphrase* of a withdrawn assertion passes.

**That limit cost the primary result document, one commit after it was written down here.**
`docs/plan3/certification-result.md` carried the same attribution as "the coreference and
entity-selection errors ADR 0007 catalogued" — a *stronger* form, naming two taxonomy categories,
on the document six ledger claims cite as evidence — and this check passed it clean. A second
surface compressed it to "grounded, well-formed, wrong-entity". Both were found by a reviewer
reading the documents.

So: **catching paraphrase is not attempted, and nothing automated fills that gap.** What fills it
is a reviewer reading the primary documents end to end and searching by meaning. `REVIEW.md`
records that as a *required manual step* rather than an aspiration, because the alternative is that
the next round reads a green suite as coverage. This register is where a paraphrase is recorded
**after** it is found; it is not the finding mechanism.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "evidence" / "withdrawn_assertions.json"

#: ``.tex`` was added on 2026-08-03, on a reviewer finding. The typeset paper is the most public
#: surface in this repository and the scan had never reached it --- while ``permitted_in`` listed
#: a ``.tex`` file, and the guard-the-guard test read that path directly and passed. **An
#: exemption from a scan that cannot reach the file is inert, and its presence is affirmative
#: evidence of coverage that does not exist.** Build products (``.aux``, ``.log``, ``.bbl``, the
#: PDF) stay out: they are generated from the ``.tex`` and would double-count it.
PROSE_SUFFIXES = frozenset({".md", ".json", ".txt", ".py", ".toml", ".tex"})


def _register() -> list[dict[str, object]]:
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    assertions = data["assertions"]
    assert isinstance(assertions, list)
    return assertions


def _flat(text: str) -> str:
    """Normalise prose for phrase matching: strip blockquote markers, then collapse whitespace.

    Two misses, both found by running this rather than reading it:

    - **Line wraps.** `tests/test_gate_state.py`'s first version matched raw text and missed the one
      file that provoked it, because the phrase was wrapped across two lines.
    - **Blockquote markers.** Collapsing whitespace alone is not enough. This repository records
      every correction as a dated `>` blockquote that *quotes the withdrawn wording*, so a phrase
      spanning two lines inside one acquires a `>` in the middle and stops matching — in exactly
      the documents most likely to contain a retired assertion legitimately.
    """

    lines = [line.lstrip().removeprefix(">").lstrip() for line in text.splitlines()]
    return " ".join(" ".join(lines).split())


#: Never scanned. Mirrors `tests/test_internal_paths.py`; `.venv*` is matched by prefix.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".hypothesis",
        ".claude",
        ".agents",
        ".superpowers",
        "__pycache__",
        "node_modules",
        "data",
        "dist",
        "build",
        "htmlcov",
    }
)


def _prose_files() -> list[str]:
    """Walk the filesystem, NOT the index.

    The first version used `git ls-files`, and that blind spot shipped a red suite reported as
    green. The offending file — a reviewer record quoting both retired phrasings — was **untracked**
    when the suite was run, so `git ls-files` did not list it; `git add -A` then tracked it in the
    same commit. **The check's scope excluded precisely the file the commit was adding**, which is
    the worst possible moment for it to be blind.

    `tests/test_internal_paths.py` already walked the filesystem, for the same reason discovered a
    day earlier. This test was written afterwards and did not inherit the lesson. Walking the tree
    scans a file whether or not git has heard of it yet.
    """

    files: list[str] = []
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in PROSE_SUFFIXES or not path.is_file():
            continue
        parts = path.relative_to(ROOT).parts[:-1]
        if any(part in SKIP_DIR_NAMES or part.startswith(".venv") for part in parts):
            continue
        files.append(path.relative_to(ROOT).as_posix())
    return files


def test_the_register_is_populated_and_the_scan_reaches_files() -> None:
    """Guard the guard: an empty register or an empty file list passes everything below.

    **This bounds cardinality only, and cardinality is not what failed.** Under the reverted
    `git ls-files` implementation this same assertion returns 202 and passes — B2 was a failure of
    scope *kind*, not of scan size. The test that catches it is the probe below.
    """

    assert _register(), "evidence/withdrawn_assertions.json lists no assertions"
    assert len(_prose_files()) > 50


def test_the_scan_reaches_untracked_files() -> None:
    """The probe that would have caught B2, and did not exist when B2 shipped.

    B2 was a red suite reported as green: the offending file was **untracked** when the suite ran,
    `git ls-files` could not see it, and `git add -A` tracked it in the same commit. Switching to a
    filesystem walk fixed the implementation — but the fix inherited the implementation **without
    the test that proves the implementation is the right kind**. `test_internal_paths.py` had
    carried exactly this probe since the day before.

    That is the same lesson recurring one level up: a scope decision that lives in an implementation
    rather than a shared rule gets rediscovered expensively — and here it recurred at the *test* of
    the scope decision, inside the commit that wrote the lesson down.
    """

    probe = ROOT / "docs" / "_untracked_prose_probe.md"
    probe.write_text("Probe file, deliberately untracked.\n", encoding="utf-8")
    try:
        assert "docs/_untracked_prose_probe.md" in _prose_files(), (
            "the scan did not see an untracked file; it must walk the filesystem, not the index"
        )
    finally:
        probe.unlink()


@pytest.mark.parametrize("entry", _register(), ids=lambda e: str(e["id"]))
def test_a_withdrawn_assertion_survives_only_where_named(entry: dict[str, object]) -> None:
    phrase = str(entry["phrase"])
    permitted = entry["permitted_in"]
    assert isinstance(permitted, dict)
    needle = _flat(phrase)

    offenders: list[str] = []
    for relative in _prose_files():
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

