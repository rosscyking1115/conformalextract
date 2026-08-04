"""Every committed evidence artifact must be registered by a test, and the list is DERIVED.

Ruling R3 required the re-analysis artifacts to be re-checked by something, because they had been
verified by hand at authoring time and nothing held them there afterwards. That was applied to the
artifacts a reviewer happened to name, using a hand-written load list in
``tests/test_reanalysis_artifacts.py``.

**A hand-written list omits silently.** Five artifacts were added after that fix --
``derived_quantities.json``, ``derived_ratios.json``, ``argument_error_counts.json``,
``programme_facts.json`` and ``external_citations.json`` -- and appeared in **zero** of 45 test
files. One of them backs seven figures in the paper and carries a ``certification_access`` block
asserting ``final_reads: 0`` that nothing checked. The countermeasure had been copied without its
verification, which is the failure mode ``REVIEW.md`` names.

So this file does not list artifacts. **It enumerates the directory and requires each entry to be
registered**, which is the difference between a register and an inventory: adding an artifact
without a test now fails here rather than passing unnoticed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
EVIDENCE_DIRS = (ROOT / "evidence" / "plan3", ROOT / "evidence" / "plan4")

#: Reviewer records are verdicts, not computed artifacts: they are read by governance, never
#: recomputed, and must not be mutated. They are excluded by KIND, from their filename prefix,
#: rather than by being listed one by one -- a list is what this file exists to replace.
RECORD_PREFIX = "reviewer_record"


def _artifacts() -> list[Path]:
    found: list[Path] = []
    for directory in EVIDENCE_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            if path.name.startswith(RECORD_PREFIX):
                continue
            found.append(path)
    return found


def _test_corpus() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in sorted(TESTS.rglob("*.py"))
    )


def test_the_enumeration_reaches_artifacts_and_tests() -> None:
    """Guard the guard: an empty walk on either side would pass everything below."""

    assert len(_artifacts()) > 5, "the artifact walk found almost nothing; check EVIDENCE_DIRS"
    assert len(list(TESTS.rglob("*.py"))) > 10, "the test walk found almost nothing"


@pytest.mark.parametrize("artifact", _artifacts(), ids=lambda p: p.name)
def test_every_committed_artifact_is_named_by_some_test(artifact: Path) -> None:
    """Adding an evidence artifact without a test must fail here, not pass silently."""

    assert artifact.name in _test_corpus(), (
        f"{artifact.relative_to(ROOT).as_posix()} is committed evidence that no test names. "
        "Register it -- assert what it must agree with -- rather than trusting it was checked "
        "when it was written. A hand-written load list is what let five artifacts through."
    )


@pytest.mark.parametrize("artifact", _artifacts(), ids=lambda p: p.name)
def test_an_access_block_that_exists_is_verified_and_discloses_no_sealed_reads(
    artifact: Path,
) -> None:
    """If an artifact claims to have opened gold, the claim must carry its own verification.

    ``derived_quantities.json`` and ``argument_error_counts.json`` both carry this block and it was
    asserted by nothing: the parametrised chain test covered a list that excluded them.
    """

    data = json.loads(artifact.read_text(encoding="utf-8"))
    access = data.get("certification_access")
    if not isinstance(access, dict) or not access.get("certification_gold_read"):
        pytest.skip("this artifact does not open certification gold")

    assert access["verified"] is True, artifact.name
    assert access["final_reads"] == 0, artifact.name
    assert access["shift_reads"] == 0, artifact.name
    assert isinstance(access.get("head_hash"), str) and len(access["head_hash"]) == 64, (
        f"{artifact.name}: an access block without a chain head gives a verifier nothing to check"
    )


def test_every_gold_opening_artifact_shares_one_access_chain() -> None:
    """One split opened once means one chain head. Divergence means a second opening."""

    heads = {}
    for artifact in _artifacts():
        data = json.loads(artifact.read_text(encoding="utf-8"))
        access = data.get("certification_access")
        if isinstance(access, dict) and access.get("certification_gold_read"):
            heads[artifact.name] = access.get("head_hash")
    assert heads, "no artifact discloses a certification read; the check would be vacuous"
    assert len(set(heads.values())) == 1, (
        f"artifacts disclose different access chain heads: {heads}"
    )
