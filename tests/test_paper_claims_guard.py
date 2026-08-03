"""The paper-claims guard must fail on every mutation it exists to catch.

A guard that has never failed is not known to work, and this repository has shipped two that
could not have caught the class they were named for. `verify_ledger` checks that evidence paths
exist and are tracked; the appendix guard checks that a generated file agrees with the ledger it
was generated from. Neither opens an artifact and compares a number, so neither could ever have
failed on a wrong figure.

So these are mutation tests, not example tests. Each one breaks the document, the artifact, or the
configuration in a way that has actually happened in this project, and asserts the guard reports
it with the right kind. The most important is `test_a_configuration_change_alone_fails`: the value
is left untouched and only the allocation moves, which is the defect class every value-only check
passes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_paper_claims import (  # noqa: E402
    CONFIG_ABSENT,
    CONFIG_MISMATCH,
    UNBACKED,
    VALUE_MISMATCH,
    check,
    load_manifest,
    render,
    resolve,
)
from paper_figures import extract_figures  # noqa: E402

MANIFEST = ROOT / "evidence" / "plan4" / "paper_claims.json"
CALIBRATION = "evidence/plan3/calibration_diagnostics.json"
CERTIFIED = "splits.certification.qa.mean.selective_risk.acceptance_certified_loss_optimal"
DELTA = "splits.certification.qa.mean.selective_risk.certified_delta"


@pytest.fixture(scope="module")
def figures():
    return extract_figures()


@pytest.fixture(scope="module")
def manifest():
    return load_manifest(MANIFEST)


def _kinds(failures, figure: str) -> set[str]:
    """Match on the NORMALISED value, which is what the manifest keys on."""

    return {f.kind for f in failures if f.value == figure or f.figure == figure}


def test_the_guard_refuses_a_vacuous_run(figures) -> None:
    """A checker with nothing to check passes everything. Both inputs must be non-empty."""

    assert figures, "no figures extracted; the guard would pass vacuously"
    assert load_manifest(MANIFEST), "manifest is empty; the guard would pass vacuously"


def test_every_manifest_entry_resolves_and_renders(manifest) -> None:
    """A pointer that no longer resolves must not degrade into a silent pass.

    An entry may legitimately disagree with the paper: where a figure was computed into an
    artifact and the written number turned out not to match, the entry is retained pointing at
    the defensible configuration so the guard reports it. Those carry ``disagrees_with_paper``
    with the value the artifact actually renders, so a KNOWN disagreement is declared in the
    manifest rather than looking like a broken pointer -- and an UNDECLARED one still fails here.
    """

    loaded: dict[str, object] = {}
    for figure, entry in manifest.items():
        relative = entry["artifact"]
        if relative not in loaded:
            loaded[relative] = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        value = resolve(loaded[relative], entry["pointer"])
        rendered = render(value, entry["render"])
        declared = entry.get("disagrees_with_paper")
        if declared is not None:
            assert rendered == declared, (
                f"{figure}: the declared disagreement is stale -- the artifact now renders "
                f"{rendered!r}, not the recorded {declared!r}"
            )
            continue
        assert rendered == figure, (
            f"{figure}: {relative}::{entry['pointer']} renders {rendered!r}. If the paper is "
            "wrong, declare it with disagrees_with_paper; do not repoint the entry."
        )


def test_declared_disagreements_are_reported_not_swallowed(figures, manifest) -> None:
    """A declared disagreement must still FAIL the guard. Declaring is disclosure, not a waiver."""

    declared = {f for f, e in manifest.items() if e.get("disagrees_with_paper") is not None}
    assert declared, "no disagreements declared; this test would pass vacuously"
    failures, _ = check(figures, dict(manifest))
    for figure in declared:
        assert VALUE_MISMATCH in _kinds(failures, figure), (
            f"{figure} is declared as disagreeing and the guard passed it"
        )


def test_a_figure_with_no_backing_fails(figures, manifest) -> None:
    """The paper is the population. A figure absent from the manifest is not exempt."""

    failures, _ = check(figures, dict(manifest))
    assert any(f.kind == UNBACKED for f in failures), (
        "no figure reported unbacked; the guard is not scoping by the paper"
    )


def test_a_changed_artifact_value_fails(figures, manifest) -> None:
    mutated = json.loads(json.dumps(dict(manifest)))
    probe = ROOT / "evidence" / "plan3" / "_test_probe.json"
    data = json.loads((ROOT / CALIBRATION).read_text(encoding="utf-8"))
    resolve(data, CERTIFIED.rsplit(".", 1)[0])["acceptance_certified_loss_optimal"] = 0.2201
    probe.write_text(json.dumps(data), encoding="utf-8")
    try:
        for entry in mutated.values():
            if entry["artifact"] == CALIBRATION:
                entry["artifact"] = "evidence/plan3/_test_probe.json"
        failures, _ = check(figures, mutated)
        assert VALUE_MISMATCH in _kinds(failures, "0.1139")
    finally:
        probe.unlink(missing_ok=True)


def test_a_configuration_change_alone_fails(figures, manifest) -> None:
    """THE load-bearing case: the value is untouched and only the allocation moves.

    0.1139 is the certified oracle at the per-system delta/3. At the full delta it is a different
    quantity that happens to be reported by the same code path. A value-only check cannot tell
    them apart, and telling them apart is the entire point.
    """

    mutated = json.loads(json.dumps(dict(manifest)))
    probe = ROOT / "evidence" / "plan3" / "_test_probe.json"
    data = json.loads((ROOT / CALIBRATION).read_text(encoding="utf-8"))
    resolve(data, DELTA.rsplit(".", 1)[0])["certified_delta"] = 0.05
    probe.write_text(json.dumps(data), encoding="utf-8")
    try:
        for entry in mutated.values():
            if entry["artifact"] == CALIBRATION:
                entry["artifact"] = "evidence/plan3/_test_probe.json"
        failures, _ = check(figures, mutated)
        assert CONFIG_MISMATCH in _kinds(failures, "0.1139"), (
            "the allocation changed and the guard passed it; it is a value-only check"
        )
        assert VALUE_MISMATCH not in _kinds(failures, "0.1139"), (
            "the value was not mutated, so this must be a configuration failure specifically"
        )
    finally:
        probe.unlink(missing_ok=True)


def test_a_configuration_the_artifact_does_not_record_fails(figures, manifest) -> None:
    """An entry may not declare a configuration its artifact cannot evidence."""

    mutated = json.loads(json.dumps(dict(manifest)))
    probe = ROOT / "evidence" / "plan3" / "_test_probe.json"
    data = json.loads((ROOT / CALIBRATION).read_text(encoding="utf-8"))
    del resolve(data, DELTA.rsplit(".", 1)[0])["certified_delta"]
    probe.write_text(json.dumps(data), encoding="utf-8")
    try:
        for entry in mutated.values():
            if entry["artifact"] == CALIBRATION:
                entry["artifact"] = "evidence/plan3/_test_probe.json"
        failures, _ = check(figures, mutated)
        assert CONFIG_ABSENT in _kinds(failures, "0.1139")
    finally:
        probe.unlink(missing_ok=True)


def test_a_changed_paper_value_fails(tmp_path, manifest) -> None:
    paper = ROOT / "docs" / "writeup" / "uncertainlp-2026-short.tex"
    text = paper.read_text(encoding="utf-8")
    assert "0.6071" in text
    mutant = tmp_path / "mutated.tex"
    mutant.write_text(text.replace("0.6071", "0.6072"), encoding="utf-8")
    failures, _ = check(extract_figures(mutant), dict(manifest))
    assert UNBACKED in _kinds(failures, "0.6072"), "a value invented in the paper was not caught"


def test_the_dotted_key_pointer_form_addresses_the_right_leaf() -> None:
    """The grounded-fraction strata are keyed '1.00'. Splitting on the dot addresses nothing."""

    data = {"a": {"1.00": {"mean_loss": 0.5}}}
    assert resolve(data, "a['1.00'].mean_loss") == 0.5
    with pytest.raises(KeyError):
        resolve(data, "a.1.00.mean_loss")
