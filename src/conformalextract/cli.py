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


@app.command("freeze-demonstrations")
def freeze_demonstrations_command(
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    roles: Annotated[Path, typer.Option()] = Path("data/private/splits/rams_roles.jsonl"),
    prompt_template: Annotated[Path, typer.Option()] = Path("docs/gate0/prompt-template.md"),
    output: Annotated[Path, typer.Option()] = Path("data/private/plan2/fs_demonstrations.jsonl"),
) -> None:
    """Freeze the two FS demonstrations (train-only; multi-arg + empty-gold; deterministic)."""

    from conformalextract.artifacts import sha256_file
    from conformalextract.profiles import (
        load_prompt_template,
        load_role_map,
        read_ontology,
        read_rams_instances,
        render_demonstrations,
        select_fs_demonstrations,
        write_demonstrations,
    )

    pair = select_fs_demonstrations(read_rams_instances(rams_archive), load_role_map(roles))
    demonstrations = render_demonstrations(
        pair,
        ontology=read_ontology(rams_archive),
        template=load_prompt_template(prompt_template),
    )
    write_demonstrations(demonstrations, output)
    typer.echo(
        json.dumps(
            {
                "output": str(output),
                "demonstration_ids": [d.demonstration_id for d in demonstrations],
                "sha256": sha256_file(output),
            },
            sort_keys=True,
        )
    )


for command_name in (
    "train",
    "generate-predictions",
    "freeze-systems",
    "certify",
    "evaluate-final",
    "evaluate-shift",
    "render-report",
    "verify-release",
):
    app.command(command_name)(lambda name=command_name: _not_ready(name))


@app.command("parse-predictions")
def parse_predictions_command(
    predictions_dir: Annotated[Path, typer.Option()] = Path("data/private/plan2/predictions"),
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    summary_out: Annotated[Path, typer.Option()] = Path(
        "evidence/plan2/prediction_parse_summary.json"
    ),
    systems: Annotated[str, typer.Option(help="Comma-separated system ids.")] = "zs,fs,qa",
) -> None:
    """Parse generated predictions under the ADR 0006 policy; emit a text-free summary.

    Grounding validates spans against source document tokens, so no gold label is read and
    every split — including the sealed ones — is safe to parse here.
    """

    from conformalextract.predictions import (
        build_document_contexts,
        parse_arm,
        read_prediction_jsonl,
    )
    from conformalextract.profiles import read_ontology, read_rams_instances

    contexts = build_document_contexts(
        read_rams_instances(rams_archive), read_ontology(rams_archive)
    )
    summaries = {}
    for system_id in [s.strip() for s in systems.split(",") if s.strip()]:
        records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
        _, summary = parse_arm(records, contexts)
        summaries[system_id] = summary.as_dict()
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(
        json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    typer.echo(json.dumps({"summary": str(summary_out), "systems": summaries}, sort_keys=True))


@app.command("development-gate")
def development_gate_command(
    predictions_dir: Annotated[Path, typer.Option()] = Path("data/private/plan2/predictions"),
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    alpha: Annotated[float, typer.Option()] = 0.20,  # ADR 0007 freeze (certification.FROZEN_ALPHA)
    acceptance_floor: Annotated[float, typer.Option()] = 0.20,  # ADR 0007 (FROZEN_ACCEPTANCE_FLOOR)
    summary_out: Annotated[Path, typer.Option()] = Path(
        "evidence/plan2/development_gate_summary.json"
    ),
) -> None:
    """Select the primary confidence candidate and check base-risk feasibility (Plan 3 Gate 0).

    Pools ZS/FS/QA development documents into ONE risk-coverage AUC selection (the same
    fairness rule ADR 0006 established for the extraction policy: one rule applied uniformly,
    not each system picking its own best-looking score), then reports each system's
    development-split base-risk feasibility at the given alpha/floor. Development gold is not
    sealed but every read is still purpose-authorized and hash-chained
    (``LabelAccessPurpose.DEVELOPMENT_SELECTION``); certification/final/shift gold is never
    reachable from this command.
    """

    import hashlib

    from conformalextract.certification import base_risk_feasibility
    from conformalextract.contracts import Argument, EventFrame, Span
    from conformalextract.development_gate import CONFIDENCE_CANDIDATES, document_loss
    from conformalextract.predictions import (
        build_document_contexts,
        parse_arm,
        read_prediction_jsonl,
    )
    from conformalextract.profiles import RamsInstance, read_ontology, read_rams_instances
    from conformalextract.selection import select_confidence_candidate
    from conformalextract.training import (
        LabelAccessPurpose,
        LabelAccessRequest,
        build_label_access_log,
    )

    instances = {
        instance.instance_key: instance for instance in read_rams_instances(rams_archive)
    }
    contexts = build_document_contexts(list(instances.values()), read_ontology(rams_archive))

    def gold_frames(instance: RamsInstance) -> list[EventFrame]:
        tokens = instance.tokens
        arguments = [
            Argument(
                role=argument.role,
                span=Span(
                    start=argument.start,
                    end=argument.end,
                    text=" ".join(tokens[argument.start : argument.end]),
                ),
            )
            for argument in instance.arguments
        ]
        return [
            EventFrame(
                document_id=instance.instance_key,
                event_type=instance.event_type,
                trigger=Span(
                    start=instance.trigger_start,
                    end=instance.trigger_end,
                    text=" ".join(tokens[instance.trigger_start : instance.trigger_end]),
                ),
                arguments=arguments,
            )
        ]

    pooled_scores: dict[str, list[float]] = {c: [] for c in CONFIDENCE_CANDIDATES}
    pooled_losses: list[float] = []
    access_requests: list[LabelAccessRequest] = []
    per_system: dict[str, dict[str, object]] = {}

    for system_id in ("zs", "fs", "qa"):
        raw_records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
        parsed, _ = parse_arm(raw_records, contexts)
        role_by_document = {r["instance_key"]: r["role"] for r in raw_records}
        confidence_by_document: dict[object, dict[str, float] | None] = {
            r["instance_key"]: r["confidence_candidates"]  # type: ignore[misc]
            for r in raw_records
        }
        development_predictions = [
            p for p in parsed if role_by_document.get(p.document_id) == "development"
        ]
        losses = [
            document_loss(gold_frames(instances[p.document_id]), p)
            for p in development_predictions
        ]
        for p, loss in zip(development_predictions, losses, strict=True):
            pooled_losses.append(loss)
            candidates = confidence_by_document.get(p.document_id)
            for candidate in CONFIDENCE_CANDIDATES:
                pooled_scores[candidate].append(
                    candidates[candidate] if candidates is not None else float("-inf")
                )
            access_requests.append(
                LabelAccessRequest(
                    data_role="development",
                    document_id_hash=hashlib.sha256(
                        f"{system_id}:{p.document_id}".encode()
                    ).hexdigest(),
                    purpose=LabelAccessPurpose.DEVELOPMENT_SELECTION,
                )
            )
        risk = base_risk_feasibility(losses, alpha=alpha, acceptance_floor=acceptance_floor)
        per_system[system_id] = {
            "n_documents": len(development_predictions),
            "base_risk": risk.base_risk,
            "base_risk_upper": risk.base_risk_upper,
            "minimum_abstention": risk.minimum_abstention,
            "max_feasible_acceptance": risk.max_feasible_acceptance,
            "floor_reachable": risk.floor_reachable,
            "verdict": risk.verdict,
        }

    label_access = build_label_access_log(access_requests)
    if not label_access.verify():
        raise RuntimeError("development label-access log failed to verify")
    pooled_selection = select_confidence_candidate(
        scores_by_candidate=pooled_scores, development_losses=pooled_losses
    )
    result = {
        "alpha": alpha,
        "acceptance_floor": acceptance_floor,
        "pooled_selection": {
            "selected": pooled_selection.selected,
            "auc_by_candidate": pooled_selection.auc_by_candidate,
            "n_pooled_documents": len(pooled_losses),
        },
        "per_system": per_system,
        "label_access_head_hash": label_access.head_hash,
        "label_access_entries": len(label_access.entries),
    }
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps({"summary": str(summary_out), **result}, sort_keys=True))


