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
    CITATION_UNSOURCED,
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
    """A declared disagreement must still FAIL the guard. Declaring is disclosure, not a waiver.

    Written against a SYNTHESISED declaration rather than a live one. The first version asserted
    that the manifest contained at least one real disagreement, which was true when three were
    open and became a false failure the moment they were fixed -- a test that requires a defect to
    exist in order to pass is a test that punishes repair. The property under test is that the
    ``disagrees_with_paper`` field cannot mute the guard, and that holds whether or not any
    disagreement is currently open.
    """

    live = {f for f, e in manifest.items() if e.get("disagrees_with_paper") is not None}
    mutated = json.loads(json.dumps(dict(manifest)))
    target = "0.1139"
    assert target in mutated, "expected a known-good entry to synthesise a declaration on"
    mutated[target]["disagrees_with_paper"] = "0.9999"
    mutated[target]["pointer"] = "splits.certification.zs.mean.selective_risk.normalized_aurc"

    failures, _ = check(figures, mutated)
    assert VALUE_MISMATCH in _kinds(failures, target), (
        "an entry declaring a disagreement was passed by the guard; declaring must disclose, "
        "not waive"
    )

    for figure in live:
        real, _ = check(figures, dict(manifest))
        assert VALUE_MISMATCH in _kinds(real, figure), (
            f"{figure} is declared as disagreeing and the guard passed it"
        )


def test_a_figure_with_no_backing_fails(figures, manifest) -> None:
    """The paper is the population. A figure absent from the manifest is not exempt.

    Written against a REMOVED entry rather than a live gap. This is the second test in this file
    that originally asserted a defect existed and turned red the moment the defect was repaired;
    a test that punishes repair is the wrong test, and the property here is that absence fails,
    not that something is currently absent.
    """

    stripped = json.loads(json.dumps(dict(manifest)))
    victim = "0.1139"
    assert victim in stripped, "expected a known-backed figure to remove"
    del stripped[victim]

    failures, _ = check(figures, stripped)
    assert UNBACKED in _kinds(failures, victim), (
        "a figure with no manifest entry was passed; the guard is not scoping by the paper"
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


def test_a_citation_entry_without_provenance_fails(figures, manifest) -> None:
    """A quoted number may not enter the paper without source, identifier and access date.

    The failure this guards against happened: a band from another group's paper was relayed with
    one cell omitted, and the omission changed what the band supported. Resolving to a value is
    not enough for a figure that is someone else's measurement.
    """

    citations = [f for f, e in manifest.items() if e.get("kind") == "citation"]
    assert citations, "no citation entries; this test would pass vacuously"

    stripped = json.loads(json.dumps(dict(manifest)))
    target = citations[0]
    stripped[target]["configuration"] = {
        pointer: value
        for pointer, value in stripped[target]["configuration"].items()
        if not pointer.endswith("accessed")
    }
    failures, _ = check(figures, stripped)
    assert CITATION_UNSOURCED in _kinds(failures, target), (
        "a citation entry lost its access date and the guard passed it"
    )


def test_the_scientific_render_ops_match_the_written_form() -> None:
    """Order-of-magnitude p-values are RENDERED, never stored a second time pre-formatted."""

    assert render(1.2235463357706085e-55, "oom") == "10^{-55}"
    assert render(8.195950323748051e-15, "sci0") == "8\\times10^{-15}"


def _values(tex: str, tmp_path: Path) -> set[str]:
    path = tmp_path / "probe.tex"
    path.write_text("\\begin{document}\n" + tex + "\n\\end{document}\n", encoding="utf-8")
    return {f.value for f in extract_figures(path)}


def test_structural_exclusion_removes_only_typesetting(tmp_path) -> None:
    """The rules must key on CONTEXT, never on the value.

    An exemption says "this is a claim, do not check it" and is refused. Better extraction says
    "this was never a claim". These are the cases where the second is true.
    """

    assert "5" not in _values("See Table 5 of the paper.", tmp_path)
    assert "2507" not in _values("a Qwen3-4B-Instruct-2507 model", tmp_path)
    assert "2" not in _values("(1) first & (2) second \\\\", tmp_path)
    assert "6" not in _values("strata from 1 to 6+ inclusive", tmp_path)
    assert "3" not in _values("at the per-system $\\delta/3$ allocation", tmp_path)
    assert "2" not in _values("the mechanism-2 quantities are post-hoc", tmp_path)


def test_structural_exclusion_keeps_genuine_claims(tmp_path) -> None:
    """The test the rules have to survive: a real claim that LOOKS like typesetting.

    ``top-75\\%`` is a hyphenated alphanumeric run exactly like ``4-bit``, and it is a real
    threshold. The identifier rule therefore requires TWO letter-bearing segments, so a
    ``word-number`` compound survives. If this ever fails, the rule has become an exemption.
    """

    assert "75" in _values("measured at top-75\\% acceptance", tmp_path)
    assert "0.20" in _values("Risk $\\alpha = 0.20$ was frozen.", tmp_path)
    assert "1396" in _values("over $n = 1{,}396$ groups", tmp_path)
    assert "28" in _values("the oracle accepted (28 groups) in total", tmp_path)
    assert "0.406" in _values("the frontier point 0.406", tmp_path)


def test_a_claim_is_not_hidden_behind_a_label_that_renders_the_same(tmp_path) -> None:
    """Exclusion is per OCCURRENCE, so a real claim survives a same-token label elsewhere.

    This was a stated limitation of the first version and it was not hypothetical: ``3`` is a
    table row label, an allocation divisor in $\\delta/3$, AND the number of non-failing groups
    the ZS AUROC rests on. Dropping the figure because its first occurrence was typesetting would
    have hidden the claim.
    """

    tex = "(3) oracle & at $\\delta/3$ \\\\ AUROC rests on only 3 non-failing groups"
    assert "3" in _values(tex, tmp_path), "a real claim was hidden behind a row label"


def test_every_figure_in_the_paper_is_backed() -> None:
    """The gate itself. A permanently red gate stops being read, so this keeps it honest.

    If this fails, either a figure was written into the paper without an artifact behind it, or
    an artifact moved. Both are the thing the guard exists to catch. Back the figure or withdraw
    it -- do NOT add an exemption, and do not repoint an entry to make it pass.
    """

    figures = extract_figures()
    failures, passed = check(figures, load_manifest(MANIFEST))
    assert not failures, "\n".join(f.line() for f in failures)
    assert len(passed) == len(figures)


def test_the_dotted_key_pointer_form_addresses_the_right_leaf() -> None:
    """The grounded-fraction strata are keyed '1.00'. Splitting on the dot addresses nothing."""

    data = {"a": {"1.00": {"mean_loss": 0.5}}}
    assert resolve(data, "a['1.00'].mean_loss") == 0.5
    with pytest.raises(KeyError):
        resolve(data, "a.1.00.mean_loss")
