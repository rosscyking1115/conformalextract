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
    rams_root: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c"),
    wikievents_root: Annotated[Path, typer.Option()] = Path("data/raw/wikievents"),
    private_manifest: Annotated[Path, typer.Option()] = Path(
        "data/private/splits/rams_roles.jsonl"
    ),
    output: Annotated[Path, typer.Option()] = Path("evidence/gate0/split_validation.json"),
) -> None:
    """Freeze deterministic grouped RAMS roles and validate shift overlap."""

    from collections import Counter

    from conformalextract.artifacts import freeze_json, freeze_jsonl, sha256_file
    from conformalextract.certification import scorc_minimum_n
    from conformalextract.data import (
        build_duplicate_groups,
        grouped_split,
        load_rams,
        load_wikievents,
    )

    rams = load_rams(rams_root)
    wikievents = load_wikievents(wikievents_root)
    documents = [*rams, *wikievents]
    groups = build_duplicate_groups(documents, threshold=0.9, permutations=128)
    roles = grouped_split(
        {document.document_id: groups[document.document_id] for document in rams},
        seed=42,
        proportions={"train": 0.45, "development": 0.10, "certification": 0.35, "final": 0.10},
    )
    records = [
        {
            "schema_version": "1",
            "document_id": document.document_id,
            "group_id": groups[document.document_id],
            "role": roles[document.document_id],
        }
        for document in sorted(rams, key=lambda item: item.document_id)
    ]
    manifest_hash = freeze_jsonl(private_manifest, records)
    role_groups: dict[str, set[str]] = {
        role: {str(record["group_id"]) for record in records if record["role"] == role}
        for role in ("train", "development", "certification", "final")
    }
    all_role_groups = [group for values in role_groups.values() for group in values]
    no_group_leakage = len(all_role_groups) == len(set(all_role_groups))
    rams_groups = {groups[document.document_id] for document in rams}
    wiki_groups = {groups[document.document_id] for document in wikievents}
    cross_dataset_groups = rams_groups & wiki_groups
    eligible_shift_documents = sum(
        groups[document.document_id] not in cross_dataset_groups for document in wikievents
    )
    minimum_n = scorc_minimum_n(candidate_count=9, delta=0.05, acceptance_floor=0.2)
    certification_n = len(role_groups["certification"])
    report = {
        "schema_version": "1",
        "status": "pass" if no_group_leakage and certification_n >= minimum_n else "revise",
        "private_manifest_sha256": manifest_hash,
        "private_manifest_verified_sha256": sha256_file(private_manifest),
        "role_group_counts": {role: len(values) for role, values in sorted(role_groups.items())},
        "role_document_counts": dict(sorted(Counter(roles.values()).items())),
        "duplicate_group_leakage": not no_group_leakage,
        "preferred_global_candidates": 9,
        "preferred_minimum_certification_groups": minimum_n,
        "cross_dataset_group_count": len(cross_dataset_groups),
        "wikievents_shift_documents_eligible": eligible_shift_documents,
        "wikievents_shift_documents_excluded_overlap": len(wikievents) - eligible_shift_documents,
    }
    digest = freeze_json(output, report)
    typer.echo(json.dumps({"output": str(output), "sha256": digest}, sort_keys=True))
    if report["status"] != "pass":
        raise typer.Exit(code=3)


@app.command("run-baseline")
def run_baseline() -> None:
    _not_ready("run-baseline")


@app.command("validate-certificate")
def validate_certificate(
    replicates: Annotated[int, typer.Option(min=1)] = 2000,
    seed: Annotated[int, typer.Option()] = 20260715,
    output: Annotated[Path, typer.Option()] = Path(
        "evidence/gate0/certificate_simulations.v2.json"
    ),
) -> None:
    """Run deterministic grouped coverage simulations and freeze the report."""

    from conformalextract.artifacts import freeze_json
    from conformalextract.simulation import run_gate0_simulations_v2

    report = run_gate0_simulations_v2(replicates=replicates, seed=seed)
    digest = freeze_json(output, report)
    typer.echo(json.dumps({"output": str(output), "sha256": digest}, sort_keys=True))
    if not report["coverage_pass"]:
        raise typer.Exit(code=3)


