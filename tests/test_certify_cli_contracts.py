from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
CLI = (ROOT / "src" / "conformalextract" / "cli.py").read_text(encoding="utf-8")
ADR_0009 = ROOT / "docs" / "adr" / "0009-within-group-aggregation.md"


def _certify_block() -> str:
    return CLI.split('@app.command("certify")', maxsplit=1)[1].split('@app.command("hash-file")')[0]


def test_certify_refuses_until_the_aggregation_adr_is_accepted() -> None:
    """The sealed split must not open while the rule that shapes the certificate is unreviewed."""
    block = _certify_block()
    # Accepted status is read from the ADR's own Status line (emphasis-tolerant) AND must be
    # backed by the reviewer record; the operator flag is required on top of both.
    assert 'line.startswith("- Status:")' in block
    assert '"reviewer_record.adr-0009.json" in adr_text' in block
    assert "i_have_reviewer_approval" in block
    assert "if not (adr_accepted and i_have_reviewer_approval):" in block
    assert '"sealed_labels_opened": False' in block
    assert "raise typer.Exit(code=3)" in block


def test_adr_0009_is_accepted_only_alongside_its_reviewer_record() -> None:
    """The ADR may only be `accepted` if the reviewer record backing it exists.

    Replaces the earlier assertion that it stays `proposed`: the flip is now deliberate and
    reviewed, but it must never be flippable without the evidence file that authorises it.
    """
    text = ADR_0009.read_text(encoding="utf-8")
    record = ROOT / "evidence" / "plan3" / "reviewer_record.adr-0009.json"
    if "- Status: **accepted" in text:
        assert record.exists(), "ADR 0009 cannot be accepted without its reviewer record"
        assert "reviewer_record.adr-0009.json" in text
    else:
        assert "- Status: **proposed" in text


def test_certify_reads_only_the_certification_role() -> None:
    block = _certify_block()
    assert 'record["role"] == "certification"' in block
    assert "build_certification_access_log" in block
    for forbidden in ('"final"', '"shift"'):
        assert f'record["role"] == {forbidden}' not in block


def test_certify_refuses_grids_not_built_at_the_split_delta() -> None:
    """Grids built at full delta would silently break the cross-system union bound."""
    block = _certify_block()
    assert "the three-way split must exhaust" in block
    assert "Rebuild grids at delta/3 before certifying" in block


def test_certification_result_is_immutable() -> None:
    block = _certify_block()
    assert "already exists and is immutable" in block


def test_certify_binds_allocation_and_construction_into_provenance() -> None:
    block = _certify_block()
    assert '"delta_allocation": allocation' in block
    assert '"primary_construction": "scorc_union_bound"' in block
    assert '"grid_hashes"' in block


def test_remaining_sealed_commands_are_still_blocked() -> None:
    """evaluate-final and evaluate-shift must stay stubs until their gates pass."""
    stub_block = CLI.split("for command_name in (", maxsplit=1)[1].split(")", maxsplit=1)[0]
    for command in ('"evaluate-final"', '"evaluate-shift"', '"render-report"'):
        assert command in stub_block
    assert '"certify"' not in stub_block
