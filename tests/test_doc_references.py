"""Every test named in the docs must exist.

Three times during the ADR 0011 review a correction was reported complete with one instance
outstanding. A phrase-level grep caught the wording residue but structurally cannot catch this
class: an **identifier that must resolve**. A doc that cites `tests/x.py::test_y` as the thing
enforcing a property is making a checkable claim, and an ADR whose named test does not exist is
an ADR asserting a guarantee nobody is holding.

This is the cheap half of that lesson made mechanical. The expensive half -- whether the test
that exists actually enforces the property the doc claims -- still needs a reader.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

#: A doc-mentioned identifier may resolve to a test module (``tests/test_x.py``) or to a test
#: function defined in any of them.
IDENTIFIER = re.compile(r"test_[a-z0-9_]+")


#: Forward-looking documents are excluded, because the premise does not hold for them. An ADR or
#: a result document naming a test is asserting that a guarantee is currently held, which is
#: checkable. An accepted plan naming one is issuing an instruction about work not yet done -- the
#: Plan 1 plan sketches a `tests/` tree (`test_grounding.py`, `test_metrics.py`, `test_splits.py`)
#: from before any code existed, and the files were ultimately named differently. Requiring those
#: to resolve would force either dead files or edits to an accepted plan, and an accepted plan is
#: a historical record: it is amended by appended note, never rewritten to match what happened.
FORWARD_LOOKING = ("accepted-plan.md",)


def _documentation_files() -> list[Path]:
    files = sorted(ROOT.joinpath("docs").rglob("*.md"))
    files += [ROOT / "CLAUDE.md", ROOT / "REVIEW.md", ROOT / "README.md"]
    return [
        path
        for path in files
        if path.exists() and not path.name.endswith(FORWARD_LOOKING)
    ]


def _known_identifiers() -> set[str]:
    modules = {path.stem for path in TESTS.glob("test_*.py")}
    functions: set[str] = set()
    for path in TESTS.glob("test_*.py"):
        functions |= set(
            re.findall(r"^def (test_[A-Za-z0-9_]+)", path.read_text(encoding="utf-8"), re.M)
        )
    return modules | functions


def _referenced_identifiers() -> dict[str, set[str]]:
    referenced: dict[str, set[str]] = {}
    for path in _documentation_files():
        for name in IDENTIFIER.findall(path.read_text(encoding="utf-8")):
            referenced.setdefault(name, set()).add(str(path.relative_to(ROOT)))
    return referenced


def test_the_scan_finds_something_to_check() -> None:
    """Guard the guard: a regex that silently matches nothing would pass the test below."""

    referenced = _referenced_identifiers()
    assert len(referenced) > 20, "doc scan found suspiciously few test references"
    assert len(_known_identifiers()) > 50


def test_every_test_named_in_the_docs_exists() -> None:
    known = _known_identifiers()
    dangling = {
        name: sorted(sources)
        for name, sources in _referenced_identifiers().items()
        if name not in known
    }
    if dangling:
        detail = "\n".join(
            f"  {name} <- {', '.join(sources)}" for name, sources in dangling.items()
        )
        pytest.fail(f"documentation names {len(dangling)} test(s) that do not exist:\n{detail}")
