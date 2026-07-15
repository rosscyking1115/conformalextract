"""Thin command-line seams for the four sequential plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True, help="Evidence-first selective extraction research CLI.")


def _not_ready(command: str) -> None:
    typer.echo(f"{command}: blocked until its preceding reviewed gate passes")
    raise typer.Exit(code=3)


@app.command("inventory-data")
def inventory_data(
    rams_root: Annotated[Path, typer.Option(help="Private extracted RAMS root.")] = Path(
        "data/raw/rams/RAMS_1.0c"
    ),
    wikievents_root: Annotated[Path, typer.Option(help="Private WikiEvents root.")] = Path(
        "data/raw/wikievents"
    ),
    output: Annotated[Path, typer.Option(help="New aggregate evidence artifact.")] = Path(
        "evidence/gate0/data_inventory.json"
    ),
) -> None:
    """Inventory official sources without writing source text or raw identifiers."""

    from conformalextract.artifacts import freeze_json
    from conformalextract.certification import largest_scorc_grid, scorc_minimum_n
    from conformalextract.data import (
        build_duplicate_groups,
        inventory_summary,
        load_rams,
        load_wikievents,
    )

    documents = [*load_rams(rams_root), *load_wikievents(wikievents_root)]
    groups = build_duplicate_groups(documents, threshold=0.9, permutations=128)
    summary = inventory_summary(documents, groups)
    rams_documents = [document for document in documents if document.dataset == "RAMS"]
    rams_group_count = len({groups[document.document_id] for document in rams_documents})
    provisional_certification_n = rams_group_count // 10
    summary["preferred_method_feasibility"] = {
        "rams_independent_groups": rams_group_count,
        "provisional_certification_documents": provisional_certification_n,
        "minimum_n_one_candidate": scorc_minimum_n(
            candidate_count=1, delta=0.05, acceptance_floor=0.2
        ),
        "largest_grid_at_provisional_n": largest_scorc_grid(
            independent_documents=provisional_certification_n,
            delta=0.05,
            acceptance_floor=0.2,
        ),
        "candidate_cap": 101,
    }
    digest = freeze_json(output, summary)
    typer.echo(json.dumps({"output": str(output), "sha256": digest}, sort_keys=True))


@app.command("validate-data")
def validate_data(
    inventory: Annotated[Path, typer.Option()] = Path("evidence/gate0/data_inventory.json"),
) -> None:
    """Check that aggregate inventory and sample-feasibility evidence are complete."""

    record = json.loads(inventory.read_text(encoding="utf-8"))
    required = {
        "document_count",
        "independent_group_count",
        "by_dataset",
        "preferred_method_feasibility",
    }
    missing = sorted(required - record.keys())
    if missing:
        typer.echo(json.dumps({"status": "invalid", "missing": missing}))
        raise typer.Exit(code=2)
    feasibility = record["preferred_method_feasibility"]
    status = "pass" if feasibility["largest_grid_at_provisional_n"] >= 1 else "revise"
    typer.echo(json.dumps({"status": status, "preferred_method": feasibility}, sort_keys=True))
    if status != "pass":
        raise typer.Exit(code=3)


@app.command("run-baseline")
def run_baseline() -> None:
    _not_ready("run-baseline")


@app.command("validate-certificate")
def validate_certificate(
    replicates: Annotated[int, typer.Option(min=1)] = 2000,
    seed: Annotated[int, typer.Option()] = 42,
    output: Annotated[Path, typer.Option()] = Path("evidence/gate0/certificate_simulations.json"),
) -> None:
    """Run deterministic grouped coverage simulations and freeze the report."""

    from conformalextract.artifacts import freeze_json
    from conformalextract.simulation import run_gate0_simulations

    report = run_gate0_simulations(replicates=replicates, seed=seed)
    digest = freeze_json(output, report)
    typer.echo(json.dumps({"output": str(output), "sha256": digest}, sort_keys=True))
    if not report["coverage_pass"]:
        raise typer.Exit(code=3)


@app.command("gate0-smoke")
def gate0_smoke() -> None:
    _not_ready("gate0-smoke")


for command_name in (
    "prepare-data",
    "train",
    "generate-predictions",
    "freeze-systems",
    "build-grid",
    "certify",
    "evaluate-final",
    "evaluate-shift",
    "render-report",
    "verify-release",
):
    app.command(command_name)(lambda name=command_name: _not_ready(name))


@app.command("hash-file")
def hash_file(path: Path) -> None:
    """Print a local artifact SHA-256 without reading it into a report."""

    from conformalextract.artifacts import sha256_file

    typer.echo(sha256_file(path))
