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
    import math

    from conformalextract.certification import base_risk_feasibility, minimum_abstention
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
        scores_by_candidate: dict[str, list[float]] = {c: [] for c in CONFIDENCE_CANDIDATES}
        for p in development_predictions:
            candidates = confidence_by_document.get(p.document_id)
            for candidate in CONFIDENCE_CANDIDATES:
                scores_by_candidate[candidate].append(
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
        # Per-system selection (reviewer Phase-A ruling 1a): the confidence score is part of
        # each system's own selective policy, so each system freezes its own candidate. A
        # pooled ranking mixes raw logprobs across systems whose scales differ by ~2.4 nats
        # and corresponds to no deployable policy.
        selection = select_confidence_candidate(
            scores_by_candidate=scores_by_candidate, development_losses=losses
        )
        risk = base_risk_feasibility(losses, alpha=alpha, acceptance_floor=acceptance_floor)
        # Two-directional robustness: the committed verdict uses the Hoeffding UPPER bound,
        # which inflates risk and so makes near_vacuous MORE likely -- the anti-conservative
        # direction for declaring a system hopeless. Re-check at the LOWER bound, i.e. the
        # reading most favourable to the system.
        radius = math.sqrt(math.log(2.0 / 0.05) / (2.0 * len(losses)))
        favourable_risk = max(0.0, risk.base_risk - radius)
        favourable_max_acceptance = 1.0 - minimum_abstention(
            base_risk=favourable_risk, alpha=alpha
        )
        per_system[system_id] = {
            "n_documents": len(development_predictions),
            "selected_candidate": selection.selected,
            "auc_by_candidate": selection.auc_by_candidate,
            "base_risk": risk.base_risk,
            "base_risk_upper": risk.base_risk_upper,
            "minimum_abstention": risk.minimum_abstention,
            "max_feasible_acceptance": risk.max_feasible_acceptance,
            "floor_reachable": risk.floor_reachable,
            "verdict": risk.verdict,
            "favourable_bound_check": {
                "base_risk_lower": favourable_risk,
                "max_feasible_acceptance": favourable_max_acceptance,
                "floor_reachable": favourable_max_acceptance >= acceptance_floor,
            },
        }

    label_access = build_label_access_log(access_requests)
    if not label_access.verify():
        raise RuntimeError("development label-access log failed to verify")
    result = {
        "alpha": alpha,
        "acceptance_floor": acceptance_floor,
        "selection_scope": "per_system",
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
    development_gate: Annotated[Path, typer.Option()] = Path(
        "evidence/plan2/development_gate_summary.json"
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
    # Each system's own frozen candidate (reviewer Phase-A ruling 1a): the score is part of
    # that system's selective policy, so its grid is built from the score it actually deploys.
    gate = json.loads(development_gate.read_text(encoding="utf-8"))
    if gate.get("selection_scope") != "per_system":
        raise RuntimeError(
            "development gate must record per-system selection before grids are built"
        )

    grids: dict[str, object] = {}
    for system_id in ("zs", "fs", "qa"):
        candidate = str(gate["per_system"][system_id]["selected_candidate"])
        raw_records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
        development_scores: list[float] = []
        for record in raw_records:
            if record["role"] != "development":
                continue
            candidates = record.get("confidence_candidates")
            if isinstance(candidates, dict):
                development_scores.append(float(candidates[candidate]))
            else:
                development_scores.append(float("-inf"))  # failures: worst-confidence treatment
        grid = build_threshold_grid(
            system_id,
            development_scores,
            grid_size=grid_size,
            n_groups=n_certification_groups,
            delta=delta,
            acceptance_floor=acceptance_floor,
        )
        grids[system_id] = {
            "confidence_candidate": candidate,
            "grid_hash": grid.grid_hash,
            "requested_grid_size": grid.requested_grid_size,
            "realized_certifiable_size": grid.realized_certifiable_size,
            "non_finite_scores": grid.non_finite_scores,
            "certifiable_thresholds": [
                "-inf" if t == float("-inf") else t for t in grid.certifiable_thresholds()
            ],
        }

    result = {
        "delta": delta,
        "acceptance_floor": acceptance_floor,
        "n_certification_groups": n_certification_groups,
        "theorem_max_grid_size": grid_size,
        "grids": grids,
    }
    grid_out.parent.mkdir(parents=True, exist_ok=True)
    grid_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps({"grid_out": str(grid_out), **result}, sort_keys=True))


@app.command("certify")
def certify_command(
    predictions_dir: Annotated[Path, typer.Option()] = Path("data/private/plan2/predictions"),
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    role_map: Annotated[Path, typer.Option()] = Path("data/private/splits/rams_roles.jsonl"),
    grids: Annotated[Path, typer.Option()] = Path("evidence/plan2/threshold_grids.json"),
    development_gate: Annotated[Path, typer.Option()] = Path(
        "evidence/plan2/development_gate_summary.json"
    ),
    aggregation_adr: Annotated[Path, typer.Option()] = Path(
        "docs/adr/0009-within-group-aggregation.md"
    ),
    result_out: Annotated[Path, typer.Option()] = Path("evidence/plan3/certification_result.json"),
    i_have_reviewer_approval: Annotated[
        bool,
        typer.Option(
            "--i-have-reviewer-approval",
            help="Required. Confirms ADR 0009 has an independent reviewer PASS.",
        ),
    ] = False,
) -> None:
    """Open the sealed certification split ONCE and write the immutable §7.4 certificate.

    This is the only irreversible command in Plan 3. It refuses to run unless ADR 0009
    (within-group aggregation) records an accepted status **and** the operator passes
    ``--i-have-reviewer-approval`` -- the aggregation rule materially determines the
    certificate, so it may not be chosen by code alone.
    """

    import hashlib

    from conformalextract.certification import (
        FROZEN_ACCEPTANCE_FLOOR,
        FROZEN_ALPHA,
        FROZEN_DELTA,
        FROZEN_MATERIAL_GAIN,
    )
    from conformalextract.certification_run import (
        aggregate_to_groups,
        build_certification_access_log,
        certification_artifact,
        run_certification,
    )
    from conformalextract.contracts import Argument, EventFrame, Span
    from conformalextract.development_gate import document_loss
    from conformalextract.predictions import (
        build_document_contexts,
        parse_arm,
        read_prediction_jsonl,
    )
    from conformalextract.profiles import RamsInstance, read_ontology, read_rams_instances

    # --- Gate: the aggregation rule must be reviewed before sealed labels open -----------
    adr_text = aggregation_adr.read_text(encoding="utf-8")
    # Tolerate markdown emphasis around the status word ("- Status: **accepted**"), but still
    # require an explicit accepted marker plus the reviewer record that authorises it.
    adr_status_line = next(
        (line for line in adr_text.splitlines() if line.startswith("- Status:")), ""
    )
    adr_accepted = "accepted" in adr_status_line.replace("*", "").lower() and (
        "reviewer_record.adr-0009.json" in adr_text
    )
    if not (adr_accepted and i_have_reviewer_approval):
        typer.echo(
            json.dumps(
                {
                    "status": "refused",
                    "reason": "ADR 0009 (within-group aggregation) is not cleared for execution",
                    "adr_status_accepted": adr_accepted,
                    "operator_flag_passed": i_have_reviewer_approval,
                    "sealed_labels_opened": False,
                },
                sort_keys=True,
            )
        )
        raise typer.Exit(code=3)

    gate = json.loads(development_gate.read_text(encoding="utf-8"))
    grid_data = json.loads(grids.read_text(encoding="utf-8"))
    delta = float(grid_data["delta"])
    allocation = {system_id: delta for system_id in ("zs", "fs", "qa")}
    if abs(sum(allocation.values()) - FROZEN_DELTA) > 1e-9:
        raise RuntimeError(
            f"grids were built at delta={delta}; the three-way split must exhaust "
            f"delta={FROZEN_DELTA}. Rebuild grids at delta/3 before certifying."
        )

    instances = {i.instance_key: i for i in read_rams_instances(rams_archive)}
    contexts = build_document_contexts(list(instances.values()), read_ontology(rams_archive))
    groups: dict[str, str] = {}
    for line in role_map.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["role"] == "certification":
            groups[str(record["document_id"])] = str(record["group_id"])

    def gold_frames(instance: RamsInstance) -> list[EventFrame]:
        tokens = instance.tokens
        return [
            EventFrame(
                document_id=instance.instance_key,
                event_type=instance.event_type,
                trigger=Span(
                    start=instance.trigger_start,
                    end=instance.trigger_end,
                    text=" ".join(tokens[instance.trigger_start : instance.trigger_end]),
                ),
                arguments=[
                    Argument(
                        role=argument.role,
                        span=Span(
                            start=argument.start,
                            end=argument.end,
                            text=" ".join(tokens[argument.start : argument.end]),
                        ),
                    )
                    for argument in instance.arguments
                ],
            )
        ]

    access_log = build_certification_access_log(sorted(groups))  # THE sealed read, audited
    rows_by_system, thresholds_by_system, candidates_by_system = {}, {}, {}
    for system_id in ("zs", "fs", "qa"):
        candidate = str(gate["per_system"][system_id]["selected_candidate"])
        raw_records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
        parsed, _ = parse_arm(raw_records, contexts, confidence_candidate=candidate)
        confidence: dict[object, object] = {
            r["instance_key"]: r["confidence_candidates"] for r in raw_records
        }

        def score_of(
            document_id: str,
            candidate: str = candidate,
            confidence: dict[object, object] = confidence,
        ) -> float:
            candidates = confidence.get(document_id)
            # Failures carry no candidates: frozen worst-confidence treatment (plan §5.3).
            if isinstance(candidates, dict):
                return float(candidates[candidate])
            return float("-inf")

        certification_predictions = [p for p in parsed if p.document_id in groups]
        rows_by_system[system_id] = aggregate_to_groups(
            document_ids=[p.document_id for p in certification_predictions],
            group_by_document=groups,
            score_by_document={
                p.document_id: score_of(p.document_id) for p in certification_predictions
            },
            valid_by_document={
                p.document_id: p.status == "valid" for p in certification_predictions
            },
            loss_by_document={
                p.document_id: document_loss(gold_frames(instances[p.document_id]), p)
                for p in certification_predictions
            },
        )
        thresholds_by_system[system_id] = [
            float("-inf") if t == "-inf" else float(t)
            for t in grid_data["grids"][system_id]["certifiable_thresholds"]
        ]
        candidates_by_system[system_id] = candidate

    run = run_certification(
        rows_by_system=rows_by_system,
        thresholds_by_system=thresholds_by_system,
        candidates_by_system=candidates_by_system,
        delta_allocation=allocation,
        access_log=access_log,
        alpha=FROZEN_ALPHA,
        delta=FROZEN_DELTA,
        acceptance_floor=FROZEN_ACCEPTANCE_FLOOR,
        material_gain=FROZEN_MATERIAL_GAIN,
    )
    artifact = certification_artifact(
        run,
        provenance={
            "alpha": FROZEN_ALPHA,
            "delta": FROZEN_DELTA,
            "acceptance_floor": FROZEN_ACCEPTANCE_FLOOR,
            "material_gain": FROZEN_MATERIAL_GAIN,
            "delta_allocation": allocation,
            "primary_construction": "scorc_union_bound",
            "grid_hashes": {s: grid_data["grids"][s]["grid_hash"] for s in ("zs", "fs", "qa")},
            "n_certification_groups": len(rows_by_system["qa"]),
        },
    )
    if result_out.exists():
        raise RuntimeError(f"certification result already exists and is immutable: {result_out}")
    result_out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    result_out.write_text(payload, encoding="utf-8")
    typer.echo(
        json.dumps(
            {
                "result": str(result_out),
                "sha256": hashlib.sha256(payload.encode()).hexdigest(),
                "h1": run.h1.outcome,
                "h2": run.h2.outcome,
                "collapsed": run.hypotheses_collapsed,
            },
            sort_keys=True,
        )
    )


@app.command("risk-coverage-diagnostic")
def risk_coverage_diagnostic_command(
    predictions_dir: Annotated[Path, typer.Option()] = Path("data/private/plan2/predictions"),
    rams_archive: Annotated[Path, typer.Option()] = Path("data/raw/rams/RAMS_1.0c.tar.gz"),
    role_map: Annotated[Path, typer.Option()] = Path("data/private/splits/rams_roles.jsonl"),
    development_gate: Annotated[Path, typer.Option()] = Path(
        "evidence/plan2/development_gate_summary.json"
    ),
    roles: Annotated[str, typer.Option(help="Comma-separated split roles.")] = (
        "development,certification"
    ),
    out: Annotated[Path, typer.Option()] = Path("evidence/plan3/risk_coverage_diagnostic.json"),
) -> None:
    """Oracle risk-coverage frontier per system and split — DIAGNOSTIC, certifies nothing.

    Answers the question that decides how the certification result must be reported: is
    infeasibility a capability gap or an artifact of the grid/bounds? Applies no finite-sample
    penalty, no grid and no multiplicity correction, so if the acceptance floor is unreachable
    here it is unreachable by any threshold rule.

    Run it on ``development`` **before** certifying: it settles feasibility at $0 with no sealed
    access, which the base-risk ceiling `(1-r)/(1-alpha)` does not (that ceiling assumes an
    oracle score; see ADR 0007's recorded miss).
    """

    from conformalextract.certification import FROZEN_ACCEPTANCE_FLOOR, FROZEN_ALPHA
    from conformalextract.certification_run import aggregate_to_groups, risk_coverage_frontier
    from conformalextract.contracts import Argument, EventFrame, Span
    from conformalextract.development_gate import document_loss
    from conformalextract.predictions import (
        build_document_contexts,
        parse_arm,
        read_prediction_jsonl,
    )
    from conformalextract.profiles import RamsInstance, read_ontology, read_rams_instances

    gate = json.loads(development_gate.read_text(encoding="utf-8"))
    instances = {i.instance_key: i for i in read_rams_instances(rams_archive)}
    contexts = build_document_contexts(list(instances.values()), read_ontology(rams_archive))
    assignments = [json.loads(line) for line in role_map.read_text(encoding="utf-8").splitlines()]

    def gold_frames(instance: RamsInstance) -> list[EventFrame]:
        tokens = instance.tokens
        return [
            EventFrame(
                document_id=instance.instance_key,
                event_type=instance.event_type,
                trigger=Span(
                    start=instance.trigger_start,
                    end=instance.trigger_end,
                    text=" ".join(tokens[instance.trigger_start : instance.trigger_end]),
                ),
                arguments=[
                    Argument(
                        role=a.role,
                        span=Span(
                            start=a.start, end=a.end, text=" ".join(tokens[a.start : a.end])
                        ),
                    )
                    for a in instance.arguments
                ],
            )
        ]

    result: dict[str, object] = {
        "diagnostic_only": True,
        "certifies_nothing": True,
        "alpha": FROZEN_ALPHA,
        "acceptance_floor": FROZEN_ACCEPTANCE_FLOOR,
        "splits": {},
    }
    for split_role in [r.strip() for r in roles.split(",") if r.strip()]:
        groups = {
            str(a["document_id"]): str(a["group_id"])
            for a in assignments
            if a["role"] == split_role
        }
        per_system: dict[str, object] = {}
        for system_id in ("zs", "fs", "qa"):
            candidate = str(gate["per_system"][system_id]["selected_candidate"])
            raw_records = read_prediction_jsonl(predictions_dir / f"{system_id}.v1.jsonl")
            parsed, _ = parse_arm(raw_records, contexts, confidence_candidate=candidate)
            confidence: dict[object, object] = {
                r["instance_key"]: r["confidence_candidates"] for r in raw_records
            }

            def score_of(
                document_id: str,
                candidate: str = candidate,
                confidence: dict[object, object] = confidence,
            ) -> float:
                candidates = confidence.get(document_id)
                if isinstance(candidates, dict):
                    return float(candidates[candidate])
                return float("-inf")

            selected = [p for p in parsed if p.document_id in groups]
            rows = aggregate_to_groups(
                document_ids=[p.document_id for p in selected],
                group_by_document=groups,
                score_by_document={p.document_id: score_of(p.document_id) for p in selected},
                valid_by_document={p.document_id: p.status == "valid" for p in selected},
                loss_by_document={
                    p.document_id: document_loss(gold_frames(instances[p.document_id]), p)
                    for p in selected
                },
            )
            frontier = risk_coverage_frontier(
                rows, alpha=FROZEN_ALPHA, acceptance_floor=FROZEN_ACCEPTANCE_FLOOR
            )
            per_system[system_id] = {
                "confidence_candidate": candidate,
                "eligible_groups": frontier.eligible_groups,
                "total_groups": frontier.total_groups,
                "risk_at_floor_acceptance": frontier.risk_at_floor_acceptance,
                "max_acceptance_within_alpha": frontier.max_acceptance_within_alpha,
                "floor_reachable": frontier.floor_reachable,
            }
        result["splits"][split_role] = per_system  # type: ignore[index]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps({"out": str(out), **result}, sort_keys=True))


@app.command("verify-claims")
def verify_claims_command(
    ledger_path: Annotated[Path, typer.Option("--ledger")] = Path(
        "evidence/plan4/claim_ledger.json"
    ),
    root: Annotated[Path, typer.Option()] = Path("."),
    surface: Annotated[str | None, typer.Option(help="Render approved prose for one surface.")] = (
        None
    ),
) -> None:
    """Validate the Plan 4 claim ledger (§3.4) and resolve every cited evidence path.

    Exits non-zero if anything would block publication: an unresolvable evidence path, a
    `planned`/`failed` claim on a public surface, a public claim without limitations, or a
    forbidden wording. Public prose is rendered from approved sentences, never rewritten.
    """

    from conformalextract.claims import load_ledger, render_surface, verify_ledger

    ledger = load_ledger(ledger_path)  # model validation raises on any rule violation
    report = verify_ledger(ledger, root=root)
    if surface:
        typer.echo(render_surface(ledger, surface))
        return
    typer.echo(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise typer.Exit(code=1)


@app.command("hash-file")
def hash_file(path: Path) -> None:
    """Print a local artifact SHA-256 without reading it into a report."""

    from conformalextract.artifacts import sha256_file

    typer.echo(sha256_file(path))
