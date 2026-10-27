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

from conformalextract.claims import CLAIM_ID, load_ledger

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
    # Amended 2026-10-27 with a dated note under the strict-document-failure sentence recording that
    # its definition was never frozen before calibration (Plan 3 disposition Amendment 2). The
    # sentence is preserved above the note. Pin moved in the same commit; previous digest afb55e4c…
    "docs/gate0/accepted-plan.md": (
        "7bf43a6d6c4eb19a570319aeace2c3d268084a63f42a0e7d64e076bcadc64883"
    ),
    "docs/plan2/accepted-plan.md": (
        "a6b4c69fad14cd56c866cbd204b9312aefb1a4fe578bb437af8cd5e3ac97fdbf"
    ),
    # Amended 2026-08-02 with a dated scope-amendment note under §12.1, pointing at the
    # independently reviewed 2026-07-30 certification-only addendum. The original sentence and its
    # eleven-category list are preserved above the note. Pin moved in the same commit, as the rule
    # above requires; previous digest 83313d47…
    # Amended again 2026-10-27 with dated notes under §12.1 (descoped), §12.2 (disposed) and the §22
    # checklist (taxonomy/audit half waived), all pointing at disposition Amendment 2. The text
    # above each note is unchanged. Pin moved in the same commit; previous digest 34bc6b4d…
    "docs/plan3/accepted-plan.md": (
        "560eee3d08d18d212ae2286f07b1c1528c66b27f83c5468aa40d804fb912fa0b"
    ),
    # Amended 2026-07-29 with a dated note reconciling its inherited-status line against the
    # records (Plan 1 complete, Plan 2 closed, Plan 3 executed but not formally closed). The
    # original paragraph is preserved above the note. Pin moved in the same commit, as the rule
    # above requires; previous digest bdad3b4f…
    "docs/plan4/accepted-plan.md": (
        "c8c2414066c309f60ab16036510c07d36bde93a3938a11ee1b444fc52596bf94"
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


#: Documents admitted byte-for-byte from an out-of-repo reviewed artifact, where hash equality with
#: that artifact IS the document's authority. Deliberately a SEPARATE dict from the accepted-plan
#: pins above: those are set-checked against `docs/**/accepted-plan.md` by the test above, so an
#: entry of this kind added there would fail it.
#:
#: Why a stored constant is the right instrument here, when the standing rule in REVIEW.md prefers a
#: cross-check against a second source of truth: that rule targets a bound with SLACK in it, and it
#: warns against a constant that must be hand-edited whenever the guarded thing legitimately
#: changes. Neither applies. SHA-256 has no slack, and these files can never legitimately change --
#: an amendment would be a NEW dated document, not an edit to this one. Nothing inside this
#: repository can tie these bytes to the review that approved them, because that review lives
#: outside it; the transcribed digest is the only available link, which is exactly the case a pin is
#: for. `tests/test_internal_paths.py` grants this file an exemption whose stated reason is its
#: byte-fidelity, so without this pin that reason would be asserted and unenforced.
FROZEN_DOCUMENT_SHA256 = {
    # The Plan 3 §12.1 certification-only scope addendum, independently PASSed 2026-07-30 and
    # admitted unchanged. Its authority record is
    # evidence/plan3/reviewer_record.s12-1-certification-scope-addendum.json.
    "docs/plan3/section-12-1-certification-only-scope-addendum-2026-07-30.md": (
        "5be8b8cf164a5ad58a54335ce3b829e6b250433b2c47e871763c177a8730fcf7"
    ),
}


@pytest.mark.parametrize("relative_path", sorted(FROZEN_DOCUMENT_SHA256))
def test_the_frozen_documents_are_byte_identical(relative_path: str) -> None:
    """A frozen document whose bytes drift has lost the only authority it had."""

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
    assert digest == FROZEN_DOCUMENT_SHA256[relative_path], (
        f"{relative_path} no longer matches the reviewed artifact it was admitted as. It is "
        f"byte-frozen: correct it back, or admit a new dated document and pin that instead."
    )


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


#: The same lesson, one identifier class over. A claim ID printed on a public surface asserts that
#: the ledger licenses that claim *for that surface*; if it does not, the surface is publishing on
#: an authority it does not hold. `claims.render_surface` exists so public prose can be assembled
#: from approved wordings instead of re-written, and the README does not use it -- it is hand-
#: written for readability. That trade is only safe while something pins the two together, and the
#: ledger was amended three times in a single day on 2026-07-22.
#:
#: Meet the argument for the machinery before accepting the trade: the independent review of that
#: hand-written README found three ledger `limitations` dropped from it, and all three were lines
#: `render_surface` would have emitted mechanically -- including the one an earlier reviewer had
#: said must travel with its claim. The case for generating the prose is made by the cost of not
#: generating it. This test buys back only the citation half; a reader still buys the rest.
#:
#: This is the minimum enforceable half: every claim ID the README cites must resolve to a ledger
#: entry that surfaces to README. The converse (every README-surfaced claim actually appears) is
#: deliberately NOT asserted -- adding a surface to the ledger should not fail an unrelated commit.
#:
#: The pattern is `claims.CLAIM_ID` unanchored, NOT a re-spelling of it. The first draft of this
#: test invented `CX-...-\d+`, which silently skipped `CX-H1-PRIMARY` and `CX-H2-SECONDARY` -- the
#: two IDs that do not end in digits, and precisely the pair the review found mis-cited. A probe
#: caught it; reading the pattern did not. Derive from the source of truth, never restate it.
CLAIM_ID_IN_PROSE = re.compile(CLAIM_ID.pattern.strip("^$"))

PUBLIC_PROSE_SURFACES = {"README.md": "README"}


@pytest.mark.parametrize("filename", sorted(PUBLIC_PROSE_SURFACES))
def test_every_claim_id_cited_in_public_prose_is_surfaced_there(filename: str) -> None:
    """A claim ID on a surface the ledger does not grant is prose outrunning its authority."""

    ledger = load_ledger(ROOT / "evidence" / "plan4" / "claim_ledger.json")
    surface = PUBLIC_PROSE_SURFACES[filename]
    by_id = {claim.claim_id: claim for claim in ledger.claims}

    # `finditer` + group(0), not `findall`: the source pattern contains a capture group, so
    # `findall` would return the group's contents ("-PRIMARY") rather than the whole ID.
    text = (ROOT / filename).read_text(encoding="utf-8")
    cited = {match.group(0) for match in CLAIM_ID_IN_PROSE.finditer(text)}
    assert cited, f"{filename} cites no claim IDs; the regex or the document has changed"

    unknown = sorted(name for name in cited if name not in by_id)
    unsurfaced = sorted(
        name for name in cited if name in by_id and surface not in by_id[name].surfaces
    )
    assert not unknown, f"{filename} cites claim IDs absent from the ledger: {unknown}"
    assert not unsurfaced, (
        f"{filename} cites claims the ledger does not surface to {surface!r}: {unsurfaced}. "
        f"Either remove them from the document or add the surface in the ledger -- and a ledger "
        f"change is a claims change, which needs its own independent review."
    )
