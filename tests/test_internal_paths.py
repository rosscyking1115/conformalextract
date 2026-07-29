"""No operator filesystem path reaches a prose file, and every exception is named.

This is the mechanical half of the 2026-07-28 lesson. A release-hygiene pass found internal paths
in three tracked files, fixed two, and **introduced two more into its own report** -- which its own
check could not see, because that check was `git grep` and the report was still untracked. The
reviewer then asserted the strings appeared "ZERO times, tracked or untracked" on the strength of
three narrower commands, one of which it had not run.

Two design rules follow, and both are load-bearing:

1. **Walk the filesystem, not the index.** `git grep` and `git ls-files` cannot see an untracked
   file, and the defect lived in one. This scanner uses `Path.rglob`.
2. **Carry an exclusion list, never a count.** Some artifacts must quote these strings: a report
   about a path leak has to name the path, and a re-runnable grep pattern cannot be redacted. A
   bare count is therefore stale the moment anything legitimately quotes one. `ALLOWED` names each
   exception and why it earns its place, and `test_every_exception_still_earns_its_place` fails when
   an entry stops being needed -- so the list cannot quietly rot into a blanket.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Files whose contents a reader could receive. Binaries, lockfiles and caches are out of scope.
PROSE_SUFFIXES = frozenset({".md", ".json", ".toml", ".txt", ".cfg", ".yaml", ".yml", ".py"})

#: Never scanned: build output, caches, virtualenvs, agent state, and the gitignored data tree.
#: `.venv*` is matched by prefix so `.venv-cuda` and friends are covered without enumeration.
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

#: Patterns are written to match the *shape* of an operator path, never a specific username -- a
#: test that hardcoded the username would itself be the leak it exists to prevent. Each alternative
#: tolerates doubled backslashes so a JSON-escaped path inside an evidence artifact still matches.
INTERNAL_PATH_PATTERNS: dict[str, re.Pattern[str]] = {
    "windows-user-home": re.compile(r"C:\\+Users\\+[A-Za-z0-9._-]+", re.IGNORECASE),
    "operator-dev-root": re.compile(r"C:\\+dev\b", re.IGNORECASE),
    "private-planning-dir": re.compile(r"(?<![A-Za-z0-9])_pmo(?![A-Za-z0-9])"),
}

#: The exceptions, each with the reason it is permitted. Mention, not use -- the same category the
#: honesty doctrine already grants the forbidden-wording list. Adding an entry here is a claim that
#: the file cannot do its job without the string; the test below checks that claim stays true.
ALLOWED: dict[str, str] = {
    "docs/release-check-2026-07-28.md": (
        "The dated report of the leak itself. It quotes the paths in its findings table and in a "
        "grep pattern that must stay re-runnable; a redacted pattern is not a reproducible check."
    ),
    "evidence/plan3/reviewer_record.reanalysis.json": (
        "Immutable evidence artifact. The paths sit inside first-person prose recording what was "
        "hashed against what, so redacting them breaks the attestation rather than tidying a "
        "citation. Whether it ships publicly is an open release decision -- see "
        "docs/plan4/open-release-decisions.md."
    ),
    "evidence/plan4/reviewer_record.release-hygiene.json": (
        "The independent review that ruled on the leak. Quoting the strings is how it reports "
        "them, and it discloses this about itself."
    ),
    "evidence/plan3/reviewer_record.b1-primary-document.json": (
        "The review that found the release-hygiene record's carried-forward obligation was "
        "tracked nowhere. Reporting that the string is still in tracked files requires naming "
        "it — the same mention-not-use ground as the record it reports on."
    ),
    "tests/test_internal_paths.py": (
        "This file. It defines the patterns above, so it necessarily contains one of them."
    ),
}
# `REVIEW.md` was on this list on first writing, pre-emptively, and the stale-exception test below
# rejected it before the change was committed: the gate there is written descriptively and quotes
# no pattern, so the entry was a blanket over a file that did not need one. Recorded because it is
# the mechanism working — an exclusion list is only as honest as its willingness to shrink.


def _prose_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in PROSE_SUFFIXES or not path.is_file():
            continue
        parts = path.relative_to(ROOT).parts[:-1]
        if any(part in SKIP_DIR_NAMES or part.startswith(".venv") for part in parts):
            continue
        files.append(path)
    return files


def _scan() -> list[tuple[str, str, int]]:
    """Every (relative path, pattern name, line number) an internal path appears at."""

    hits: list[tuple[str, str, int]] = []
    for path in _prose_files():
        relative = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover - prose files are utf-8 by convention
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in INTERNAL_PATH_PATTERNS.items():
                if pattern.search(line):
                    hits.append((relative, name, number))
    return hits


def test_the_scan_finds_files_to_check() -> None:
    """Guard the guard: a walker that silently matched nothing would pass everything below."""

    files = _prose_files()
    assert len(files) > 50, f"prose scan found only {len(files)} files; the walker is broken"
    assert any(path.name == "README.md" for path in files)


def test_the_scan_reaches_untracked_files() -> None:
    """The defect this test exists for lived in an untracked file, invisible to `git grep`.

    Proven by probe rather than by reading: write an untracked file containing an operator path,
    confirm the scanner sees it, remove it. If this ever passes trivially the scanner has quietly
    become index-based and the whole test is theatre.
    """

    probe = ROOT / "docs" / "_untracked_scan_probe.md"
    probe.write_text("A path like C:\\Users\\someone\\proj is a leak.\n", encoding="utf-8")
    try:
        found = {relative for relative, _, _ in _scan()}
        assert "docs/_untracked_scan_probe.md" in found, (
            "the scanner did not see an untracked file; it must walk the filesystem, not the index"
        )
    finally:
        probe.unlink()


def test_no_internal_path_outside_the_named_exceptions() -> None:
    unexpected = [hit for hit in _scan() if hit[0] not in ALLOWED]
    if unexpected:
        detail = "\n".join(f"  {path}:{line} — {name}" for path, name, line in unexpected)
        raise AssertionError(
            f"{len(unexpected)} internal path reference(s) outside the named "
            f"exceptions:\n{detail}\n"
            f"Reword the path, or add the file to ALLOWED with the reason it cannot do its job "
            f"without the string."
        )


def test_every_exception_still_earns_its_place() -> None:
    """An exception that no longer matches is a blanket waiting to hide the next leak."""

    hit_paths = {relative for relative, _, _ in _scan()}
    stale = sorted(name for name in ALLOWED if name not in hit_paths)
    missing = sorted(name for name in ALLOWED if not (ROOT / name).exists())
    assert not missing, f"ALLOWED names files that do not exist: {missing}"
    assert not stale, (
        f"ALLOWED entries no longer contain any internal path: {stale}. Remove them — an exception "
        f"kept past its need silently widens the gate."
    )