@app.command("gate0-smoke")
def gate0_smoke(
    metadata_root: Annotated[Path, typer.Option()] = Path("data/private/qwen-metadata"),
    output: Annotated[Path, typer.Option()] = Path("evidence/gate0/model_score_smoke.v2.json"),
) -> None:
    """Validate pinned tokenizer/runtime metadata and the completion-only score path."""

    from conformalextract.artifacts import freeze_json
    from conformalextract.model_smoke import validate_local_model_metadata

    report = validate_local_model_metadata(metadata_root)
    digest = freeze_json(output, report)
    typer.echo(json.dumps({"output": str(output), "sha256": digest}, sort_keys=True))
    if not report["gate0e_pass"]:
        raise typer.Exit(code=3)


@app.command("prepare-data")
def prepare_data(
    profiles: Annotated[
        Path, typer.Option(help="Private text-free trigger-frame profiles.")
    ] = Path("data/private/plan2/example_profiles.jsonl"),
    split_assignment: Annotated[
        Path, typer.Option(help="Private metadata-only grouped role assignment.")
    ] = Path("data/private/splits/rams_roles.jsonl"),
    source_contract: Annotated[
        Path, typer.Option(help="Official ephemeral-download and checksum contract.")
    ] = Path("configs/plan2_sources.json"),
    prompt_template: Annotated[Path, typer.Option()] = Path("docs/gate0/prompt-template.md"),
    demonstrations: Annotated[Path, typer.Option()] = Path(
        "data/private/plan2/fs_demonstrations.jsonl"
    ),
    model_config: Annotated[Path, typer.Option()] = Path("configs/model.json"),
    output_dir: Annotated[Path, typer.Option()] = Path("manifests/plan2"),
) -> None:
    """Freeze role-bound, text-free Plan 2 preparation manifests."""

    from conformalextract.preparation import freeze_preparation_manifests

    hashes = freeze_preparation_manifests(
        profiles_path=profiles,
        split_assignment_path=split_assignment,
        source_contract_path=source_contract,
        prompt_template_path=prompt_template,
        demonstrations_path=demonstrations,
        model_config_path=model_config,
        output_dir=output_dir,
    )
    typer.echo(json.dumps({"output_dir": str(output_dir), "sha256": hashes}, sort_keys=True))


@app.command("build-profiles")
def build_profiles_command(
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    roles: Annotated[Path, typer.Option()] = Path("data/private/splits/rams_roles.jsonl"),
    tokenizer_dir: Annotated[Path, typer.Option()] = Path("data/private/qwen-metadata"),
    prompt_template: Annotated[Path, typer.Option()] = Path("docs/gate0/prompt-template.md"),
    output: Annotated[Path, typer.Option()] = Path("data/private/plan2/example_profiles.jsonl"),
) -> None:
    """Generate the text-free example_profiles.jsonl from raw RAMS (CPU, no upload)."""

    from conformalextract.profiles import (
        build_profiles,
        load_prompt_template,
        load_role_map,
        qwen_token_counter,
        read_ontology,
        read_rams_instances,
        write_profiles,
    )

    instances = read_rams_instances(rams_archive)
    ontology = read_ontology(rams_archive)
    role_map = load_role_map(roles)
    template = load_prompt_template(prompt_template)
    profiles, summary = build_profiles(
        instances=instances, role_map=role_map, ontology=ontology, template=template,
        count_tokens=qwen_token_counter(tokenizer_dir),
    )
    write_profiles(profiles, output)
    typer.echo(
        json.dumps(
            {"output": str(output), "emitted": summary.emitted,
             "sealed_dropped": summary.sealed_dropped, "total": summary.total},
            sort_keys=True,
        )
    )


for command_name in (
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
