"""Thin command-line seams for the four sequential plans."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="Evidence-first selective extraction research CLI.")


def _not_ready(command: str) -> None:
    typer.echo(f"{command}: blocked until its preceding reviewed gate passes")
    raise typer.Exit(code=3)


@app.command("inventory-data")
def inventory_data() -> None:
    _not_ready("inventory-data")


@app.command("validate-data")
def validate_data() -> None:
    _not_ready("validate-data")


@app.command("run-baseline")
def run_baseline() -> None:
    _not_ready("run-baseline")


@app.command("validate-certificate")
def validate_certificate() -> None:
    _not_ready("validate-certificate")


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
