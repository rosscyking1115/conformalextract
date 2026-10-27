r"""Run the §3.2 input preflight, after the fact, on the inputs the 2026-07-22 certificate used.

**Why.** Plan 3 §3.2 required a preflight before the certification labels were read. The function
existed and was tested, but ``certify`` never called it (independent review 2026-10-27, finding
B1), so the one run that opened the sealed split did so without it. That cannot be undone. What
can be established is whether the inputs that run used would have passed the checks a run-time
preflight can make, and that is what this script records.

**What it reads, and what it does not.** The three prediction files and the role map, as files:
their SHA-256, each prediction record's ``instance_key``, and each role-map record's role and
group. No prediction text is kept or printed. **The RAMS archive is not opened and no gold is
read**, so no split is touched and the label-access record is unchanged.

**What a pass does not show.** It cannot show the preflight ran on 2026-07-22, because it did not.
It shows that the inputs, which are hash-identical to the ones the certificate recorded, satisfy
the checkable preconditions. The two bullets a run-time check cannot discharge are carried on
the artifact as ``not_checked_at_run_time``.

**Cost: $0.** CPU only, no network.

Usage::

    uv run python scripts/certification_preflight_retrospective.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from conformalextract.certification_preflight import (
    CertificationPreflightError,
    run_certification_input_preflight,
)
from conformalextract.predictions import read_prediction_jsonl

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "data" / "private" / "plan2" / "predictions"
ROLE_MAP = ROOT / "data" / "private" / "splits" / "rams_roles.jsonl"
FROZEN = ROOT / "manifests" / "plan3" / "certification_inputs.json"
GRIDS = ROOT / "evidence" / "plan2" / "threshold_grids.json"
GATE = ROOT / "evidence" / "plan2" / "development_gate_summary.json"
OUT = ROOT / "evidence" / "plan3" / "certification_preflight_retrospective.json"
SYSTEMS = ("zs", "fs", "qa")


def main() -> int:
    paths = {s: PREDICTIONS / f"{s}.v1.jsonl" for s in SYSTEMS}
    roles: dict[str, tuple[str, str]] = {}
    for line in ROLE_MAP.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            roles[str(record["document_id"])] = (str(record["role"]), str(record["group_id"]))
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    prediction_sha256 = {s: hashlib.sha256(p.read_bytes()).hexdigest() for s, p in paths.items()}
    document_ids = {
        s: frozenset(str(r["instance_key"]) for r in read_prediction_jsonl(p))
        for s, p in paths.items()
    }
    role_map_sha256 = hashlib.sha256(ROLE_MAP.read_bytes()).hexdigest()
    role_counts: dict[str, int] = {}
    for role, _ in roles.values():
        role_counts[role] = role_counts.get(role, 0) + 1
    outcome: dict[str, object]
    try:
        result = run_certification_input_preflight(
            prediction_sha256=prediction_sha256,
            prediction_document_ids=document_ids,
            role_map_sha256=role_map_sha256,
            roles=roles,
            grids=json.loads(GRIDS.read_text(encoding="utf-8")),
            selected_candidates={
                s: str(gate["per_system"][s]["selected_candidate"]) for s in SYSTEMS
            },
            frozen=json.loads(FROZEN.read_text(encoding="utf-8")),
        )
        outcome = {
            "status": result.status,
            "certification_documents": result.certification_documents,
            "certification_groups": result.certification_groups,
            "not_checked_at_run_time": dict(result.not_checked_at_run_time),
        }
    except CertificationPreflightError as error:
        outcome = {"status": "failed", "failure": str(error)}
    artifact = {
        "schema_version": "1",
        "_notice": (
            "Retrospective: the section 3.2 input preflight run on 2026-10-27 over the inputs the "
            "2026-07-22 certificate used. It did NOT run on 2026-07-22; certify never called it "
            "(independent review 2026-10-27, B1). Label-free: the RAMS archive was not opened and "
            "no gold was read. Produced by scripts/certification_preflight_retrospective.py."
        ),
        "inputs_sha256": {
            **{f"{s}.v1.jsonl": prediction_sha256[s] for s in SYSTEMS},
            "rams_roles.jsonl": role_map_sha256,
        },
        "role_map_records_by_role": dict(sorted(role_counts.items())),
        "prediction_records_by_system": {s: len(document_ids[s]) for s in SYSTEMS},
        "preflight": outcome,
        "certification_access": {"archive_opened": False, "gold_read": False},
    }
    OUT.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "preflight": outcome["status"]}))
    return 0 if outcome["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
