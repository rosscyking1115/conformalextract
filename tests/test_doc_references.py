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


#: The accepted plans, pinned. The exemption above is only safe while they are never edited, and
#: until this pin existed nothing enforced that -- the reviewer verified the copies by hand, and
#: that guarantee expired the moment they finished. Hashes are over git-canonical (LF) bytes, so a
#: Windows working copy checked out CRLF must be compared via `git show`, exactly as
#: `docs/plan3/certification-result.md` records for the certification artifact.
#:
#: An accepted plan is a historical record: it is amended by appended, dated note, never rewritten
#: to match what was built. If one of these legitimately gains an amendment, update the hash in
#: the same commit and say why in the message.
ACCEPTED_PLAN_SHA256 = {
    "docs/gate0/accepted-plan.md": (
        "afb55e4c89300cdb2559587e29b43601a13c30b1638049918691a6ed509ac6fe"
    ),
    "docs/plan2/accepted-plan.md": (
        "a6b4c69fad14cd56c866cbd204b9312aefb1a4fe578bb437af8cd5e3ac97fdbf"
    ),
    "docs/plan3/accepted-plan.md": (
        "83313d47ec2a9869dcc580bda8cc543a606b5a894be269c9fdd6a229308a07e9"
    ),
    "docs/plan4/accepted-plan.md": (
        "bdad3b4fcb2879d0c13499e4f6eded99e5f33269598e96776090c775bd35d2b1"
    ),
}


@pytest.mark.parametrize("relative_path", sorted(ACCEPTED_PLAN_SHA256))
def test_the_accepted_plans_are_unmodified(relative_path: str) -> None:
    """Every doc that cites a section number depends on these not drifting."""

    import hashlib
    import subprocess

    completed = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:  # pragma: no cover - only outside a git checkout
        pytest.skip(f"{relative_path} is not retrievable from git")
    digest = hashlib.sha256(completed.stdout).hexdigest()
    assert digest == ACCEPTED_PLAN_SHA256[relative_path], (
        f"{relative_path} has changed. An accepted plan is amended by appended note, never "
        f"rewritten; if the amendment is intended, update the pin in the same commit."
    )


def test_every_accepted_plan_on_disk_is_pinned() -> None:
    """A new plan must not slip in unpinned and inherit the doc-reference exemption."""

    on_disk = {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in ROOT.joinpath("docs").rglob("accepted-plan.md")
    }
    assert on_disk == set(ACCEPTED_PLAN_SHA256)


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
