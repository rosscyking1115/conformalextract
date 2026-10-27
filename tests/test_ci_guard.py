"""The CI restricted-data guard must cover every restricted data directory .gitignore names.

``.gitignore`` keeps ``data/raw/``, ``data/sealed/`` and ``data/private/`` out of a fresh clone,
but a forced add bypasses it; the CI guard is the backstop. It listed ``raw`` and ``private``
and not ``sealed``, the one directory whose contents the whole label-access discipline exists to
protect (independent review 2026-10-27, finding B4). Derived from .gitignore, not restated, so a
new restricted directory fails here until the guard covers it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _restricted_data_dirs() -> set[str]:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    return {m.group(1) for line in lines if (m := re.fullmatch(r"(data/[a-z_]+)/", line.strip()))}


def test_gitignore_names_the_restricted_directories() -> None:
    assert {"data/raw", "data/sealed", "data/private"} <= _restricted_data_dirs()


def test_the_ci_guard_covers_every_restricted_data_directory() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    guard = next(line for line in workflow.splitlines() if "git ls-files" in line)
    missing = {d for d in _restricted_data_dirs() if f"'{d}/**'" not in guard}
    assert not missing, f"CI guard does not refuse tracked files under: {sorted(missing)}"