@app.command("build-grid")
def build_grid_command(
    predictions_dir: Annotated[Path, typer.Option()] = Path("data/private/plan2/predictions"),
    split_manifest: Annotated[Path, typer.Option()] = Path(
        "manifests/plan2/split_manifest.json"
    ),
    delta: Annotated[float, typer.Option()] = 0.05,  # ADR 0007 (certification.FROZEN_DELTA)
    acceptance_floor: Annotated[float, typer.Option()] = 0.20,  # ADR 0007
    grid_out: Annotated[Path, typer.Option()] = Path("evidence/plan2/threshold_grids.json"),
) -> None:
    """Build and commit each system's §5.4 threshold grid from development scores only.

    Development-only (plan §13.1): reads the frozen ``minimum`` confidence candidate (ADR 0007)
    for each system's development-split documents, builds a theorem-sized quantile grid plus
    boundary policies, and writes committable grid hashes. No certification/final/shift label
    is touched; grid size is the theorem-eligible maximum for the certification split's
    independent-group count, a feasibility choice not a performance one.
    """

    from conformalextract.predictions import read_prediction_jsonl
    from conformalextract.threshold_grid import build_threshold_grid, theorem_max_grid_size

    split = json.loads(split_manifest.read_text(encoding="utf-8"))
    n_certification_groups = int(split["role_group_counts"]["certification"])
    grid_size = theorem_max_grid_size(
        n_groups=n_certification_groups, delta=delta, acceptance_floor=acceptance_floor
    )

    grids: dict[str, object] = {}
    for system_id in ("zs", "fs", "qa"):
        raw_records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
        # Frozen candidate = "minimum" (ADR 0007). Failures carry no candidates -> -inf.
        development_scores: list[float] = []
        for record in raw_records:
            if record["role"] != "development":
                continue
            candidates = record.get("confidence_candidates")
            if isinstance(candidates, dict):
                development_scores.append(float(candidates["minimum"]))
            else:
                development_scores.append(float("-inf"))
        grid = build_threshold_grid(
            system_id,
            development_scores,
            grid_size=grid_size,
            n_groups=n_certification_groups,
            delta=delta,
            acceptance_floor=acceptance_floor,
        )
        grids[system_id] = {
            "grid_hash": grid.grid_hash,
            "requested_grid_size": grid.requested_grid_size,
            "realized_certifiable_size": grid.realized_certifiable_size,
            "non_finite_scores": grid.non_finite_scores,
            "certifiable_thresholds": [
                "-inf" if t == float("-inf") else t for t in grid.certifiable_thresholds()
            ],
        }

    result = {
        "confidence_candidate": "minimum",
        "delta": delta,
        "acceptance_floor": acceptance_floor,
        "n_certification_groups": n_certification_groups,
        "theorem_max_grid_size": grid_size,
        "grids": grids,
    }
    grid_out.parent.mkdir(parents=True, exist_ok=True)
    grid_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps({"grid_out": str(grid_out), **result}, sort_keys=True))


@app.command("hash-file")
def hash_file(path: Path) -> None:
    """Print a local artifact SHA-256 without reading it into a report."""

    from conformalextract.artifacts import sha256_file

    typer.echo(sha256_file(path))
